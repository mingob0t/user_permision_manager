"""Conector tipo API HTTP (FNC-051, SEC-CON-06, ADR-005).

Otorga, revoca y consulta contra una API HTTPS configurable. Lo específico de
cada plataforma va en `params` (sin secretos); el código es genérico.

Esquema de `params` (cerrado: una clave desconocida se rechaza):
- `base_path` (opcional): prefijo de la ruta, p. ej. `/api/v1`.
- `auth` (obligatorio): `{"esquema": "bearer" | "basic" | "cabecera",
  "nombre": "X-Api-Token"}`; `nombre` solo con `cabecera`. La credencial sale
  del gestor (nunca de `params`): `bearer` → `Authorization: Bearer <secreto>`;
  `basic` → `Authorization: Basic base64(usuario:secreto)`; `cabecera` → el
  secreto tal cual en la cabecera `nombre`.
- `otorgar`, `revocar` (obligatorios) y `consultar` (opcional): `{"metodo":
  GET|POST|PUT|PATCH|DELETE, "ruta": "/usuarios/{correo}", "consulta":
  {"email": "{correo}"}, "cuerpo": {"email": "{correo}"}, "sin_cambios":
  [409]}`. `cuerpo` solo con POST, PUT o PATCH. `sin_cambios`: estados 4xx que
  cuentan como «ya estaba así»; por defecto `[404, 410]` al revocar y ninguno
  al otorgar.

Plantillas sin inyección:
- Solo existen tres marcas, `{correo}`, `{nivel}` y `{plataforma}`, que se
  reemplazan en una sola pasada con datos del servidor (SEC-CON-03). No hay
  `eval`, `str.format` ni expresiones.
- En la ruta y en la consulta el valor se codifica por porcentaje (un solo
  segmento, sin `/`, `?`, `#`, espacios ni saltos de línea). El cuerpo es una
  estructura JSON de la que solo se reemplazan valores de texto y se
  serializa con `json.dumps`: comillas y saltos quedan escapados.
- La ruta de la plantilla admite solo `[A-Za-z0-9._~/:-]`, sin segmentos `..`.
- Los `params` guardados se revalidan en cada operación.

Estados HTTP: 2xx éxito (`presente` al consultar); 404 al consultar = ausente;
estados de `sin_cambios` → `sin_cambios`; 408, 425, 429, 500, 502, 503 y 504
transitorios; 3xx permanente (nunca se sigue una redirección); el resto,
permanente. El detalle es solo `HTTP <estado>`: no se guarda el cuerpo de la
respuesta. Falla de red o DNS: transitoria; certificado inválido: permanente.
"""
import base64
import http.client
import json
import os
import re
import socket
import ssl
from urllib.parse import quote, urlencode

from app.modules.connectors.base import Conector
from app.modules.connectors.destino_seguro import (DestinoNoPermitido,
                                                   ErrorResolucion,
                                                   resolver_seguro)
from app.modules.connectors.http_transporte import (TransporteHttps,
                                                    crear_contexto)
from app.modules.connectors.registry import TipoConector
from app.modules.connectors.tipos import TIPO_API
from app.modules.provisioning.providers import (ResultadoProveedor,
                                                permanente, transitorio)
from app.modules.provisioning.saneo import (MOTIVO_CONFIGURACION_INVALIDA,
                                            MOTIVO_CREDENCIAL_NO_ENCONTRADA,
                                            MOTIVO_DESTINO_NO_PERMITIDO,
                                            MOTIVO_HTTP_RECHAZADO,
                                            MOTIVO_HTTP_TRANSITORIO,
                                            MOTIVO_RED, MOTIVO_REDIRECCION,
                                            MOTIVO_TLS)
from app.modules.provisioning.tipos import (OPERACION_OTORGAR,
                                            OPERACION_REVOCAR,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)

VAR_CA = 'CONNECTOR_HTTP_CA_FILE'

OPERACIONES_OBLIGATORIAS = ('otorgar', 'revocar')
OPERACION_CONSULTAR = 'consultar'
METODOS = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')
METODOS_CON_CUERPO = ('POST', 'PUT', 'PATCH')
ESQUEMA_BEARER, ESQUEMA_BASIC, ESQUEMA_CABECERA = 'bearer', 'basic', 'cabecera'
ESQUEMAS = (ESQUEMA_BEARER, ESQUEMA_BASIC, ESQUEMA_CABECERA)
CAMPOS_PARAMS = ('base_path', 'auth') + OPERACIONES_OBLIGATORIAS + (
    OPERACION_CONSULTAR,)
CAMPOS_OPERACION = ('metodo', 'ruta', 'consulta', 'cuerpo', 'sin_cambios')

# Marcas permitidas de las plantillas (datos del servidor).
MARCAS = ('correo', 'nivel', 'plataforma')
_MARCA = re.compile(r'\{([^{}]*)\}')
_RUTA = re.compile(r'[A-Za-z0-9._~/:-]*')
_NOMBRE_CAMPO = re.compile(r'[A-Za-z0-9_.-]{1,50}')
_NOMBRE_CABECERA = re.compile(r'[A-Za-z][A-Za-z0-9-]{0,63}')
# Cabeceras que el conector controla: no se pueden usar para el secreto.
CABECERAS_RESERVADAS = frozenset({
    'host', 'authorization', 'content-type', 'content-length', 'accept',
    'connection', 'transfer-encoding', 'te', 'upgrade', 'expect', 'cookie',
    'user-agent', 'proxy-authorization', 'proxy-connection', 'keep-alive',
    'trailer'})

LARGO_MAXIMO_RUTA = 200
LARGO_MAXIMO_TEXTO = 200
MAXIMO_CONSULTA = 5
MAXIMO_CAMPOS_CUERPO = 20
PROFUNDIDAD_MAXIMA_CUERPO = 4
ESTADO_MINIMO_SIN_CAMBIOS, ESTADO_MAXIMO_SIN_CAMBIOS = 400, 499
SIN_CAMBIOS_POR_DEFECTO = {OPERACION_OTORGAR: (), OPERACION_REVOCAR: (404, 410)}
ESTADOS_TRANSITORIOS = frozenset({408, 425, 429, 500, 502, 503, 504})
MAXIMO_DIRECCIONES = 3  # IP validadas que se prueban si una no conecta

MENSAJE_OBLIGATORIO = 'Es obligatorio.'
MENSAJE_DESCONOCIDO = 'Campo no admitido.'
MENSAJE_OBJETO = 'Debe ser un objeto.'
MENSAJE_BASE = ('Usa una ruta que empiece con "/", con letras, dígitos y '
                '". _ ~ / : -", sin "..".')
MENSAJE_RUTA = ('Usa una ruta que empiece con "/", con letras, dígitos y '
                '". _ ~ / : -", sin "..", y solo las marcas '
                '{correo}, {nivel} y {plataforma}.')
MENSAJE_METODO = f'Usa uno de: {", ".join(METODOS)}.'
MENSAJE_ESQUEMA = f'Usa uno de: {", ".join(ESQUEMAS)}.'
MENSAJE_NOMBRE_CABECERA = ('Usa un nombre de cabecera propio (letras, '
                           'dígitos y "-"), distinto de las que controla el '
                           'conector.')
MENSAJE_NOMBRE_SOBRA = 'Solo aplica con el esquema "cabecera".'
MENSAJE_CONSULTA = (f'Debe ser un objeto de hasta {MAXIMO_CONSULTA} campos, '
                    'con nombres de letras, dígitos y "_.-" y plantillas '
                    'de texto.')
MENSAJE_CUERPO = ('Debe ser un objeto JSON (texto, números, booleanos, '
                  f'listas y objetos hasta {PROFUNDIDAD_MAXIMA_CUERPO} '
                  'niveles) con las marcas {correo}, {nivel} y {plataforma} '
                  'solo en valores de texto.')
MENSAJE_CUERPO_SIN_METODO = 'Solo aplica con POST, PUT o PATCH.'
MENSAJE_SIN_CAMBIOS = ('Debe ser una lista de estados HTTP '
                       f'{ESTADO_MINIMO_SIN_CAMBIOS}-{ESTADO_MAXIMO_SIN_CAMBIOS}.')


# --------------------------------------------------------------------------- #
# Esquema de params
# --------------------------------------------------------------------------- #

def _plantilla_valida(texto, con_marcas=True):
    """Texto con solo marcas conocidas y sin llaves sueltas."""
    if not isinstance(texto, str) or len(texto) > LARGO_MAXIMO_TEXTO:
        return False
    resto = texto
    for marca in _MARCA.findall(texto):
        if not con_marcas or marca not in MARCAS:
            return False
    resto = _MARCA.sub('', texto)
    return '{' not in resto and '}' not in resto


def _ruta_valida(ruta, con_marcas):
    if (not isinstance(ruta, str) or not ruta.startswith('/')
            or len(ruta) > LARGO_MAXIMO_RUTA
            or not _plantilla_valida(ruta, con_marcas)):
        return False
    literal = _MARCA.sub('', ruta)
    return (_RUTA.fullmatch(literal) is not None
            and '..' not in ruta.split('/') and '//' not in ruta)


def _cuerpo_valido(valor, nivel=1):
    if nivel > PROFUNDIDAD_MAXIMA_CUERPO + 1:
        return False
    if isinstance(valor, dict):
        return (len(valor) <= MAXIMO_CAMPOS_CUERPO
                and all(isinstance(k, str) and _NOMBRE_CAMPO.fullmatch(k)
                        and _cuerpo_valido(v, nivel + 1)
                        for k, v in valor.items()))
    if isinstance(valor, list):
        return (len(valor) <= MAXIMO_CAMPOS_CUERPO
                and all(_cuerpo_valido(v, nivel + 1) for v in valor))
    if isinstance(valor, str):
        return _plantilla_valida(valor)
    return valor is None or isinstance(valor, (bool, int))


def _consulta_valida(consulta):
    return (isinstance(consulta, dict) and len(consulta) <= MAXIMO_CONSULTA
            and all(isinstance(k, str) and _NOMBRE_CAMPO.fullmatch(k)
                    and _plantilla_valida(v) for k, v in consulta.items()))


def _sin_cambios_valido(estados):
    return (isinstance(estados, list) and len(estados) <= 10 and all(
        isinstance(e, int) and not isinstance(e, bool)
        and ESTADO_MINIMO_SIN_CAMBIOS <= e <= ESTADO_MAXIMO_SIN_CAMBIOS
        for e in estados))


def _errores_operacion(nombre, spec, errores):
    if not isinstance(spec, dict):
        errores[nombre] = MENSAJE_OBJETO
        return
    for clave in spec:
        if clave not in CAMPOS_OPERACION:
            errores[f'{nombre}.{clave}'] = MENSAJE_DESCONOCIDO
    metodo = spec.get('metodo')
    if metodo not in METODOS:
        errores[f'{nombre}.metodo'] = MENSAJE_METODO
    if not _ruta_valida(spec.get('ruta'), con_marcas=True):
        errores[f'{nombre}.ruta'] = MENSAJE_RUTA
    if 'consulta' in spec and not _consulta_valida(spec['consulta']):
        errores[f'{nombre}.consulta'] = MENSAJE_CONSULTA
    if 'cuerpo' in spec:
        if metodo in METODOS and metodo not in METODOS_CON_CUERPO:
            errores[f'{nombre}.cuerpo'] = MENSAJE_CUERPO_SIN_METODO
        elif not isinstance(spec['cuerpo'], dict) or not _cuerpo_valido(
                spec['cuerpo']):
            errores[f'{nombre}.cuerpo'] = MENSAJE_CUERPO
    if 'sin_cambios' in spec and not _sin_cambios_valido(spec['sin_cambios']):
        errores[f'{nombre}.sin_cambios'] = MENSAJE_SIN_CAMBIOS


def _errores_auth(auth, errores):
    if not isinstance(auth, dict):
        errores['auth'] = MENSAJE_OBLIGATORIO if auth is None else MENSAJE_OBJETO
        return
    for clave in auth:
        if clave not in ('esquema', 'nombre'):
            errores[f'auth.{clave}'] = MENSAJE_DESCONOCIDO
    esquema = auth.get('esquema')
    if esquema not in ESQUEMAS:
        errores['auth.esquema'] = MENSAJE_ESQUEMA
    nombre = auth.get('nombre')
    if esquema == ESQUEMA_CABECERA:
        if (not isinstance(nombre, str)
                or not _NOMBRE_CABECERA.fullmatch(nombre)
                or nombre.lower() in CABECERAS_RESERVADAS):
            errores['auth.nombre'] = MENSAJE_NOMBRE_CABECERA
    elif 'nombre' in auth:
        errores['auth.nombre'] = MENSAJE_NOMBRE_SOBRA


def validar_params(params):
    """`{campo: mensaje}` del esquema; vacío si `params` es válido."""
    errores = {}
    if not isinstance(params, dict):
        return {'params': MENSAJE_OBJETO}
    for clave in params:
        if clave not in CAMPOS_PARAMS:
            errores[str(clave)] = MENSAJE_DESCONOCIDO
    if 'base_path' in params and not _ruta_valida(params['base_path'],
                                                  con_marcas=False):
        errores['base_path'] = MENSAJE_BASE
    _errores_auth(params.get('auth'), errores)
    for nombre in OPERACIONES_OBLIGATORIAS:
        if params.get(nombre) is None:
            errores[nombre] = MENSAJE_OBLIGATORIO
        else:
            _errores_operacion(nombre, params[nombre], errores)
    if OPERACION_CONSULTAR in params:
        _errores_operacion(OPERACION_CONSULTAR, params[OPERACION_CONSULTAR],
                           errores)
    return errores


# --------------------------------------------------------------------------- #
# Plantillas
# --------------------------------------------------------------------------- #

def _sustituir(texto, valores, codificar=None):
    """Reemplaza las marcas en una sola pasada (el valor no se reinterpreta)."""
    def reemplazo(coincidencia):
        valor = valores[coincidencia.group(1)]
        return codificar(valor) if codificar else valor
    return _MARCA.sub(reemplazo, texto)


def _codificar(valor):
    return quote(valor, safe='')


def _en_cuerpo(valor, valores):
    if isinstance(valor, dict):
        return {k: _en_cuerpo(v, valores) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_en_cuerpo(v, valores) for v in valor]
    if isinstance(valor, str):
        return _sustituir(valor, valores)
    return valor


def _con_control(texto):
    return any(ord(c) < 32 or ord(c) == 127 for c in texto)


# --------------------------------------------------------------------------- #
# Conector
# --------------------------------------------------------------------------- #

class ConectorApi(Conector):
    """`transporte`, `getaddrinfo` y `archivo_ca` se inyectan en las pruebas;
    sin ellos: HTTPS real, DNS del sistema y `CONNECTOR_HTTP_CA_FILE`."""

    def __init__(self, destino, credencial, transporte=None,
                 getaddrinfo=None, archivo_ca=None):
        super().__init__(destino, credencial)
        self._transporte = transporte or TransporteHttps()
        self._getaddrinfo = getaddrinfo or socket.getaddrinfo
        self._archivo_ca = archivo_ca

    # -- armado de la petición ------------------------------------------- #

    def _cabecera_auth(self, auth):
        secreto = self.credencial.secreto or ''
        usuario = self.credencial.usuario or ''
        if not secreto or _con_control(secreto) or _con_control(usuario):
            return None
        esquema = auth['esquema']
        if esquema == ESQUEMA_BEARER:
            return 'Authorization', f'Bearer {secreto}'
        if esquema == ESQUEMA_BASIC:
            if not usuario or ':' in usuario:
                return None
            token = base64.b64encode(f'{usuario}:{secreto}'.encode()).decode()
            return 'Authorization', f'Basic {token}'
        return auth['nombre'], secreto

    def _peticion(self, nombre, params, solicitud):
        spec = params[nombre]
        valores = {'correo': solicitud.cuenta, 'nivel': solicitud.nivel,
                   'plataforma': str(solicitud.plataforma_id)}
        base = params.get('base_path', '').rstrip('/')
        ruta = base + _sustituir(spec['ruta'], valores, _codificar)
        if spec.get('consulta'):
            ruta += '?' + urlencode({k: _sustituir(v, valores)
                                     for k, v in spec['consulta'].items()},
                                    quote_via=quote)
        cuerpo = None
        cabeceras = {'Accept': 'application/json'}
        if spec.get('cuerpo') is not None:
            cuerpo = json.dumps(_en_cuerpo(spec['cuerpo'], valores),
                                separators=(',', ':')).encode('ascii')
            cabeceras['Content-Type'] = 'application/json'
        return spec['metodo'], ruta, cabeceras, cuerpo

    def _contexto(self):
        try:
            return crear_contexto(self._archivo_ca
                                  or os.environ.get(VAR_CA) or None)
        except (OSError, ssl.SSLError):
            return None

    # -- envío ------------------------------------------------------------ #

    def _enviar(self, ips, metodo, ruta, cabeceras, cuerpo, contexto):
        """Estado HTTP o un `ResultadoProveedor` de error."""
        for ip in ips[:MAXIMO_DIRECCIONES]:
            try:
                return self._transporte.enviar(
                    ip, self.destino.host, self.destino.puerto, metodo, ruta,
                    cabeceras, cuerpo, self.destino.tiempo_espera,
                    contexto).estado
            except (ssl.SSLEOFError, ssl.SSLZeroReturnError):
                continue
            except ssl.SSLError:
                return permanente(MOTIVO_TLS)
            except OSError:
                continue
            except http.client.HTTPException:
                break
        return transitorio(MOTIVO_RED)

    def _llamar(self, nombre, solicitud):
        """`(estado, None)` o `(None, ResultadoProveedor)` de error."""
        params = dict(self.destino.params)
        if validar_params(params):
            return None, permanente(MOTIVO_CONFIGURACION_INVALIDA)
        metodo, ruta, cabeceras, cuerpo = self._peticion(nombre, params,
                                                         solicitud)
        auth = self._cabecera_auth(params['auth'])
        if auth is None:
            return None, permanente(MOTIVO_CREDENCIAL_NO_ENCONTRADA)
        cabeceras[auth[0]] = auth[1]
        contexto = self._contexto()
        if contexto is None:
            return None, permanente(MOTIVO_TLS)
        try:
            ips = resolver_seguro(self.destino.host, self.destino.puerto,
                                  self._getaddrinfo)
        except DestinoNoPermitido:
            return None, permanente(MOTIVO_DESTINO_NO_PERMITIDO)
        except ErrorResolucion:
            return None, transitorio(MOTIVO_RED)
        resultado = self._enviar(ips, metodo, ruta, cabeceras, cuerpo,
                                 contexto)
        if isinstance(resultado, ResultadoProveedor):
            return None, resultado
        return resultado, None

    # -- clasificación ---------------------------------------------------- #

    @staticmethod
    def _error_http(estado):
        detalle = f'HTTP {estado}'
        if estado in ESTADOS_TRANSITORIOS:
            return transitorio(MOTIVO_HTTP_TRANSITORIO, detalle)
        if 300 <= estado < 400:
            return permanente(MOTIVO_REDIRECCION, detalle)
        return permanente(MOTIVO_HTTP_RECHAZADO, detalle)

    def _modificar(self, nombre, solicitud):
        estado, error = self._llamar(nombre, solicitud)
        if error is not None:
            return error
        if 200 <= estado < 300:
            return ResultadoProveedor(RESULTADO_EXITOSO)
        sin_cambios = self.destino.params[nombre].get(
            'sin_cambios', SIN_CAMBIOS_POR_DEFECTO[nombre])
        if estado in sin_cambios:
            return ResultadoProveedor(RESULTADO_SIN_CAMBIOS)
        return self._error_http(estado)

    def otorgar(self, solicitud):
        return self._modificar(OPERACION_OTORGAR, solicitud)

    def revocar(self, solicitud):
        return self._modificar(OPERACION_REVOCAR, solicitud)

    def consultar(self, solicitud):
        if OPERACION_CONSULTAR not in self.destino.params:
            return super().consultar(solicitud)
        estado, error = self._llamar(OPERACION_CONSULTAR, solicitud)
        if error is not None:
            return error
        if 200 <= estado < 300:
            return ResultadoProveedor(RESULTADO_EXITOSO, presente=True)
        if estado == 404:
            return ResultadoProveedor(RESULTADO_EXITOSO, presente=False)
        return self._error_http(estado)


TIPO = TipoConector(TIPO_API, ConectorApi, validar_params)
