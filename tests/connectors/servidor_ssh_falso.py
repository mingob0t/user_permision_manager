"""Servidor SSH falso en loopback para las pruebas del conector `ssh` (FNC-052).

Es un servidor paramiko real en `127.0.0.1` con puerto efímero: sirve para
probar la verificación de la llave del host, la autenticación, el comando
fijo, la entrada estándar, el límite de salida y los tiempos. No sale a la red.
"""
import io
import socket
import threading
import time

import paramiko

USUARIO = 'svc-pokemon'
CONTRASENA = 'Contrasena-Ficticia-De-Prueba'


def generar_llave():
    return paramiko.ECDSAKey.generate()


def llave_a_texto(llave):
    archivo = io.StringIO()
    llave.write_private_key(archivo)
    return archivo.getvalue()


class _Interfaz(paramiko.ServerInterface):

    def __init__(self, servidor):
        self.servidor = servidor

    def get_allowed_auths(self, username):
        return 'publickey,password'

    def check_auth_publickey(self, username, key):
        self.servidor.intentos_auth += 1
        ok = (username == USUARIO and self.servidor.llave_cliente is not None
              and key.asbytes() == self.servidor.llave_cliente.asbytes())
        return paramiko.AUTH_SUCCESSFUL if ok else paramiko.AUTH_FAILED

    def check_auth_password(self, username, password):
        self.servidor.intentos_auth += 1
        ok = (username == USUARIO and self.servidor.acepta_contrasena
              and password == CONTRASENA)
        return paramiko.AUTH_SUCCESSFUL if ok else paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_exec_request(self, channel, command):
        threading.Thread(target=self.servidor.atender,
                         args=(channel, command), daemon=True).start()
        return True

    # Todo lo demás se rechaza: sin pty, reenvíos ni agente.
    def check_channel_pty_request(self, *args):
        return False

    def check_port_forward_request(self, *args):
        return False


class ServidorSshFalso:
    """`comportamiento(comando, entrada, canal) -> código de salida`."""

    def __init__(self, comportamiento, llave_host=None, llave_cliente=None,
                 acepta_contrasena=False, cifrados=None, macs=None):
        self.comportamiento = comportamiento
        self.llave_host = llave_host or generar_llave()
        self.llave_cliente = llave_cliente
        self.acepta_contrasena = acepta_contrasena
        self.cifrados = cifrados
        self.macs = macs
        self.intentos_auth = 0
        self.comandos = []
        self.entradas = []
        self._socket = socket.socket()
        self._socket.bind(('127.0.0.1', 0))
        self._socket.listen(5)
        self.puerto = self._socket.getsockname()[1]
        self._activo = True
        self._transportes = []
        threading.Thread(target=self._aceptar, daemon=True).start()

    def _aceptar(self):
        while self._activo:
            try:
                conexion, _ = self._socket.accept()
            except OSError:
                return
            transporte = paramiko.Transport(conexion)
            transporte.add_server_key(self.llave_host)
            opciones = transporte.get_security_options()
            if self.cifrados:
                opciones.ciphers = self.cifrados
            if self.macs:
                opciones.digests = self.macs
            self._transportes.append(transporte)
            try:
                transporte.start_server(server=_Interfaz(self))
            except (paramiko.SSHException, EOFError, OSError):
                continue

    def atender(self, canal, comando):
        self.comandos.append(comando.decode() if isinstance(comando, bytes)
                             else comando)
        entrada = canal.makefile('rb').read()
        self.entradas.append(entrada)
        codigo = self.comportamiento(comando, entrada, canal)
        time.sleep(0.05)
        canal.send_exit_status(codigo)
        canal.close()

    def cerrar(self):
        self._activo = False
        self._socket.close()
        for transporte in self._transportes:
            transporte.close()
