"""Endpoints de asignación directa retirados (FNC-065): responden 410.

`PUT /platforms/<id>/users` y `PUT /users/<id>/platforms` ya no escriben en
`user_platforms` (tabla obsoleta). La protección por rol se conserva: un
rol sin permiso sigue recibiendo 401/403, no un 410.
"""
import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from tests import fabricas

A = '/api/v1'


@pytest.fixture
def escena(app):
    area = fabricas.crear_area('Finanzas')
    plataforma = fabricas.crear_plataforma(area, 'Contabilidad')
    cuenta = fabricas.crear_usuario(ROLE_USER, areas=[area])
    return {'area': area, 'plataforma': plataforma, 'cuenta': cuenta,
            'admin': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                            areas_administradas=[area]),
            'super': fabricas.crear_usuario(ROLE_ADMIN)}


def _rutas(esc):
    return [
        ('PUT', f"{A}/platforms/{esc['plataforma'].id}/users",
         {'user_ids': [esc['cuenta'].id]}),
        ('PUT', f"{A}/users/{esc['cuenta'].id}/platforms",
         {'platform_ids': [esc['plataforma'].id]}),
    ]


@pytest.mark.parametrize('quien', ['admin', 'super'])
def test_los_dos_endpoints_responden_410_y_no_escriben(escena, cliente_como,
                                                       quien):
    cliente = cliente_como(escena[quien])
    for metodo, ruta, cuerpo in _rutas(escena):
        respuesta = cliente.open(ruta, method=metodo, json=cuerpo)

        assert respuesta.status_code == 410, (ruta, respuesta.get_json())
        datos = respuesta.get_json()
        assert datos['status'] == 'error'
        assert datos['code'] == 'endpoint_retirado'
        assert datos['use'] == 'POST /access-requests'
    db.session.expire_all()
    assert escena['cuenta'].platforms == []


def test_un_usuario_sigue_recibiendo_403(escena, cliente_como):
    cliente = cliente_como(escena['cuenta'])
    for metodo, ruta, cuerpo in _rutas(escena):
        assert cliente.open(ruta, method=metodo, json=cuerpo).status_code == 403


def test_sin_sesion_sigue_siendo_401(escena, client):
    for metodo, ruta, cuerpo in _rutas(escena):
        assert client.open(ruta, method=metodo, json=cuerpo).status_code == 401


def test_la_plataforma_no_expone_user_ids(escena, cliente_como):
    respuesta = cliente_como(escena['super']).get(f'{A}/platforms')

    plataformas = respuesta.get_json()
    assert isinstance(plataformas, list) and plataformas and all('user_ids' not in p for p in plataformas)
