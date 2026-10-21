"""Transporte HTTPS real contra un servidor TLS local (FNC-051, SEC-CON-06).

Solo loopback: comprueba que el certificado y el nombre del host se validan
de verdad y que no se siguen redirecciones. No sale a ninguna red.
"""
import datetime
import socket
import ssl
import threading

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from app.modules.connectors.http_transporte import (TransporteHttps,
                                                    crear_contexto)

HOST = 'erp.pruebas.local'
LOOPBACK = '.'.join(('127', '0', '0', '1'))


@pytest.fixture
def servidor_tls(tmp_path):
    llave = ec.generate_private_key(ec.SECP256R1())
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, HOST)])
    ahora = datetime.datetime.now(datetime.timezone.utc)
    certificado = (x509.CertificateBuilder().subject_name(nombre)
                   .issuer_name(nombre).public_key(llave.public_key())
                   .serial_number(x509.random_serial_number())
                   .not_valid_before(ahora - datetime.timedelta(days=1))
                   .not_valid_after(ahora + datetime.timedelta(days=1))
                   .add_extension(x509.SubjectAlternativeName(
                       [x509.DNSName(HOST)]), critical=False)
                   .sign(llave, hashes.SHA256()))
    archivo_cert = tmp_path / 'cert.pem'
    archivo_llave = tmp_path / 'llave.pem'
    archivo_cert.write_bytes(certificado.public_bytes(serialization.Encoding.PEM))
    archivo_llave.write_bytes(llave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto.load_cert_chain(archivo_cert, archivo_llave)
    escucha = socket.socket()
    escucha.bind((LOOPBACK, 0))
    escucha.listen(5)
    escucha.settimeout(5)
    estado = {'respuesta': b'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'}

    def servir():
        while True:
            try:
                conexion, _ = escucha.accept()
            except OSError:
                return
            try:
                with contexto.wrap_socket(conexion, server_side=True) as tls:
                    tls.recv(65536)
                    tls.sendall(estado['respuesta'])
            except (OSError, ssl.SSLError):
                pass

    hilo = threading.Thread(target=servir, daemon=True)
    hilo.start()
    yield escucha.getsockname()[1], str(archivo_cert), estado
    escucha.close()


def enviar(puerto, contexto, host=HOST):
    return TransporteHttps().enviar(LOOPBACK, host, puerto, 'GET', '/x', {},
                                    None, 5, contexto).estado


def test_certificado_no_confiable_se_rechaza(servidor_tls):
    puerto, _, _ = servidor_tls
    with pytest.raises(ssl.SSLCertVerificationError):
        enviar(puerto, crear_contexto())


def test_con_la_ca_correcta_conecta_a_la_ip_validando_el_nombre(servidor_tls):
    puerto, ca, _ = servidor_tls
    assert enviar(puerto, crear_contexto(ca)) == 200


def test_nombre_de_host_distinto_al_del_certificado_se_rechaza(servidor_tls):
    puerto, ca, _ = servidor_tls
    with pytest.raises(ssl.SSLCertVerificationError):
        enviar(puerto, crear_contexto(ca), host='otro.pruebas.local')


def test_no_sigue_redirecciones(servidor_tls):
    puerto, ca, estado = servidor_tls
    estado['respuesta'] = (b'HTTP/1.1 302 Found\r\nLocation: https://otro/\r\n'
                           b'Content-Length: 0\r\n\r\n')
    assert enviar(puerto, crear_contexto(ca)) == 302


def test_el_contexto_exige_verificacion_y_tls_12():
    contexto = crear_contexto()
    assert contexto.verify_mode == ssl.CERT_REQUIRED
    assert contexto.check_hostname is True
    assert contexto.minimum_version >= ssl.TLSVersion.TLSv1_2
