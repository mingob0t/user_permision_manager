"""Otorgar y revocar accesos (FNC-054, contrato `accesos.md`).

- Cada operación cambia el acceso, encola el trabajo del ejecutor
  (`provisioning.queue.encolar`) y audita, **en la transacción del llamador**:
  no hace `commit` (SEC-AUD-06). Si el llamador revierte, no queda nada.
- El resultado del trabajo lo aplican los manejadores (`manejadores.py`): el
  acceso pasa a `activo`/`revocado` solo tras confirmar el éxito (SEC-CON-09).
- Subir de nivel (P5): el acceso anterior pasa a `revocando` con motivo
  `reemplazado_por_nivel_superior` y el nuevo a `en_proceso`, juntos.
- `actor`: la cuenta de la sesión (los endpoints pasan `current_user`) o
  `None` para el sistema (FNC-055). La auditoría toma el actor de la sesión.
- Dos peticiones simultáneas que pasan las reglas chocan con las
  restricciones únicas de `platform_access_grants` en el `flush`
  (`IntegrityError`): el llamador revierte.
"""
from app import db
from app.modules.access import errores, rules
from app.modules.access.consultas import vigentes_de
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO, ESTADO_FALLIDO,
                                      ESTADO_FALLO_REVOCACION,
                                      ESTADO_REVOCANDO, MOTIVO_REEMPLAZO,
                                      ORIGEN_ADMIN_DE_AREA)
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.provisioning import queue
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (OPERACION_OTORGAR,
                                            OPERACION_REVOCAR)

MODULO_AUDITORIA = 'Accesos'
# Reintento de un trabajo fallido (FNC-062): estado del acceso que vuelve.
REAPERTURA = {
    (OPERACION_OTORGAR, ESTADO_FALLIDO): ESTADO_EN_PROCESO,
    (OPERACION_REVOCAR, ESTADO_FALLO_REVOCACION): ESTADO_REVOCANDO,
}


def clave_idempotencia(acceso, operacion):
    """Una operación de cada tipo por acceso: el reintento reabre el mismo
    trabajo (FNC-062), no crea otro."""
    return f'acceso-{acceso.id}-{operacion}'


def estado_auditado(acceso):
    return {'status': acceso.status, 'level': acceso.level,
            'origin': acceso.origin, 'revoke_reason': acceso.revoke_reason}


def _encolar(acceso, operacion, plataforma):
    trabajo = queue.encolar(operacion, acceso.user_id, plataforma,
                            acceso.level, clave_idempotencia(acceso, operacion),
                            access_id=acceso.id)
    acceso.last_job_id = trabajo.id
    return trabajo


def _auditar(evento, acceso, usuario, plataforma, antes, detalle, sistema):
    add_audit_log(
        evento, status='info', detail=detalle, module=MODULO_AUDITORIA,
        target=usuario.email, target_user_id=usuario.id,
        area_id=plataforma.area_id, platform_id=plataforma.id,
        request_id=acceso.request_id, grant_id=acceso.id, before=antes,
        after=estado_auditado(acceso), as_system=sistema, commit=False)


def _pedir_revocacion(acceso, actor, motivo, momento):
    antes = estado_auditado(acceso)
    acceso.status = ESTADO_REVOCANDO
    acceso.revoked_by = actor.id if actor is not None else None
    acceso.revoke_reason = motivo
    acceso.updated_at = momento
    acceso.sincronizar_slots()
    db.session.flush()  # libera el lugar del nivel antes del nuevo acceso
    plataforma, usuario = acceso.platform, acceso.user
    _encolar(acceso, OPERACION_REVOCAR, plataforma)
    _auditar(Evento.ACCESO_REVOCADO, acceso, usuario, plataforma, antes,
             f'Revocación de nivel {acceso.level} en {plataforma.name} '
             f'solicitada.', actor is None)


def otorgar(usuario, plataforma, nivel, origen, actor=None, request_id=None):
    """Crea el acceso `en_proceso` y su trabajo `otorgar`; lo devuelve."""
    rules.validar_datos(nivel, origen, request_id)
    rules.validar_otorgamiento(actor, usuario, plataforma, origen)
    reemplazado = rules.acceso_a_reemplazar(
        vigentes_de(usuario.id, plataforma.id), nivel)

    momento = ahora()
    if reemplazado is not None:
        _pedir_revocacion(reemplazado, actor, MOTIVO_REEMPLAZO, momento)
    acceso = PlatformAccessGrant(
        user_id=usuario.id, platform_id=plataforma.id, level=nivel,
        origin=origen, request_id=request_id,
        granted_by=actor.id if actor is not None else None,
        granted_at=momento, status=ESTADO_EN_PROCESO, updated_at=momento)
    acceso.sincronizar_slots()
    db.session.add(acceso)
    db.session.flush()
    _encolar(acceso, OPERACION_OTORGAR, plataforma)
    detalle = (f'sistema dio permisos de acceso a admin {usuario.email}'
               if origen == ORIGEN_ADMIN_DE_AREA else
               f'Acceso nivel {nivel} a {plataforma.name} otorgado.')
    _auditar(Evento.ACCESO_OTORGADO, acceso, usuario, plataforma, None,
             detalle, actor is None)
    return acceso


def revocar(acceso, actor=None, motivo=None):
    """`activo` → `revocando` y trabajo `revocar`; lo devuelve.

    Desde otro estado (incluido `revocado`) no encola nada:
    `409 estado_invalido`.
    """
    motivo = rules.limpiar_motivo(motivo)
    rules.validar_revocacion(actor, acceso)
    if acceso.status != ESTADO_ACTIVO:
        # `fallo_revocacion` → `revocando` es solo el reintento (FNC-062).
        raise errores.estado_invalido()
    _pedir_revocacion(acceso, actor, motivo, ahora())
    return acceso


def reabrir_acceso(trabajo):
    """Al reabrir un trabajo fallido (FNC-062), el acceso vuelve a
    `en_proceso` o `revocando`. Sin commit ni auditoría (los hace FNC-062)."""
    acceso = (db.session.get(PlatformAccessGrant, trabajo.access_id)
              if trabajo.access_id else None)
    if acceso is None:
        return None
    destino = REAPERTURA.get((trabajo.operation, acceso.status))
    if destino is None:
        raise errores.estado_invalido(
            'El acceso no está en un estado fallido.')
    acceso.status = destino
    acceso.updated_at = ahora()
    acceso.sincronizar_slots()
    return acceso
