"""Bandeja de aprobación y decisión de solicitudes (FNC-057).

Contrato `solicitudes.md` 1.1. Las operaciones cambian la solicitud, otorgan
(`access.services.otorgar`) y auditan **en la transacción del llamador**: no
hacen `commit` (SEC-AUD-06). El endpoint confirma y después avisa (FNC-048).

- Alcance (`validar_decisor`): el superadmin decide todas; un admin de área,
  las de plataformas de sus áreas cuyo solicitante administra
  (`can_manage_user`: nunca las de otro admin, SEC-AUTHZ-06). Fuera de
  alcance = inexistente: `404` (SEC-AUTHZ-03/07, RF-03).
- Propia → `403 solicitud_propia` (P12, SEC-AUTHZ-08).
- Solo se decide una `pendiente`: `UPDATE ... WHERE status = 'pendiente'`
  (`_tomar_pendiente`, como `access.services._tomar_activo`). Con dos
  decisiones simultáneas la segunda espera el bloqueo de la fila, no cambia
  nada y responde `409 solicitud_ya_decidida` (SEC-AUTHZ-10).
- Las reglas del acceso son las de FNC-054 (`otorgar`): P1, P5
  (`409 nivel_vigente`, `409 estado_invalido`) y `409 cuenta_inactiva`. Si
  fallan, el llamador revierte y la solicitud sigue `pendiente`.

Decisiones del orquestador (pendientes de validar en la prueba de concepto):
- La bandeja no muestra las solicitudes propias ni las que el actor no puede
  decidir (otro admin como solicitante): solo el superadmin las ve.
- Aprobar un nivel que la plataforma ya no tiene integrado (o con la
  plataforma o el área inactivas) → `409 plataforma_no_disponible`, sin
  cambios; el admin puede rechazarla.
- Aprobar con el nivel ya vigente → `409 nivel_vigente`, sin cambios.
- Rechazar no mira la cuenta ni la plataforma: se puede rechazar aunque la
  cuenta esté inactiva o la plataforma sin integración.
"""
from app import db
from app.authz import (can_manage_platform, can_manage_user, is_admin,
                       managed_area_ids, scoped_users)
from app.modules.access import errores as errores_acceso
from app.modules.access.services import otorgar
from app.modules.access.tipos import ORIGEN_SOLICITUD
from app.modules.access_requests import catalogo, errores
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.services import (MODULO_AUDITORIA,
                                                  estado_auditado)
from app.modules.access_requests.tipos import (
    ACCESS_REQUEST_REJECTION_MAX_LENGTH, ACCESS_REQUEST_REJECTION_MIN_LENGTH,
    ESTADO_APROBADA, ESTADO_PENDIENTE, ESTADO_RECHAZADA)
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.core.models import Platform
from app.modules.provisioning.reloj import ahora

MENSAJE_MOTIVO = (f'Escribe entre {ACCESS_REQUEST_REJECTION_MIN_LENGTH} y '
                  f'{ACCESS_REQUEST_REJECTION_MAX_LENGTH} caracteres.')


# --------------------------------------------------------------------------- #
# Alcance
# --------------------------------------------------------------------------- #

def bandeja(actor):
    """Consulta de las solicitudes que el actor puede decidir (sin orden)."""
    consulta = (PlatformAccessRequest.query
                .join(Platform, Platform.id == PlatformAccessRequest.platform_id)
                .filter(PlatformAccessRequest.user_id != actor.id))
    if is_admin(actor):
        return consulta
    administrables = scoped_users(actor).with_entities(User.id)
    return consulta.filter(
        Platform.area_id.in_(managed_area_ids(actor)),
        PlatformAccessRequest.user_id.in_(administrables))


def validar_decisor(actor, solicitud):
    """Propia → 403; fuera de alcance → 404 (antes de mirar el cuerpo)."""
    if solicitud is None:
        raise errores_acceso.fuera_de_alcance()
    if solicitud.user_id == actor.id:
        raise errores.solicitud_propia()
    if is_admin(actor):
        return
    if not (can_manage_platform(solicitud.platform, actor)
            and can_manage_user(solicitud.requester, actor)):
        raise errores_acceso.fuera_de_alcance()


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #

def limpiar_motivo_rechazo(valor):
    """RF-06: obligatorio, recortado, 10–500 caracteres; si no, `422`."""
    motivo = valor.strip() if isinstance(valor, str) else ''
    if not (ACCESS_REQUEST_REJECTION_MIN_LENGTH <= len(motivo)
            <= ACCESS_REQUEST_REJECTION_MAX_LENGTH):
        raise errores_acceso.validacion('reason', MENSAJE_MOTIVO)
    return motivo


def estado_decidido(solicitud):
    """Estado auditado de la solicitud, con la decisión."""
    return {**estado_auditado(solicitud), 'decided_by': solicitud.decided_by,
            'rejection_reason': solicitud.rejection_reason}


# --------------------------------------------------------------------------- #
# Decisión
# --------------------------------------------------------------------------- #

def _tomar_pendiente(solicitud, cambios):
    """`UPDATE ... WHERE status = 'pendiente'`: solo una decisión gana.

    `slot_pendiente` vuelve a NULL junto con el estado (libera el lugar de
    la pendiente). Devuelve `True` si esta transacción tomó la solicitud.
    """
    tomadas = (PlatformAccessRequest.query
               .filter(PlatformAccessRequest.id == solicitud.id,
                       PlatformAccessRequest.status == ESTADO_PENDIENTE)
               .update({**cambios, PlatformAccessRequest.slot_pendiente: None},
                       synchronize_session=False))
    if tomadas != 1:
        return False
    db.session.refresh(solicitud)
    return True


def _decidir(solicitud, actor, estado, motivo=None):
    if solicitud.status != ESTADO_PENDIENTE:
        raise errores.solicitud_ya_decidida()
    antes = estado_decidido(solicitud)
    tomada = _tomar_pendiente(solicitud, {
        PlatformAccessRequest.status: estado,
        PlatformAccessRequest.decided_by: actor.id,
        PlatformAccessRequest.decided_at: ahora(),
        PlatformAccessRequest.rejection_reason: motivo,
    })
    if not tomada:
        raise errores.solicitud_ya_decidida()
    return antes


def _auditar(evento, solicitud, antes, detalle, acceso=None):
    plataforma, usuario = solicitud.platform, solicitud.requester
    add_audit_log(
        evento, status='success', module=MODULO_AUDITORIA, detail=detalle,
        target=usuario.email, target_user_id=usuario.id,
        area_id=plataforma.area_id, platform_id=plataforma.id,
        request_id=solicitud.id,
        grant_id=acceso.id if acceso is not None else None,
        before=antes, after=estado_decidido(solicitud), commit=False)


def aprobar(solicitud, actor):
    """`pendiente` → `aprobada` y acceso `en_proceso` con su trabajo; devuelve
    el acceso."""
    validar_decisor(actor, solicitud)
    if solicitud.status != ESTADO_PENDIENTE:
        raise errores.solicitud_ya_decidida()
    plataforma = solicitud.platform
    if solicitud.level not in catalogo.niveles_integrados(plataforma):
        raise errores.plataforma_no_disponible()
    antes = _decidir(solicitud, actor, ESTADO_APROBADA)
    acceso = otorgar(solicitud.requester, plataforma, solicitud.level,
                     ORIGEN_SOLICITUD, actor=actor, request_id=solicitud.id)
    _auditar(Evento.SOLICITUD_APROBADA, solicitud, antes,
             f'Solicitud de nivel {solicitud.level} a {plataforma.name} '
             'aprobada.', acceso)
    return acceso


def rechazar(solicitud, actor, motivo):
    """`pendiente` → `rechazada` con motivo (RF-06); sin acceso."""
    validar_decisor(actor, solicitud)
    motivo = limpiar_motivo_rechazo(motivo)
    antes = _decidir(solicitud, actor, ESTADO_RECHAZADA, motivo)
    _auditar(Evento.SOLICITUD_RECHAZADA, solicitud, antes,
             f'Solicitud de nivel {solicitud.level} a '
             f'{solicitud.platform.name} rechazada.')
    return solicitud
