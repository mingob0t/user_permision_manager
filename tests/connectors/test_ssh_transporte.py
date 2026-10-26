"""Transporte SSH (FNC-052) contra un servidor paramiko real en loopback:
llave del host obligatoria, autenticación, comando fijo, entrada estándar,
límite de salida y tiempos. Sin red externa."""
import dataclasses
import socket

import paramiko
import pytest

from app.modules.connectors.ssh_transporte import (AUTH_CONTRASENA, AUTH_LLAVE,
                                                   ErrorAutenticacion,
                                                   ErrorConexionSsh,
                                                   ErrorHuella,
                                                   ErrorSalidaExcesiva,
                                                   ErrorTiempoEjecucion,
                                                   PeticionSsh, TransporteSsh,
                                                   cargar_llave)
from tests.connectors.servidor_ssh_falso import (CONTRASENA, USUARIO,
                                                 ServidorSshFalso,
                                                 generar_llave,
                                                 llave_a_texto)

COMANDO = "/usr/local/bin/acceso otorgar"


def peticion(servidor, llave_cliente, **cambios):
    valores = dict(
        ip='127.0.0.1', host='ssh.pruebas.local', puerto=servidor.puerto,
        usuario=USUARIO, secreto=llave_a_texto(llave_cliente),
        metodo_auth=AUTH_LLAVE, comando=COMANDO, entrada=b'{"a":1}\n',
        huellas=(servidor.llave_host.fingerprint,), archivo_known_hosts='',
        tiempo_conexion=5, tiempo_ejecucion=5, maximo_salida=100)
    valores.update(cambios)
    return PeticionSsh(**valores)


@pytest.fixture
def cliente():
    return generar_llave()


@pytest.fixture
def levantar(cliente):
    servidores = []

    def _levantar(comportamiento=lambda *_: 0, **opciones):
        opciones.setdefault('llave_cliente', cliente)
        servidor = ServidorSshFalso(comportamiento, **opciones)
        servidores.append(servidor)
        return servidor
    yield _levantar
    for servidor in servidores:
        servidor.cerrar()


def test_ejecuta_el_comando_fijo_y_pasa_los_datos_por_stdin(levantar, cliente):
    servidor = levantar(lambda *_: 0)
    codigo = TransporteSsh().ejecutar(peticion(servidor, cliente))
    assert codigo == 0
    assert servidor.comandos == [COMANDO]
    assert servidor.entradas == [b'{"a":1}\n']


def test_devuelve_el_codigo_de_salida(levantar, cliente):
    servidor = levantar(lambda *_: 3)
    assert TransporteSsh().ejecutar(peticion(servidor, cliente)) == 3


def test_huella_distinta_es_error_y_no_envia_la_credencial(levantar, cliente):
    servidor = levantar()
    otra = generar_llave().fingerprint
    with pytest.raises(ErrorHuella):
        TransporteSsh().ejecutar(peticion(servidor, cliente, huellas=(otra,)))
    assert servidor.intentos_auth == 0 and servidor.comandos == []


def test_sin_huellas_ni_known_hosts_nunca_conecta(levantar, cliente):
    servidor = levantar()
    with pytest.raises(ErrorHuella):
        TransporteSsh().ejecutar(peticion(servidor, cliente, huellas=()))
    assert servidor.intentos_auth == 0


def test_acepta_cualquiera_de_las_huellas_fijadas(levantar, cliente):
    servidor = levantar()
    huellas = (generar_llave().fingerprint, servidor.llave_host.fingerprint)
    assert TransporteSsh().ejecutar(
        peticion(servidor, cliente, huellas=huellas)) == 0


def _known_hosts(tmp_path, servidor, llave, host='ssh.pruebas.local'):
    ruta = tmp_path / 'known_hosts'
    ruta.write_text(f'[{host}]:{servidor.puerto} {llave.get_name()} '
                    f'{llave.get_base64()}\n')
    return str(ruta)


def test_known_hosts_del_despliegue_con_la_llave_correcta(levantar, cliente,
                                                          tmp_path):
    servidor = levantar()
    archivo = _known_hosts(tmp_path, servidor, servidor.llave_host)
    assert TransporteSsh().ejecutar(peticion(
        servidor, cliente, huellas=(), archivo_known_hosts=archivo)) == 0


def test_known_hosts_con_otra_llave_o_sin_el_host_se_rechaza(levantar, cliente,
                                                             tmp_path):
    servidor = levantar()
    otra = _known_hosts(tmp_path, servidor, generar_llave())
    with pytest.raises(ErrorHuella):
        TransporteSsh().ejecutar(peticion(
            servidor, cliente, huellas=(), archivo_known_hosts=otra))
    ajeno = _known_hosts(tmp_path, servidor, servidor.llave_host,
                         host='otro.pruebas.local')
    with pytest.raises(ErrorHuella):
        TransporteSsh().ejecutar(peticion(
            servidor, cliente, huellas=(), archivo_known_hosts=ajeno))
    with pytest.raises(ErrorHuella):
        TransporteSsh().ejecutar(peticion(
            servidor, cliente, huellas=(),
            archivo_known_hosts=str(tmp_path / 'no-existe')))
    assert servidor.intentos_auth == 0


def test_llave_de_cliente_no_autorizada_es_error_de_autenticacion(levantar,
                                                                  cliente):
    servidor = levantar()
    with pytest.raises(ErrorAutenticacion):
        TransporteSsh().ejecutar(peticion(
            servidor, cliente, secreto=llave_a_texto(generar_llave())))
    assert servidor.comandos == []


def test_llave_ilegible_no_abre_conexion(levantar, cliente):
    servidor = levantar()
    with pytest.raises(ErrorAutenticacion):
        TransporteSsh().ejecutar(peticion(servidor, cliente,
                                          secreto='no es una llave'))
    assert servidor.intentos_auth == 0


def test_autenticacion_por_contrasena_solo_si_se_pide(levantar, cliente):
    servidor = levantar(llave_cliente=None, acepta_contrasena=True)
    assert TransporteSsh().ejecutar(peticion(
        servidor, cliente, metodo_auth=AUTH_CONTRASENA,
        secreto=CONTRASENA)) == 0
    with pytest.raises(ErrorAutenticacion):
        TransporteSsh().ejecutar(peticion(
            servidor, cliente, metodo_auth=AUTH_CONTRASENA, secreto='mala'))


def test_la_salida_remota_se_descarta_y_tiene_limite(levantar, cliente):
    def verboso(comando, entrada, canal):
        canal.send(b'x' * 500)
        return 0
    servidor = levantar(verboso)
    with pytest.raises(ErrorSalidaExcesiva):
        TransporteSsh().ejecutar(peticion(servidor, cliente, maximo_salida=100))
    ok = levantar(verboso)
    assert TransporteSsh().ejecutar(
        peticion(ok, cliente, maximo_salida=1000)) == 0


def test_el_tiempo_de_ejecucion_se_corta(levantar, cliente):
    import time

    def lento(comando, entrada, canal):
        time.sleep(3)
        return 0
    servidor = levantar(lento)
    with pytest.raises(ErrorTiempoEjecucion):
        TransporteSsh().ejecutar(peticion(servidor, cliente,
                                          tiempo_ejecucion=1))


def test_puerto_cerrado_es_error_de_conexion(levantar, cliente):
    servidor = levantar()
    with socket.socket() as libre:  # puerto sin nadie escuchando
        libre.bind(('127.0.0.1', 0))
        puerto = libre.getsockname()[1]
    base = peticion(servidor, cliente)
    with pytest.raises(ErrorConexionSsh):
        TransporteSsh().ejecutar(dataclasses.replace(
            base, puerto=puerto, tiempo_conexion=2))


def test_cargar_llave_acepta_ecdsa_y_rechaza_texto_cualquiera():
    assert isinstance(cargar_llave(llave_a_texto(generar_llave())),
                      paramiko.PKey)
    with pytest.raises(ErrorAutenticacion):
        cargar_llave('-----BEGIN ' + 'OPENSSH' + ' KEY-----\nbasura')


def test_la_peticion_no_muestra_el_secreto(levantar, cliente):
    servidor = levantar()
    texto = repr(peticion(servidor, cliente))
    assert 'BEGIN' not in texto and 'PRIVATE' not in texto
