"""Prueba de conexión de un conector (FNC-061, contrato
`conectores-y-ejecuciones.md`, `POST /platforms/<id>/connector/test`).

- Reutiliza el proveedor `conector` (FNC-050) con una operación `consultar`:
  mismas reglas que el ejecutor (lista blanca de hosts, referencia sin
  ambigüedad, credencial desde la fuente del despliegue, saneo). No otorga ni
  revoca.
- La cuenta consultada es la del superadmin que prueba (dato del servidor,
  SEC-CON-03); el nivel es `usuario`.
- Antes de probar se vacía la caché de credenciales, para que el resultado
  refleje el gestor de secretos actual.
- `credential_status`: éxito → `ok`; credencial inexistente → `no_encontrada`;
  cualquier otro fallo no lo cambia (no prueba nada sobre la credencial).
- El motivo solo va al log; hacia afuera, el mensaje genérico.
"""
import logging
import uuid

from app.modules.connectors import credenciales
from app.modules.connectors.provider import ProveedorConector
from app.modules.connectors.tipos import (CREDENCIAL_NO_ENCONTRADA,
                                          CREDENCIAL_OK)
from app.modules.platforms.tipos import NIVEL_USUARIO
from app.modules.provisioning.providers import Operacion
from app.modules.provisioning.saneo import MOTIVO_CREDENCIAL_NO_ENCONTRADA
from app.modules.provisioning.tipos import OPERACION_OTORGAR

logger = logging.getLogger(__name__)

PREFIJO_OPERACION = 'prueba-conector-'

# `credential_status` que deja cada desenlace; `None` = sin cambio.
ESTADO_POR_MOTIVO = {MOTIVO_CREDENCIAL_NO_ENCONTRADA: CREDENCIAL_NO_ENCONTRADA}


def probar_conexion(configuracion, usuario_id):
    """`(exito, motivo)` de consultar con la configuración guardada.

    Actualiza `credential_status` de `configuracion` (sin hacer commit).
    """
    credenciales.limpiar_cache()
    identificador = PREFIJO_OPERACION + uuid.uuid4().hex
    resultado = ProveedorConector().consultar(Operacion(
        id_operacion=identificador, clave_idempotencia=identificador,
        operacion=OPERACION_OTORGAR, nivel=NIVEL_USUARIO,
        plataforma_id=configuracion.platform_id, usuario_id=usuario_id))
    if resultado.exito:
        configuracion.credential_status = CREDENCIAL_OK
        return True, None
    estado = ESTADO_POR_MOTIVO.get(resultado.motivo)
    if estado is not None:
        configuracion.credential_status = estado
    logger.warning('Conector: prueba fallida en la plataforma %s (%s).',
                   configuracion.platform_id, resultado.motivo)
    return False, resultado.motivo
