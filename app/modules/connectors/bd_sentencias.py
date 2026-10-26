"""Validación de las sentencias parametrizadas del conector `bd` (FNC-053,
SEC-CON-05).

Las sentencias son **plantillas fijas** de la configuración de la plataforma
(no SQL libre) con marcadores del driver (`%s`); los valores (`correo`,
`nivel`, `plataforma`) viajan siempre como parámetros, nunca dentro del texto.
Una plantilla se acepta solo si:
- es una sola línea de texto (≤ `LARGO_MAXIMO_SENTENCIA`) sin caracteres de
  control, y empieza con el verbo de su operación: `INSERT` o `UPDATE` (otorgar),
  `DELETE` o `UPDATE` (revocar), `SELECT` (consultar);
- no tiene `;` (una sola sentencia), comentarios (`--`, `#`, `/* */`), comillas
  (`'`, `"`, `` ` ``), barra invertida, `$` ni `?`: todo valor va como
  parámetro y no hay literales de texto ni identificadores entrecomillados;
- usa solo `%s` como marcador (ningún otro `%`);
- `UPDATE` y `DELETE` llevan `WHERE` (nunca afectan toda la tabla);
- no contiene palabras de definición, permisos, archivos o espera (`DROP`,
  `GRANT`, `OUTFILE`, `SLEEP`, `COPY`…). Es una defensa en profundidad: el
  usuario de la BD de la plataforma debe tener solo los permisos de estas
  sentencias.
"""
import re

MARCADOR = '%s'
MARCAS = ('correo', 'nivel', 'plataforma')
LARGO_MAXIMO_SENTENCIA = 500
MAXIMO_PARAMETROS = 10

VERBOS = {'otorgar': ('INSERT', 'UPDATE'), 'revocar': ('DELETE', 'UPDATE'),
          'consultar': ('SELECT',)}
VERBOS_CON_WHERE = ('UPDATE', 'DELETE')

_CARACTERES_PROHIBIDOS = ';#\'"`\\$?'
_COMENTARIOS = ('--', '/*', '*/')
_PALABRAS_PROHIBIDAS = re.compile(
    r'\b(DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|CALL|EXEC|EXECUTE|DO|COPY|'
    r'OUTFILE|DUMPFILE|LOAD_FILE|LOAD|SLEEP|BENCHMARK|PG_SLEEP|LO_IMPORT|'
    r'LO_EXPORT|PG_READ_FILE|DBLINK|SHUTDOWN|KILL)\b', re.IGNORECASE)
_WHERE = re.compile(r'\bWHERE\b', re.IGNORECASE)
_VERBO_INICIAL = re.compile(r'([A-Za-z]+)\s')


def _con_control(texto):
    return any(ord(c) < 32 or ord(c) == 127 for c in texto)


def error_sentencia(texto, operacion):
    """Motivo de rechazo de `texto` como sentencia de `operacion`, o `None`."""
    if not isinstance(texto, str) or not texto or texto != texto.strip():
        return 'Debe ser un texto sin espacios al inicio ni al final.'
    if len(texto) > LARGO_MAXIMO_SENTENCIA:
        return f'Máximo {LARGO_MAXIMO_SENTENCIA} caracteres.'
    if _con_control(texto):
        return 'Debe ser una sola línea, sin caracteres de control.'
    if any(c in texto for c in _CARACTERES_PROHIBIDOS):
        return ('No uses ";", "#", comillas, "\\", "$" ni "?": una sola '
                'sentencia y los valores como parámetros.')
    if any(c in texto for c in _COMENTARIOS):
        return 'No uses comentarios.'
    if '%' in texto.replace(MARCADOR, ''):
        return f'El único marcador permitido es {MARCADOR}.'
    inicio = _VERBO_INICIAL.match(texto)
    verbo = inicio.group(1).upper() if inicio else None
    if verbo not in VERBOS.get(operacion, ()):
        return f'Debe empezar con {" o ".join(VERBOS.get(operacion, ()))}.'
    if _PALABRAS_PROHIBIDAS.search(texto):
        return 'Contiene una palabra no permitida (definición, permisos o archivos).'
    if verbo in VERBOS_CON_WHERE and not _WHERE.search(texto):
        return f'{verbo} debe llevar WHERE.'
    return None


def contar_marcadores(texto):
    return texto.count(MARCADOR)
