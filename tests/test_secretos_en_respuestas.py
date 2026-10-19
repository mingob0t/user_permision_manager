"""Las respuestas de SMTP y LDAP nunca devuelven contraseñas (FNC-023).

Se comprueba sobre el texto completo de la respuesta: ni la clave ni un campo
de contraseña aparecen, venga la configuración de la BD o del entorno.
"""

import pytest
from sqlalchemy import text

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
    """BD previa a la migración 0004 (FNC-043): clave de bind guardada.

    Por SQL directo: el modelo ya no permite escribirla.
    """
    db.session.execute(text(
        'INSERT INTO auth_config (ldap_host, ldap_user, ldap_pass) '
        'VALUES (:host, :usuario, :clave)'),
        {'host': HOST_LDAP_FICTICIO, 'usuario': 'cn=servicio',
         'clave': CLAVE_LDAP})
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


def test_put_auth_config_no_guarda_la_clave(app, cliente_admin):
    """FNC-043 (SEG-08): la clave de bind ya no se guarda en la BD."""
    respuesta = cliente_admin.put(f'{A}/auth-config', json={
        'ldap_host': HOST_LDAP_FICTICIO, 'ldap_pass': CLAVE_LDAP})

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'campo_no_permitido'
    assert CLAVE_LDAP not in respuesta.get_data(as_text=True)
    assert AuthConfig.query.filter(AuthConfig.ldap_pass.isnot(None)).count() == 0


def test_clave_vacia_no_borra_la_guardada(smtp_en_bd, cliente_admin):
    respuesta = cliente_admin.put(f'{A}/smtp', json={'password': ''})

    assert respuesta.status_code == 200
    assert SMTPConfig.query.one().password == CLAVE_SMTP
