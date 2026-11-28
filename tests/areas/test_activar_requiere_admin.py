"""Un área no se activa ni se crea activa sin administrador (FNC-220)."""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN
from app.modules.core.models import Area
from tests import fabricas

A = '/api/v1'
CODIGO = 'area_sin_admin'
MENSAJE = 'Asigna al menos un administrador antes de activar el área.'


@pytest.fixture
def escena(app):
    return {
        'sin_admin': fabricas.crear_area('Inactiva sin admin',
                                         status='Inactivo').id,
        'con_admin_area': fabricas.crear_area('Inactiva con admin',
                                              status='Inactivo'),
        'super': fabricas.crear_usuario(ROLE_ADMIN),
    }


def _bloqueada(respuesta):
    assert respuesta.status_code == 409, respuesta.get_data(as_text=True)
    cuerpo = respuesta.get_json()
    assert cuerpo['code'] == CODIGO and cuerpo['message'] == MENSAJE


def test_activar_area_sin_admin_da_409_y_no_cambia(escena, cliente_como):
    r = cliente_como(escena['super']).put(
        f"{A}/areas/{escena['sin_admin']}", json={'status': 'Activo'})

    _bloqueada(r)
    assert db.session.get(Area, escena['sin_admin']).status == 'Inactivo'


def test_activar_area_con_admin_pasa(escena, cliente_como):
    area = escena['con_admin_area']
    fabricas.crear_usuario(ROLE_AREA_ADMIN, areas_administradas=[area])

    r = cliente_como(escena['super']).put(
        f'{A}/areas/{area.id}', json={'status': 'Activo'})

    assert r.status_code == 200 and r.get_json()['area']['status'] == 'Activo'


def test_editar_otros_campos_de_area_inactiva_sin_admin_pasa(
        escena, cliente_como):
    r = cliente_como(escena['super']).put(
        f"{A}/areas/{escena['sin_admin']}", json={'description': 'Nueva'})

    assert r.status_code == 200


def test_editar_area_activa_sin_admin_no_se_bloquea(app, cliente_como):
    """Datos previos a la regla: solo se bloquea la activación."""
    activa = fabricas.crear_area('Activa heredada')
    r = cliente_como(fabricas.crear_usuario(ROLE_ADMIN)).put(
        f'{A}/areas/{activa.id}', json={'description': 'Cambio'})

    assert r.status_code == 200


def test_crear_area_activa_sin_admin_da_409(escena, cliente_como):
    cliente = cliente_como(escena['super'])
    for cuerpo in ({'name': 'Nueva'},
                   {'name': 'Nueva', 'status': 'Activo'}):
        _bloqueada(cliente.post(f'{A}/areas', json=cuerpo))
    assert Area.query.filter_by(name='Nueva').first() is None


def test_crear_area_inactiva_sin_admin_pasa(escena, cliente_como):
    r = cliente_como(escena['super']).post(
        f'{A}/areas', json={'name': 'Nueva', 'status': 'Inactivo'})

    assert r.status_code == 201


def test_admin_de_area_crea_activa_y_queda_como_admin(app, cliente_como):
    admin = fabricas.crear_usuario(ROLE_AREA_ADMIN)

    r = cliente_como(admin).post(f'{A}/areas', json={'name': 'Propia'})

    assert r.status_code == 201
    assert r.get_json()['area']['status'] == 'Activo'
