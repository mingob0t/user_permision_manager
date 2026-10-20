"""Alta de cuentas en OpenLDAP desde el portal (FNC-064).

Contrato: `POST /users/directory` en `docs/contratos/usuarios-directorio.md`.

- Permisos (P2): el superadmin y los admins de área; el admin solo para sus
  áreas (`area_ids` ajenas o inexistentes → 404, SEC-AUTHZ-03/04). El rol es
  siempre `usuario` (SEC-AUTHZ-05).
- Sin contraseña (P8, SEC-LDAP-09): la entrada nace sin `userPassword` y la
  cuenta del portal con `auth_source='ldap'` y `password_hash` NULL
  (SEC-AUTH-04); la contraseña la maneja Authelia.
- Orden: lista blanca y validación → duplicados en la BD → reserva del
  correo (fila de `users` sin confirmar; `users.email` UNIQUE serializa dos
  altas con el mismo correo) → `mail` en el directorio, justo antes de
  escribir → entrada en el directorio → `commit` de la cuenta. Si el
  directorio falla, se deshace la reserva: no queda nada en la BD.
- Fallo parcial (entrada creada, `commit` no): rollback, auditoría `warning`
  con el DN (entrada para revisión; sin borrado en v1) y `500 error_interno`.
  Un reintento da `409`; la persona queda registrada en el portal, como
  `usuario` sin áreas, en su primer login de directorio o SSO (por `mail`).
- Auditoría `cuenta_directorio_creada`: actor de la sesión; el éxito va en la
  misma transacción que la cuenta (SEC-AUD-06); los `409` como `warning`,
  los fallos del directorio como `error`.
"""
import logging
import re
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db
from app.authz import ROLE_USER, is_area_admin, managed_area_ids
from app.modules.api.crud import RESERVED_NAMES
from app.modules.api.helpers import NO_ENCONTRADO, is_id_list
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.auth.services import ORIGEN_DIRECTORIO, normalizar_correo
from app.modules.core.models import Area
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 directorio_activo)
from app.modules.directory.errors import Resultado
from app.modules.directory.ldap_client import ErrorDirectorio, PersonaAmbigua
from app.modules.directory.writer import (PATRON_CORREO, DatosCuenta,
                                          EscritorDirectorio)
from app.modules.users.areas_administradas import (CAMPO_AREAS,
                                                   validar_area_ids)
from app.modules.users.correos import correos_registrados
from app.modules.users.roles import MODULO_AUDITORIA
from app.utils.naming import _CONTROL as CARACTERES_DE_CONTROL
from app.utils.naming import sanitize_display_name

logger = logging.getLogger(__name__)

# Lista blanca del cuerpo (SEC-AUTHZ-09); cualquier otro campo, incluida
# `password`, es `400 campo_no_permitido`.
CAMPO_UID = 'uid'
CAMPO_CORREO = 'email'
CAMPO_NOMBRE = 'given_name'
CAMPO_APELLIDO = 'surname'
CAMPOS_PERMITIDOS = frozenset({CAMPO_UID, CAMPO_CORREO, CAMPO_NOMBRE,
                               CAMPO_APELLIDO, CAMPO_AREAS})

# Reglas del contrato. El correo además no supera la columna `users.email`.
MIN_UID = 3
MAX_UID = 64
PATRON_UID = re.compile(r'[a-z][a-z0-9._-]*')
MAX_CORREO_CONTRATO = 254
MAX_CORREO = min(MAX_CORREO_CONTRATO, User.__table__.c.email.type.length)
MIN_NOMBRE = 1
MAX_NOMBRE = 100

MENSAJE_OBLIGATORIO = 'Es obligatorio.'
MENSAJE_TEXTO = 'Debe ser texto.'
MENSAJE_UID = 'Usa minúsculas, números, punto, guion o guion bajo.'
MENSAJE_UID_LARGO = f'Entre {MIN_UID} y {MAX_UID} caracteres.'
MENSAJE_CORREO = 'Correo no válido.'
MENSAJE_CORREO_LARGO = f'Máximo {MAX_CORREO} caracteres.'
MENSAJE_NOMBRE_LARGO = f'Entre {MIN_NOMBRE} y {MAX_NOMBRE} caracteres.'
MENSAJE_NOMBRE_CONTROL = 'Contiene caracteres no permitidos.'
MENSAJE_AREAS_ADMIN = 'Indica al menos un área.'

# (mensaje, HTTP, code) del contrato.
UID_DUPLICADO = ('Ese identificador ya existe en el directorio o en el '
                 'portal.', 409, 'uid_duplicado')
CORREO_DUPLICADO = ('El correo ya está registrado.', 409, 'correo_duplicado')
DIRECTORIO_NO_DISPONIBLE = ('No se pudo crear la cuenta en el directorio; '
                            'intenta más tarde.', 503,
                            'directorio_no_disponible')
ERROR_INTERNO = ('Ocurrió un error. Intenta de nuevo.', 500, 'error_interno')

# Motivos para la auditoría y el log (sin datos de la persona).
MOTIVO_NO_CONFIGURADO = 'directorio_no_configurado'
MOTIVO_SIN_CONEXION = 'directorio_no_disponible'
MOTIVO_REGISTRO_PORTAL = 'registro_en_portal_fallido'
MOTIVO_REVISION = 'entrada_para_revision'
SISTEMA_DIRECTORIO = 'directorio'
SISTEMA_PORTAL = 'portal'


@dataclass(frozen=True)
class AltaDirectorio:
    """Datos validados de una cuenta nueva (sin contraseña)."""

    uid: str
    correo: str
    nombre: str
    apellido: str
    area_ids: tuple


def campos_no_permitidos(datos):
    """Campos del cuerpo fuera de la lista blanca, ordenados."""
    return sorted(set(datos) - CAMPOS_PERMITIDOS)


def _texto(datos, campo, errores):
    """Valor sin espacios de un campo de texto obligatorio, o `None`."""
    valor = datos.get(campo)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        errores[campo] = MENSAJE_OBLIGATORIO
        return None
    if not isinstance(valor, str):
        errores[campo] = MENSAJE_TEXTO
        return None
    return valor.strip()


def _validar_uid(uid, errores):
    if uid is None:
        return
    if not MIN_UID <= len(uid) <= MAX_UID:
        errores[CAMPO_UID] = MENSAJE_UID_LARGO
    elif not PATRON_UID.fullmatch(uid):
        errores[CAMPO_UID] = MENSAJE_UID


def _validar_correo(correo, errores):
    if correo is None:
        return
    if len(correo) > MAX_CORREO:
        errores[CAMPO_CORREO] = MENSAJE_CORREO_LARGO
    elif not (correo.isascii() and PATRON_CORREO.fullmatch(correo)):
        errores[CAMPO_CORREO] = MENSAJE_CORREO


def _validar_nombre(campo, valor, errores):
    if valor is None:
        return
    if not MIN_NOMBRE <= len(valor) <= MAX_NOMBRE:
        errores[campo] = MENSAJE_NOMBRE_LARGO
    elif CARACTERES_DE_CONTROL.search(valor):
        errores[campo] = MENSAJE_NOMBRE_CONTROL


def validar_alta(datos):
    """`(alta, error, fields)`: solo uno de los tres tiene valor.

    - `alta`: `AltaDirectorio` si el cuerpo es válido;
    - `error`: `NO_ENCONTRADO` si un admin pide áreas fuera de su alcance;
    - `fields`: detalle por campo del `422 validacion`.
    """
    errores = {}
    uid = _texto(datos, CAMPO_UID, errores)
    _validar_uid(uid, errores)
    correo = _texto(datos, CAMPO_CORREO, errores)
    correo = normalizar_correo(correo) if correo else correo
    _validar_correo(correo, errores)
    nombre = _texto(datos, CAMPO_NOMBRE, errores)
    _validar_nombre(CAMPO_NOMBRE, nombre, errores)
    apellido = _texto(datos, CAMPO_APELLIDO, errores)
    _validar_nombre(CAMPO_APELLIDO, apellido, errores)

    valor_areas = datos.get(CAMPO_AREAS, [])
    if is_area_admin():
        # Alcance antes que existencia: un área ajena o inexistente es 404
        # para el admin (no revela qué áreas existen).
        if (is_id_list(valor_areas)
                and set(valor_areas) - set(managed_area_ids())):
            return None, NO_ENCONTRADO, None
        if valor_areas == []:
            errores[CAMPO_AREAS] = MENSAJE_AREAS_ADMIN
    area_ids = []
    if CAMPO_AREAS not in errores:
        area_ids, problema = validar_area_ids(valor_areas)
        if problema:
            errores[CAMPO_AREAS] = problema

    if errores:
        return None, None, errores
    return AltaDirectorio(uid, correo, nombre, apellido,
                          tuple(area_ids)), None, None


def _uid_en_portal(uid):
    """El portal no guarda el uid: choca con un nombre reservado o con una
    cuenta heredada cuyo `email` es un identificador (p. ej. `admin`)."""
    if uid in RESERVED_NAMES:
        return True
    return User.query.filter(db.func.lower(User.email) == uid).first() \
        is not None


def _auditar(alta, status, detalle, cuenta=None, commit=True):
    despues = {'uid': alta.uid, 'role': ROLE_USER,
               'auth_source': ORIGEN_DIRECTORIO,
               'area_ids': list(alta.area_ids)}
    add_audit_log(Evento.CUENTA_DIRECTORIO_CREADA, status=status,
                  module=MODULO_AUDITORIA, target=alta.correo,
                  target_user_id=cuenta.id if cuenta else None,
                  detail=detalle, after=despues, commit=commit)


def _conflicto(alta, error):
    """Audita (aviso) un `409` y lo devuelve; la sesión ya está limpia."""
    _auditar(alta, 'warning', f'conflicto: {error[2]}')
    return None, error


def _descartar_reserva(alta, error, estado=None, detalle=None):
    """Deshace la reserva y, si se pide, audita el fallo."""
    db.session.rollback()
    if error[1] == 409:
        return _conflicto(alta, error)
    if estado:
        _auditar(alta, estado, detalle)
    return None, error


def _reservar_en_portal(alta):
    """Cuenta del portal sin confirmar: reserva el correo (`users.email`
    UNIQUE) y serializa las altas con el mismo correo hasta el `commit`."""
    cuenta = User(
        email=alta.correo,
        nombre=sanitize_display_name(f'{alta.nombre} {alta.apellido}',
                                     fallback=alta.correo),
        role=ROLE_USER,
        auth_source=ORIGEN_DIRECTORIO,
        is_active=True,
    )
    cuenta.password_hash = None
    cuenta.areas = (Area.query.filter(Area.id.in_(alta.area_ids)).all()
                    if alta.area_ids else [])
    db.session.add(cuenta)
    db.session.flush()
    return cuenta


def crear_cuenta_directorio(alta, escritor_factory=EscritorDirectorio):
    """Crea la entrada en OpenLDAP y la cuenta del portal.

    Orden: reserva del correo en la BD → `mail` en el directorio (justo antes
    de escribir) → entrada → `commit` de la cuenta y su auditoría.
    Devuelve `(cuenta, None)` o `(None, (mensaje, HTTP, code))`.
    """
    if _uid_en_portal(alta.uid):
        return _conflicto(alta, UID_DUPLICADO)
    if correos_registrados({alta.correo}):
        return _conflicto(alta, CORREO_DUPLICADO)

    if not directorio_activo():
        logger.error('Alta de cuenta: el directorio no está configurado')
        _auditar(alta, 'error', f'{SISTEMA_DIRECTORIO}: '
                 f'{MOTIVO_NO_CONFIGURADO}')
        return None, DIRECTORIO_NO_DISPONIBLE
    try:
        escritor = escritor_factory()
    except ErrorConfiguracionDirectorio as exc:
        logger.error('Directorio: configuración inválida: %s', exc)
        _auditar(alta, 'error', f'{SISTEMA_DIRECTORIO}: {MOTIVO_SIN_CONEXION}')
        return None, DIRECTORIO_NO_DISPONIBLE

    try:
        cuenta = _reservar_en_portal(alta)
    except IntegrityError:
        return _descartar_reserva(alta, CORREO_DUPLICADO)
    except SQLAlchemyError:
        logger.exception('Alta de cuenta: no se pudo reservar el correo')
        return _descartar_reserva(alta, ERROR_INTERNO)

    try:
        if escritor.cliente.buscar_por_correo(alta.correo) is not None:
            return _descartar_reserva(alta, CORREO_DUPLICADO)
    except PersonaAmbigua:
        return _descartar_reserva(alta, CORREO_DUPLICADO)
    except ErrorDirectorio:
        return _descartar_reserva(
            alta, DIRECTORIO_NO_DISPONIBLE, 'error',
            f'{SISTEMA_DIRECTORIO}: {MOTIVO_SIN_CONEXION}')

    resultado = escritor.create_user(DatosCuenta(
        identificador=alta.uid, nombre=alta.nombre, apellido=alta.apellido,
        correo=alta.correo))
    if resultado.resultado is Resultado.YA_ESTABA:
        return _descartar_reserva(alta, UID_DUPLICADO)
    if resultado.resultado is not Resultado.HECHO:
        return _descartar_reserva(
            alta, DIRECTORIO_NO_DISPONIBLE, 'error',
            f'{SISTEMA_DIRECTORIO}: {resultado.resultado.value} '
            f'({resultado.motivo or MOTIVO_SIN_CONEXION})')

    try:
        _auditar(alta, 'success',
                 f'Sistemas: {SISTEMA_DIRECTORIO} y {SISTEMA_PORTAL}',
                 cuenta=cuenta, commit=False)
        db.session.commit()
    except SQLAlchemyError:
        logger.exception('Alta de cuenta: la entrada quedó en el directorio '
                         'y falló el registro en el portal')
        try:
            # Sin borrado en v1: la entrada queda marcada para revisión.
            _descartar_reserva(
                alta, ERROR_INTERNO, 'warning',
                f'{SISTEMA_DIRECTORIO}: creada ({resultado.dn}); '
                f'{SISTEMA_PORTAL}: {MOTIVO_REGISTRO_PORTAL}; '
                f'{MOTIVO_REVISION}')
        except Exception:  # la auditoría no oculta la respuesta
            logger.exception('Alta de cuenta: no se pudo auditar el fallo')
        return None, ERROR_INTERNO
    return cuenta, None
