"""Configuración del directorio y validación al arrancar (FNC-040, ADR-004).

Criterio: sin TLS configurado la app no arranca con el directorio activo.
"""

import pytest

from app import create_app
from app.modules.directory.configuracion import (ATRIBUTO_MIEMBRO_POR_DEFECTO,
                                          ATRIBUTO_USUARIO_POR_DEFECTO,
                                          CLASE_GRUPO_POR_DEFECTO,
                                          TIEMPO_ESPERA_POR_DEFECTO,
                                          ErrorConfiguracionDirectorio,
                                          cargar_configuracion,
                                          directorio_activo,
                                          validar_al_arrancar)
from tests.directory.conftest import ENTORNO_VALIDO
from tests.matriz_proteccion import CONTRASENA_FICTICIA, HOST_LDAP_FICTICIO


def _con(**cambios):
    entorno = dict(ENTORNO_VALIDO)
    for nombre, valor in cambios.items():
        if valor is None:
            entorno.pop(nombre, None)
        else:
            entorno[nombre] = valor
    return entorno


def test_sin_url_el_directorio_esta_inactivo_y_no_se_valida():
    assert directorio_activo({}) is False
    assert validar_al_arrancar({'LDAP_BIND_DN': 'no-es-un-dn'}) is None


def test_configuracion_valida_con_valores_por_defecto_de_openldap():
    cfg = validar_al_arrancar(dict(ENTORNO_VALIDO))

    assert cfg.host == HOST_LDAP_FICTICIO
    assert cfg.puerto == 636
    assert cfg.usa_ldaps is True
    assert cfg.ca_cert_file is None
    assert cfg.atributo_usuario == ATRIBUTO_USUARIO_POR_DEFECTO == 'uid'
    assert cfg.clase_grupo == CLASE_GRUPO_POR_DEFECTO == 'groupOfNames'
    assert cfg.atributo_miembro == ATRIBUTO_MIEMBRO_POR_DEFECTO == 'member'
    assert cfg.tiempo_espera == TIEMPO_ESPERA_POR_DEFECTO


def test_ldap_sin_s_usa_starttls_en_el_puerto_389():
    cfg = cargar_configuracion(_con(LDAP_URL=f'ldap://{HOST_LDAP_FICTICIO}'))

    assert cfg.usa_ldaps is False
    assert cfg.puerto == 389


def test_atributos_y_tiempo_de_espera_se_leen_de_variables():
    cfg = cargar_configuracion(_con(
        LDAP_URL=f'ldaps://{HOST_LDAP_FICTICIO}:1636',
        LDAP_USER_ATTR='mail', LDAP_GROUP_OBJECT_CLASS='posixGroup',
        LDAP_GROUP_MEMBER_ATTR='memberUid', LDAP_TIMEOUT_SECONDS='9'))

    assert (cfg.puerto, cfg.atributo_usuario, cfg.clase_grupo,
            cfg.atributo_miembro, cfg.tiempo_espera) == (
        1636, 'mail', 'posixGroup', 'memberUid', 9)


@pytest.mark.parametrize('url', [
    f'http://{HOST_LDAP_FICTICIO}',      # esquema sin TLS de LDAP
    f'ldapi://{HOST_LDAP_FICTICIO}',
    HOST_LDAP_FICTICIO,                  # sin esquema
    'ldaps://',                          # sin host
    f'ldaps://{HOST_LDAP_FICTICIO}/dc=x',
    f'ldaps://{HOST_LDAP_FICTICIO}:no-numero',
])
def test_url_sin_tls_o_mal_formada_detiene_el_arranque(url):
    with pytest.raises(ErrorConfiguracionDirectorio, match='LDAP_URL'):
        validar_al_arrancar(_con(LDAP_URL=url))


def test_url_con_ip_se_rechaza():
    # Dirección de documentación (RFC 3849). Los lineamientos prohíben IPv4
    # literales en el código, también en pruebas; la regla es la misma
    # (`ipaddress.ip_address`) para ambas versiones.
    with pytest.raises(ErrorConfiguracionDirectorio, match='no una dirección IP'):
        validar_al_arrancar(_con(LDAP_URL='ldaps://[2001:db8::1]'))


@pytest.mark.parametrize('variable', ['LDAP_BIND_DN', 'LDAP_BIND_PASSWORD',
                                      'LDAP_USERS_BASE_DN',
                                      'LDAP_GROUPS_BASE_DN'])
def test_variable_obligatoria_faltante_detiene_el_arranque(variable):
    with pytest.raises(ErrorConfiguracionDirectorio, match=variable):
        validar_al_arrancar(_con(**{variable: None}))


def test_dn_invalido_detiene_el_arranque():
    with pytest.raises(ErrorConfiguracionDirectorio, match='LDAP_USERS_BASE_DN'):
        validar_al_arrancar(_con(LDAP_USERS_BASE_DN='sin-igual'))


@pytest.mark.parametrize('variable', ['LDAP_USER_ATTR',
                                      'LDAP_GROUP_OBJECT_CLASS',
                                      'LDAP_GROUP_MEMBER_ATTR'])
def test_atributo_con_caracteres_de_filtro_se_rechaza(variable):
    with pytest.raises(ErrorConfiguracionDirectorio, match=variable):
        validar_al_arrancar(_con(**{variable: 'uid)(objectClass=*'}))


@pytest.mark.parametrize('valor', ['0', '-3', 'cinco'])
def test_tiempo_de_espera_invalido_se_rechaza(valor):
    with pytest.raises(ErrorConfiguracionDirectorio,
                       match='LDAP_TIMEOUT_SECONDS'):
        validar_al_arrancar(_con(LDAP_TIMEOUT_SECONDS=valor))


def test_ca_inexistente_detiene_el_arranque(tmp_path):
    with pytest.raises(ErrorConfiguracionDirectorio, match='LDAP_CA_CERT_FILE'):
        validar_al_arrancar(_con(LDAP_CA_CERT_FILE=str(tmp_path / 'no.pem')))


def test_ca_existente_se_acepta(tmp_path):
    ca = tmp_path / 'ca.pem'
    ca.write_text('certificado de prueba')

    assert cargar_configuracion(_con(LDAP_CA_CERT_FILE=str(ca))).ca_cert_file \
        == str(ca)


def test_el_error_y_el_repr_no_muestran_la_contrasena_de_bind():
    cfg = cargar_configuracion(dict(ENTORNO_VALIDO))
    assert CONTRASENA_FICTICIA not in repr(cfg)

    with pytest.raises(ErrorConfiguracionDirectorio) as error:
        validar_al_arrancar(_con(LDAP_URL='http://x.invalid'))
    assert CONTRASENA_FICTICIA not in str(error.value)


def test_create_app_no_arranca_con_directorio_sin_tls(monkeypatch, tmp_path):
    monkeypatch.setenv('LDAP_URL', f'ldap+plain://{HOST_LDAP_FICTICIO}')

    with pytest.raises(ErrorConfiguracionDirectorio, match='TLS'):
        create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI':
                    f"sqlite:///{tmp_path / 'pruebas.db'}"})


def test_create_app_arranca_con_directorio_valido(monkeypatch, tmp_path):
    for nombre, valor in ENTORNO_VALIDO.items():
        monkeypatch.setenv(nombre, valor)

    aplicacion = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI':
                             f"sqlite:///{tmp_path / 'pruebas.db'}"})
    assert aplicacion is not None
