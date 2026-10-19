"""Cliente LDAP centralizado: lecturas, escape y errores (FNC-040).

`ldap3` corre con `MOCK_SYNC` (ver `conftest.py`): sin red.
"""

import logging
import ssl

import ldap3
import pytest

from app.modules.directory import ldap_client
from app.modules.directory.ldap_client import (MENSAJE_AMBIGUO, MENSAJE_ERROR,
                                               ErrorDirectorio,
                                               escapar_filtro,
                                               escapar_valor_dn)
from tests.directory.conftest import (CUENTA_SERVICIO, USUARIOS_BASE_DN,
                                      dn_persona)
from tests.matriz_proteccion import CONTRASENA_FICTICIA, HOST_LDAP_FICTICIO

CONTRASENA_ERRONEA = 'clave-erronea-de-prueba'


# --------------------------------------------------------------------------- #
# Escape (SEC-LDAP-06, SEG-12)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('valor, esperado', [
    ('*', r'\2a'),
    ('(', r'\28'),
    (')', r'\29'),
    ('\\', r'\5c'),
    ('\0', r'\00'),
    ('*)(uid=*', r'\2a\29\28uid=\2a'),
    ('jperez', 'jperez'),
])
def test_filtro_escapa_caracteres_especiales(valor, esperado):
    assert escapar_filtro(valor) == esperado


@pytest.mark.parametrize('valor, esperado', [
    ('a,b', r'a\,b'),
    ('a=b', r'a\=b'),
    ('a+b', r'a\+b'),
    ('a\\b', r'a\\b'),
    (' borde ', r'\ borde\ '),
])
def test_valor_de_dn_se_escapa(valor, esperado):
    assert escapar_valor_dn(valor) == esperado


# --------------------------------------------------------------------------- #
# Conexión: TLS validado y tiempos de espera
# --------------------------------------------------------------------------- #

def test_servidor_exige_certificado_valido_y_tiempo_de_espera(directorio):
    servidor = directorio.servidor

    assert servidor.host == HOST_LDAP_FICTICIO
    assert servidor.ssl is True
    assert servidor.tls.validate == ssl.CERT_REQUIRED
    assert servidor.tls.sni == HOST_LDAP_FICTICIO
    assert servidor.connect_timeout == directorio.configuracion.tiempo_espera


def test_ca_configurada_se_usa_para_validar(crear_directorio, tmp_path):
    ca = tmp_path / 'ca.pem'
    ca.write_text('certificado de prueba')

    directorio = crear_directorio(LDAP_CA_CERT_FILE=str(ca))

    assert directorio.servidor.tls.ca_certs_file == str(ca)


def test_conexion_de_servicio_es_de_solo_lectura_y_con_espera(directorio):
    with directorio.cliente.conexion_servicio() as conexion:
        assert conexion.bound is True
        assert conexion.read_only is True
        assert conexion.receive_timeout == directorio.configuracion.tiempo_espera
        assert conexion.user == CUENTA_SERVICIO


def test_ldap_negocia_starttls_antes_de_enviar_la_credencial(
        crear_directorio, monkeypatch):
    directorio = crear_directorio(LDAP_URL=f'ldap://{HOST_LDAP_FICTICIO}')
    orden = []
    bind_original = ldap3.Connection.bind

    def start_tls(self, *args, **kwargs):
        orden.append('start_tls')
        self.tls_started = True  # como ldap3 tras un StartTLS exitoso
        return True

    def bind(self, *args, **kwargs):
        orden.append('bind')
        return bind_original(self, *args, **kwargs)

    monkeypatch.setattr(ldap3.Connection, 'start_tls', start_tls)
    monkeypatch.setattr(ldap3.Connection, 'bind', bind)

    with directorio.cliente.conexion_servicio():
        pass

    assert orden == ['start_tls', 'bind']


def test_si_starttls_falla_no_se_envia_la_credencial(crear_directorio,
                                                     monkeypatch):
    # MOCK_SYNC responde unwillingToPerform a StartTLS, como un servidor sin TLS.
    directorio = crear_directorio(LDAP_URL=f'ldap://{HOST_LDAP_FICTICIO}')
    binds = []
    monkeypatch.setattr(ldap3.Connection, 'bind',
                        lambda self, *a, **k: binds.append(1))

    with pytest.raises(ErrorDirectorio, match=MENSAJE_ERROR):
        directorio.cliente.buscar_usuario('jperez')
    assert binds == []


def test_bind_rechazado_da_error_controlado_sin_la_contrasena(
        crear_directorio, caplog):
    directorio = crear_directorio(LDAP_BIND_PASSWORD=CONTRASENA_ERRONEA)
    caplog.set_level(logging.DEBUG)

    with pytest.raises(ErrorDirectorio) as error:
        directorio.cliente.buscar_usuario('jperez')

    assert str(error.value) == MENSAJE_ERROR
    assert 'LDAPInvalidCredentialsResult' in caplog.text
    assert CONTRASENA_ERRONEA not in caplog.text
    assert CONTRASENA_ERRONEA not in str(error.value)


def test_la_contrasena_se_oculta_si_aparece_en_el_detalle(directorio, caplog):
    error = directorio.cliente.registrar_error(
        'prueba', ldap3.core.exceptions.LDAPException(
            f'detalle con {CONTRASENA_FICTICIA}'))

    assert CONTRASENA_FICTICIA not in caplog.text
    assert '***' in caplog.text
    assert str(error) == MENSAJE_ERROR


# --------------------------------------------------------------------------- #
# Búsqueda de usuario
# --------------------------------------------------------------------------- #

def test_buscar_usuario_por_uid(directorio):
    directorio.persona('jperez', correo='jperez@pruebas.local')

    usuario = directorio.cliente.buscar_usuario('jperez')

    assert usuario.dn == dn_persona('jperez')
    assert usuario.identificador == 'jperez'
    assert usuario.atributos['mail'] == 'jperez@pruebas.local'
    assert usuario.atributos['displayName'] == 'Persona jperez'


def test_usuario_inexistente_da_none(directorio):
    directorio.persona('jperez')

    assert directorio.cliente.buscar_usuario('mlopez') is None


@pytest.mark.parametrize('inyeccion', ['*', 'j*', '*)(uid=*', 'jperez)(|(uid=*'])
def test_comodin_o_parentesis_no_amplian_la_busqueda(directorio, inyeccion):
    directorio.persona('jperez')
    directorio.persona('mlopez')

    assert directorio.cliente.buscar_usuario(inyeccion) is None


def test_atributo_de_usuario_configurable(crear_directorio):
    directorio = crear_directorio(LDAP_USER_ATTR='mail')
    directorio.persona('jperez', correo='jperez@pruebas.local')

    usuario = directorio.cliente.buscar_usuario('jperez@pruebas.local')

    assert usuario.dn == dn_persona('jperez')
    assert usuario.identificador == 'jperez@pruebas.local'


def test_identificador_duplicado_es_error_ambiguo(directorio):
    directorio.persona('jperez')
    directorio.agregar(f'uid=jperez,ou=otra,{USUARIOS_BASE_DN}',
                       objectClass='inetOrgPerson', uid='jperez', cn='x',
                       sn='x')

    with pytest.raises(ErrorDirectorio, match=MENSAJE_AMBIGUO):
        directorio.cliente.buscar_usuario('jperez')


# --------------------------------------------------------------------------- #
# Grupos de un usuario
# --------------------------------------------------------------------------- #

def test_grupos_groupofnames_por_dn_del_miembro(directorio):
    dn = directorio.persona('jperez')
    otro = directorio.persona('mlopez')
    grupo_a = directorio.grupo('plataforma-a-usuario', [dn, otro])
    grupo_b = directorio.grupo('plataforma-b-admin', [dn])
    directorio.grupo('plataforma-c-usuario', [otro])
    directorio.grupo('otra-clase', [dn], clase='groupOfUniqueNames',
                     atributo='uniqueMember')

    usuario = directorio.cliente.buscar_usuario('jperez')

    assert directorio.cliente.grupos_de_usuario(usuario) == sorted(
        [grupo_a, grupo_b])


def test_grupos_posixgroup_por_memberuid(crear_directorio):
    directorio = crear_directorio(LDAP_GROUP_OBJECT_CLASS='posixGroup',
                                  LDAP_GROUP_MEMBER_ATTR='memberUid')
    directorio.persona('jperez')
    grupo = directorio.grupo('plataforma-a-usuario', ['jperez'],
                             clase='posixGroup', atributo='memberUid')
    directorio.grupo('plataforma-b-usuario', ['mlopez'], clase='posixGroup',
                     atributo='memberUid')

    usuario = directorio.cliente.buscar_usuario('jperez')

    assert directorio.cliente.grupos_de_usuario(usuario) == [grupo]


def test_usuario_sin_grupos_da_lista_vacia(directorio):
    directorio.persona('jperez')
    usuario = directorio.cliente.buscar_usuario('jperez')

    assert directorio.cliente.grupos_de_usuario(usuario) == []


# --------------------------------------------------------------------------- #
# Existencia de un DN
# --------------------------------------------------------------------------- #

def test_existe_dn(directorio):
    dn = directorio.persona('jperez')

    assert directorio.cliente.existe_dn(dn) is True
    assert directorio.cliente.existe_dn(dn_persona('mlopez')) is False


@pytest.mark.parametrize('dn', ['', 'sin-igual', 'uid=a,,dc=x'])
def test_dn_mal_formado_no_existe_y_no_consulta(directorio, monkeypatch, dn):
    monkeypatch.setattr(ldap_client, 'Connection', None)  # falla si conecta

    assert directorio.cliente.existe_dn(dn) is False


# --------------------------------------------------------------------------- #
# Regresiones de auditor-seguridad (FNC-040, hallazgos Baja)
# --------------------------------------------------------------------------- #

def test_starttls_sin_efecto_no_envia_la_credencial(crear_directorio,
                                                    monkeypatch):
    # start_tls() devuelve sin error pero la conexión sigue sin TLS.
    directorio = crear_directorio(LDAP_URL=f'ldap://{HOST_LDAP_FICTICIO}')
    binds = []
    monkeypatch.setattr(ldap3.Connection, 'start_tls',
                        lambda self, *a, **k: False)
    monkeypatch.setattr(ldap3.Connection, 'bind',
                        lambda self, *a, **k: binds.append(1))

    with pytest.raises(ErrorDirectorio, match=MENSAJE_ERROR):
        directorio.cliente.buscar_usuario('jperez')
    assert binds == []


def test_busqueda_ambigua_no_registra_el_identificador(directorio, caplog):
    identificador = 'jperez'
    directorio.persona(identificador)
    directorio.agregar(f'uid={identificador},ou=otra,{USUARIOS_BASE_DN}',
                       objectClass='inetOrgPerson', uid=identificador,
                       cn='x', sn='x')
    caplog.set_level(logging.DEBUG)

    with pytest.raises(ErrorDirectorio, match=MENSAJE_AMBIGUO):
        directorio.cliente.buscar_usuario(identificador)

    assert identificador not in caplog.text
    assert 'uid' in caplog.text and USUARIOS_BASE_DN in caplog.text
