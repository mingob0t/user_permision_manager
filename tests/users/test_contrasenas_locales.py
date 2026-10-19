"""Contraseñas locales en `POST /users` y `PUT /users/<id>` (FNC-077, SEG-02).

- El portal no fija contraseñas locales: `password` -> `400 campo_no_permitido`.
- Excepción: la cuenta de emergencia (superadmin local).
- En desarrollo, con `LOGIN_LOCAL_TODAS_LAS_CUENTAS=true` y
  `APP_ENV=development`, se aceptan para cuentas locales del alcance.
- Sin contraseña, la cuenta nace sin clave (ya no `nexus123`).
- Fuera de desarrollo, `POST /users` crea una cuenta de directorio (`ldap`)
  que se vincula al entrar por directorio con ese correo; con la bandera, local.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.auth.models import User
from tests import fabricas
from tests.directorio_falso import DOMINIO_CORREO, instalar_directorio
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import (activar_login_local_de_todas,
                                   iniciar_sesion_api)

A = '/api/v1'
CONTRASENA_NUEVA = 'otra-clave-ficticia-de-prueba'
# Valor que `POST /users` fijaba a toda cuenta sin contraseña (SEG-02).
CONTRASENA_FIJA_ANTERIOR = 'nexus123'
CORREO_NUEVO = 'nuevo@pruebas.local'


def _cuenta(user_id):
    db.session.expire_all()
    return db.session.get(User, user_id)


def _campo_no_permitido(respuesta):
    assert respuesta.status_code == 400, respuesta.get_data(as_text=True)
    assert respuesta.get_json()['code'] == 'campo_no_permitido'


@pytest.fixture
def escena(app):
    area = fabricas.crear_area('Área A')
    return {
        'A': area.id,
        'super': fabricas.crear_usuario(
            ROLE_ADMIN, contrasena=CONTRASENA_FICTICIA).id,
        'admin_a': fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area],
                                          areas_administradas=[area]).id,
        'usuario_a': fabricas.crear_usuario(
            ROLE_USER, areas=[area], contrasena=CONTRASENA_FICTICIA).id,
    }


@pytest.fixture
def como(cliente_como):
    return lambda user_id: cliente_como(_cuenta(user_id))


def _alta(cliente, escena, **extra):
    return cliente.post(f'{A}/users', json={
        'email': CORREO_NUEVO, 'area_ids': [escena['A']], **extra})


# --------------------------------------------------------------------------- #
# POST /users
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('cuerpo', [{}, {'password': ''}])
def test_alta_sin_contrasena_nace_de_directorio_sin_clave(escena, como,
                                                          cuerpo):
    """Regresión SEG-02 (se fijaba `nexus123`) y FNC-077 (nacía `local`)."""
    respuesta = _alta(como(escena['super']), escena, **cuerpo)

    assert respuesta.status_code == 201, respuesta.get_data(as_text=True)
    cuenta = _cuenta(respuesta.get_json()['id'])
    assert cuenta.auth_source == 'ldap'
    assert cuenta.password_hash is None


def test_alta_fuera_de_desarrollo_se_vincula_al_entrar_por_directorio(
        app, escena, como, monkeypatch):
    """Regresión FNC-077: la cuenta nacía `local` y el directorio la
    bloqueaba (`cuenta_local_en_conflicto`)."""
    uid = 'nueva.persona'
    correo = f'{uid}@{DOMINIO_CORREO}'
    alta = como(escena['admin_a']).post(f'{A}/users', json={
        'email': correo, 'area_ids': [escena['A']]})
    assert alta.status_code == 201, alta.get_data(as_text=True)
    directorio = instalar_directorio(monkeypatch)
    directorio.agregar(uid, CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(app.test_client(), uid, CONTRASENA_FICTICIA,
                                   metodo='directory')

    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    assert respuesta.get_json()['role'] == ROLE_USER
    assert User.query.filter(db.func.lower(User.email) == correo).count() == 1
    cuenta = _cuenta(alta.get_json()['id'])
    assert cuenta.auth_source == 'ldap'
    assert cuenta.password_hash is None
    assert cuenta.last_login_at is not None
    assert [a.id for a in cuenta.areas] == [escena['A']]


def test_la_contrasena_fija_anterior_no_abre_sesion(app, escena, como,
                                                    monkeypatch):
    """SEG-02: ni con la bandera de desarrollo entra con `nexus123`."""
    _alta(como(escena['super']), escena)
    activar_login_local_de_todas(monkeypatch)

    respuesta = iniciar_sesion_api(app.test_client(), CORREO_NUEVO,
                                   CONTRASENA_FIJA_ANTERIOR)

    assert respuesta.status_code == 401


@pytest.mark.parametrize('actor', ('super', 'admin_a'))
def test_alta_con_contrasena_da_400(escena, como, actor):
    respuesta = _alta(como(escena[actor]), escena,
                      password=CONTRASENA_FICTICIA)

    _campo_no_permitido(respuesta)
    assert User.query.filter_by(email=CORREO_NUEVO).first() is None


@pytest.mark.parametrize('entorno', [None, 'production'])
def test_alta_con_contrasena_y_bandera_fuera_de_desarrollo_da_400(
        escena, como, monkeypatch, entorno):
    activar_login_local_de_todas(monkeypatch, entorno=entorno)

    _campo_no_permitido(_alta(como(escena['super']), escena,
                              password=CONTRASENA_FICTICIA))


def test_alta_con_contrasena_y_bandera_en_desarrollo(app, escena, como,
                                                     monkeypatch):
    activar_login_local_de_todas(monkeypatch)

    respuesta = _alta(como(escena['admin_a']), escena,
                      password=CONTRASENA_FICTICIA)

    assert respuesta.status_code == 201, respuesta.get_data(as_text=True)
    cuenta = _cuenta(respuesta.get_json()['id'])
    assert cuenta.auth_source == 'local'
    assert cuenta.check_password(CONTRASENA_FICTICIA)
    assert iniciar_sesion_api(app.test_client(), CORREO_NUEVO,
                              CONTRASENA_FICTICIA).status_code == 200


# --------------------------------------------------------------------------- #
# PUT /users/<id>
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor', ('super', 'admin_a'))
def test_no_se_cambia_la_contrasena_de_una_cuenta_local_comun(escena, como,
                                                              actor):
    """Regresión FNC-077: superadmin y admin de área la cambiaban."""
    respuesta = como(escena[actor]).put(
        f"{A}/users/{escena['usuario_a']}", json={'password': CONTRASENA_NUEVA})

    _campo_no_permitido(respuesta)
    assert _cuenta(escena['usuario_a']).check_password(CONTRASENA_FICTICIA)


def test_superadmin_cambia_la_contrasena_de_la_cuenta_de_emergencia(
        app, escena, como):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['super']}", json={'password': CONTRASENA_NUEVA})

    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    cuenta = _cuenta(escena['super'])
    assert cuenta.check_password(CONTRASENA_NUEVA)
    assert iniciar_sesion_api(app.test_client(), cuenta.email,
                              CONTRASENA_NUEVA).status_code == 200


def test_cuenta_de_emergencia_no_local_no_recibe_contrasena(escena, como):
    cuenta = _cuenta(escena['super'])
    cuenta.auth_source = 'sso'
    db.session.commit()

    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['super']}", json={'password': CONTRASENA_NUEVA})

    _campo_no_permitido(respuesta)
    assert _cuenta(escena['super']).check_password(CONTRASENA_FICTICIA)
