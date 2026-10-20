"""Crear una solicitud de acceso (FNC-056, contrato `solicitudes.md`).

- `crear` valida, agrega la solicitud y su auditoría `solicitud_creada` **en
  la transacción del llamador**: no hace `commit` (SEC-AUD-06).
- Orden de las reglas (el primero que falla responde):
  1. superadmin → `403 sin_permiso` (acceso por defecto, P6);
  2. formato → `422 validacion`;
  3. plataforma fuera de las áreas del catálogo del actor (P1) → `404`;
  4. área que administra → `409 ya_administra_area` (RF-03);
  5. plataforma o área inactiva, o nivel sin integración → `409
     plataforma_no_disponible`;
  6. pendiente en la plataforma → `409 solicitud_duplicada`;
  7. mismo nivel vigente o superior → `409 nivel_vigente` (P5; las reglas
     son las de `access.rules.acceso_a_reemplazar`).
- Dos peticiones simultáneas que pasan las reglas chocan en el `flush` con
  `uq_platform_access_requests_pendiente` (`IntegrityError`): el llamador
  revierte y responde `409 solicitud_duplicada`.
"""
from app import db
from app.authz import is_admin
from app.modules.access import errores as errores_acceso
from app.modules.access.rules import acceso_a_reemplazar
from app.modules.access.tipos import NIVELES
from app.modules.access_requests import catalogo, errores
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.tipos import (
    ACCESS_REQUEST_JUSTIFICATION_MAX_LENGTH, ESTADO_PENDIENTE)
from app.modules.audit.events import Evento
from app.modules.audit.parametros import MAX_DIGITOS_ENTERO
from app.modules.audit.services import add_audit_log
from app.modules.provisioning.reloj import ahora

MODULO_AUDITORIA = 'Solicitudes'
MENSAJE_LARGO = (f'Escribe como máximo {ACCESS_REQUEST_JUSTIFICATION_MAX_LENGTH} '
                 'caracteres.')


def estado_auditado(solicitud):
    return {'status': solicitud.status, 'level': solicitud.level,
            'current_level': solicitud.current_level,
            'justification': solicitud.justification}


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #

# Mismo criterio que los ids de consulta (`audit/parametros.py`): más dígitos
# desbordarían el entero de la BD (SEG-FNC056-01: 10^30 daba 500).
ID_MAXIMO = 10 ** MAX_DIGITOS_ENTERO - 1


def _es_id(valor):
    """Entero (sin booleanos) de 1 a `ID_MAXIMO`."""
    return (isinstance(valor, int) and not isinstance(valor, bool)
            and 1 <= valor <= ID_MAXIMO)


def limpiar_justificacion(valor):
    """Opcional (decisión del dueño, 2026-10-20); recortada y ≤ 500."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise errores_acceso.validacion('justification', 'Debe ser texto.')
    valor = valor.strip()
    if len(valor) > ACCESS_REQUEST_JUSTIFICATION_MAX_LENGTH:
        raise errores_acceso.validacion('justification', MENSAJE_LARGO)
    return valor or None


def validar_datos(plataforma_id, nivel, justificacion):
    """(plataforma_id, nivel, justificación limpia) o `422 validacion`."""
    if not _es_id(plataforma_id):
        raise errores_acceso.validacion('platform_id',
                                        'Indica una plataforma.')
    if nivel not in NIVELES:
        raise errores_acceso.validacion('level', 'Nivel desconocido.')
    return plataforma_id, nivel, limpiar_justificacion(justificacion)


# --------------------------------------------------------------------------- #
# Alta
# --------------------------------------------------------------------------- #

def _plataforma_solicitable(actor, plataforma_id, nivel):
    plataforma = catalogo.plataforma_en_alcance(actor, plataforma_id)
    if plataforma is None:
        raise errores_acceso.fuera_de_alcance()
    if catalogo.administra_area(actor, plataforma.area_id):
        raise errores.ya_administra_area()
    if nivel not in catalogo.niveles_integrados(plataforma):
        raise errores.plataforma_no_disponible()
    return plataforma


def crear(actor, plataforma_id, nivel, justificacion=None):
    """Agrega la solicitud `pendiente` y su auditoría; la devuelve."""
    if is_admin(actor):
        raise errores.sin_permiso()
    plataforma_id, nivel, justificacion = validar_datos(
        plataforma_id, nivel, justificacion)
    plataforma = _plataforma_solicitable(actor, plataforma_id, nivel)
    estado = catalogo.estado(actor.id, plataforma.id)
    if estado.pendiente is not None:
        raise errores.solicitud_duplicada()
    acceso_a_reemplazar(estado.vigentes, nivel)  # P5: nivel_vigente u otro 409

    solicitud = PlatformAccessRequest(
        user_id=actor.id, platform_id=plataforma.id, level=nivel,
        justification=justificacion, status=ESTADO_PENDIENTE,
        current_level=estado.nivel_actual, created_at=ahora())
    solicitud.sincronizar_slot()
    db.session.add(solicitud)
    db.session.flush()
    add_audit_log(
        Evento.SOLICITUD_CREADA, status='success', module=MODULO_AUDITORIA,
        detail=f'Solicitud de nivel {nivel} a {plataforma.name}.',
        target=actor.email, target_user_id=actor.id,
        area_id=plataforma.area_id, platform_id=plataforma.id,
        request_id=solicitud.id, before=None,
        after=estado_auditado(solicitud), commit=False)
    return solicitud
