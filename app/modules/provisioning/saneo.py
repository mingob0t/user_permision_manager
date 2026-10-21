"""Error saneado para la bitácora de ejecuciones (SEC-CON-10).

- Se guarda un mensaje del catálogo según el motivo del proveedor; nunca el
  texto de una excepción.
- El detalle opcional que devuelva un proveedor (p. ej. la salida de un
  conector, FNC-050) pasa por `sanear_error`: sin saltos ni caracteres de
  control, sin el valor de las variables secretas del despliegue, sin
  `clave=valor` sensibles (mismos fragmentos que la auditoría, SEC-AUD-05),
  sin credenciales en URL ni `Bearer`, y truncado a `LARGO_ERROR`.
"""
import os
import re

from app.modules.audit.sanitizar import FRAGMENTOS_SENSIBLES, VALOR_OMITIDO
from app.modules.directory.errors import (MOTIVO_DATOS_INCOMPLETOS,
                                          MOTIVO_DATOS_INVALIDOS,
                                          MOTIVO_DIRECTORIO,
                                          MOTIVO_FUERA_DE_BASE,
                                          MOTIVO_GRUPO_INEXISTENTE,
                                          MOTIVO_ULTIMO_MIEMBRO,
                                          MOTIVO_USUARIO_INEXISTENTE)
from app.modules.provisioning.tipos import (LARGO_ERROR,
                                            RESULTADO_ERROR_TRANSITORIO)

# Variables secretas cuyo valor nunca debe quedar en la bitácora.
VARIABLES_SECRETAS = ('LDAP_BIND_PASSWORD', 'REDIS_PASS', 'DB_PASS',
                      'SMTP_PASSWORD', 'SECRET_KEY',
                      # Credencial de arranque de Vaultwarden (FNC-068/108).
                      'VAULTWARDEN_CLIENT_SECRET', 'VAULTWARDEN_MASTER_PASSWORD')
# Un valor más corto no se busca (reemplazaría letras sueltas).
LARGO_MINIMO_SECRETO = 4
SEPARADOR_DETALLE = ': '

_CONTROL = re.compile(r'[\x00-\x1f\x7f]+')
_FRAGMENTOS = '|'.join(sorted((re.escape(f) for f in FRAGMENTOS_SENSIBLES),
                              key=len, reverse=True))
_CLAVE_VALOR = re.compile(
    rf'(?i)([\w.-]*(?:{_FRAGMENTOS})[\w.-]*)(\s*[:=]\s*)'
    r'("[^"]*"|\'[^\']*\'|\S+)')
_BEARER = re.compile(r'(?i)\b(bearer|basic)\s+\S+')
_URL_CON_CREDENCIAL = re.compile(r'(?i)\b([a-z][a-z0-9+.-]*://)[^/\s@]+@')

# Motivos de los proveedores → mensaje para la bitácora (sin datos de la
# persona ni del servidor).
MOTIVO_TIEMPO_AGOTADO = 'tiempo_agotado'
MOTIVO_INESPERADO = 'inesperado'
MOTIVO_INTERRUMPIDO = 'interrumpido'
MOTIVO_CONECTOR_NO_DISPONIBLE = 'conector_no_disponible'
MOTIVO_TIPO_INTEGRACION = 'tipo_integracion'
MOTIVO_GRUPO_NO_CONFIGURADO = 'grupo_no_configurado'
MOTIVO_DIRECTORIO_NO_CONFIGURADO = 'directorio_no_configurado'
MOTIVO_PERSONA_AMBIGUA = 'persona_ambigua'
# Conectores (FNC-050).
MOTIVO_CONSULTA_NO_DISPONIBLE = 'consulta_no_disponible'
MOTIVO_HOST_NO_AUTORIZADO = 'host_no_autorizado'
MOTIVO_CREDENCIAL_NO_ENCONTRADA = 'credencial_no_encontrada'
MOTIVO_GESTOR_NO_DISPONIBLE = 'gestor_no_disponible'
MOTIVO_GESTOR_NO_CONFIGURADO = 'gestor_no_configurado'
# Conector API HTTP (FNC-051).
MOTIVO_CONFIGURACION_INVALIDA = 'configuracion_invalida'
MOTIVO_DESTINO_NO_PERMITIDO = 'destino_no_permitido'
MOTIVO_TLS = 'tls_no_valido'
MOTIVO_VALOR_NO_VALIDO = 'valor_no_valido'
MOTIVO_HTTP_RECHAZADO = 'http_rechazado'
MOTIVO_HTTP_TRANSITORIO = 'http_transitorio'
MOTIVO_RED = 'red_no_disponible'
MOTIVO_REDIRECCION = 'redireccion_no_permitida'

MENSAJES = {
    MOTIVO_TIEMPO_AGOTADO: 'Tiempo de espera agotado.',
    MOTIVO_INESPERADO: 'Error inesperado del proveedor.',
    MOTIVO_INTERRUMPIDO: 'El intento se interrumpió antes de terminar.',
    MOTIVO_CONECTOR_NO_DISPONIBLE: 'El conector de la plataforma no está disponible.',
    MOTIVO_DATOS_INCOMPLETOS: 'Faltan datos del usuario o de la plataforma.',
    MOTIVO_TIPO_INTEGRACION: 'La plataforma ya no usa este tipo de integración.',
    MOTIVO_GRUPO_NO_CONFIGURADO: 'La plataforma no tiene grupo para este nivel.',
    MOTIVO_DIRECTORIO_NO_CONFIGURADO: 'El directorio no está configurado.',
    MOTIVO_PERSONA_AMBIGUA: 'El correo corresponde a más de una persona en el directorio.',
    MOTIVO_CONSULTA_NO_DISPONIBLE: 'El conector no permite consultar el acceso.',
    MOTIVO_HOST_NO_AUTORIZADO: 'El host del conector no está autorizado.',
    MOTIVO_CREDENCIAL_NO_ENCONTRADA: 'La credencial del conector no existe en el gestor de secretos.',
    MOTIVO_GESTOR_NO_DISPONIBLE: 'El gestor de secretos no respondió.',
    MOTIVO_GESTOR_NO_CONFIGURADO: 'El gestor de secretos no está configurado.',
    MOTIVO_CONFIGURACION_INVALIDA: 'La configuración del conector no es válida.',
    MOTIVO_DESTINO_NO_PERMITIDO: 'El host del conector resuelve a una dirección no pública.',
    MOTIVO_VALOR_NO_VALIDO: 'La cuenta o el nivel no son válidos para la plataforma.',
    MOTIVO_TLS: 'No se pudo validar el certificado TLS de la plataforma.',
    MOTIVO_HTTP_RECHAZADO: 'La plataforma rechazó la operación.',
    MOTIVO_HTTP_TRANSITORIO: 'La plataforma no pudo atender la operación por ahora.',
    MOTIVO_RED: 'No se pudo conectar con la plataforma.',
    MOTIVO_REDIRECCION: 'La plataforma respondió con una redirección, que no se sigue.',
    # Motivos del escritor LDAP (`directory/errors.py`).
    MOTIVO_FUERA_DE_BASE: 'El grupo o la persona están fuera de la base autorizada.',
    MOTIVO_GRUPO_INEXISTENTE: 'El grupo no existe en el directorio.',
    MOTIVO_USUARIO_INEXISTENTE: 'La persona no existe en el directorio.',
    MOTIVO_ULTIMO_MIEMBRO: 'No se puede quitar al último miembro del grupo.',
    MOTIVO_DATOS_INVALIDOS: 'Los datos de la cuenta no son válidos.',
}
MENSAJE_DIRECTORIO_TRANSITORIO = 'El directorio no respondió.'
MENSAJE_DIRECTORIO_PERMANENTE = 'El directorio rechazó la operación.'
MENSAJE_GENERICO = 'Error del proveedor.'


def _secretos(entorno):
    valores = (str(entorno.get(nombre) or '') for nombre in VARIABLES_SECRETAS)
    return sorted({v for v in valores if len(v) >= LARGO_MINIMO_SECRETO},
                  key=len, reverse=True)


def sanear_error(texto, entorno=None):
    """Texto apto para la bitácora, o `None` si queda vacío."""
    if texto is None:
        return None
    entorno = os.environ if entorno is None else entorno
    limpio = _CONTROL.sub(' ', str(texto))
    for secreto in _secretos(entorno):
        limpio = limpio.replace(secreto, VALOR_OMITIDO)
    limpio = _URL_CON_CREDENCIAL.sub(rf'\1{VALOR_OMITIDO}@', limpio)
    limpio = _BEARER.sub(rf'\1 {VALOR_OMITIDO}', limpio)
    limpio = _CLAVE_VALOR.sub(rf'\1\2{VALOR_OMITIDO}', limpio)
    limpio = ' '.join(limpio.split())
    return limpio[:LARGO_ERROR] or None


def mensaje_de_error(resultado, motivo, detalle=None, entorno=None):
    """Mensaje del catálogo para `motivo` más el detalle saneado."""
    if motivo == MOTIVO_DIRECTORIO:
        mensaje = (MENSAJE_DIRECTORIO_TRANSITORIO
                   if resultado == RESULTADO_ERROR_TRANSITORIO
                   else MENSAJE_DIRECTORIO_PERMANENTE)
    else:
        mensaje = MENSAJES.get(motivo, MENSAJE_GENERICO)
    if detalle:
        mensaje = f'{mensaje}{SEPARADOR_DETALLE}{detalle}'
    return sanear_error(mensaje, entorno)
