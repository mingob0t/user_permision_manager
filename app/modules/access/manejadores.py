"""Resultado del ejecutor → estado del acceso (FNC-054 sobre FNC-049).

- Se llaman dentro de la transacción del resultado del trabajo, junto con su
  auditoría `acceso_activo`/`acceso_fallido`/`acceso_revocado`/
  `revocacion_fallida` (actor `sistema`): no hacen `commit`.
- Un trabajo sin acceso (`access_id` nulo) o un acceso en un estado que no
  admite la transición se ignora con un aviso en el log: nunca se fuerza un
  estado (SEC-CON-09).
- Otorgar confirmado de un acceso automático cuya cuenta ya no administra el
  área: el sistema lo revoca en la misma transacción (FNC-055).
"""
import logging

from app import db
from app.modules.access.area_admin_sync import revocar_si_ya_no_administra
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.rules import puede_pasar
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_FALLIDO,
                                      ESTADO_FALLO_REVOCACION,
                                      ESTADO_REVOCADO)
from app.modules.provisioning.manejadores import registrar_manejador
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (OPERACION_OTORGAR,
                                            OPERACION_REVOCAR)

logger = logging.getLogger(__name__)

DESTINO = {
    (OPERACION_OTORGAR, True): ESTADO_ACTIVO,
    (OPERACION_OTORGAR, False): ESTADO_FALLIDO,
    (OPERACION_REVOCAR, True): ESTADO_REVOCADO,
    (OPERACION_REVOCAR, False): ESTADO_FALLO_REVOCACION,
}


def aplicar_resultado(trabajo, exito):
    if not trabajo.access_id:
        return None
    acceso = db.session.get(PlatformAccessGrant, trabajo.access_id)
    if acceso is None:
        return None
    destino = DESTINO[(trabajo.operation, exito)]
    if not puede_pasar(acceso.status, destino):
        logger.warning('Accesos: el trabajo %s no cambia el acceso %s '
                       '(%s → %s no es válido).', trabajo.id, acceso.id,
                       acceso.status, destino)
        return acceso
    momento = ahora()
    acceso.status = destino
    acceso.updated_at = momento
    if destino == ESTADO_REVOCADO:
        acceso.revoked_at = momento
    acceso.sincronizar_slots()
    return acceso


def al_exito(trabajo):
    acceso = aplicar_resultado(trabajo, True)
    if trabajo.operation == OPERACION_OTORGAR:
        revocar_si_ya_no_administra(acceso)


def al_fallo(trabajo):
    aplicar_resultado(trabajo, False)


def registrar():
    """Conecta los manejadores al ejecutor (idempotente)."""
    registrar_manejador(on_success=al_exito, on_failure=al_fallo)
