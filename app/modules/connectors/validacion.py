"""Validación de la configuración de un conector (FNC-050).

Reglas del contrato `conectores-y-ejecuciones.md` (`PUT
/platforms/<id>/connector`); el endpoint es FNC-061:
- `type`: un tipo registrado (`noop` solo en dev y pruebas; los no
  implementados no se aceptan).
- `host`: nombre de host de `CONNECTOR_ALLOWED_HOSTS`; IP o ajeno → error
  (SEC-CON-07).
- `port`: entero 1–65535.
- `params`: objeto sin claves que parezcan secretos (mismos fragmentos que la
  auditoría, SEC-AUD-05; también dentro de listas), con a lo más
  `PROFUNDIDAD_MAXIMA_PARAMS` niveles, y válido para el esquema del tipo.
- `credential_ref`: referencia del ítem del gestor (≤ 200), nunca el valor;
  sin `__` en su variable de dev ni equivalente a otra en uso (B3).
- `active`: booleano (por defecto `true`).

`validar_configuracion(datos)` → `(limpio, errores)` con errores
`{campo: mensaje}` (`params.<clave>` para los parámetros).
"""
import re

from app.modules.audit.sanitizar import FRAGMENTOS_SENSIBLES
from app.modules.connectors.configuracion import (cargar_configuracion,
                                                  host_permitido,
                                                  normalizar_host)
from app.modules.connectors.credenciales import (referencia_reservada,
                                                 referencia_valida,
                                                 referencias_en_conflicto)
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
MENSAJE_PARAMS_PROFUNDOS = 'Los parámetros tienen demasiados niveles.'
MENSAJE_REFERENCIA_RESERVADA = ('Esa referencia está reservada para el '
                                'directorio; usa una propia del conector.')
MENSAJE_REFERENCIA_EN_CONFLICTO = ('La referencia equivale a otra ya usada; '
                                   'usa la misma o una distinta.')

# Niveles de objetos y listas que se revisan en `params` (auditor-seguridad
# B2): más profundo se rechaza en lugar de agotar la recursión.
PROFUNDIDAD_MAXIMA_PARAMS = 8

# Segmentos separados por "/" de letras, dígitos, ".", "_" y "-", sin
# empezar por punto ni guion.
PATRON_REFERENCIA = re.compile(
    r'[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*')
PREFIJO_PARAMS = 'params.'


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


class _DemasiadoProfundo(Exception):
    """`params` supera `PROFUNDIDAD_MAXIMA_PARAMS`."""


def _claves_sensibles(valor, ruta='', nivel=1):
    """Claves (con su ruta; índice en las listas) que parecen nombrar un
    secreto, en objetos y listas hasta `PROFUNDIDAD_MAXIMA_PARAMS`."""
    if isinstance(valor, dict):
        hijos = ((str(clave), hijo, True) for clave, hijo in valor.items())
    elif isinstance(valor, list):
        hijos = ((str(i), hijo, False) for i, hijo in enumerate(valor))
    else:
        return []
    if nivel > PROFUNDIDAD_MAXIMA_PARAMS:
        raise _DemasiadoProfundo()
    encontradas = []
    for nombre, hijo, es_clave in hijos:
        actual = f'{ruta}.{nombre}' if ruta else nombre
        if es_clave and any(f in nombre.lower() for f in FRAGMENTOS_SENSIBLES):
            encontradas.append(actual)
        else:
            encontradas.extend(_claves_sensibles(hijo, actual, nivel + 1))
    return encontradas


def _validar_params(params, tipo, errores):
    if not isinstance(params, dict):
        errores['params'] = MENSAJE_PARAMS
        return
    try:
        sensibles = _claves_sensibles(params)
    except _DemasiadoProfundo:
        errores['params'] = MENSAJE_PARAMS_PROFUNDOS
        return
    for ruta in sensibles:
        errores[PREFIJO_PARAMS + ruta] = MENSAJE_PARAM_SECRETO
    if tipo is not None and not sensibles:
        for campo, mensaje in tipo.validar_params(params).items():
            errores[PREFIJO_PARAMS + campo] = mensaje


def validar_configuracion(datos, entorno=None, referencias_en_uso=()):
    """Configuración normalizada y errores por campo (vacío si es válida).

    `referencias_en_uso`: `credential_ref` de las demás plataformas (FNC-061
    las pasa); una distinta con la misma variable de dev se rechaza (B3).
    """
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
            or not PATRON_REFERENCIA.fullmatch(referencia)
            or not referencia_valida(referencia)):
        errores['credential_ref'] = MENSAJE_REFERENCIA
    elif referencia_reservada(referencia, entorno):
        errores['credential_ref'] = MENSAJE_REFERENCIA_RESERVADA
    elif referencias_en_conflicto(referencia, referencias_en_uso):
        errores['credential_ref'] = MENSAJE_REFERENCIA_EN_CONFLICTO

    activo = datos.get('active', True)
    if not isinstance(activo, bool):
        errores['active'] = MENSAJE_ACTIVO

    if errores:
        return None, errores
    return {'type': tipo.nombre, 'host': host, 'port': puerto,
            'params': params, 'credential_ref': referencia,
            'active': activo}, {}
