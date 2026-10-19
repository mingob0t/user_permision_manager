"""API v1 de plataformas: alta, edición, baja y usuarios asignados (FNC-046).

Contrato `docs/contratos/plataformas-integracion.md`. Las rutas salieron de
`api/crud.py` para no hacerlo crecer; `DELETE` y `PUT .../users` se movieron
sin cambios.

Orden de las comprobaciones en `POST` y `PUT`:
1. Cuerpo JSON y lista blanca (`400`).
2. DN de grupos: solo el superadmin (`403 dn_solo_superadmin`, SEC-LDAP-05).
3. Alcance: plataforma y área deben existir y estar en el alcance (`404`).
4. Formato de los campos (`422 validacion`).
5. Grupos: base, derivación y que sean distintos (`422`, `409 grupos_iguales`).
6. Con accesos vigentes no cambian el tipo, los grupos ni el área (`409`).
7. Comprobación en el directorio (avisos, nunca error) y guardado con su
   auditoría en la misma transacción (SEC-AUD-06).
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import (any_admin_required, can_manage_area,
                       can_manage_platform, is_admin,
                       platform_manage_required, scoped_users)
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, CUERPO_INVALIDO,
                                     NO_ENCONTRADO, error_response,
                                     json_object, validation_error)
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from app.modules.directory.dn import mismo_dn
from app.modules.platforms import grupos
from app.modules.platforms.estado import accesos_vigentes
from app.modules.platforms.tipos import (CAMPOS_DN, GRUPOS_SIN_VERIFICAR,
                                         NIVEL_ADMIN, NIVEL_USUARIO,
                                         TIPO_CONECTOR)
from app.modules.platforms.validacion import (MENSAJE_DN_BASE,
                                              campos_no_permitidos,
                                              validar_campos)

platforms_api_bp = Blueprint('api_platforms', __name__, url_prefix='/api/v1')

MODULO_AUDITORIA = 'Plataformas'

DN_SOLO_SUPERADMIN = ('Solo el superadmin define los grupos del directorio.',
                      403, 'dn_solo_superadmin')
PLATAFORMA_CON_ACCESOS = ('No se puede cambiar el tipo, los grupos ni el área '
                          'con accesos vigentes.', 409, 'plataforma_con_accesos')
GRUPOS_IGUALES = ('Los grupos de usuario y admin deben ser distintos.', 409,
                  'grupos_iguales')
MENSAJE_SIN_DIRECTORIO = ('El directorio no está configurado; usa conector o '
                          'configura las variables LDAP_*.')
MENSAJE_SIN_CONVENCION = ('No hay convención de grupos configurada '
                          '(LDAP_PLATFORM_GROUP_TEMPLATE): el superadmin debe '
                          'indicar el grupo.')
MENSAJE_DN_CON_CONECTOR = 'Una plataforma con conector no usa grupos del directorio.'

# Valores por defecto del alta (los mismos de antes de FNC-046).
POR_DEFECTO_ALTA = {'icon': 'box', 'bg_color': '#6366f1',
                    'text_color': '#ffffff', 'status': 'Activo'}
CAMPOS_SIMPLES = ('name', 'description', 'direct_link', 'logo_url', 'icon',
                  'bg_color', 'text_color', 'status')
# Campos que se guardan en la auditoría (antes y después).
CAMPOS_AUDITADOS = ('name', 'area_id', 'integration_type',
                    *CAMPOS_DN.values(), 'direct_link', 'logo_url', 'status')


class Rechazo(Exception):
    """Respuesta de error ya armada para cortar la validación."""

    def __init__(self, respuesta):
        super().__init__()
        self.respuesta = respuesta


def _leer_cuerpo():
    datos = json_object()
    if datos is None:
        raise Rechazo(error_response(*CUERPO_INVALIDO))
    if campos_no_permitidos(datos):
        raise Rechazo(error_response(*CAMPO_NO_PERMITIDO))
    if not is_admin() and any(c in datos for c in CAMPOS_DN.values()):
        raise Rechazo(error_response(*DN_SOLO_SUPERADMIN))
    return datos


def _area_en_alcance(area_id):
    """Área existente que el actor administra; si no, 404 (SEC-AUTHZ-03/04)."""
    if isinstance(area_id, bool) or not isinstance(area_id, int):
        return None  # el formato lo reporta `validar_campos`
    area = db.session.get(Area, area_id)
    if area is None or not can_manage_area(area_id):
        raise Rechazo(error_response(*NO_ENCONTRADO))
    return area


def _validar(datos, alta):
    limpios, errores = validar_campos(datos, alta=alta)
    if errores:
        raise Rechazo(validation_error(errores))
    return limpios


def _resolver_grupos(tipo, dns_pedidos, nombre, area):
    """DN finales por nivel: los pedidos o los derivados, validados."""
    if tipo == TIPO_CONECTOR:
        errores = {CAMPOS_DN[n]: MENSAJE_DN_CON_CONECTOR
                   for n, dn in dns_pedidos.items() if dn}
        if errores:
            raise Rechazo(validation_error(errores))
        return None, {NIVEL_USUARIO: None, NIVEL_ADMIN: None}

    configuracion = grupos.configuracion_directorio()
    if configuracion is None:
        raise Rechazo(validation_error(
            {'integration_type': MENSAJE_SIN_DIRECTORIO}))
    dns, errores = {}, {}
    for nivel in (NIVEL_USUARIO, NIVEL_ADMIN):
        dn = dns_pedidos.get(nivel) or grupos.derivar_dn(
            configuracion, nivel, nombre, area.name)
        if not dn:
            errores[CAMPOS_DN[nivel]] = MENSAJE_SIN_CONVENCION
        elif not grupos.dn_en_base(configuracion, dn):
            errores[CAMPOS_DN[nivel]] = MENSAJE_DN_BASE
        dns[nivel] = dn
    if errores:
        raise Rechazo(validation_error(errores))
    if mismo_dn(dns[NIVEL_USUARIO], dns[NIVEL_ADMIN]):
        raise Rechazo(error_response(*GRUPOS_IGUALES))
    return configuracion, dns


def _comprobar(configuracion, dns):
    if configuracion is None:
        return GRUPOS_SIN_VERIFICAR, []
    return grupos.comprobar_grupos(configuracion, dns)


def _estado_auditado(plataforma):
    return {campo: getattr(plataforma, campo) for campo in CAMPOS_AUDITADOS}


def _actor():
    rol = 'superadmin' if is_admin() else 'admin'
    return f'{rol} {current_user.email}'


def _respuesta(plataforma, avisos, codigo=200):
    return jsonify({'status': 'success', 'platform': plataforma.to_dict(),
                    'warnings': avisos}), codigo


def _dns_pedidos(limpios):
    return {nivel: limpios.get(campo) for nivel, campo in CAMPOS_DN.items()
            if campo in limpios}


# --------------------------------------------------------------------------- #
# Alta y edición
# --------------------------------------------------------------------------- #

@platforms_api_bp.route('/platforms', methods=['POST'])
@login_required
@any_admin_required
def create_platform():
    try:
        datos = _leer_cuerpo()
        area = _area_en_alcance(datos.get('area_id'))
        limpios = _validar(datos, alta=True)
        configuracion, dns = _resolver_grupos(
            limpios['integration_type'], _dns_pedidos(limpios),
            limpios['name'], area)
    except Rechazo as rechazo:
        return rechazo.respuesta

    estado_grupos, avisos = _comprobar(configuracion, dns)
    plataforma = Platform(
        area_id=area.id,
        integration_type=limpios['integration_type'],
        ldap_group_user_dn=dns[NIVEL_USUARIO],
        ldap_group_admin_dn=dns[NIVEL_ADMIN],
        groups_status=estado_grupos,
        **{campo: limpios.get(campo) or POR_DEFECTO_ALTA.get(campo)
           for campo in CAMPOS_SIMPLES},
    )
    db.session.add(plataforma)
    db.session.flush()
    add_audit_log(Evento.PLATAFORMA_CREADA, status='success',
                  module=MODULO_AUDITORIA, target=plataforma.name,
                  platform_id=plataforma.id, area_id=area.id,
                  after=_estado_auditado(plataforma),
                  detail=f'{_actor()} dio de alta la plataforma '
                         f'{plataforma.name}',
                  commit=False)
    db.session.commit()
    return _respuesta(plataforma, avisos, 201)


def _cambios_de_grupos(plataforma, limpios, area):
    """(tipo, configuración, DN nuevos) si el tipo o los grupos cambian; si no, None."""
    tipo = limpios.get('integration_type', plataforma.integration_type)
    pedidos = _dns_pedidos(limpios)
    actuales = {NIVEL_USUARIO: plataforma.ldap_group_user_dn,
                NIVEL_ADMIN: plataforma.ldap_group_admin_dn}
    mismo_tipo = tipo == plataforma.integration_type
    # Reenviar el tipo y los grupos actuales no es un cambio.
    if mismo_tipo and all(_mismo_grupo(dn, actuales[n])
                          for n, dn in pedidos.items()):
        return None
    # Un DN no enviado conserva el actual, salvo al cambiar de tipo (se deriva).
    if mismo_tipo:
        pedidos = {**actuales, **pedidos}
    configuracion, dns = _resolver_grupos(
        tipo, pedidos, limpios.get('name', plataforma.name), area)
    return tipo, configuracion, dns


def _mismo_grupo(uno, otro):
    return uno == otro or mismo_dn(uno, otro)


@platforms_api_bp.route('/platforms/<int:platform_id>', methods=['PUT'])
@login_required
@any_admin_required
def update_platform(platform_id):
    plataforma = db.session.get(Platform, platform_id)
    if plataforma is None or not can_manage_platform(plataforma):
        return error_response(*NO_ENCONTRADO)
    try:
        datos = _leer_cuerpo()
        cambia_area = 'area_id' in datos and \
            datos['area_id'] != plataforma.area_id
        area = (_area_en_alcance(datos['area_id']) if cambia_area
                else plataforma.area)
        limpios = _validar(datos, alta=False)
        cambio_grupos = _cambios_de_grupos(plataforma, limpios, area)
        if (cambia_area or cambio_grupos) and accesos_vigentes(plataforma) > 0:
            raise Rechazo(error_response(*PLATAFORMA_CON_ACCESOS))
    except Rechazo as rechazo:
        return rechazo.respuesta

    avisos = []
    antes = _estado_auditado(plataforma)
    if cambio_grupos:
        tipo, configuracion, dns = cambio_grupos
        plataforma.groups_status, avisos = _comprobar(configuracion, dns)
        plataforma.integration_type = tipo
        plataforma.ldap_group_user_dn = dns[NIVEL_USUARIO]
        plataforma.ldap_group_admin_dn = dns[NIVEL_ADMIN]
    if cambia_area:
        plataforma.area_id = area.id
    for campo in CAMPOS_SIMPLES:
        if campo in limpios:
            setattr(plataforma, campo, limpios[campo])

    despues = _estado_auditado(plataforma)
    add_audit_log(Evento.PLATAFORMA_EDITADA, status='success',
                  module=MODULO_AUDITORIA, target=plataforma.name,
                  platform_id=plataforma.id, area_id=plataforma.area_id,
                  before={k: v for k, v in antes.items() if despues[k] != v},
                  after={k: v for k, v in despues.items() if antes[k] != v},
                  commit=False)
    db.session.commit()
    return _respuesta(plataforma, avisos)


# --------------------------------------------------------------------------- #
# Baja y usuarios asignados (movidas de `api/crud.py` sin cambios)
# --------------------------------------------------------------------------- #

@platforms_api_bp.route('/platforms/<int:platform_id>', methods=['DELETE'])
@login_required
@platform_manage_required('platform_id')
def delete_platform(platform_id):
    platform = Platform.query.get_or_404(platform_id)
    name = platform.name
    db.session.delete(platform)
    db.session.commit()
    add_audit_log(f"ELIMINAR PLATAFORMA: {name}", module='Plataformas',
                  target=name, status='warning')
    return jsonify({'status': 'success'})


@platforms_api_bp.route('/platforms/<int:platform_id>/users', methods=['PUT'])
@login_required
@platform_manage_required('platform_id')
def set_platform_users(platform_id):
    """Define qué usuarios tienen asignada la plataforma."""
    platform = Platform.query.get_or_404(platform_id)
    user_ids = (request.get_json(silent=True) or {}).get('user_ids') or []

    allowed = {u.id for u in scoped_users().all()}
    if [i for i in user_ids if i not in allowed]:
        return error_response('Hay usuarios fuera de tu alcance.', 403)

    keep = [u for u in platform.platform_users.all() if u.id not in allowed]
    platform.platform_users = keep + User.query.filter(User.id.in_(user_ids)).all()
    db.session.commit()
    add_audit_log(f"ACTUALIZAR ACCESO: {platform.name}", module='Plataformas',
                  target=platform.name, status='success')
    return jsonify({'status': 'success'})
