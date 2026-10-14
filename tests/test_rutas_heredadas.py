"""Rutas heredadas: solo responden 410 o redirigen, sin lógica (FNC-023).

Recorre todas las rutas de los blueprints heredados (los mismos que excluye la
guardia de FNC-020) con y sin sesión, y con y sin `FRONTEND_URL`. Se retiran en
FNC-027; entonces estas pruebas se eliminan junto con ellas.
"""

import re

import pytest

from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from tests.matriz_proteccion import BLUEPRINTS_HEREDADOS

FRONTEND_FICTICIO = 'https://portal.pruebas.invalid'
METODOS_IMPLICITOS = {'HEAD', 'OPTIONS'}
REDIRECCIONES = {301, 302, 303, 307, 308}
# `GET /` sin FRONTEND_URL responde 200 con la indicación de que es solo API:
# redirigir a "/" crearía un bucle (ver app/modules/core/routes.py).
INFORMATIVAS = {('GET', '/')}
_CONVERTIDOR = re.compile(r'<(?:int:)?[^>]+>')


def _rutas_heredadas(app):
    """(método, regla, URL concreta) de cada ruta heredada."""
    for regla in app.url_map.iter_rules():
        if regla.endpoint.split('.')[0] not in BLUEPRINTS_HEREDADOS:
            continue
        url = _CONVERTIDOR.sub(
            lambda m: '1' if m.group(0).startswith('<int:') else 'prueba',
            regla.rule)
        for metodo in sorted(regla.methods - METODOS_IMPLICITOS):
            yield metodo, regla.rule, url


def _problemas(app, cliente, frontend):
    """Lista de rutas cuya respuesta no es 410 ni redirección válida."""
    problemas = []
    for metodo, regla, url in _rutas_heredadas(app):
        respuesta = cliente.open(url, method=metodo)
        codigo = respuesta.status_code
        if (metodo, regla) in INFORMATIVAS and codigo == 200:
            continue
        if codigo == 410:
            if respuesta.get_json().get('status') not in ('error', 'deprecated',
                                                           'moved'):
                problemas.append((metodo, regla, codigo, 'sin status'))
        elif codigo in REDIRECCIONES:
            destino = respuesta.headers['Location']
            if not (destino.startswith('/') or
                    (frontend and destino.startswith(frontend))):
                problemas.append((metodo, regla, codigo, destino))
        else:
            problemas.append((metodo, regla, codigo, ''))
    return problemas


@pytest.fixture(params=['sin_frontend', 'con_frontend'])
def frontend(request, monkeypatch):
    if request.param == 'con_frontend':
        monkeypatch.setenv('FRONTEND_URL', FRONTEND_FICTICIO)
        return FRONTEND_FICTICIO
    return None


def test_hay_rutas_heredadas_que_revisar(app):
    assert len(list(_rutas_heredadas(app))) >= 40


@pytest.mark.parametrize('con_sesion', [False, True], ids=['anonimo', 'admin'])
def test_rutas_heredadas_responden_410_o_redirigen(app, client, cliente_admin,
                                                   frontend, con_sesion):
    usuarios_antes = User.query.count()
    cliente = cliente_admin if con_sesion else client

    problemas = _problemas(app, cliente, frontend)

    assert not problemas, problemas
    assert User.query.count() == usuarios_antes
    assert AuditLog.query.count() == 0


def test_con_frontend_las_pantallas_redirigen_al_frontend(app, client,
                                                          monkeypatch):
    monkeypatch.setenv('FRONTEND_URL', FRONTEND_FICTICIO)
    for ruta, destino in [('/auth/login', '/login'), ('/settings/', '/settings'),
                          ('/admin/users', '/users'),
                          ('/admin/areas/', '/areas'), ('/audit/', '/audit')]:
        respuesta = client.get(ruta)
        assert respuesta.status_code in REDIRECCIONES, ruta
        assert respuesta.headers['Location'] == FRONTEND_FICTICIO + destino


def test_410_indica_el_endpoint_que_lo_reemplaza(client):
    respuesta = client.post('/admin/add-user')

    assert respuesta.status_code == 410
    assert respuesta.get_json()['use'] == 'POST /api/v1/users'
