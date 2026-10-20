"""Reintento manual de un trabajo fallido (FNC-062, P10: solo el superadmin).

En una transacción del llamador (sin `commit`, SEC-AUD-06):
1. `ejecucion.reabrir`: `UPDATE … WHERE status = 'fallido'` (de dos
   reintentos simultáneos, el segundo recibe 409) y rechazo de un otorgar con
   una revocación posterior de su terna (no vuelve a meter a la persona).
2. `access.services.reabrir_acceso`: el acceso vuelve a `en_proceso` o
   `revocando`, también con `UPDATE` condicional; un acceso que ya no está
   fallido (p. ej. `revocado`) → 409.
3. Auditoría `ejecucion_reintentada` con el actor de la sesión.
4. Aviso al worker después del `commit` (`queue.despertar_tras_commit`).

Antes de reabrir (SEG-062-01/02, re-auditoría FNC-062):
- Un trabajo sin acceso (`access_id` NULL) no se reintenta (defensa en
  profundidad).
- Un otorgar vuelve a pasar `access.rules.validar_otorgamiento` con la
  cuenta y la plataforma actuales: cuenta borrada, inactiva, ahora
  superadmin o que ya no es del área (P1) → 409 sin reabrir nada. El actor es
  el de la sesión para un acceso por solicitud y el sistema (`None`) para uno
  automático (`admin_de_area`, FNC-055), como al otorgarlo.
"""
from app import db
from app.modules.access import rules
from app.modules.access import services as servicios_accesos
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import ORIGEN_ADMIN_DE_AREA
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.core.models import Platform
from app.modules.provisioning import ejecucion, queue
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.tipos import ESTADO_FALLIDO, OPERACION_OTORGAR

MODULO_AUDITORIA = 'Aprovisionamiento'
MENSAJE_ESTADO_INVALIDO = 'Solo se reintenta una ejecución fallida.'


class ReintentoInvalido(ValueError):
    """El trabajo o su acceso no admiten el reintento (409 `estado_invalido`)."""


def _revalidar(trabajo, actor):
    """Las reglas de otorgar con los datos de hoy; `ErrorDeAcceso` si no."""
    acceso = (db.session.get(PlatformAccessGrant, trabajo.access_id)
              if trabajo.access_id else None)
    if acceso is None:
        raise ReintentoInvalido(MENSAJE_ESTADO_INVALIDO)
    if trabajo.operation != OPERACION_OTORGAR:
        return
    usuario = db.session.get(User, trabajo.user_id) if trabajo.user_id else None
    plataforma = (db.session.get(Platform, trabajo.platform_id)
                  if trabajo.platform_id else None)
    otorgante = None if acceso.origin == ORIGEN_ADMIN_DE_AREA else actor
    rules.validar_otorgamiento(otorgante, usuario, plataforma, acceso.origin)


def reintentar(trabajo, actor):
    """Reabre `trabajo` y su acceso; lo devuelve. Sin `commit`.

    `actor`: la cuenta de la sesión (superadmin, P10).
    """
    try:
        _revalidar(trabajo, actor)
        ejecucion.reabrir(trabajo, cargar_configuracion())
        acceso = servicios_accesos.reabrir_acceso(trabajo)
    except (ejecucion.EstadoInvalido, ErrorDeAcceso):
        raise ReintentoInvalido(MENSAJE_ESTADO_INVALIDO) from None
    add_audit_log(
        Evento.EJECUCION_REINTENTADA, status='info',
        detail=(f'Reintento manual de {trabajo.operation} nivel '
                f'{trabajo.level} (trabajo {trabajo.id}).'),
        module=MODULO_AUDITORIA, target_user_id=trabajo.user_id,
        area_id=trabajo.area_id, platform_id=trabajo.platform_id,
        grant_id=trabajo.access_id,
        before={'job_id': trabajo.id, 'status': ESTADO_FALLIDO},
        after={'job_id': trabajo.id, 'status': trabajo.status,
               'max_attempts': trabajo.max_attempts,
               'access_status': acceso.status if acceso else None},
        commit=False)
    queue.despertar_tras_commit(trabajo.id)
    return trabajo
