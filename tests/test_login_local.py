"""Login con cuenta local: `POST /api/v1/auth/login` con `method: local` (FNC-022).

Desde FNC-077 solo entra la cuenta de emergencia (superadmin local); con
`LOGIN_LOCAL_TODAS_LAS_CUENTAS=true` y `APP_ENV=development`, cualquier cuenta
local.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.models import AuditLog
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import (MENSAJE_CREDENCIALES,
                                   activar_login_local_de_todas, hay_auditoria,
                                   iniciar_sesion_api, usuario_en_sesion)

CONTRASENA_ERRONEA = 'clave-erronea-de-prueba'

# Umbral provisional (SEC-AUTH-10 lo deja "Por confirmar"): FNC-014 lo ajusta.
INTENTOS_ANTES_DEL_LIMITE = 20


def test_login_local_de_la_cuenta_de_emergencia_abre_sesion(client,
                                                            crear_usuario):
    usuario = crear_usuario(ROLE_ADMIN, contrasena=CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {'status': 'success', 'role': ROLE_ADMIN}
    assert usuario_en_sesion(client) == usuario.email
    assert hay_auditoria('ACCESO LOCAL', 'success', target=usuario.email)


@pytest.mark.parametrize('rol', [ROLE_USER, ROLE_AREA_ADMIN])
def test_cuenta_local_que_no_es_de_emergencia_no_entra(client, crear_usuario,
                                                       rol):
    """Regresión FNC-077: con la contraseña correcta abría sesión."""
    usuario = crear_usuario(rol, contrasena=CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 401
    assert respuesta.get_json() == {'status': 'error',
                                    'message': MENSAJE_CREDENCIALES}
    assert usuario_en_sesion(client) is None
    registro = AuditLog.query.filter_by(action='ACCESO FALLIDO',
                                        target=usuario.email).one()
    assert 'login_local_solo_cuenta_de_emergencia' in registro.detail


@pytest.mark.parametrize('rol', [ROLE_USER, ROLE_AREA_ADMIN])
def test_bandera_de_desarrollo_permite_cualquier_cuenta_local(
        client, crear_usuario, monkeypatch, rol):
    activar_login_local_de_todas(monkeypatch)
    usuario = crear_usuario(rol, contrasena=CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 200
    assert usuario_en_sesion(client) == usuario.email


@pytest.mark.parametrize('entorno', [None, 'production', 'staging', ''])
def test_bandera_de_desarrollo_se_ignora_fuera_de_desarrollo(
        client, crear_usuario, monkeypatch, entorno):
    activar_login_local_de_todas(monkeypatch, entorno=entorno)
    usuario = crear_usuario(ROLE_USER, contrasena=CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None


def test_contrasena_erronea_da_401_sin_sesion(client, crear_usuario):
    usuario = crear_usuario(contrasena=CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_ERRONEA)

    assert respuesta.status_code == 401
    assert respuesta.get_json() == {'status': 'error',
                                    'message': MENSAJE_CREDENCIALES}
    assert usuario_en_sesion(client) is None
    assert hay_auditoria('ACCESO FALLIDO', 'error', target=usuario.email)


def test_mensaje_uniforme_exista_o_no_la_cuenta(app, crear_usuario):
    """Contraseña mala, cuenta inexistente y cuenta sin clave local responden igual."""
    con_clave = crear_usuario(contrasena=CONTRASENA_FICTICIA)
    sin_clave = crear_usuario()

    respuestas = [
        iniciar_sesion_api(app.test_client(), con_clave.email,
                           CONTRASENA_ERRONEA),
        iniciar_sesion_api(app.test_client(), 'no-existe@pruebas.local',
                           CONTRASENA_ERRONEA),
        iniciar_sesion_api(app.test_client(), sin_clave.email,
                           CONTRASENA_ERRONEA),
    ]

    assert {r.status_code for r in respuestas} == {401}
    assert all(r.get_json() == respuestas[0].get_json() for r in respuestas)


def test_usuario_inactivo_no_obtiene_sesion_y_da_el_mensaje_uniforme(
        client, crear_usuario):
    # Regresión (FNC-042, decisión del dueño 2026-10-15, SEC-AUTH-09): con la
    # contraseña correcta respondía 403 "La cuenta está desactivada.", lo
    # que confirmaba la contraseña de una cuenta desactivada.
    usuario = crear_usuario(ROLE_ADMIN, contrasena=CONTRASENA_FICTICIA,
                            activo=False)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 401
    assert respuesta.get_json() == {'status': 'error',
                                    'message': MENSAJE_CREDENCIALES}
    assert usuario_en_sesion(client) is None
    assert hay_auditoria('ACCESO FALLIDO', 'error', target=usuario.email)


def test_usuario_inactivo_con_contrasena_erronea_da_el_mensaje_uniforme(
        client, crear_usuario):
    usuario = crear_usuario(contrasena=CONTRASENA_FICTICIA, activo=False)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_ERRONEA)

    assert respuesta.status_code == 401
    assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES


@pytest.mark.parametrize('rol', [ROLE_USER, ROLE_ADMIN])
@pytest.mark.parametrize('origen', ['ldap', 'sso'])
def test_cuenta_no_local_no_entra_por_login_local(client, crear_usuario,
                                                  monkeypatch, origen, rol):
    """SEG-02 / SEC-AUTH-04 (FNC-077, antes xfail): ni con la bandera."""
    activar_login_local_de_todas(monkeypatch)
    usuario = crear_usuario(rol, contrasena=CONTRASENA_FICTICIA)
    usuario.auth_source = origen
    db.session.commit()

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None


@pytest.mark.xfail(strict=True, reason='SEG-11 / FNC-014: sin límite de '
                   'intentos en el login')
def test_limite_de_intentos_responde_429(client, crear_usuario):
    usuario = crear_usuario(contrasena=CONTRASENA_FICTICIA)

    for _ in range(INTENTOS_ANTES_DEL_LIMITE):
        iniciar_sesion_api(client, usuario.email, CONTRASENA_ERRONEA)
    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_ERRONEA)

    assert respuesta.status_code == 429
