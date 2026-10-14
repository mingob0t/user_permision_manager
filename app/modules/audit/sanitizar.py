"""Limpieza del detalle antes/después de la auditoría (SEC-AUD-05).

- Nunca se guardan contraseñas, hashes, tokens, cookies, cabeceras ni secretos:
  el valor de una clave sensible se sustituye por `VALOR_OMITIDO`.
- Una clave es sensible si su nombre (en minúsculas) contiene alguna de
  `FRAGMENTOS_SENSIBLES`; se aplica en todos los niveles del diccionario.
- Forma par `{"key": "smtp_password", "value": "..."}`: si el nombre del par
  es sensible se omite su valor (el nombre se conserva).
- Los valores no serializables en JSON (fechas, etc.) se guardan como texto.
"""

import json

FRAGMENTOS_SENSIBLES = (
    'password', 'passwd', 'pass', 'pwd', 'contrasena', 'contraseña', 'hash',
    'token', 'secret', 'secreto', 'cookie', 'session', 'authorization',
    'header', 'cabecera', 'key', 'private_key', 'api_key', 'apikey', 'otp',
    'credential', 'credencial', 'clave',
)
VALOR_OMITIDO = '[omitido]'
# Forma par nombre/valor: campos que nombran el dato y campo que lo contiene.
CAMPOS_NOMBRE_PAR = ('key', 'name')
CAMPO_VALOR_PAR = 'value'


def _es_sensible(clave):
    nombre = str(clave).lower()
    return any(fragmento in nombre for fragmento in FRAGMENTOS_SENSIBLES)


def _nombre_de_par(valor):
    """Nombre del par si `valor` tiene la forma {key|name, value}; si no, None."""
    if CAMPO_VALOR_PAR not in valor:
        return None
    for campo in CAMPOS_NOMBRE_PAR:
        if isinstance(valor.get(campo), str):
            return campo
    return None


def _limpiar_par(valor, campo_nombre):
    omitir = _es_sensible(valor[campo_nombre])
    return {k: (v if k == campo_nombre
                else VALOR_OMITIDO if (k == CAMPO_VALOR_PAR and omitir)
                or (k != CAMPO_VALOR_PAR and _es_sensible(k))
                else _limpiar(v))
            for k, v in valor.items()}


def _limpiar(valor):
    if isinstance(valor, dict):
        campo_nombre = _nombre_de_par(valor)
        if campo_nombre:
            return _limpiar_par(valor, campo_nombre)
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
