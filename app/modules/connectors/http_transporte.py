"""Transporte HTTPS de los conectores (FNC-051, SEC-CON-06).

- Solo biblioteca estándar (`http.client` + `ssl`): no agrega dependencias.
- Se conecta a la **IP ya validada** (`destino_seguro`) y verifica el
  certificado contra el **nombre del host** (SNI y `check_hostname`), con
  `CERT_REQUIRED` y TLS 1.2 como mínimo; la CA del sistema o la de
  `CONNECTOR_HTTP_CA_FILE`. Nunca se desactiva la verificación.
- El tiempo de espera es por operación de red (conexión, envío y cada
  lectura), no del total de la petición.
- No sigue redirecciones: devuelve el estado tal cual y quien llama decide.
- No lee el cuerpo de la respuesta: solo el estado (no se guarda ni se
  registra nada que venga del servidor remoto).
"""
import http.client
import socket
import ssl
from dataclasses import dataclass


class ErrorConexion(OSError):
    """No se pudo abrir la conexión TCP (aún no se envió nada): único caso
    en que el conector prueba otra IP; después de enviar no se reintenta."""


@dataclass(frozen=True)
class RespuestaHttp:
    estado: int


def crear_contexto(archivo_ca=None):
    """Contexto TLS con verificación obligatoria."""
    contexto = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                          cafile=archivo_ca or None)
    contexto.minimum_version = ssl.TLSVersion.TLSv1_2
    contexto.verify_mode = ssl.CERT_REQUIRED
    contexto.check_hostname = True
    return contexto


class _ConexionFijada(http.client.HTTPSConnection):
    """Conecta a una IP concreta y valida el certificado contra el host."""

    def __init__(self, host, ip, puerto, contexto, tiempo_espera):
        super().__init__(host, puerto, timeout=tiempo_espera, context=contexto)
        self._ip = ip

    def connect(self):
        try:
            conexion = socket.create_connection((self._ip, self.port),
                                                self.timeout)
        except OSError as exc:
            raise ErrorConexion(str(exc)) from None
        try:
            self.sock = self._context.wrap_socket(conexion,
                                                  server_hostname=self.host)
        except BaseException:
            conexion.close()
            raise


class TransporteHttps:

    def enviar(self, ip, host, puerto, metodo, ruta, cabeceras, cuerpo,
               tiempo_espera, contexto):
        """Estado HTTP de la respuesta; las fallas de red o TLS se propagan."""
        conexion = _ConexionFijada(host, ip, puerto, contexto, tiempo_espera)
        try:
            conexion.request(metodo, ruta, body=cuerpo, headers=cabeceras)
            return RespuestaHttp(conexion.getresponse().status)
        finally:
            conexion.close()
