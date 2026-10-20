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
"""
from app.modules.access import services as servicios_accesos
from app.modules.access.errores import ErrorDeAcceso
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.provisioning import ejecucion, queue
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.tipos import ESTADO_FALLIDO

MODULO_AUDITORIA = 'Aprovisionamiento'
MENSAJE_ESTADO_INVALIDO = 'Solo se reintenta una ejecución fallida.'


class ReintentoInvalido(ValueError):
    """El trabajo o su acceso no admiten el reintento (409 `estado_invalido`)."""


def reintentar(trabajo):
    """Reabre `trabajo` y su acceso; lo devuelve. Sin `commit`."""
    try:
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
