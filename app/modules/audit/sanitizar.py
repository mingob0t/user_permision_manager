"""Limpieza del detalle antes/después de la auditoría (SEC-AUD-05).

- Nunca se guardan contraseñas, hashes, tokens, cookies, cabeceras ni secretos:
  el valor de una clave sensible se sustituye por `VALOR_OMITIDO`.
- Una clave es sensible si su nombre (en minúsculas) contiene alguna de
  `FRAGMENTOS_SENSIBLES`; se aplica en todos los niveles del diccionario.
- Los valores no serializables en JSON (fechas, etc.) se guardan como texto.
"""

import json

FRAGMENTOS_SENSIBLES = (
    'password', 'contrasena', 'contraseña', 'hash', 'token', 'secret',
    'secreto', 'cookie', 'authorization', 'header', 'cabecera', 'api_key',
    'apikey', 'credential', 'credencial', 'clave', 'bind_pass', 'ldap_pass',
)
VALOR_OMITIDO = '[omitido]'


def _es_sensible(clave):
    nombre = str(clave).lower()
    return any(fragmento in nombre for fragmento in FRAGMENTOS_SENSIBLES)


def _limpiar(valor):
    if isinstance(valor, dict):
        return {k: VALOR_OMITIDO if _es_sensible(k) else _limpiar(v)
                for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_limpiar(v) for v in valor]
    return valor


def limpiar_detalle(detalle):
    """Copia de `detalle` apta para guardar en la auditoría, o None."""
    if detalle is None:
        return None
    return json.loads(json.dumps(_limpiar(detalle), default=str))
