"""Login con cuenta local: `POST /api/v1/auth/login` con `method: local` (FNC-022)."""

import pytest

from app import db
from app.authz import ROLE_AREA_ADMIN, ROLE_USER
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import (MENSAJE_CREDENCIALES, hay_auditoria,
                                   iniciar_sesion_api, usuario_en_sesion)

CONTRASENA_ERRONEA = 'clave-erronea-de-prueba'

# Umbral provisional (SEC-AUTH-10 lo deja "Por confirmar"): FNC-014 lo ajusta.
INTENTOS_ANTES_DEL_LIMITE = 20


def test_login_local_correcto_abre_sesion(client, crear_usuario):
    usuario = crear_usuario(ROLE_AREA_ADMIN, contrasena=CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {'status': 'success',
                                    'role': ROLE_AREA_ADMIN}
    assert usuario_en_sesion(client) == usuario.email
    assert hay_auditoria(f'ACCESO LOCAL: {usuario.email}', 'success')


def test_contrasena_erronea_da_401_sin_sesion(client, crear_usuario):
    usuario = crear_usuario(contrasena=CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_ERRONEA)

    assert respuesta.status_code == 401
    assert respuesta.get_json() == {'status': 'error',
                                    'message': MENSAJE_CREDENCIALES}
    assert usuario_en_sesion(client) is None
    assert hay_auditoria(f'ACCESO FALLIDO: {usuario.email}', 'error')


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


def test_usuario_inactivo_no_obtiene_sesion(client, crear_usuario):
    usuario = crear_usuario(contrasena=CONTRASENA_FICTICIA, activo=False)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_FICTICIA)

    assert respuesta.status_code == 403
    assert respuesta.get_json()['status'] == 'error'
    assert usuario_en_sesion(client) is None


def test_usuario_inactivo_con_contrasena_erronea_da_el_mensaje_uniforme(
        client, crear_usuario):
    usuario = crear_usuario(contrasena=CONTRASENA_FICTICIA, activo=False)

    respuesta = iniciar_sesion_api(client, usuario.email, CONTRASENA_ERRONEA)

    assert respuesta.status_code == 401
    assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES


@pytest.mark.xfail(strict=True, reason='SEG-02 / FNC-003: el login local no '
                   'comprueba auth_source y acepta cuentas ldap o sso con clave')
@pytest.mark.parametrize('origen', ['ldap', 'sso'])
def test_cuenta_no_local_no_entra_por_login_local(client, crear_usuario, origen):
    usuario = crear_usuario(ROLE_USER, contrasena=CONTRASENA_FICTICIA)
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
