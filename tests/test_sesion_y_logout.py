"""Sesión tras el login y cierre de sesión: `POST /api/v1/auth/logout` (FNC-022)."""

import pytest

from app import db
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import (A, hay_auditoria, iniciar_sesion_api,
                                   usuario_en_sesion)

COOKIE_SESION = 'nexus_session'
URL_SLO_FICTICIA = 'https://auth.pruebas.invalid/logout'
URL_BASE_FICTICIA = 'https://portal.pruebas.invalid'


@pytest.fixture
def usuario_local(crear_usuario):
    return crear_usuario(contrasena=CONTRASENA_FICTICIA)


@pytest.fixture
def cliente_con_login(client, usuario_local):
    """Cliente con sesión abierta por el login real."""
    respuesta = iniciar_sesion_api(client, usuario_local.email,
                                   CONTRASENA_FICTICIA)
    assert respuesta.status_code == 200
    return client


# --------------------------------------------------------------------------- #
# Sesión
# --------------------------------------------------------------------------- #

def test_login_emite_la_cookie_de_sesion(cliente_con_login):
    assert cliente_con_login.get_cookie(COOKIE_SESION) is not None


def test_sesion_identifica_al_usuario_en_peticiones_siguientes(
        cliente_con_login, usuario_local):
    assert usuario_en_sesion(cliente_con_login) == usuario_local.email
    contexto = cliente_con_login.get(f'{A}/context').get_json()
    assert contexto['authenticated'] is True


def test_sin_login_no_hay_sesion(client):
    assert usuario_en_sesion(client) is None
    assert client.get(f'{A}/context').get_json()['authenticated'] is False


def test_cuenta_desactivada_pierde_la_sesion(cliente_con_login, usuario_local):
    """SEC-AUTH-11. Hoy ya se cumple: en Flask-Login 0.6.3 `is_authenticated`
    devuelve `is_active`, así que `@login_required` responde 401."""
    usuario_local.is_active = False
    db.session.commit()

    assert usuario_en_sesion(cliente_con_login) is None


# --------------------------------------------------------------------------- #
# Logout
# --------------------------------------------------------------------------- #

def test_logout_cierra_la_sesion(cliente_con_login, usuario_local):
    respuesta = cliente_con_login.post(f'{A}/logout')

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {'status': 'success', 'redirect': None}
    assert usuario_en_sesion(cliente_con_login) is None
    assert hay_auditoria('CIERRE DE SESIÓN',
                         'success', target=usuario_local.email)


def test_logout_sin_sesion_da_401(client):
    assert client.post(f'{A}/logout').status_code == 401


def test_logout_con_sso_devuelve_la_url_de_cierre_de_authelia(
        cliente_con_login, monkeypatch):
    monkeypatch.setenv('AUTHELIA_ENABLED', 'true')
    monkeypatch.setenv('AUTHELIA_SLO_URL', URL_SLO_FICTICIA)
    monkeypatch.setenv('BASE_URL', URL_BASE_FICTICIA)

    respuesta = cliente_con_login.post(f'{A}/logout')

    assert respuesta.get_json()['redirect'] == \
        f'{URL_SLO_FICTICIA}?rd={URL_BASE_FICTICIA}/login'
    assert usuario_en_sesion(cliente_con_login) is None


def test_logout_con_sso_sin_url_de_cierre_no_redirige(cliente_con_login,
                                                      monkeypatch):
    monkeypatch.setenv('AUTHELIA_ENABLED', 'true')

    respuesta = cliente_con_login.post(f'{A}/logout')

    assert respuesta.get_json()['redirect'] is None
