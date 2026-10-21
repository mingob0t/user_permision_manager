"""Cliente de Vaultwarden de solo lectura (FNC-068, ADR-005 alternativa A).

Decisión (ficha FNC-068): API HTTP compatible con Bitwarden y descifrado del
lado del cliente con `cryptography`; sin la CLI `bw` (sesión desbloqueada y
Node en el servidor, ADR-005 B) ni el SDK de Bitwarden (no es compatible con
Vaultwarden ni con su API de cuentas).

Flujo de `leer(referencia)`:
1. Sesión: `POST /identity/connect/token` (`client_credentials` con la llave de
   API personal). Con la respuesta (`Kdf*`, `Key`, `PrivateKey`; si faltan,
   `POST /identity/accounts/prelogin` y el perfil de `sync`) se derivan en
   memoria la clave de usuario y la llave privada. La sesión vive hasta
   `expires_in - MARGEN_TOKEN_SEGUNDOS`.
2. `GET /api/sync?excludeDomains=true`; un 401 renueva la sesión una sola vez.
3. Se toma la organización dueña de `VAULTWARDEN_COLLECTION_ID`, se descifra su
   clave y se buscan los ítems de tipo *login* de esa colección, no borrados,
   cuyo **nombre** es exactamente la referencia. Cero → no encontrada; más de
   uno → ambigua (no se adivina). Secreto = `login.password`; usuario =
   `login.username`.

Reglas: solo `https`, TLS 1.2+ con certificado y nombre validados, sin
proxies del entorno, sin redirecciones, tiempo de espera por operación y
respuestas de a lo más `TAMANO_MAXIMO_RESPUESTA`. Falla cerrado: cualquier
duda es un error. Los errores y los logs llevan solo el tipo y el estado
HTTP, nunca cuerpos, tokens, claves ni valores.
"""
import http.client
import json
import logging
import ssl
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlencode

from app.modules.secretos import cifrado
from app.modules.secretos.configuracion import (ErrorConfiguracionSecretos,
                                                cargar_configuracion)

logger = logging.getLogger(__name__)

RUTA_TOKEN = '/identity/connect/token'
RUTA_PRELOGIN = '/identity/accounts/prelogin'
RUTA_SYNC = '/api/sync?excludeDomains=true'
ALCANCE = 'api'
TIPO_DISPOSITIVO = '25'           # Linux CLI en el enum de Bitwarden
NOMBRE_DISPOSITIVO = 'pokemon-portal'
# Id de dispositivo estable por cuenta: evita registrar uno nuevo por arranque.
ESPACIO_DISPOSITIVO = uuid.UUID('6f1c2d3e-0a4b-4c5d-8e9f-a0b1c2d3e4f5')
TIPO_ITEM_LOGIN = 1

TAMANO_MAXIMO_RESPUESTA = 8 * 1024 * 1024  # bytes
MARGEN_TOKEN_SEGUNDOS = 60
VIDA_TOKEN_POR_DEFECTO = 3600
VIDA_TOKEN_MAXIMA = 86400
ESTADOS_TRANSITORIOS = frozenset({408, 425, 429, 500, 502, 503, 504})
ESTADO_NO_AUTORIZADO = 401


class ErrorDeGestor(Exception):
    """Base: el texto es solo para el log interno; nunca lleva valores."""


class SecretoNoEncontrado(ErrorDeGestor):
    """No hay un ítem con ese nombre en la colección (permanente)."""


class SecretoAmbiguo(SecretoNoEncontrado):
    """Hay más de un ítem con ese nombre en la colección (permanente)."""


class GestorCaido(ErrorDeGestor):
    """Vaultwarden no respondió o respondió con un error transitorio."""


class GestorMalConfigurado(ErrorDeGestor):
    """Configuración, credencial de arranque o datos rechazados (permanente)."""


@dataclass(frozen=True)
class ItemSecreto:
    secreto: str = field(repr=False)
    usuario: str | None = None

    def __str__(self):
        return repr(self)


@dataclass(frozen=True)
class Respuesta:
    estado: int
    cuerpo: bytes = field(repr=False)


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    """Una redirección termina en `HTTPError` 3xx: nunca se sigue."""

    def redirect_request(self, *args, **kwargs):
        return None


def contexto_tls(ca_cert_file=None):
    """TLS 1.2+, certificado obligatorio y nombre de host verificado."""
    contexto = ssl.create_default_context(cafile=ca_cert_file)
    contexto.minimum_version = ssl.TLSVersion.TLSv1_2
    contexto.verify_mode = ssl.CERT_REQUIRED
    contexto.check_hostname = True
    return contexto


class TransporteHttps:
    """HTTPS con `urllib` (sin dependencias nuevas)."""

    def __init__(self, configuracion):
        self._tiempo = configuracion.tiempo_espera
        self._abridor = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(
                context=contexto_tls(configuracion.ca_cert_file)),
            _SinRedirecciones())

    def __call__(self, metodo, url, cabeceras, cuerpo=None):
        peticion = urllib.request.Request(url, data=cuerpo, method=metodo,
                                          headers=cabeceras)
        try:
            with self._abridor.open(peticion, timeout=self._tiempo) as resp:
                return Respuesta(resp.status, _leer_acotado(resp))
        except urllib.error.HTTPError as exc:
            exc.close()
            return Respuesta(exc.code, b'')
        except (urllib.error.URLError, OSError, ValueError,
                http.client.HTTPException) as exc:
            # `IncompleteRead`, `BadStatusLine`: conexión cortada (B1).
            # `urllib` envuelve el error de TLS en `URLError.reason`.
            causa = getattr(exc, 'reason', exc)
            if isinstance(causa, ssl.SSLCertVerificationError):
                raise GestorMalConfigurado(
                    'Certificado de Vaultwarden no válido.') from None
            raise GestorCaido(f'Vaultwarden no responde ({type(exc).__name__}).') \
                from None


def _leer_acotado(respuesta):
    datos = respuesta.read(TAMANO_MAXIMO_RESPUESTA + 1)
    if len(datos) > TAMANO_MAXIMO_RESPUESTA:
        raise GestorMalConfigurado('Respuesta de Vaultwarden demasiado grande.')
    return datos


def _campo(datos, nombre):
    """Campo de un objeto JSON sin importar mayúsculas (Vaultwarden usó
    PascalCase y hoy camelCase)."""
    if not isinstance(datos, dict):
        return None
    if nombre in datos:
        return datos[nombre]
    buscado = nombre.lower()
    for clave, valor in datos.items():
        if isinstance(clave, str) and clave.lower() == buscado:
            return valor
    return None


def _lista(datos, nombre):
    valor = _campo(datos, nombre)
    return valor if isinstance(valor, list) else []


def _entero(valor):
    return valor if isinstance(valor, int) and not isinstance(valor, bool) \
        else None


@dataclass
class _Sesion:
    token: str = field(repr=False)
    vence: float
    clave_usuario: cifrado.ClaveSimetrica | None = field(default=None,
                                                         repr=False)
    llave_privada: object = field(default=None, repr=False)
    datos_token: dict = field(default_factory=dict, repr=False)


class ClienteVaultwarden:
    """Lee ítems de la colección configurada. Seguro entre hilos."""

    def __init__(self, configuracion, transporte=None, reloj=time.monotonic):
        self._cfg = configuracion
        self._transporte = transporte or TransporteHttps(configuracion)
        self._reloj = reloj
        self._sesion = None
        self._candado = threading.Lock()

    def __repr__(self):
        return '<ClienteVaultwarden>'

    # ---------------------------------------------------------------- HTTP

    def _pedir(self, metodo, ruta, cabeceras, cuerpo=None):
        respuesta = self._transporte(metodo, self._cfg.url + ruta, cabeceras,
                                     cuerpo)
        return respuesta

    @staticmethod
    def _json(respuesta, operacion):
        if respuesta.estado in ESTADOS_TRANSITORIOS:
            raise GestorCaido(f'Vaultwarden: {operacion} respondió '
                              f'{respuesta.estado}.')
        if not 200 <= respuesta.estado < 300:
            raise GestorMalConfigurado(f'Vaultwarden: {operacion} respondió '
                                       f'{respuesta.estado}.')
        try:
            datos = json.loads(respuesta.cuerpo)
        except (ValueError, UnicodeDecodeError):
            raise GestorCaido(f'Vaultwarden: {operacion} sin JSON válido.') \
                from None
        except RecursionError:
            # Anidado anómalo: no es un corte de red, no se reintenta (B1).
            raise GestorMalConfigurado(
                f'Vaultwarden: {operacion} con JSON demasiado anidado.') \
                from None
        if not isinstance(datos, dict):
            raise GestorMalConfigurado(f'Vaultwarden: {operacion} inesperado.')
        return datos

    # -------------------------------------------------------------- Sesión

    def _iniciar_sesion(self):
        cfg = self._cfg
        formulario = urlencode({
            'grant_type': 'client_credentials', 'scope': ALCANCE,
            'client_id': cfg.client_id, 'client_secret': cfg.client_secret,
            'deviceType': TIPO_DISPOSITIVO, 'deviceName': NOMBRE_DISPOSITIVO,
            'deviceIdentifier': str(uuid.uuid5(ESPACIO_DISPOSITIVO,
                                               cfg.client_id)),
        }).encode()
        datos = self._json(self._pedir('POST', RUTA_TOKEN, {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'}, formulario), 'el inicio de sesión')
        token = _campo(datos, 'access_token')
        if not isinstance(token, str) or not token:
            raise GestorMalConfigurado('Vaultwarden: sesión sin token.')
        vida = _entero(_campo(datos, 'expires_in')) or VIDA_TOKEN_POR_DEFECTO
        vida = min(max(vida - MARGEN_TOKEN_SEGUNDOS, 0), VIDA_TOKEN_MAXIMA)
        return _Sesion(token=token, vence=self._reloj() + vida,
                       datos_token=datos)

    def _parametros_kdf(self, sesion):
        datos = sesion.datos_token
        if _entero(_campo(datos, 'Kdf')) is None:
            datos = self._json(self._pedir(
                'POST', RUTA_PRELOGIN,
                {'Content-Type': 'application/json',
                 'Accept': 'application/json'},
                json.dumps({'email': self._cfg.correo}).encode()), 'prelogin')
        return (_entero(_campo(datos, 'Kdf')),
                _entero(_campo(datos, 'KdfIterations')),
                _entero(_campo(datos, 'KdfMemory')),
                _entero(_campo(datos, 'KdfParallelism')))

    def _abrir_claves(self, sesion, perfil):
        """Clave de usuario y llave privada (una vez por sesión)."""
        if sesion.clave_usuario is not None:
            return
        clave = _campo(sesion.datos_token, 'Key') or _campo(perfil, 'key')
        privada = (_campo(sesion.datos_token, 'PrivateKey')
                   or _campo(perfil, 'privateKey'))
        if not isinstance(clave, str) or not isinstance(privada, str):
            raise GestorMalConfigurado('Vaultwarden: cuenta sin claves.')
        kdf, iteraciones, memoria, paralelismo = self._parametros_kdf(sesion)
        try:
            maestra = cifrado.derivar_clave_maestra(
                self._cfg.contrasena_maestra, self._cfg.correo, kdf,
                iteraciones, memoria, paralelismo)
            usuario = cifrado.ClaveSimetrica.desde_bytes(
                cifrado.descifrar_simetrico(clave, cifrado.estirar(maestra)))
            sesion.llave_privada = cifrado.cargar_llave_privada(
                cifrado.descifrar_simetrico(privada, usuario))
        except cifrado.ErrorDeCifrado:
            raise GestorMalConfigurado(
                'Vaultwarden: no se pudo abrir la bóveda (contraseña maestra, '
                'correo o KDF).') from None
        sesion.clave_usuario = usuario

    def _sesion_vigente(self):
        if self._sesion is None or self._sesion.vence <= self._reloj():
            self._sesion = self._iniciar_sesion()
        return self._sesion

    def _sincronizar(self):
        for intento in range(2):
            sesion = self._sesion_vigente()
            respuesta = self._pedir('GET', RUTA_SYNC, {
                'Authorization': f'Bearer {sesion.token}',
                'Accept': 'application/json'})
            if respuesta.estado == ESTADO_NO_AUTORIZADO and intento == 0:
                self._sesion = None
                continue
            return sesion, self._json(respuesta, 'la sincronización')
        raise GestorMalConfigurado('Vaultwarden: sesión rechazada.')

    # -------------------------------------------------------------- Lectura

    def _clave_coleccion(self, sesion, datos):
        coleccion = self._cfg.coleccion_id
        organizacion = None
        for item in _lista(datos, 'collections'):
            if str(_campo(item, 'id') or '').lower() == coleccion:
                organizacion = str(_campo(item, 'organizationId') or '').lower()
                break
        if not organizacion:
            raise GestorMalConfigurado(
                'Vaultwarden: la cuenta no ve la colección configurada.')
        perfil = _campo(datos, 'profile') or {}
        for org in _lista(perfil, 'organizations'):
            if str(_campo(org, 'id') or '').lower() == organizacion:
                try:
                    return organizacion, cifrado.ClaveSimetrica.desde_bytes(
                        cifrado.descifrar_rsa(_campo(org, 'key'),
                                              sesion.llave_privada))
                except cifrado.ErrorDeCifrado:
                    break
        raise GestorMalConfigurado(
            'Vaultwarden: sin clave de la organización de la colección.')

    def _candidatos(self, datos, organizacion):
        coleccion = self._cfg.coleccion_id
        for item in _lista(datos, 'ciphers'):
            if (_campo(item, 'type') == TIPO_ITEM_LOGIN
                    and not _campo(item, 'deletedDate')
                    and str(_campo(item, 'organizationId') or '').lower()
                    == organizacion
                    and coleccion in {str(c).lower() for c in
                                      _lista(item, 'collectionIds')}):
                yield item

    @staticmethod
    def _clave_item(item, clave_org):
        propia = _campo(item, 'key')
        if not propia:
            return clave_org
        return cifrado.ClaveSimetrica.desde_bytes(
            cifrado.descifrar_simetrico(propia, clave_org))

    def leer(self, referencia):
        """`ItemSecreto` del ítem llamado `referencia` en la colección."""
        if not isinstance(referencia, str) or not referencia:
            raise SecretoNoEncontrado('Referencia vacía.')
        with self._candado:
            sesion, datos = self._sincronizar()
            self._abrir_claves(sesion, _campo(datos, 'profile') or {})
            organizacion, clave_org = self._clave_coleccion(sesion, datos)
        encontrados, ilegibles = [], 0
        for item in self._candidatos(datos, organizacion):
            try:
                clave = self._clave_item(item, clave_org)
                if cifrado.descifrar_texto(_campo(item, 'name'), clave) \
                        == referencia:
                    encontrados.append((item, clave))
            except cifrado.ErrorDeCifrado:
                ilegibles += 1
        if ilegibles:
            logger.warning('Vaultwarden: %d ítems de la colección no se '
                           'pudieron descifrar.', ilegibles)
        if not encontrados:
            raise SecretoNoEncontrado('Sin ítem para la referencia.')
        # Solo cuentan los ítems legibles y con contraseña: uno ilegible con
        # el mismo nombre no vuelve ambiguo al legible (B2).
        legibles, sin_contrasena = [], 0
        for item, clave in encontrados:
            leido = self._leer_login(item, clave)
            if leido is None:
                continue
            if not leido.secreto:
                sin_contrasena += 1
                continue
            legibles.append(leido)
        if len(legibles) > 1:
            raise SecretoAmbiguo('Más de un ítem para la referencia.')
        if legibles:
            if len(encontrados) > 1:
                logger.warning('Vaultwarden: se ignoraron %d ítems ilegibles o '
                               'sin contraseña con el mismo nombre.',
                               len(encontrados) - 1)
            return legibles[0]
        if sin_contrasena:
            raise SecretoNoEncontrado('El ítem no tiene contraseña.')
        raise GestorMalConfigurado('Vaultwarden: ítem ilegible.')

    @staticmethod
    def _leer_login(item, clave):
        """`ItemSecreto` del *login* (secreto vacío si no tiene), o `None`
        si no se puede descifrar."""
        login = _campo(item, 'login') or {}
        cifrada = _campo(login, 'password')
        try:
            secreto = cifrado.descifrar_texto(cifrada, clave) if cifrada else ''
            usuario_cifrado = _campo(login, 'username')
            usuario = (cifrado.descifrar_texto(usuario_cifrado, clave).strip()
                       if usuario_cifrado else '')
        except cifrado.ErrorDeCifrado:
            return None
        return ItemSecreto(secreto=secreto, usuario=usuario or None)

    def reiniciar(self):
        with self._candado:
            self._sesion = None


_CLIENTE = None
_CANDADO_CLIENTE = threading.Lock()


def cliente_del_entorno(entorno=None):
    """Cliente compartido del proceso para la configuración vigente."""
    global _CLIENTE
    try:
        cfg = cargar_configuracion(entorno)
    except ErrorConfiguracionSecretos as exc:
        raise GestorMalConfigurado(str(exc)) from None
    with _CANDADO_CLIENTE:
        if _CLIENTE is None or _CLIENTE._cfg != cfg:
            _CLIENTE = ClienteVaultwarden(cfg)
        return _CLIENTE


def reiniciar_cliente():
    """Olvida el cliente compartido y su sesión (pruebas o cambio de cuenta)."""
    global _CLIENTE
    with _CANDADO_CLIENTE:
        _CLIENTE = None
