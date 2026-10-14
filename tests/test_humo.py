"""Pruebas humo: demuestran que la base de pruebas funciona.

La matriz completa de permisos por endpoint es FNC-020.
"""

import smtplib

import pytest

from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.auth.models import User
from tests.conftest import ServicioExternoBloqueado
from tests.fabricas import ROLES


def test_la_app_arranca_con_bd_temporal_vacia(app, tmp_path):
    assert app.config['TESTING'] is True
    assert str(tmp_path) in app.config['SQLALCHEMY_DATABASE_URI']
    # El usuario semilla de create_app no queda en la BD de pruebas.
    assert User.query.count() == 0


def test_contexto_de_acceso_responde_sin_sesion(client):
    respuesta = client.get('/api/v1/auth/context')
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['authenticated'] is False
    assert datos['sso_enabled'] is False


def test_endpoint_protegido_sin_sesion_devuelve_401(client):
    respuesta = client.get('/api/v1/users')
    assert respuesta.status_code == 401
    assert respuesta.get_json()['status'] == 'error'


def test_endpoint_protegido_con_admin_devuelve_200(cliente_admin):
    respuesta = cliente_admin.get('/api/v1/users')
    assert respuesta.status_code == 200
    assert isinstance(respuesta.get_json(), list)


def test_endpoint_de_admin_con_usuario_normal_devuelve_403(cliente_usuario):
    assert cliente_usuario.get('/api/v1/users').status_code == 403


@pytest.mark.parametrize('rol', ROLES)
def test_cliente_de_rol_queda_autenticado_con_su_rol(cliente_de_rol, rol):
    cliente, usuario = cliente_de_rol(rol)
    respuesta = cliente.get('/api/v1/me')
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['id'] == usuario.id
    assert datos['role'] == rol
    assert datos['permissions']['is_admin'] is (rol == ROLE_ADMIN)
    assert datos['permissions']['is_area_admin'] is (rol == ROLE_AREA_ADMIN)
    if rol == ROLE_AREA_ADMIN:
        assert len(datos['managed_areas']) == 1
    if rol == ROLE_USER:
        assert len(datos['areas']) == 1


def test_fabricas_crean_area_y_plataforma(crear_area, crear_plataforma):
    area = crear_area()
    plataforma = crear_plataforma(area)
    assert plataforma.id is not None
    assert plataforma.area_id == area.id


def test_servicios_externos_bloqueados(app):
    with pytest.raises(ServicioExternoBloqueado):
        smtplib.SMTP('correo.invalid', 25)
