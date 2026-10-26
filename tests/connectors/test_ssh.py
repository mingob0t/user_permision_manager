"""Conector tipo SSH (FNC-052): esquema, comando fijo sin inyección, clasificación
de códigos de salida y de errores, destino seguro y registro del tipo. Sin red
externa: transporte falso y, de punta a punta, un servidor paramiko en loopback."""
import dataclasses
import json
import socket
from types import MappingProxyType

import pytest

from app.modules.connectors import registry
from app.modules.connectors.base import Destino, SolicitudConector
from app.modules.connectors.configuracion import (ConfiguracionConectores,
                                                  ErrorConfiguracionConectores,
                                                  cargar_configuracion)
from app.modules.connectors.credenciales import Credencial
from app.modules.connectors.ssh import (TIPO, ConectorSsh, errores_esquema,
                                        validar_params)
from app.modules.connectors.ssh_transporte import (ErrorAutenticacion,
                                                   ErrorConexionSsh,
                                                   ErrorHuella,
                                                   ErrorSalidaExcesiva,
                                                   ErrorTiempoEjecucion,
                                                   ErrorTransporteSsh,
                                                   TransporteSsh)
from app.modules.connectors.tipos import TIPO_SSH
from app.modules.connectors.validacion import validar_configuracion
from app.modules.provisioning.saneo import MENSAJES
from app.modules.provisioning.tipos import (RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)
from tests.connectors.servidor_ssh_falso import (USUARIO, ServidorSshFalso,
                                                 generar_llave,
                                                 llave_a_texto)

HOST = 'ssh.pruebas.local'
SECRETO = 'Cr3dencial-Ficticia-De-Prueba'
PUBLICA = '.'.join(('8', '8', '8', '8'))
PUBLICA_2 = '.'.join(('8', '8', '4', '4'))
PRIVADA = '.'.join(('10', '0', '0', '5'))
OTRA_1 = '.'.join(('1', '1', '1', '1'))
OTRA_2 = '.'.join(('9', '9', '9', '9'))
HUELLA = 'SHA256:' + 'A' * 43

PARAMS = {
    'huellas': [HUELLA],
    'otorgar': {'comando': ['/usr/local/bin/acceso', 'otorgar'],
                'sin_cambios': [3]},
    'revocar': {'comando': ['/usr/local/bin/acceso', 'revocar'],
                'sin_cambios': [4], 'transitorios': [75, 111]},
    'consultar': {'comando': ['/usr/local/bin/acceso', 'consultar'],
                  'ausente': [1]},
}
CFG = ConfiguracionConectores(hosts_permitidos=frozenset({HOST}),
                              tiempo_espera=7, segundos_cache=0,
                              ssh_tiempo=11, ssh_maximo_salida=2048)


def params(**cambios):
    valores = json.loads(json.dumps(PARAMS))
    valores.update(cambios)
    return valores


def solicitud(cuenta='ana.ruiz@pruebas.local', nivel='usuario'):
    return SolicitudConector(id_operacion='1', clave_idempotencia='c-1',
                             operacion='otorgar', nivel=nivel,
                             plataforma_id=7, cuenta=cuenta)


def dns(*direcciones):
    def getaddrinfo(host, puerto, **_):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (d, puerto))
                for d in direcciones]
    return getaddrinfo


class TransporteFalso:
    """Registra las peticiones y responde con códigos o fallas programadas."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.peticiones = []

    def ejecutar(self, peticion):
        self.peticiones.append(peticion)
        respuesta = self.respuestas.pop(0) if self.respuestas else 0
        if isinstance(respuesta, BaseException):
            raise respuesta
        return respuesta


def conector(*respuestas, valores=None, credencial=None,
             direcciones=(PUBLICA,), cfg=CFG):
    transporte = TransporteFalso(*respuestas)
    destino = Destino(host=HOST, puerto=22, tiempo_espera=7,
                      params=MappingProxyType(valores or params()))
    ssh = ConectorSsh(destino, credencial or Credencial(SECRETO, USUARIO),
                      transporte=transporte, getaddrinfo=dns(*direcciones),
                      configuracion=cfg)
    return ssh, transporte


# --------------------------------------------------------------------------- #
# Comando fijo e inyección
# --------------------------------------------------------------------------- #

def test_el_comando_es_fijo_y_los_datos_van_por_stdin():
    ssh, transporte = conector(0)
    resultado = ssh.otorgar(solicitud(nivel='admin'))
    assert resultado.resultado == RESULTADO_EXITOSO
    peticion, = transporte.peticiones
    assert peticion.comando == '/usr/local/bin/acceso otorgar'
    assert json.loads(peticion.entrada) == {
        'operacion': 'otorgar', 'correo': 'ana.ruiz@pruebas.local',
        'nivel': 'admin', 'plataforma': '7'}
    assert peticion.entrada.endswith(b'\n') and peticion.entrada.count(b'\n') == 1
    assert 'ana.ruiz' not in peticion.comando and 'admin' not in peticion.comando


@pytest.mark.parametrize('correo', [
    'a;rm -rf /@x.com', 'a"b@x.com', "a'b@x.com", 'a$(id)@x.com',
    'a`id`@x.com', 'a|b@x.com', 'a&b@x.com', 'a b@x.com', 'a\\b@x.com',
    '${IFS}@x.com'])
def test_entrada_maliciosa_no_altera_el_comando(correo):
    ssh, transporte = conector(0, 0, 0)
    for accion in (ssh.otorgar, ssh.revocar, ssh.consultar):
        accion(solicitud(cuenta=correo))
    comandos = {p.comando for p in transporte.peticiones}
    assert comandos == {'/usr/local/bin/acceso otorgar',
                        '/usr/local/bin/acceso revocar',
                        '/usr/local/bin/acceso consultar'}
    for peticion in transporte.peticiones:
        assert json.loads(peticion.entrada)['correo'] == correo
        assert peticion.entrada.count(b'\n') == 1  # una sola línea JSON


@pytest.mark.parametrize('cuenta, nivel', [
    ('ana\nroot@x.com', 'usuario'), ('ana\r@x.com', 'usuario'),
    ('ana@x.com', 'nivel\n2'), ('ana@x.com', 'a\x00b'), ('', 'usuario'),
    ('sin-arroba', 'usuario'), ('..', 'usuario'), ('ana@x.com', '..'),
    ('ana@x.com', ''), ('ana@x.com', 'a/../b')])
def test_valores_con_control_o_de_recorrido_se_rechazan_sin_conectar(cuenta,
                                                                    nivel):
    ssh, transporte = conector(0)
    resultado = ssh.otorgar(solicitud(cuenta=cuenta, nivel=nivel))
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'valor_no_valido'
    assert transporte.peticiones == []


@pytest.mark.parametrize('comando', [
    ['/bin/sh', '-c', 'x; y'], ['/bin/acceso;id'], ['/bin/acceso', '$(id)'],
    ['/bin/acceso', 'a b'], ['/bin/acceso', '`id`'], ['/bin/acceso', 'a|b'],
    ['/bin/acceso', '"x"'], ['/bin/acceso', 'a\nb'], ['acceso'],
    ['/bin/../acceso'], ['/bin//acceso'], [], 'acceso otorgar',
    ['/bin/acceso'] + ['x'] * 8, ['/bin/acceso', 7], [''],
    ['/bin/acceso', 'x' * 101]])
def test_el_esquema_rechaza_comandos_con_metacaracteres(comando):
    valores = params()
    valores['otorgar']['comando'] = comando
    assert 'otorgar.comando' in validar_params(valores)


def test_comando_guardado_invalido_no_se_ejecuta():
    valores = params()
    valores['otorgar']['comando'] = ['/bin/acceso;id']
    ssh, transporte = conector(0, valores=valores)
    resultado = ssh.otorgar(solicitud())
    assert resultado.motivo == 'configuracion_invalida'
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert transporte.peticiones == []


# --------------------------------------------------------------------------- #
# Esquema de params
# --------------------------------------------------------------------------- #

def test_params_validos(monkeypatch):
    monkeypatch.delenv('CONNECTOR_SSH_KNOWN_HOSTS_FILE', raising=False)
    assert validar_params(params()) == {}


def test_clave_desconocida_y_faltantes():
    errores = validar_params({'huellas': [HUELLA], 'x': 1, 'otorgar': {
        'comando': ['/a'], 'extra': 1}})
    assert errores['x'] == 'Campo no admitido.'
    assert errores['otorgar.extra'] == 'Campo no admitido.'
    assert errores['revocar'] == 'Es obligatorio.'


@pytest.mark.parametrize('huellas', [
    [], ['SHA256:corta'], ['MD5:aa:bb'], 'SHA256:' + 'A' * 43, [7],
    [HUELLA] * 6, ['sha256:' + 'A' * 43], [HUELLA + '=']])
def test_huellas_invalidas(huellas, monkeypatch):
    monkeypatch.delenv('CONNECTOR_SSH_KNOWN_HOSTS_FILE', raising=False)
    assert 'huellas' in validar_params(params(huellas=huellas))


def test_sin_huellas_exige_known_hosts_del_despliegue():
    valores = params()
    del valores['huellas']
    assert 'huellas' in errores_esquema(valores, con_known_hosts=False)
    assert errores_esquema(valores, con_known_hosts=True) == {}


@pytest.mark.parametrize('codigos', [[0], [256], [True], ['3'], list(range(1, 12))])
def test_codigos_invalidos(codigos):
    valores = params()
    valores['otorgar']['sin_cambios'] = codigos
    assert 'otorgar.sin_cambios' in validar_params(valores)


def test_un_codigo_no_puede_tener_dos_clasificaciones():
    valores = params()
    valores['revocar']['sin_cambios'] = [75]
    assert 'revocar.transitorios' in validar_params(valores)


def test_auth_solo_llave_o_contrasena_y_sin_secretos_en_params():
    assert 'auth.metodo' in validar_params(params(auth={'metodo': 'agente'}))
    assert 'auth.x' in validar_params(params(auth={'metodo': 'llave', 'x': 1}))
    assert 'auth' in validar_params(params(auth='llave'))
    assert validar_params(params(auth={'metodo': 'contrasena'})) == {}


def test_consultar_usa_ausente_y_no_sin_cambios():
    valores = params()
    valores['consultar']['sin_cambios'] = [1]
    assert 'consultar.sin_cambios' in validar_params(valores)


# --------------------------------------------------------------------------- #
# Clasificación de códigos
# --------------------------------------------------------------------------- #

def test_codigos_de_otorgar():
    ssh, _ = conector(0, 3, 75, 2, -1)
    assert ssh.otorgar(solicitud()).resultado == RESULTADO_EXITOSO
    assert ssh.otorgar(solicitud()).resultado == RESULTADO_SIN_CAMBIOS
    transitorio = ssh.otorgar(solicitud())
    assert (transitorio.resultado, transitorio.motivo, transitorio.detalle) == (
        RESULTADO_ERROR_TRANSITORIO, 'ssh_comando_transitorio', 'salida 75')
    permanente = ssh.otorgar(solicitud())
    assert (permanente.resultado, permanente.motivo, permanente.detalle) == (
        RESULTADO_ERROR_PERMANENTE, 'ssh_comando_rechazado', 'salida 2')
    sin_estado = ssh.otorgar(solicitud())
    assert (sin_estado.resultado, sin_estado.motivo) == (
        RESULTADO_ERROR_TRANSITORIO, 'red_no_disponible')


def test_codigos_de_revocar_con_transitorios_propios():
    ssh, _ = conector(4, 111, 75, 1)
    assert ssh.revocar(solicitud()).resultado == RESULTADO_SIN_CAMBIOS
    assert ssh.revocar(solicitud()).resultado == RESULTADO_ERROR_TRANSITORIO
    assert ssh.revocar(solicitud()).resultado == RESULTADO_ERROR_TRANSITORIO
    assert ssh.revocar(solicitud()).resultado == RESULTADO_ERROR_PERMANENTE


def test_otorgar_con_el_codigo_de_revocar_no_es_sin_cambios():
    ssh, _ = conector(4)
    assert ssh.otorgar(solicitud()).resultado == RESULTADO_ERROR_PERMANENTE


def test_consultar_presente_ausente_y_error():
    ssh, transporte = conector(0, 1, 9)
    assert ssh.consultar(solicitud()).presente is True
    ausente = ssh.consultar(solicitud())
    assert (ausente.resultado, ausente.presente) == (RESULTADO_EXITOSO, False)
    assert ssh.consultar(solicitud()).resultado == RESULTADO_ERROR_PERMANENTE
    assert json.loads(transporte.peticiones[0].entrada)['operacion'] == (
        'consultar')


def test_consultar_sin_comando_no_esta_disponible():
    valores = params()
    del valores['consultar']
    ssh, transporte = conector(valores=valores)
    resultado = ssh.consultar(solicitud())
    assert resultado.motivo == 'consulta_no_disponible'
    assert transporte.peticiones == []


# --------------------------------------------------------------------------- #
# Errores de transporte
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('error, resultado, motivo', [
    (ErrorHuella(), RESULTADO_ERROR_PERMANENTE, 'ssh_huella_no_coincide'),
    (ErrorAutenticacion(), RESULTADO_ERROR_PERMANENTE,
     'ssh_autenticacion_rechazada'),
    (ErrorSalidaExcesiva(), RESULTADO_ERROR_PERMANENTE, 'ssh_salida_excesiva'),
    (ErrorTiempoEjecucion(), RESULTADO_ERROR_TRANSITORIO, 'tiempo_agotado'),
    (ErrorTransporteSsh(), RESULTADO_ERROR_TRANSITORIO, 'red_no_disponible'),
])
def test_errores_del_transporte_se_clasifican(error, resultado, motivo):
    ssh, transporte = conector(error)
    res = ssh.otorgar(solicitud())
    assert (res.resultado, res.motivo) == (resultado, motivo)
    assert res.detalle is None
    assert len(transporte.peticiones) == 1  # sin reintento


def test_si_no_conecta_prueba_otra_ip_hasta_tres():
    ssh, transporte = conector(ErrorConexionSsh(), ErrorConexionSsh(), 0,
                               direcciones=(PUBLICA, PUBLICA_2, OTRA_1, OTRA_2))
    assert ssh.otorgar(solicitud()).resultado == RESULTADO_EXITOSO
    assert [p.ip for p in transporte.peticiones] == [PUBLICA, PUBLICA_2,
                                                     OTRA_1]
    ssh, transporte = conector(*[ErrorConexionSsh()] * 5,
                               direcciones=(PUBLICA, PUBLICA_2, OTRA_1,
                                            OTRA_2))
    res = ssh.otorgar(solicitud())
    assert (res.resultado, res.motivo) == (RESULTADO_ERROR_TRANSITORIO,
                                           'red_no_disponible')
    assert len(transporte.peticiones) == 3


def test_huella_distinta_no_prueba_otra_ip():
    ssh, transporte = conector(ErrorHuella(),
                               direcciones=(PUBLICA, PUBLICA_2))
    assert ssh.otorgar(solicitud()).motivo == 'ssh_huella_no_coincide'
    assert len(transporte.peticiones) == 1


def test_destino_privado_se_rechaza_sin_conectar():
    ssh, transporte = conector(direcciones=(PUBLICA, PRIVADA))
    res = ssh.otorgar(solicitud())
    assert (res.resultado, res.motivo) == (RESULTADO_ERROR_PERMANENTE,
                                           'destino_no_permitido')
    assert transporte.peticiones == []


def test_falla_de_dns_es_transitoria():
    destino = Destino(host=HOST, puerto=22, tiempo_espera=7,
                      params=MappingProxyType(params()))

    def sin_dns(*_args, **_kw):
        raise socket.gaierror()
    transporte = TransporteFalso()
    ssh = ConectorSsh(destino, Credencial(SECRETO, USUARIO),
                      transporte=transporte, getaddrinfo=sin_dns,
                      configuracion=CFG)
    res = ssh.otorgar(solicitud())
    assert (res.resultado, res.motivo) == (RESULTADO_ERROR_TRANSITORIO,
                                           'red_no_disponible')
    assert transporte.peticiones == []


@pytest.mark.parametrize('credencial', [Credencial(SECRETO),
                                        Credencial('', USUARIO)])
def test_credencial_sin_usuario_o_sin_secreto_es_permanente(credencial):
    ssh, transporte = conector(credencial=credencial)
    res = ssh.otorgar(solicitud())
    assert res.motivo == 'credencial_no_encontrada'
    assert transporte.peticiones == []


def test_la_peticion_lleva_la_ip_validada_los_tiempos_y_la_verificacion():
    ssh, transporte = conector(0)
    ssh.otorgar(solicitud())
    p, = transporte.peticiones
    assert (p.ip, p.host, p.puerto) == (PUBLICA, HOST, 22)
    assert p.huellas == (HUELLA,) and p.archivo_known_hosts == ''
    assert (p.tiempo_conexion, p.tiempo_ejecucion, p.maximo_salida) == (
        7, 11, 2048)
    assert p.metodo_auth == 'llave' and p.usuario == USUARIO
    assert SECRETO not in repr(p)


def test_known_hosts_del_despliegue_si_no_hay_huellas():
    valores = params()
    del valores['huellas']
    cfg = dataclasses.replace(CFG, ssh_known_hosts='/etc/pokemon/known_hosts')
    ssh, transporte = conector(0, valores=valores, cfg=cfg)
    assert ssh.otorgar(solicitud()).resultado == RESULTADO_EXITOSO
    p, = transporte.peticiones
    assert p.huellas == () and p.archivo_known_hosts == (
        '/etc/pokemon/known_hosts')


def test_sin_huellas_ni_known_hosts_no_conecta():
    valores = params()
    del valores['huellas']
    ssh, transporte = conector(0, valores=valores)
    assert ssh.otorgar(solicitud()).motivo == 'configuracion_invalida'
    assert transporte.peticiones == []


def test_contrasena_solo_si_la_configuracion_la_declara():
    ssh, transporte = conector(0, 0, valores=params(
        auth={'metodo': 'contrasena'}))
    ssh.otorgar(solicitud())
    assert transporte.peticiones[0].metodo_auth == 'contrasena'
    ssh, transporte = conector(0)
    ssh.otorgar(solicitud())
    assert transporte.peticiones[0].metodo_auth == 'llave'


def test_los_motivos_nuevos_tienen_mensaje():
    for motivo in ('ssh_huella_no_coincide', 'ssh_autenticacion_rechazada',
                   'ssh_comando_rechazado', 'ssh_comando_transitorio',
                   'ssh_salida_excesiva'):
        assert motivo in MENSAJES


# --------------------------------------------------------------------------- #
# De punta a punta con un servidor SSH real en loopback
# --------------------------------------------------------------------------- #

class TransporteLoopback(TransporteSsh):
    """Desvía la IP pública validada al servidor de pruebas en loopback."""

    def __init__(self, puerto):
        self.puerto = puerto

    def ejecutar(self, peticion):
        return super().ejecutar(dataclasses.replace(
            peticion, ip='127.0.0.1', puerto=self.puerto))


@pytest.fixture
def servidor_real():
    cliente = generar_llave()
    servidores = []

    def levantar(comportamiento):
        servidor = ServidorSshFalso(comportamiento, llave_cliente=cliente)
        servidores.append(servidor)
        return servidor
    yield levantar, cliente
    for servidor in servidores:
        servidor.cerrar()


def _conector_real(servidor, cliente, **cambios):
    valores = params(huellas=[servidor.llave_host.fingerprint])
    valores.update(cambios)
    destino = Destino(host=HOST, puerto=22, tiempo_espera=5,
                      params=MappingProxyType(valores))
    return ConectorSsh(
        destino, Credencial(llave_a_texto(cliente), USUARIO),
        transporte=TransporteLoopback(servidor.puerto),
        getaddrinfo=dns(PUBLICA),
        configuracion=dataclasses.replace(CFG, ssh_tiempo=5))


def test_de_punta_a_punta_otorgar_y_revocar(servidor_real):
    levantar, cliente = servidor_real
    servidor = levantar(lambda comando, *_: 3 if b'revocar' in comando else 0)
    ssh = _conector_real(servidor, cliente)
    assert ssh.otorgar(solicitud()).resultado == RESULTADO_EXITOSO
    assert ssh.revocar(solicitud()).resultado == RESULTADO_ERROR_PERMANENTE
    assert servidor.comandos == ['/usr/local/bin/acceso otorgar',
                                 '/usr/local/bin/acceso revocar']


def test_de_punta_a_punta_la_inyeccion_llega_inerte(servidor_real):
    levantar, cliente = servidor_real
    servidor = levantar(lambda *_: 0)
    ssh = _conector_real(servidor, cliente)
    malicioso = 'a";touch /tmp/x;\'$(id)`id`@x.com'
    assert ssh.otorgar(solicitud(cuenta=malicioso)).resultado == (
        RESULTADO_EXITOSO)
    assert servidor.comandos == ['/usr/local/bin/acceso otorgar']
    assert json.loads(servidor.entradas[0])['correo'] == malicioso


def test_de_punta_a_punta_huella_distinta_es_permanente_y_no_autentica(
        servidor_real):
    levantar, cliente = servidor_real
    servidor = levantar(lambda *_: 0)
    ssh = _conector_real(servidor, cliente,
                         huellas=[generar_llave().fingerprint])
    res = ssh.otorgar(solicitud())
    assert (res.resultado, res.motivo) == (RESULTADO_ERROR_PERMANENTE,
                                           'ssh_huella_no_coincide')
    assert servidor.intentos_auth == 0 and servidor.comandos == []


def test_de_punta_a_punta_llave_rechazada(servidor_real):
    levantar, cliente = servidor_real
    servidor = levantar(lambda *_: 0)
    ssh = _conector_real(servidor, generar_llave())
    res = ssh.otorgar(solicitud())
    assert res.motivo == 'ssh_autenticacion_rechazada'
    assert servidor.comandos == []


# --------------------------------------------------------------------------- #
# Registro, configuración y variables
# --------------------------------------------------------------------------- #

def test_el_tipo_ssh_queda_registrado(app):
    assert registry.obtener_tipo(TIPO_SSH) is TIPO
    assert TIPO_SSH in registry.tipos_disponibles()


def test_validar_configuracion_acepta_ssh_y_reporta_params(app, monkeypatch):
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS', HOST)
    limpio, errores = validar_configuracion({
        'type': 'ssh', 'host': HOST, 'port': 22, 'params': params(),
        'credential_ref': 'pokemon/erp-ssh'})
    assert errores == {} and limpio['type'] == 'ssh'
    _, errores = validar_configuracion({
        'type': 'ssh', 'host': HOST, 'port': 22,
        'params': {'otorgar': {'comando': ['x;y']}},
        'credential_ref': 'pokemon/erp-ssh'})
    assert {'params.huellas', 'params.revocar',
            'params.otorgar.comando'} <= set(errores)


def test_variables_ssh_por_defecto_y_validacion():
    cfg = cargar_configuracion({})
    assert (cfg.ssh_tiempo, cfg.ssh_maximo_salida, cfg.ssh_known_hosts) == (
        30, 4096, '')
    cfg = cargar_configuracion({
        'CONNECTOR_SSH_TIMEOUT_SECONDS': '20',
        'CONNECTOR_SSH_MAX_OUTPUT_BYTES': '100',
        'CONNECTOR_SSH_KNOWN_HOSTS_FILE': ' /etc/kh '})
    assert (cfg.ssh_tiempo, cfg.ssh_maximo_salida, cfg.ssh_known_hosts) == (
        20, 100, '/etc/kh')


@pytest.mark.parametrize('entorno', [
    {'CONNECTOR_SSH_TIMEOUT_SECONDS': '0'},
    {'CONNECTOR_SSH_TIMEOUT_SECONDS': 'x'},
    {'CONNECTOR_SSH_TIMEOUT_SECONDS': '60'},  # no menor que el intento (60)
    {'CONNECTOR_SSH_MAX_OUTPUT_BYTES': '0'},
    {'CONNECTOR_SSH_MAX_OUTPUT_BYTES': '65537'}])
def test_variables_ssh_invalidas_detienen_el_arranque(entorno):
    with pytest.raises(ErrorConfiguracionConectores):
        cargar_configuracion(entorno)
