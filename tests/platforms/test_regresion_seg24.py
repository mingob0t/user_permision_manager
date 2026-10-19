"""Regresión SEG-24 (FNC-017 parcial, cerrado por FNC-046; SEC-SES-10).

`direct_link` y `logo_url` aceptaban cualquier esquema: `javascript:` quedaba
guardado y el catálogo lo usaba como enlace. Solo se acepta `https://`.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN
from app.modules.core.models import Platform
from tests import fabricas

A = '/api/v1'

URLS_INVALIDAS = (
    'javascript:alert(1)',
    ' JavaScript:alert(1)',
    'data:text/html,<b>x</b>',
    'http://portal.pruebas.local',
    'https:sin-host',
    'https://pruebas.local/con espacio',
)


def _alta(area_id, **campos):
    return {'name': 'Plataforma URL', 'description': 'Prueba de URL',
            'area_id': area_id, 'integration_type': 'conector', **campos}


@pytest.mark.parametrize('campo', ['direct_link', 'logo_url'])
@pytest.mark.parametrize('url', URLS_INVALIDAS)
def test_alta_con_url_no_https_responde_422(app, cliente_como, campo, url):
    area = fabricas.crear_area()
    cliente = cliente_como(fabricas.crear_usuario(ROLE_ADMIN))

    respuesta = cliente.post(f'{A}/platforms', json=_alta(area.id, **{campo: url}))

    assert respuesta.status_code == 422, respuesta.get_json()
    assert respuesta.get_json()['code'] == 'validacion'
    assert campo in respuesta.get_json()['fields']
    assert Platform.query.count() == 0


@pytest.mark.parametrize('campo', ['direct_link', 'logo_url'])
def test_edicion_con_javascript_responde_422(app, cliente_como, campo):
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(area, direct_link='https://ok.pruebas.local')
    cliente = cliente_como(fabricas.crear_usuario(ROLE_ADMIN))

    respuesta = cliente.put(f'{A}/platforms/{plataforma.id}',
                            json={campo: 'javascript:alert(1)'})

    assert respuesta.status_code == 422, respuesta.get_json()
    db.session.expire_all()
    assert getattr(db.session.get(Platform, plataforma.id), campo) != \
        'javascript:alert(1)'
