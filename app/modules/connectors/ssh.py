"""Conector tipo SSH (FNC-052, SEC-CON-04, ADR-005).

Otorga, revoca y consulta ejecutando **un comando fijo por operación** en el
servidor de la plataforma. Lo específico de cada plataforma va en `params`
(sin secretos); el código es genérico.

Esquema de `params` (cerrado: una clave desconocida se rechaza):
- `huellas` (lista de `SHA256:<base64>`, hasta 5): llaves del host fijadas
  (varias para rotarlas). Si falta, se exige `CONNECTOR_SSH_KNOWN_HOSTS_FILE`
  en el despliegue; sin ninguna de las dos no se conecta. Nunca se acepta una
  llave desconocida (sin confianza en el primer uso).
- `auth` (opcional): `{"metodo": "llave" | "contrasena"}`; por defecto
  `llave`. La contraseña solo si la plataforma no admite llave. La credencial
  (usuario y llave privada sin frase de paso, o contraseña) sale del gestor.
- `otorgar`, `revocar` (obligatorios) y `consultar` (opcional): `{"comando":
  ["/usr/local/bin/acceso", "otorgar"], "sin_cambios": [3], "transitorios":
  [75]}`; en `consultar`, `ausente` en lugar de `sin_cambios`.

Técnica contra la inyección (decisión del orquestador, pendiente de validar en
la prueba de concepto):
- El comando es **fijo y no contiene datos de la solicitud**: una lista de
  argumentos de la configuración (ruta absoluta y literales con la lista
  blanca `[A-Za-z0-9_./=:+-]`, sin `..`), que se arma con `shlex.quote` por
  si el valor llegara con otra forma. Nunca un shell con una cadena
  interpolada.
- Los datos variables (`correo`, `nivel`, `plataforma`) viajan por la entrada
  estándar como **una línea JSON** (`json.dumps`, ASCII): ningún shell ni
  analizador de argumentos los interpreta. Se recomienda en el servidor un
  comando forzado (`command="..."` con `restrict` en `authorized_keys`) que
  lea esa línea; el comando enviado queda entonces como información.
- Los valores se validan con las mismas reglas que el conector `api`
  (`_valores_seguros`: sin vacíos, `.`/`..` ni segmentos así, `{correo}` con
  `@`) y además sin caracteres de control.

Código de salida: `0` éxito (`presente` al consultar); `sin_cambios`/`ausente`
→ ya estaba así; `transitorios` (por defecto `[75]`, EX_TEMPFAIL) →
transitorio; un cierre sin código → transitorio; el resto, permanente. El
detalle es solo `salida <n>`: la salida remota nunca se guarda.

Red: se resuelve el DNS y se conecta a la IP validada (`destino_seguro`); solo
se prueba otra IP si falla la conexión o el saludo (aún sin credencial). Huella
distinta o credencial rechazada: permanente. `CONNECTOR_SSH_TIMEOUT_SECONDS`
es el **plazo único** de la operación (DNS, todas las IP, TCP, saludo,
autenticación, sesión y comando; vencido: transitorio `tiempo_agotado`); una
salida mayor que `CONNECTOR_SSH_MAX_OUTPUT_BYTES` es permanente.
"""
import json
import re
import shlex
import socket
import time

from app.modules.connectors.base import Conector
from app.modules.connectors.configuracion import cargar_configuracion
from app.modules.connectors.destino_seguro import (DestinoNoPermitido,
                                                   ErrorResolucion,
                                                   resolver_seguro)
from app.modules.connectors.registry import TipoConector
from app.modules.connectors.ssh_transporte import (AUTH_CONTRASENA, AUTH_LLAVE,
                                                   CODIGO_SIN_ESTADO,
                                                   ErrorAutenticacion,
                                                   ErrorConexionSsh,
                                                   ErrorHuella, ErrorSsh,
                                                   ErrorSalidaExcesiva,
                                                   ErrorTiempoEjecucion,
                                                   ErrorTransporteSsh,
                                                   PeticionSsh, TransporteSsh)
from app.modules.connectors.tipos import TIPO_SSH
from app.modules.provisioning.providers import (ResultadoProveedor,
                                                permanente, transitorio)
from app.modules.provisioning.saneo import (MOTIVO_CONFIGURACION_INVALIDA,
                                            MOTIVO_CREDENCIAL_NO_ENCONTRADA,
                                            MOTIVO_DESTINO_NO_PERMITIDO,
                                            MOTIVO_RED, MOTIVO_SSH_AUTENTICACION,
                                            MOTIVO_SSH_HUELLA,
                                            MOTIVO_SSH_RECHAZADO,
                                            MOTIVO_SSH_SALIDA,
                                            MOTIVO_SSH_TRANSITORIO,
                                            MOTIVO_TIEMPO_AGOTADO,
                                            MOTIVO_VALOR_NO_VALIDO)
from app.modules.provisioning.tipos import (OPERACION_OTORGAR,
                                            OPERACION_REVOCAR,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)

OPERACIONES_OBLIGATORIAS = ('otorgar', 'revocar')
OPERACION_CONSULTAR = 'consultar'
CAMPOS_PARAMS = ('huellas', 'auth') + OPERACIONES_OBLIGATORIAS + (
    OPERACION_CONSULTAR,)
CAMPOS_OPERACION = ('comando', 'sin_cambios', 'transitorios')
CAMPOS_CONSULTAR = ('comando', 'ausente', 'transitorios')
METODOS_AUTH = (AUTH_LLAVE, AUTH_CONTRASENA)

_HUELLA = re.compile(r'SHA256:[A-Za-z0-9+/]{43}')
_ARGUMENTO = re.compile(r'[A-Za-z0-9_./=:+-]{1,100}')
MAXIMO_HUELLAS = 5
MAXIMO_ARGUMENTOS = 8
MAXIMO_CODIGOS = 10
CODIGO_MINIMO, CODIGO_MAXIMO = 1, 255
CODIGOS_TRANSITORIOS_POR_DEFECTO = (75,)  # EX_TEMPFAIL de sysexits.h
MAXIMO_DIRECCIONES = 3  # IP validadas que se prueban si una no conecta

MENSAJE_OBLIGATORIO = 'Es obligatorio.'
MENSAJE_DESCONOCIDO = 'Campo no admitido.'
MENSAJE_OBJETO = 'Debe ser un objeto.'
MENSAJE_HUELLAS = (f'Usa hasta {MAXIMO_HUELLAS} huellas con el formato '
                   '"SHA256:<base64>" (ssh-keygen -lf), o configura el '
                   'known_hosts del despliegue.')
MENSAJE_METODO = f'Usa uno de: {", ".join(METODOS_AUTH)}.'
MENSAJE_COMANDO = (f'Usa una lista de hasta {MAXIMO_ARGUMENTOS} textos de '
                   'letras, dígitos y "_ . / = : + -"; el primero es una '
                   'ruta absoluta sin "..".')
MENSAJE_CODIGOS = (f'Debe ser una lista de hasta {MAXIMO_CODIGOS} códigos de '
                   f'salida entre {CODIGO_MINIMO} y {CODIGO_MAXIMO}.')
MENSAJE_CODIGOS_REPETIDOS = ('Un código no puede estar en dos clasificaciones '
                             'a la vez.')


# --------------------------------------------------------------------------- #
# Esquema de params
# --------------------------------------------------------------------------- #

def _comando_valido(comando):
    if (not isinstance(comando, list) or not 1 <= len(comando)
            <= MAXIMO_ARGUMENTOS
            or not all(isinstance(a, str) and _ARGUMENTO.fullmatch(a)
                       for a in comando)):
        return False
    ejecutable = comando[0]
    return (ejecutable.startswith('/') and '..' not in ejecutable.split('/')
            and '//' not in ejecutable)


def _codigos_validos(codigos):
    return (isinstance(codigos, list) and len(codigos) <= MAXIMO_CODIGOS
            and all(isinstance(c, int) and not isinstance(c, bool)
                    and CODIGO_MINIMO <= c <= CODIGO_MAXIMO for c in codigos))


def _errores_operacion(nombre, spec, errores):
    if not isinstance(spec, dict):
        errores[nombre] = MENSAJE_OBJETO
        return
    permitidos = (CAMPOS_CONSULTAR if nombre == OPERACION_CONSULTAR
                  else CAMPOS_OPERACION)
    for clave in spec:
        if clave not in permitidos:
            errores[f'{nombre}.{clave}'] = MENSAJE_DESCONOCIDO
    if not _comando_valido(spec.get('comando')):
        errores[f'{nombre}.comando'] = MENSAJE_COMANDO
    clasificados = []
    for clave in permitidos[1:]:
        if clave in spec:
            if not _codigos_validos(spec[clave]):
                errores[f'{nombre}.{clave}'] = MENSAJE_CODIGOS
            else:
                clasificados.extend(spec[clave])
    if len(set(clasificados)) != len(clasificados):
        errores[f'{nombre}.transitorios'] = MENSAJE_CODIGOS_REPETIDOS


def _huellas_validas(huellas):
    return (isinstance(huellas, list) and 1 <= len(huellas) <= MAXIMO_HUELLAS
            and all(isinstance(h, str) and _HUELLA.fullmatch(h)
                    for h in huellas))


def _errores_auth(auth, errores):
    if not isinstance(auth, dict):
        errores['auth'] = MENSAJE_OBJETO
        return
    for clave in auth:
        if clave != 'metodo':
            errores[f'auth.{clave}'] = MENSAJE_DESCONOCIDO
    if auth.get('metodo') not in METODOS_AUTH:
        errores['auth.metodo'] = MENSAJE_METODO


def errores_esquema(params, con_known_hosts):
    """`{campo: mensaje}` del esquema; `con_known_hosts`: el despliegue
    tiene `CONNECTOR_SSH_KNOWN_HOSTS_FILE` (alternativa a `huellas`)."""
    errores = {}
    if not isinstance(params, dict):
        return {'params': MENSAJE_OBJETO}
    for clave in params:
        if clave not in CAMPOS_PARAMS:
            errores[str(clave)] = MENSAJE_DESCONOCIDO
    if 'huellas' in params:
        if not _huellas_validas(params['huellas']):
            errores['huellas'] = MENSAJE_HUELLAS
    elif not con_known_hosts:
        errores['huellas'] = MENSAJE_HUELLAS
    if 'auth' in params:
        _errores_auth(params['auth'], errores)
    for nombre in OPERACIONES_OBLIGATORIAS:
        if params.get(nombre) is None:
            errores[nombre] = MENSAJE_OBLIGATORIO
        else:
            _errores_operacion(nombre, params[nombre], errores)
    if OPERACION_CONSULTAR in params:
        _errores_operacion(OPERACION_CONSULTAR, params[OPERACION_CONSULTAR],
                           errores)
    return errores


def validar_params(params):
    """Esquema de `params` con el `known_hosts` del despliegue actual."""
    return errores_esquema(params, bool(cargar_configuracion().ssh_known_hosts))


# --------------------------------------------------------------------------- #
# Armado de la orden (sin datos de la solicitud en el comando)
# --------------------------------------------------------------------------- #

def _comando(spec):
    """Cadena de `exec` formada solo con argumentos de la configuración."""
    return ' '.join(shlex.quote(argumento) for argumento in spec['comando'])


def _entrada(operacion, solicitud):
    """Línea JSON con los datos del servidor, para la entrada estándar."""
    datos = {'operacion': operacion, 'correo': solicitud.cuenta,
             'nivel': solicitud.nivel,
             'plataforma': str(solicitud.plataforma_id)}
    return (json.dumps(datos, separators=(',', ':')) + '\n').encode('ascii')


def _con_control(texto):
    return any(ord(c) < 32 or ord(c) == 127 for c in texto)


def _valores_seguros(solicitud):
    """Mismas reglas del conector `api` y sin caracteres de control."""
    valores = (solicitud.cuenta, solicitud.nivel, str(solicitud.plataforma_id))
    if any(_con_control(v) for v in valores):
        return False
    segmentos = [re.split(r'[/\\]', v) for v in valores]
    if any(not v or any(s in ('.', '..') for s in partes)
           for v, partes in zip(valores, segmentos)):
        return False
    local, arroba, dominio = solicitud.cuenta.partition('@')
    return bool(local and arroba and dominio)


# --------------------------------------------------------------------------- #
# Conector
# --------------------------------------------------------------------------- #

_ERRORES = (
    (ErrorHuella, permanente, MOTIVO_SSH_HUELLA),
    (ErrorAutenticacion, permanente, MOTIVO_SSH_AUTENTICACION),
    (ErrorSalidaExcesiva, permanente, MOTIVO_SSH_SALIDA),
    (ErrorTiempoEjecucion, transitorio, MOTIVO_TIEMPO_AGOTADO),
    (ErrorTransporteSsh, transitorio, MOTIVO_RED),
)


class ConectorSsh(Conector):
    """`transporte`, `getaddrinfo` y `configuracion` se inyectan en las
    pruebas; sin ellos: SSH real, DNS del sistema y variables `CONNECTOR_*`."""

    def __init__(self, destino, credencial, transporte=None, getaddrinfo=None,
                 configuracion=None, reloj=time.monotonic):
        super().__init__(destino, credencial)
        self._transporte = transporte or TransporteSsh()
        self._getaddrinfo = getaddrinfo or socket.getaddrinfo
        self._configuracion = configuracion
        self._reloj = reloj

    def _peticion(self, ip, params, spec, operacion, solicitud, cfg, limite):
        huellas = tuple(params.get('huellas', ()))
        return PeticionSsh(
            ip=ip, host=self.destino.host, puerto=self.destino.puerto,
            usuario=self.credencial.usuario,
            secreto=self.credencial.secreto,
            metodo_auth=params.get('auth', {}).get('metodo', AUTH_LLAVE),
            comando=_comando(spec), entrada=_entrada(operacion, solicitud),
            huellas=huellas,
            archivo_known_hosts='' if huellas else cfg.ssh_known_hosts,
            tiempo_conexion=self.destino.tiempo_espera,
            limite=limite,
            maximo_salida=cfg.ssh_maximo_salida)

    def _ejecutar(self, ips, construir, limite):
        """Código de salida o un `ResultadoProveedor` de error."""
        for ip in ips[:MAXIMO_DIRECCIONES]:
            if self._reloj() >= limite:
                return transitorio(MOTIVO_TIEMPO_AGOTADO)
            try:
                return self._transporte.ejecutar(construir(ip))
            except ErrorConexionSsh:
                continue  # sin credencial enviada: se puede probar otra IP
            except ErrorSsh as exc:
                for clase, fabrica, motivo in _ERRORES:
                    if isinstance(exc, clase):
                        return fabrica(motivo)
                return transitorio(MOTIVO_RED)
        return transitorio(MOTIVO_RED)

    def _llamar(self, operacion, solicitud):
        """`(código, None)` o `(None, ResultadoProveedor)` de error."""
        params = dict(self.destino.params)
        cfg = self._configuracion or cargar_configuracion()
        limite = self._reloj() + cfg.ssh_tiempo  # plazo único de la operación
        if errores_esquema(params, bool(cfg.ssh_known_hosts)):
            return None, permanente(MOTIVO_CONFIGURACION_INVALIDA)
        if not _valores_seguros(solicitud):
            return None, permanente(MOTIVO_VALOR_NO_VALIDO)
        if not self.credencial.usuario or not self.credencial.secreto:
            return None, permanente(MOTIVO_CREDENCIAL_NO_ENCONTRADA)
        try:
            ips = resolver_seguro(self.destino.host, self.destino.puerto,
                                  self._getaddrinfo)
        except DestinoNoPermitido:
            return None, permanente(MOTIVO_DESTINO_NO_PERMITIDO)
        except ErrorResolucion:
            return None, transitorio(MOTIVO_RED)
        spec = params[operacion]
        resultado = self._ejecutar(ips, lambda ip: self._peticion(
            ip, params, spec, operacion, solicitud, cfg, limite), limite)
        if isinstance(resultado, ResultadoProveedor):
            return None, resultado
        return resultado, None

    # -- clasificación ---------------------------------------------------- #

    @staticmethod
    def _error_codigo(codigo, spec):
        if codigo == CODIGO_SIN_ESTADO:
            return transitorio(MOTIVO_RED)
        transitorios = spec.get('transitorios', CODIGOS_TRANSITORIOS_POR_DEFECTO)
        detalle = f'salida {codigo}'
        if codigo in transitorios:
            return transitorio(MOTIVO_SSH_TRANSITORIO, detalle)
        return permanente(MOTIVO_SSH_RECHAZADO, detalle)

    def _modificar(self, operacion, solicitud):
        codigo, error = self._llamar(operacion, solicitud)
        if error is not None:
            return error
        if codigo == 0:
            return ResultadoProveedor(RESULTADO_EXITOSO)
        spec = self.destino.params[operacion]
        if codigo in spec.get('sin_cambios', ()):
            return ResultadoProveedor(RESULTADO_SIN_CAMBIOS)
        return self._error_codigo(codigo, spec)

    def otorgar(self, solicitud):
        return self._modificar(OPERACION_OTORGAR, solicitud)

    def revocar(self, solicitud):
        return self._modificar(OPERACION_REVOCAR, solicitud)

    def consultar(self, solicitud):
        if OPERACION_CONSULTAR not in self.destino.params:
            return super().consultar(solicitud)
        codigo, error = self._llamar(OPERACION_CONSULTAR, solicitud)
        if error is not None:
            return error
        spec = self.destino.params[OPERACION_CONSULTAR]
        if codigo == 0:
            return ResultadoProveedor(RESULTADO_EXITOSO, presente=True)
        if codigo in spec.get('ausente', ()):
            return ResultadoProveedor(RESULTADO_EXITOSO, presente=False)
        return self._error_codigo(codigo, spec)


TIPO = TipoConector(TIPO_SSH, ConectorSsh, validar_params)
