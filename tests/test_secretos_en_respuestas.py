"""Las respuestas de SMTP y LDAP nunca devuelven contraseñas (FNC-023).

Se comprueba sobre el texto completo de la respuesta: ni la clave ni un campo
de contraseña aparecen, venga la configuración de la BD o del entorno.
"""

import pytest

from app import db
from app.modules.auth.models import AuthConfig
from app.modules.notifications.models import SMTPConfig
from tests.matriz_proteccion import HOST_LDAP_FICTICIO, HOST_SMTP_FICTICIO

A = '/api/v1'
CLAVE_SMTP = 'clave-smtp-ficticia'
CLAVE_LDAP = 'clave-ldap-ficticia'
CAMPOS_DE_CLAVE = ('password', 'ldap_pass')


def _sin_secretos(respuesta, clave):
    assert respuesta.status_code == 200, respuesta.get_json()
    texto = respuesta.get_data(as_text=True)
    assert clave not in texto
    datos = respuesta.get_json()
    for valor in (datos, *(v for v in datos.values() if isinstance(v, dict))):
        assert not set(CAMPOS_DE_CLAVE) & set(valor)


@pytest.fixture
def smtp_en_bd(app):
    db.session.add(SMTPConfig(server=HOST_SMTP_FICTICIO, username='cuenta',
                              password=CLAVE_SMTP))
    db.session.commit()


@pytest.fixture
def ldap_en_bd(app):
    db.session.add(AuthConfig(ldap_host=HOST_LDAP_FICTICIO,
                              ldap_user='cn=servicio', ldap_pass=CLAVE_LDAP))
    db.session.commit()


def test_get_smtp_desde_bd(smtp_en_bd, cliente_admin):
    _sin_secretos(cliente_admin.get(f'{A}/smtp'), CLAVE_SMTP)


def test_get_smtp_desde_entorno(app, cliente_admin, monkeypatch):
    monkeypatch.setenv('SMTP_SERVER', HOST_SMTP_FICTICIO)
    monkeypatch.setenv('SMTP_USER', 'cuenta')
    monkeypatch.setenv('SMTP_PASSWORD', CLAVE_SMTP)

    respuesta = cliente_admin.get(f'{A}/smtp')

    _sin_secretos(respuesta, CLAVE_SMTP)
    assert respuesta.get_json()['source'] == 'env'


def test_put_smtp_no_devuelve_la_clave(app, cliente_admin):
    respuesta = cliente_admin.put(f'{A}/smtp', json={
        'server': HOST_SMTP_FICTICIO, 'password': CLAVE_SMTP})

    _sin_secretos(respuesta, CLAVE_SMTP)
    assert SMTPConfig.query.one().password == CLAVE_SMTP


def test_get_auth_config(ldap_en_bd, cliente_admin):
    _sin_secretos(cliente_admin.get(f'{A}/auth-config'), CLAVE_LDAP)


def test_put_auth_config_no_devuelve_la_clave(app, cliente_admin):
    respuesta = cliente_admin.put(f'{A}/auth-config', json={
        'ldap_host': HOST_LDAP_FICTICIO, 'ldap_pass': CLAVE_LDAP})

    _sin_secretos(respuesta, CLAVE_LDAP)
    assert AuthConfig.query.one().ldap_pass == CLAVE_LDAP


@pytest.mark.parametrize('ruta,campo,modelo,clave', [
    ('/smtp', 'password', SMTPConfig, CLAVE_SMTP),
    ('/auth-config', 'ldap_pass', AuthConfig, CLAVE_LDAP),
])
def test_clave_vacia_no_borra_la_guardada(smtp_en_bd, ldap_en_bd,
                                          cliente_admin, ruta, campo, modelo,
                                          clave):
    respuesta = cliente_admin.put(A + ruta, json={campo: ''})

    assert respuesta.status_code == 200
    assert getattr(modelo.query.one(), campo) == clave
