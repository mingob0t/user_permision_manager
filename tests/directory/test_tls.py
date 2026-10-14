"""TLS real contra un servidor local: el certificado se valida (FNC-040, SEG-13).

Criterio: con certificado no confiable la conexión falla con error controlado.
Un hilo levanta un servidor TLS en `localhost` con un certificado autofirmado
generado en la prueba; no hay LDAP detrás, solo el saludo TLS. El lado del
servidor registra si el saludo se completó: así el caso de control (CA
confiable y nombre correcto) demuestra que el rechazo viene de la validación.
"""

import datetime
import logging
import socket
import ssl
import threading

import ldap3
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from app.modules.directory import ldap_client
from app.modules.directory.configuracion import cargar_configuracion
from app.modules.directory.ldap_client import (MENSAJE_ERROR,
                                               ClienteDirectorio,
                                               ErrorDirectorio)
from tests.directory.conftest import ENTORNO_VALIDO
from tests.matriz_proteccion import CONTRASENA_FICTICIA

HOST_LOCAL = 'localhost'
HOST_AJENO = 'otro.pruebas.invalid'
ESPERA = 5  # segundos


def _certificado(directorio, nombre):
    """Certificado autofirmado para `nombre`; devuelve (cert.pem, llave.pem)."""
    llave = ec.generate_private_key(ec.SECP256R1())
    sujeto = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, nombre)])
    ahora = datetime.datetime.now(datetime.timezone.utc)
    certificado = (
        x509.CertificateBuilder()
        .subject_name(sujeto).issuer_name(sujeto)
        .public_key(llave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - datetime.timedelta(minutes=5))
        .not_valid_after(ahora + datetime.timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(nombre)]),
                       critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None),
                       critical=True)
        .sign(llave, hashes.SHA256()))
    ruta_cert = directorio / f'{nombre}.crt'
    ruta_llave = directorio / f'{nombre}.key'
    ruta_cert.write_bytes(certificado.public_bytes(serialization.Encoding.PEM))
    ruta_llave.write_bytes(llave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    return ruta_cert, ruta_llave


class ServidorTls:
    """Acepta conexiones en `localhost` y registra si el saludo TLS terminó."""

    def __init__(self, cert, llave):
        self.contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.contexto.load_cert_chain(cert, llave)
        self.socket = socket.create_server((HOST_LOCAL, 0))
        self.socket.settimeout(ESPERA)
        self.puerto = self.socket.getsockname()[1]
        self.saludos = []  # True: completado; False: rechazado
        self.hilo = threading.Thread(target=self._atender, daemon=True)
        self.hilo.start()

    def _atender(self):
        try:
            crudo, _ = self.socket.accept()
        except OSError:
            return
        crudo.settimeout(ESPERA)
        try:
            with self.contexto.wrap_socket(crudo, server_side=True):
                self.saludos.append(True)
        except (ssl.SSLError, OSError):
            self.saludos.append(False)
        finally:
            crudo.close()

    def cerrar(self):
        self.socket.close()
        self.hilo.join(ESPERA)


@pytest.fixture
def servidor_tls(tmp_path):
    servidores = []

    def _crear(nombre):
        servidor = ServidorTls(*_certificado(tmp_path, nombre))
        servidores.append(servidor)
        return servidor

    yield _crear
    for servidor in servidores:
        servidor.cerrar()


@pytest.fixture
def con_red(monkeypatch):
    """Este archivo sí abre sockets, solo hacia `localhost`."""
    monkeypatch.setattr(ldap_client, 'Connection', ldap3.Connection)


def _cliente(puerto, ca=None):
    variables = {**ENTORNO_VALIDO,
                 'LDAP_URL': f'ldaps://{HOST_LOCAL}:{puerto}',
                 'LDAP_TIMEOUT_SECONDS': str(ESPERA)}
    if ca:
        variables['LDAP_CA_CERT_FILE'] = str(ca)
    return ClienteDirectorio(cargar_configuracion(variables))


def test_certificado_no_confiable_falla_con_error_controlado(
        con_red, servidor_tls, caplog):
    servidor = servidor_tls(HOST_LOCAL)
    caplog.set_level(logging.ERROR)

    with pytest.raises(ErrorDirectorio) as error:
        _cliente(servidor.puerto).buscar_usuario('jperez')

    assert str(error.value) == MENSAJE_ERROR
    servidor.hilo.join(ESPERA)
    assert servidor.saludos == [False]
    assert 'CERTIFICATE_VERIFY_FAILED' in caplog.text
    assert CONTRASENA_FICTICIA not in caplog.text


def test_nombre_del_certificado_distinto_al_host_falla(
        con_red, servidor_tls, tmp_path, caplog):
    servidor = servidor_tls(HOST_AJENO)
    ca = tmp_path / f'{HOST_AJENO}.crt'  # CA confiable, pero de otro nombre
    caplog.set_level(logging.ERROR)

    with pytest.raises(ErrorDirectorio, match=MENSAJE_ERROR):
        _cliente(servidor.puerto, ca=ca).buscar_usuario('jperez')

    assert "doesn't match" in caplog.text


def test_control_ca_confiable_y_nombre_correcto_completa_el_saludo(
        con_red, servidor_tls, tmp_path):
    servidor = servidor_tls(HOST_LOCAL)
    ca = tmp_path / f'{HOST_LOCAL}.crt'

    # Tras el saludo el servidor cierra sin hablar LDAP: el bind falla, pero
    # el TLS se completó con la CA configurada.
    with pytest.raises(ErrorDirectorio):
        _cliente(servidor.puerto, ca=ca).buscar_usuario('jperez')

    servidor.hilo.join(ESPERA)
    assert servidor.saludos == [True]
