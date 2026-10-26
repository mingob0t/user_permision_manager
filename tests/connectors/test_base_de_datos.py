"""Conector tipo base de datos (FNC-053): sentencias parametrizadas, inyección,
transacción, TLS, destino seguro y clasificación de errores. Sin red real:
SQLite en memoria como doble, DNS falso y drivers simulados."""
import json
import socket
import sqlite3
import ssl
from types import MappingProxyType

import psycopg2
import pymysql
import pytest

from app.modules.connectors import bd_motores, registry
from app.modules.connectors.base import Destino, SolicitudConector
from app.modules.connectors.base_de_datos import (TIPO, ConectorBd,
                                                  validar_params)
from app.modules.connectors.bd_configuracion import (
    VAR_TIEMPO_BD, cargar_configuracion_bd)
from app.modules.connectors.bd_motores import (MOTORES, ErrorConexion,
                                               ParametrosConexion)
from app.modules.connectors.bd_sentencias import error_sentencia
from app.modules.connectors.configuracion import ErrorConfiguracionConectores
from app.modules.connectors.credenciales import Credencial
from app.modules.connectors.tipos import TIPO_BD
from app.modules.connectors.validacion import validar_configuracion
from app.modules.provisioning.saneo import MENSAJES
from app.modules.provisioning.tipos import (RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)

HOST = 'erp.pruebas.local'
SECRETO = 'Cr3dencial-Ficticia-De-Prueba'
USUARIO = 'portal'
PUBLICA = '.'.join(('8', '8', '8', '8'))
OTRA_PUBLICA = '.'.join(('8', '8', '4', '4'))
PRIVADA = '.'.join(('10', '0', '0', '5'))
CUENTA = 'ana.ruiz@pruebas.local'

PARAMS = {
    'motor': 'mysql',
    'base_datos': 'erp',
    'otorgar': {'sentencia': 'INSERT OR IGNORE INTO usuarios (email, rol) '
                             'VALUES (%s, %s)',
                'parametros': ['correo', 'nivel']},
    'revocar': {'sentencia': 'DELETE FROM usuarios WHERE email = %s',
                'parametros': ['correo']},
    'consultar': {'sentencia': 'SELECT 1 FROM usuarios WHERE email = %s',
                  'parametros': ['correo']},
}


def params(**cambios):
    valores = json.loads(json.dumps(PARAMS))
    valores.update(cambios)
    return valores


def solicitud(cuenta=CUENTA, nivel='usuario'):
    return SolicitudConector(id_operacion='1', clave_idempotencia='c-1',
                             operacion='otorgar', nivel=nivel,
                             plataforma_id=7, cuenta=cuenta)


def dns(*direcciones):
    def getaddrinfo(host, puerto, **_):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (d, puerto))
                for d in direcciones]
    return getaddrinfo


# --------------------------------------------------------------------------- #
# Doble: SQLite con el marcador `%s` de los drivers
# --------------------------------------------------------------------------- #

class CursorSqlite:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sentencia, parametros=()):
        self._cursor.execute(sentencia.replace('%s', '?'), parametros)

    def fetchone(self):
        return self._cursor.fetchone()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class BdFalsa:
    """Conexión DB-API sobre SQLite que registra commit, rollback y cierre."""

    def __init__(self):
        self.sqlite = sqlite3.connect(':memory:', check_same_thread=False)
        self.sqlite.execute('CREATE TABLE usuarios (email TEXT UNIQUE, '
                            'rol TEXT)')
        self.sqlite.commit()
        self.eventos = []
        self.parametros = []
        self.falla = None

    def cursor(self):
        if self.falla:
            raise self.falla
        return CursorSqlite(self.sqlite.cursor())

    def commit(self):
        self.eventos.append('commit')
        self.sqlite.commit()

    def rollback(self):
        self.eventos.append('rollback')
        self.sqlite.rollback()

    def close(self):
        self.eventos.append('close')

    def filas(self):
        return self.sqlite.execute('SELECT email, rol FROM usuarios '
                                   'ORDER BY rowid').fetchall()


def conector(bd=None, valores=None, credencial=None, direcciones=(PUBLICA,),
             conectar=None):
    bd = bd or BdFalsa()
    llamadas = []

    def abrir(motor, parametros):
        llamadas.append((motor.nombre, parametros))
        return bd

    destino = Destino(host=HOST, puerto=3306, tiempo_espera=7,
                      params=MappingProxyType(valores or params()))
    c = ConectorBd(destino, credencial or Credencial(SECRETO, USUARIO),
                   getaddrinfo=dns(*direcciones), conectar=conectar or abrir)
    return c, bd, llamadas


# --------------------------------------------------------------------------- #
# Operaciones
# --------------------------------------------------------------------------- #

def test_otorga_y_es_idempotente():
    c, bd, _ = conector()
    assert c.otorgar(solicitud()).resultado == RESULTADO_EXITOSO
    assert c.otorgar(solicitud()).resultado == RESULTADO_SIN_CAMBIOS
    assert bd.filas() == [(CUENTA, 'usuario')]
    assert bd.eventos.count('commit') == 2
    assert bd.eventos.count('close') == 2


def test_revoca_y_es_idempotente():
    c, bd, _ = conector()
    c.otorgar(solicitud())
    assert c.revocar(solicitud()).resultado == RESULTADO_EXITOSO
    assert c.revocar(solicitud()).resultado == RESULTADO_SIN_CAMBIOS
    assert bd.filas() == []


def test_consulta_presencia_y_nunca_confirma():
    c, bd, _ = conector()
    assert c.consultar(solicitud()).presente is False
    c.otorgar(solicitud())
    resultado = c.consultar(solicitud())
    assert resultado.resultado == RESULTADO_EXITOSO and resultado.presente
    assert bd.eventos[-2:] == ['rollback', 'close']
    assert bd.eventos.count('commit') == 1  # solo el otorgar


def test_sin_consultar_configurado_es_permanente():
    valores = params()
    del valores['consultar']
    c, _, llamadas = conector(valores=valores)
    resultado = c.consultar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'consulta_no_disponible' and llamadas == []


# --------------------------------------------------------------------------- #
# Inyección
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('cuenta', [
    "x'); DROP TABLE usuarios;--@pruebas.local",
    'a"b@pruebas.local',
    "a'b@pruebas.local",
    'a;b@pruebas.local',
    'a`b@pruebas.local',
    'a\\b@pruebas.local',
    'a%s@pruebas.local',
    'a--b@pruebas.local',
])
def test_entrada_maliciosa_viaja_como_dato_y_no_altera_la_operacion(cuenta):
    c, bd, _ = conector()
    assert c.otorgar(solicitud(cuenta=cuenta)).resultado == RESULTADO_EXITOSO
    assert bd.filas() == [(cuenta, 'usuario')]  # guardada literal; tabla viva
    assert c.revocar(solicitud(cuenta=cuenta)).resultado == RESULTADO_EXITOSO
    assert bd.filas() == []


def test_valores_con_saltos_de_linea_o_control_no_se_envian():
    c, bd, llamadas = conector()
    resultado = c.otorgar(solicitud(cuenta='ana@pruebas.local\n; DROP'))
    assert resultado.motivo == 'valor_no_valido' and llamadas == []
    assert c.otorgar(solicitud(cuenta='sin-arroba')).motivo == 'valor_no_valido'
    assert c.otorgar(solicitud(nivel='')).motivo == 'valor_no_valido'


@pytest.mark.parametrize('sentencia', [
    'INSERT INTO usuarios (email) VALUES (%s); DROP TABLE usuarios',
    'INSERT INTO usuarios (email) VALUES (%s) -- x',
    'INSERT INTO usuarios (email) VALUES (%s) # x',
    'INSERT INTO usuarios (email) VALUES (%s) /* x */',
    "INSERT INTO usuarios (email) VALUES ('fijo')",
    'INSERT INTO usuarios (email) VALUES ("fijo")',
    'INSERT INTO `usuarios` (email) VALUES (%s)',
    'INSERT INTO usuarios (email) VALUES (%(correo)s)',
    'INSERT INTO usuarios (email) VALUES (%d)',
    'INSERT INTO usuarios (email) VALUES (?)',
    'INSERT INTO usuarios (email) VALUES ($$x$$)',
    'INSERT INTO usuarios (email)\nVALUES (%s)',
    ' INSERT INTO usuarios (email) VALUES (%s)',
    'SELECT * FROM usuarios WHERE email = %s',
    'DROP TABLE usuarios',
    'INSERT INTO usuarios (email) SELECT SLEEP(5) FROM x WHERE a = %s',
    'INSERT INTO usuarios (email) VALUES (%s) INTO OUTFILE x',
    '',
    None,
])
def test_sentencia_de_otorgar_inaceptable(sentencia):
    assert error_sentencia(sentencia, 'otorgar') is not None


@pytest.mark.parametrize('operacion,sentencia', [
    ('revocar', 'DELETE FROM usuarios'),
    ('revocar', 'UPDATE usuarios SET rol = %s'),
    ('revocar', 'INSERT INTO usuarios (email) VALUES (%s)'),
    ('consultar', 'DELETE FROM usuarios WHERE email = %s'),
    ('consultar', 'SELECT 1 FROM usuarios WHERE email = %s; SELECT 2'),
])
def test_sentencia_inaceptable_por_operacion(operacion, sentencia):
    assert error_sentencia(sentencia, operacion) is not None


@pytest.mark.parametrize('operacion,sentencia', [
    ('otorgar', 'INSERT INTO usuarios (email, rol) VALUES (%s, %s) ON '
                'DUPLICATE KEY UPDATE rol = VALUES(rol)'),
    ('otorgar', 'UPDATE usuarios SET activo = 1 WHERE email = %s'),
    ('revocar', 'DELETE FROM usuarios WHERE email = %s AND rol = %s'),
    ('consultar', 'SELECT 1 FROM usuarios WHERE email = %s'),
])
def test_sentencias_validas(operacion, sentencia):
    assert error_sentencia(sentencia, operacion) is None


# --------------------------------------------------------------------------- #
# Esquema de params
# --------------------------------------------------------------------------- #

def test_params_validos():
    assert validar_params(params()) == {}
    assert validar_params(params(motor='postgresql')) == {}


@pytest.mark.parametrize('cambios,campo', [
    ({'motor': 'oracle'}, 'motor'),
    ({'motor': None}, 'motor'),
    ({'base_datos': 'erp;drop'}, 'base_datos'),
    ({'base_datos': ''}, 'base_datos'),
    ({'otorgar': None}, 'otorgar'),
    ({'revocar': 'texto'}, 'revocar'),
    ({'host': 'evil.pruebas.local'}, 'host'),
    ({'otorgar': {'sentencia': 'DROP TABLE x', 'parametros': []}},
     'otorgar.sentencia'),
    ({'otorgar': {'sentencia': PARAMS['otorgar']['sentencia'],
                  'parametros': ['correo']}}, 'otorgar.parametros'),
    ({'otorgar': {'sentencia': PARAMS['otorgar']['sentencia'],
                  'parametros': ['correo', 'password']}},
     'otorgar.parametros'),
    ({'otorgar': {**PARAMS['otorgar'], 'max_filas': 11}}, 'otorgar.max_filas'),
    ({'otorgar': {**PARAMS['otorgar'], 'max_filas': True}},
     'otorgar.max_filas'),
    ({'otorgar': {**PARAMS['otorgar'], 'extra': 1}}, 'otorgar.extra'),
    ({'consultar': {**PARAMS['consultar'], 'max_filas': 2}},
     'consultar.max_filas'),
])
def test_params_invalidos(cambios, campo):
    assert campo in validar_params(params(**cambios))


def test_params_no_objeto():
    assert validar_params([]) == {'params': 'Debe ser un objeto.'}


def test_params_guardados_se_revalidan_en_cada_operacion():
    malos = params(otorgar={'sentencia': 'DROP TABLE usuarios',
                            'parametros': []})
    c, _, llamadas = conector(valores=malos)
    resultado = c.otorgar(solicitud())
    assert resultado.motivo == 'configuracion_invalida' and llamadas == []


def test_el_tipo_esta_registrado_y_se_valida_en_la_configuracion(monkeypatch):
    registry.registrar_tipo(TIPO)
    assert registry.obtener_tipo(TIPO_BD) is TIPO
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS', HOST)
    limpio, errores = validar_configuracion(
        {'type': 'bd', 'host': HOST, 'port': 3306, 'params': params(),
         'credential_ref': 'pokemon/erp-bd'}, entorno={
            'CONNECTOR_ALLOWED_HOSTS': HOST, 'APP_ENV': 'development'})
    assert errores == {} and limpio['type'] == 'bd'
    _, errores = validar_configuracion(
        {'type': 'bd', 'host': HOST, 'port': 3306,
         'params': params(motor='x'), 'credential_ref': 'pokemon/erp-bd'},
        entorno={'CONNECTOR_ALLOWED_HOSTS': HOST})
    assert 'params.motor' in errores


# --------------------------------------------------------------------------- #
# Destino seguro y credencial
# --------------------------------------------------------------------------- #

def test_conecta_a_la_ip_validada_con_el_host_del_destino():
    c, _, llamadas = conector()
    c.otorgar(solicitud())
    (motor, p), = llamadas
    assert motor == 'mysql'
    assert (p.ip, p.host, p.puerto, p.base_datos, p.usuario) == (
        PUBLICA, HOST, 3306, 'erp', USUARIO)
    assert p.tiempo == 10  # CONNECTOR_DB_TIMEOUT_SECONDS por defecto
    assert SECRETO not in repr(p)


def test_host_que_resuelve_a_ip_interna_no_se_conecta():
    c, _, llamadas = conector(direcciones=(PUBLICA, PRIVADA))
    resultado = c.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'destino_no_permitido' and llamadas == []


def test_dns_caido_es_transitorio():
    def sin_dns(*_a, **_k):
        raise socket.gaierror()
    destino = Destino(host=HOST, puerto=3306,
                      params=MappingProxyType(params()))
    c = ConectorBd(destino, Credencial(SECRETO, USUARIO), getaddrinfo=sin_dns)
    assert c.otorgar(solicitud()).resultado == RESULTADO_ERROR_TRANSITORIO


def test_prueba_otra_ip_solo_si_falla_la_conexion_de_red():
    intentos = []
    bd = BdFalsa()

    def abrir(motor, p):
        intentos.append(p.ip)
        if p.ip == PUBLICA:
            raise ErrorConexion()
        return bd

    c, _, _ = conector(bd=bd, direcciones=(PUBLICA, OTRA_PUBLICA),
                       conectar=abrir)
    assert c.otorgar(solicitud()).resultado == RESULTADO_EXITOSO
    assert intentos == [PUBLICA, OTRA_PUBLICA]


def test_sin_red_en_ninguna_ip_es_transitorio():
    def abrir(motor, p):
        raise ErrorConexion()
    c, _, _ = conector(conectar=abrir)
    resultado = c.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_TRANSITORIO
    assert resultado.motivo == 'red_no_disponible'


def test_un_error_tras_conectar_no_prueba_otra_ip():
    intentos = []

    def abrir(motor, p):
        intentos.append(p.ip)
        raise pymysql.err.OperationalError(1045, 'Access denied for secreto')

    c, _, _ = conector(direcciones=(PUBLICA, OTRA_PUBLICA), conectar=abrir)
    assert c.otorgar(solicitud()).motivo == 'bd_autenticacion_rechazada'
    assert intentos == [PUBLICA]


@pytest.mark.parametrize('credencial', [
    Credencial(SECRETO), Credencial('', USUARIO), Credencial(SECRETO, ''),
    Credencial('a\nb', USUARIO), Credencial(SECRETO, 'u\x00')])
def test_credencial_incompleta_o_con_control_no_conecta(credencial):
    c, _, llamadas = conector(credencial=credencial)
    resultado = c.otorgar(solicitud())
    assert resultado.motivo == 'credencial_no_encontrada' and llamadas == []


# --------------------------------------------------------------------------- #
# Transacción
# --------------------------------------------------------------------------- #

def test_mas_filas_de_las_permitidas_se_deshace():
    valores = params(revocar={'sentencia': 'DELETE FROM usuarios WHERE rol = %s',
                              'parametros': ['nivel']})
    c, bd, _ = conector(valores=valores)
    for correo in ('a@pruebas.local', 'b@pruebas.local', 'c@pruebas.local'):
        c.otorgar(solicitud(cuenta=correo))
    resultado = c.revocar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'bd_filas_excesivas'
    assert len(bd.filas()) == 3  # nada se borró
    assert bd.eventos[-2:] == ['rollback', 'close']


def test_max_filas_configurado_permite_varias():
    valores = params(revocar={'sentencia': 'DELETE FROM usuarios WHERE rol = %s',
                              'parametros': ['nivel'], 'max_filas': 5})
    c, bd, _ = conector(valores=valores)
    for correo in ('a@pruebas.local', 'b@pruebas.local'):
        c.otorgar(solicitud(cuenta=correo))
    assert c.revocar(solicitud()).resultado == RESULTADO_EXITOSO
    assert bd.filas() == []


def test_error_en_la_sentencia_hace_rollback_y_cierra():
    c, bd, _ = conector(valores=params(otorgar={
        'sentencia': 'INSERT INTO inexistente (email) VALUES (%s)',
        'parametros': ['correo']}))
    with pytest.raises(sqlite3.OperationalError):
        c.otorgar(solicitud())  # error ajeno al driver: lo trata el proveedor
    assert bd.eventos == ['rollback', 'close']


def test_error_del_driver_hace_rollback_cierra_y_se_clasifica():
    class Cursor(CursorSqlite):
        def execute(self, *_a):
            raise pymysql.err.OperationalError(1213, 'Deadlock en tabla secreta')

    bd = BdFalsa()
    bd.cursor = lambda: Cursor(bd.sqlite.cursor())
    c, _, _ = conector(bd=bd)
    resultado = c.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_TRANSITORIO
    assert resultado.motivo == 'bd_operacion_transitoria'
    assert resultado.detalle == 'MySQL 1213'
    assert 'secreta' not in repr(resultado)
    assert bd.eventos == ['rollback', 'close']


def test_falla_al_confirmar_es_transitoria():
    bd = BdFalsa()

    def commit():
        raise pymysql.err.OperationalError(2013, 'Lost connection')
    bd.commit = commit
    c, _, _ = conector(bd=bd)
    assert c.otorgar(solicitud()).resultado == RESULTADO_ERROR_TRANSITORIO
    assert 'close' in bd.eventos


# --------------------------------------------------------------------------- #
# Clasificación de errores
# --------------------------------------------------------------------------- #

def _mysql(codigo):
    return pymysql.err.OperationalError(codigo, 'texto del servidor')


@pytest.mark.parametrize('exc,transitorio,motivo', [
    (_mysql(1045), False, 'bd_autenticacion_rechazada'),
    (_mysql(1044), False, 'bd_autenticacion_rechazada'),
    (_mysql(2026), False, 'tls_no_valido'),
    (_mysql(1213), True, 'bd_operacion_transitoria'),
    (_mysql(1205), True, 'bd_operacion_transitoria'),
    (_mysql(2003), True, 'bd_operacion_transitoria'),
    (_mysql(2013), True, 'bd_operacion_transitoria'),
    (_mysql(9999), True, 'bd_operacion_transitoria'),
    (pymysql.err.IntegrityError(1062, 'Duplicate'), False,
     'bd_operacion_rechazada'),
    (pymysql.err.ProgrammingError(1146, 'no table'), False,
     'bd_operacion_rechazada'),
    (pymysql.err.OperationalError(1142, 'denied'), True,
     'bd_operacion_transitoria'),
])
def test_clasificacion_mysql(exc, transitorio, motivo):
    clase = MOTORES['mysql'].clasificar(exc)
    assert (clase.transitorio, clase.motivo) == (transitorio, motivo)


def test_certificado_invalido_en_la_cadena_de_causas_es_tls_permanente():
    try:
        try:
            raise ssl.SSLCertVerificationError('certificate verify failed')
        except ssl.SSLError as causa:
            raise pymysql.err.OperationalError(2003, "Can't connect") from causa
    except pymysql.err.OperationalError as exc:
        clase = MOTORES['mysql'].clasificar(exc)
    assert (clase.transitorio, clase.motivo) == (False, 'tls_no_valido')


def _pg(estado, clase=psycopg2.OperationalError):
    return type('ErrorPg', (clase,), {'pgcode': estado})('mensaje del servidor')


@pytest.mark.parametrize('estado,transitorio,motivo', [
    ('28P01', False, 'bd_autenticacion_rechazada'),
    ('28000', False, 'bd_autenticacion_rechazada'),
    ('40001', True, 'bd_operacion_transitoria'),
    ('40P01', True, 'bd_operacion_transitoria'),
    ('57014', True, 'bd_operacion_transitoria'),
    ('08006', True, 'bd_operacion_transitoria'),
    ('53300', True, 'bd_operacion_transitoria'),
    ('55P03', True, 'bd_operacion_transitoria'),
    ('23505', False, 'bd_operacion_rechazada'),
    ('42501', False, 'bd_operacion_rechazada'),
    ('42P01', False, 'bd_operacion_rechazada'),
])
def test_clasificacion_postgresql(estado, transitorio, motivo):
    clase = MOTORES['postgresql'].clasificar(_pg(estado))
    assert (clase.transitorio, clase.motivo) == (transitorio, motivo)
    assert clase.detalle == f'SQLSTATE {estado}'


@pytest.mark.parametrize('texto,transitorio,motivo', [
    ('SSL error: certificate verify failed', False, 'tls_no_valido'),
    ('password authentication failed for user "x"', False,
     'bd_autenticacion_rechazada'),
    ('connection refused', True, 'red_no_disponible'),
])
def test_clasificacion_postgresql_sin_codigo(texto, transitorio, motivo):
    clase = MOTORES['postgresql'].clasificar(psycopg2.OperationalError(texto))
    assert (clase.transitorio, clase.motivo) == (transitorio, motivo)


def test_el_mensaje_del_driver_nunca_llega_al_resultado():
    def abrir(motor, p):
        raise pymysql.err.OperationalError(1045, f"Access denied {SECRETO}")
    c, _, _ = conector(conectar=abrir)
    resultado = c.otorgar(solicitud())
    assert SECRETO not in repr(resultado) and 'Access denied' not in repr(
        resultado)
    assert resultado.motivo in MENSAJES


def test_motivos_nuevos_tienen_mensaje():
    for motivo in ('bd_autenticacion_rechazada', 'bd_operacion_rechazada',
                   'bd_operacion_transitoria', 'bd_filas_excesivas'):
        assert motivo in MENSAJES


# --------------------------------------------------------------------------- #
# TLS verificado y conexión a la IP validada (drivers simulados)
# --------------------------------------------------------------------------- #

def _parametros(ca=None):
    return ParametrosConexion(host=HOST, ip=PUBLICA, puerto=3306,
                              base_datos='erp', usuario=USUARIO,
                              secreto=SECRETO, tiempo=7, archivo_ca=ca)


def test_mysql_conecta_a_la_ip_y_exige_tls_verificado(monkeypatch):
    capturado = {}

    class EnchufeFalso:
        def settimeout(self, t):
            capturado['tiempo_enchufe'] = t

    class ConexionFalsa:
        def __init__(self, **kwargs):
            capturado['kwargs'] = kwargs

        def connect(self, enchufe):
            capturado['enchufe'] = enchufe

    def crear(direccion, tiempo):
        capturado['direccion'] = (direccion, tiempo)
        return EnchufeFalso()

    monkeypatch.setattr(bd_motores.socket, 'create_connection', crear)
    monkeypatch.setattr(bd_motores.pymysql.connections, 'Connection',
                        ConexionFalsa)
    MOTORES['mysql'].conectar(_parametros())
    kwargs = capturado['kwargs']
    assert capturado['direccion'] == ((PUBLICA, 3306), 7)
    assert kwargs['host'] == HOST  # el nombre, para verificar el certificado
    contexto = kwargs['ssl']
    assert contexto.verify_mode == ssl.CERT_REQUIRED
    assert contexto.check_hostname is True
    assert contexto.minimum_version >= ssl.TLSVersion.TLSv1_2
    assert kwargs['autocommit'] is False
    assert (kwargs['connect_timeout'], kwargs['read_timeout'],
            kwargs['write_timeout']) == (7, 7, 7)
    assert kwargs['password'] == SECRETO.encode()
    assert kwargs['defer_connect'] is True
    assert capturado['enchufe'] is not None


def test_mysql_sin_red_a_la_ip_es_error_de_conexion(monkeypatch):
    def falla(*_a):
        raise OSError('refused')
    monkeypatch.setattr(bd_motores.socket, 'create_connection', falla)
    with pytest.raises(ErrorConexion):
        MOTORES['mysql'].conectar(_parametros())


def test_mysql_con_ca_ilegible_es_tls_permanente(monkeypatch, tmp_path):
    with pytest.raises(pymysql.err.OperationalError) as info:
        MOTORES['mysql'].conectar(_parametros(ca=str(tmp_path / 'no-existe')))
    clase = MOTORES['mysql'].clasificar(info.value)
    assert (clase.transitorio, clase.motivo) == (False, 'tls_no_valido')


def test_postgresql_exige_verify_full_con_hostaddr(monkeypatch):
    capturado = {}
    monkeypatch.setattr(bd_motores.psycopg2, 'connect',
                        lambda **kw: capturado.update(kw) or object())
    MOTORES['postgresql'].conectar(_parametros(ca='/etc/ca/bd.pem'))
    assert capturado['sslmode'] == 'verify-full'
    assert capturado['host'] == HOST and capturado['hostaddr'] == PUBLICA
    assert capturado['sslrootcert'] == '/etc/ca/bd.pem'
    assert capturado['gssencmode'] == 'disable'
    assert capturado['connect_timeout'] == 7
    assert 'statement_timeout=7000' in capturado['options']
    MOTORES['postgresql'].conectar(_parametros())
    assert capturado['sslrootcert'] == 'system'


@pytest.mark.parametrize('texto,motivo', [
    ('SSL error: certificate verify failed', 'tls_no_valido'),
    ('connection to server failed: Connection refused', 'red'),
])
def test_postgresql_error_de_conexion(monkeypatch, texto, motivo):
    def falla(**_kw):
        raise psycopg2.OperationalError(texto)
    monkeypatch.setattr(bd_motores.psycopg2, 'connect', falla)
    if motivo == 'red':
        with pytest.raises(ErrorConexion):
            MOTORES['postgresql'].conectar(_parametros())
        return
    with pytest.raises(psycopg2.OperationalError) as info:
        MOTORES['postgresql'].conectar(_parametros())
    assert MOTORES['postgresql'].clasificar(info.value).motivo == motivo


def test_no_hay_opcion_para_desactivar_tls():
    assert 'tls' in validar_params(params(tls=False))  # campo no admitido


# --------------------------------------------------------------------------- #
# Configuración (CONNECTOR_DB_*)
# --------------------------------------------------------------------------- #

def test_configuracion_por_defecto():
    cfg = cargar_configuracion_bd({})
    assert (cfg.tiempo, cfg.archivo_ca) == (10, '')


def test_configuracion_con_valores():
    cfg = cargar_configuracion_bd({VAR_TIEMPO_BD: '15',
                                   'CONNECTOR_DB_CA_FILE': ' /etc/ca.pem '})
    assert (cfg.tiempo, cfg.archivo_ca) == (15, '/etc/ca.pem')


@pytest.mark.parametrize('valor', ['x', '0', '121', '-1', '30', '60'])
def test_configuracion_invalida_detiene_el_arranque(valor):
    # El intento por defecto es de 60 s: 30 s x 2 ya no cabe.
    with pytest.raises(ErrorConfiguracionConectores):
        cargar_configuracion_bd({VAR_TIEMPO_BD: valor})


def test_el_tiempo_de_la_configuracion_llega_al_driver(monkeypatch):
    monkeypatch.setenv(VAR_TIEMPO_BD, '12')
    c, _, llamadas = conector()
    c.otorgar(solicitud())
    assert llamadas[0][1].tiempo == 12
