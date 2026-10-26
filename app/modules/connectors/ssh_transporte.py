"""Transporte SSH de los conectores (FNC-052, SEC-CON-04, SEC-CON-06).

- Usa `paramiko.Transport` sobre un socket abierto **a la IP ya validada**
  (`destino_seguro`): nunca `SSHClient`, así que no hay `AutoAddPolicy`, ni
  `ssh_config`, ni `ProxyCommand`/`ProxyJump`, ni agente (no se consulta ni se
  reenvía), ni túneles ni reenvío de puertos; solo un canal `exec`.
- La llave del host se verifica **antes** de enviar la credencial: contra las
  huellas `SHA256:` fijadas en `params` o contra el `known_hosts` del
  despliegue (`CONNECTOR_SSH_KNOWN_HOSTS_FILE`). Sin coincidencia →
  `ErrorHuella` (permanente); no hay confianza en el primer uso.
- Sin *pty*. El comando es fijo (sin datos de la solicitud) y los datos van
  por la entrada estándar. De la salida remota solo se cuentan los bytes
  (límite) y se descarta: nunca se guarda ni se devuelve; sale el código de
  salida.
- Algoritmos débiles (`ssh-rsa` con SHA-1 y `ssh-dss`) desactivados.
"""
import hmac
import io
import socket
import time
from dataclasses import dataclass, field

import paramiko

PUERTO_SSH_ESTANDAR = 22
INTERVALO_LECTURA_SEGUNDOS = 0.05
TAMANO_LECTURA = 4096
CODIGO_SIN_ESTADO = -1  # el canal se cerró sin código de salida
ALGORITMOS_DESACTIVADOS = {'keys': ['ssh-rsa', 'ssh-dss'],
                           'pubkeys': ['ssh-rsa', 'ssh-dss']}
TIPOS_DE_LLAVE = (paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key)

AUTH_LLAVE = 'llave'
AUTH_CONTRASENA = 'contrasena'


class ErrorSsh(Exception):
    """Base: el texto es solo interno; nunca lleva datos del servidor."""


class ErrorConexionSsh(ErrorSsh):
    """TCP o saludo SSH sin completar (transitorio): se puede probar otra IP."""


class ErrorTransporteSsh(ErrorSsh):
    """Falla de red tras autenticar (transitorio): no se reintenta."""


class ErrorHuella(ErrorSsh):
    """La llave del host no coincide (permanente)."""


class ErrorAutenticacion(ErrorSsh):
    """Credencial rechazada o llave inválida (permanente)."""


class ErrorSalidaExcesiva(ErrorSsh):
    """El comando devolvió más bytes que el límite (permanente)."""


class ErrorTiempoEjecucion(ErrorSsh):
    """El comando no terminó a tiempo (transitorio)."""


@dataclass(frozen=True)
class PeticionSsh:
    """Todo lo que `ejecutar` necesita (sin lógica de negocio)."""

    ip: str
    host: str
    puerto: int
    usuario: str
    secreto: str = field(repr=False)
    metodo_auth: str
    comando: str
    entrada: bytes
    huellas: tuple
    archivo_known_hosts: str
    tiempo_conexion: int
    tiempo_ejecucion: int
    maximo_salida: int


def cargar_llave(texto):
    """Llave privada (RSA, ECDSA o Ed25519) sin frase de paso, o
    `ErrorAutenticacion`."""
    for tipo in TIPOS_DE_LLAVE:
        try:
            return tipo.from_private_key(io.StringIO(texto))
        except (paramiko.SSHException, ValueError, TypeError):
            continue
    raise ErrorAutenticacion()


def _nombre_known_hosts(host, puerto):
    return host if puerto == PUERTO_SSH_ESTANDAR else f'[{host}]:{puerto}'


def _huella_en_known_hosts(clave, peticion):
    try:
        conocidas = paramiko.HostKeys(peticion.archivo_known_hosts)
    except (OSError, paramiko.SSHException):
        return False
    entradas = conocidas.lookup(_nombre_known_hosts(peticion.host,
                                                    peticion.puerto))
    fijada = entradas.get(clave.get_name()) if entradas else None
    return fijada is not None and hmac.compare_digest(fijada.asbytes(),
                                                      clave.asbytes())


def llave_de_host_valida(clave, peticion):
    """`True` solo si la llave del servidor es la fijada (huellas o
    `known_hosts`); sin ninguna de las dos fuentes, nunca."""
    if peticion.huellas:
        huella = clave.fingerprint.encode()
        return any(hmac.compare_digest(huella, h.encode())
                   for h in peticion.huellas)
    if peticion.archivo_known_hosts:
        return _huella_en_known_hosts(clave, peticion)
    return False


def _abrir(peticion):
    try:
        conexion = socket.create_connection((peticion.ip, peticion.puerto),
                                            peticion.tiempo_conexion)
    except OSError:
        raise ErrorConexionSsh() from None
    transporte = paramiko.Transport(
        conexion, disabled_algorithms=ALGORITMOS_DESACTIVADOS)
    transporte.banner_timeout = peticion.tiempo_conexion
    transporte.auth_timeout = peticion.tiempo_conexion
    try:
        transporte.start_client(timeout=peticion.tiempo_conexion)
    except (paramiko.SSHException, OSError, EOFError):
        transporte.close()
        raise ErrorConexionSsh() from None
    return transporte


def _autenticar(transporte, peticion, llave):
    try:
        if peticion.metodo_auth == AUTH_LLAVE:
            transporte.auth_publickey(peticion.usuario, llave)
        else:
            transporte.auth_password(peticion.usuario, peticion.secreto,
                                     fallback=False)
    except paramiko.AuthenticationException:
        raise ErrorAutenticacion() from None
    except (paramiko.SSHException, OSError, EOFError):
        raise ErrorTransporteSsh() from None


def _ejecutar_canal(transporte, peticion):
    """Código de salida; la salida remota se cuenta y se descarta."""
    limite = time.monotonic() + peticion.tiempo_ejecucion
    try:
        canal = transporte.open_session(timeout=peticion.tiempo_conexion)
        canal.settimeout(peticion.tiempo_ejecucion)
        canal.exec_command(peticion.comando)
        canal.sendall(peticion.entrada)
        canal.shutdown_write()
        total = 0
        while not canal.exit_status_ready():
            if time.monotonic() > limite:
                raise ErrorTiempoEjecucion()
            leido = 0
            if canal.recv_ready():
                leido += len(canal.recv(TAMANO_LECTURA))
            if canal.recv_stderr_ready():
                leido += len(canal.recv_stderr(TAMANO_LECTURA))
            total += leido
            if total > peticion.maximo_salida:
                raise ErrorSalidaExcesiva()
            if not leido:
                time.sleep(INTERVALO_LECTURA_SEGUNDOS)
        while canal.recv_ready() or canal.recv_stderr_ready():
            total += len(canal.recv(TAMANO_LECTURA)
                         if canal.recv_ready()
                         else canal.recv_stderr(TAMANO_LECTURA))
            if total > peticion.maximo_salida:
                raise ErrorSalidaExcesiva()
        return canal.exit_status
    except (paramiko.SSHException, OSError, EOFError):
        raise ErrorTransporteSsh() from None


class TransporteSsh:

    def ejecutar(self, peticion):
        """Código de salida del comando remoto (`CODIGO_SIN_ESTADO` si el
        canal se cerró sin él). Las fallas se propagan como `ErrorSsh`."""
        llave = (cargar_llave(peticion.secreto)
                 if peticion.metodo_auth == AUTH_LLAVE else None)
        transporte = _abrir(peticion)
        try:
            try:
                clave = transporte.get_remote_server_key()
            except paramiko.SSHException:
                raise ErrorConexionSsh() from None
            if not llave_de_host_valida(clave, peticion):
                raise ErrorHuella()
            _autenticar(transporte, peticion, llave)
            return _ejecutar_canal(transporte, peticion)
        finally:
            transporte.close()
