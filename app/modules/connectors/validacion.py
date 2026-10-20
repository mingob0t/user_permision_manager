"""Validación de la configuración de un conector (FNC-050).

Reglas del contrato `conectores-y-ejecuciones.md` (`PUT
/platforms/<id>/connector`); el endpoint es FNC-061:
- `type`: un tipo registrado (`noop` solo en dev y pruebas; los no
  implementados no se aceptan).
- `host`: nombre de host de `CONNECTOR_ALLOWED_HOSTS`; IP o ajeno → error
  (SEC-CON-07).
- `port`: entero 1–65535.
- `params`: objeto sin claves que parezcan secretos (mismos fragmentos que la
  auditoría, SEC-AUD-05) y válido para el esquema del tipo.
- `credential_ref`: referencia del ítem del gestor (≤ 200), nunca el valor.
- `active`: booleano (por defecto `true`).

`validar_configuracion(datos)` → `(limpio, errores)` con errores
`{campo: mensaje}` (`params.<clave>` para los parámetros).
"""
import re

from app.modules.audit.sanitizar import FRAGMENTOS_SENSIBLES
from app.modules.connectors.configuracion import (cargar_configuracion,
                                                  host_permitido,
                                                  normalizar_host)
from app.modules.connectors.registry import obtener_tipo
from app.modules.connectors.tipos import (LARGO_REFERENCIA, PUERTO_MAXIMO,
                                          PUERTO_MINIMO)

MENSAJE_TIPO = 'Tipo de conector no disponible.'
MENSAJE_HOST = 'Usa un nombre de host autorizado.'
MENSAJE_PUERTO = f'Usa un puerto entre {PUERTO_MINIMO} y {PUERTO_MAXIMO}.'
MENSAJE_PARAMS = 'Debe ser un objeto.'
MENSAJE_PARAM_SECRETO = 'No incluyas secretos en los parámetros.'
MENSAJE_REFERENCIA = ('Usa la referencia del ítem en el gestor de secretos '
                      f'(máximo {LARGO_REFERENCIA} caracteres).')
MENSAJE_ACTIVO = 'Debe ser verdadero o falso.'

# Segmentos separados por "/" de letras, dígitos, ".", "_" y "-", sin
# empezar por punto ni guion.
PATRON_REFERENCIA = re.compile(
    r'[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*')
PREFIJO_PARAMS = 'params.'


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _claves_sensibles(params, prefijo=''):
    """Claves (con su ruta) que parecen nombrar un secreto."""
    encontradas = []
    for clave, valor in params.items():
        ruta = f'{prefijo}{clave}'
        if any(f in str(clave).lower() for f in FRAGMENTOS_SENSIBLES):
            encontradas.append(ruta)
        elif isinstance(valor, dict):
            encontradas.extend(_claves_sensibles(valor, f'{ruta}.'))
    return encontradas


def _validar_params(params, tipo, errores):
    if not isinstance(params, dict):
        errores['params'] = MENSAJE_PARAMS
        return
    sensibles = _claves_sensibles(params)
    for ruta in sensibles:
        errores[PREFIJO_PARAMS + ruta] = MENSAJE_PARAM_SECRETO
    if tipo is not None and not sensibles:
        for campo, mensaje in tipo.validar_params(params).items():
            errores[PREFIJO_PARAMS + campo] = mensaje


def validar_configuracion(datos, entorno=None):
    """Configuración normalizada y errores por campo (vacío si es válida)."""
    cfg = cargar_configuracion(entorno)
    errores = {}

    tipo = obtener_tipo(datos.get('type'))
    if tipo is None:
        errores['type'] = MENSAJE_TIPO

    host = normalizar_host(datos.get('host'))
    if host is None or not host_permitido(host, cfg):
        errores['host'] = MENSAJE_HOST

    puerto = datos.get('port')
    if not _es_entero(puerto) or not PUERTO_MINIMO <= puerto <= PUERTO_MAXIMO:
        errores['port'] = MENSAJE_PUERTO

    params = datos.get('params')
    _validar_params(params, tipo, errores)

    referencia = datos.get('credential_ref')
    if (not isinstance(referencia, str) or len(referencia) > LARGO_REFERENCIA
            or not PATRON_REFERENCIA.fullmatch(referencia)):
        errores['credential_ref'] = MENSAJE_REFERENCIA

    activo = datos.get('active', True)
    if not isinstance(activo, bool):
        errores['active'] = MENSAJE_ACTIVO

    if errores:
        return None, errores
    return {'type': tipo.nombre, 'host': host, 'port': puerto,
            'params': params, 'credential_ref': referencia,
            'active': activo}, {}
