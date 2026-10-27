"""Rutas heredadas retiradas: ya no existen y responden 404 (FNC-027).

Sustituye a `test_rutas_heredadas.py` (FNC-023), que comprobaba su 410 o su
redirección. Los blueprints heredados de NEXUS y `app/decorators.py` se
retiraron; la API vive solo en `/api/v1`.
"""

import importlib
import re

import pytest

PREFIJO_API = '/api/v1'
METODOS_IMPLICITOS = {'HEAD', 'OPTIONS'}
_CONVERTIDOR = re.compile(r'<(?:int:)?[^>]+>')

# (método, regla) de las 44 rutas que tenían los siete blueprints heredados.
RUTAS_RETIRADAS = (
    ('GET', '/'),
    ('POST', '/admin/add-user'),
    ('GET', '/admin/areas-api'),
    ('GET', '/admin/areas/'),
    ('POST', '/admin/areas/add'),
    ('POST', '/admin/areas/delete-bulk'),
    ('DELETE', '/admin/areas/delete/<int:area_id>'),
    ('POST', '/admin/areas/edit/<int:area_id>'),
    ('GET', '/admin/areas/users/<int:area_id>'),
    ('POST', '/admin/areas/users/update/<int:area_id>'),
    ('POST', '/admin/delete-user/<int:user_id>'),
    ('POST', '/admin/edit-user/<int:user_id>'),
    ('GET', '/admin/ldap-search-api'),
    ('POST', '/admin/update-user-access/<int:user_id>'),
    ('POST', '/admin/update-user-areas/<int:user_id>'),
    ('GET', '/admin/user-access/<int:user_id>'),
    ('GET', '/admin/users'),
    ('GET', '/api/stats'),
    ('GET', '/audit/'),
    ('GET', '/audit/api/list'),
    ('GET', '/auth/'),
    ('GET', '/auth/login'),
    ('POST', '/auth/login'),
    ('GET', '/auth/logout'),
    ('POST', '/auth/preferences/save'),
    ('POST', '/auth/save'),
    ('POST', '/auth/test_ldap'),
    ('POST', '/auth/users/create'),
    ('POST', '/auth/users/delete'),
    ('GET', '/auth/users/list'),
    ('POST', '/auth/users/purge'),
    ('POST', '/auth/users/update'),
    ('GET', '/notifications/'),
    ('GET', '/notifications/api/active'),
    ('DELETE', '/notifications/api/delete-all'),
    ('POST', '/notifications/api/mark-read'),
    ('POST', '/notifications/save'),
    ('GET', '/notifications/templates/get/<slug>'),
    ('POST', '/notifications/templates/save'),
    ('POST', '/notifications/test'),
    ('GET', '/portal'),
    ('GET', '/settings/'),
    ('GET', '/settings/export'),
    ('POST', '/settings/import'),
    ('POST', '/settings/save'),
)


def _url(regla):
    return _CONVERTIDOR.sub(
        lambda m: '1' if m.group(0).startswith('<int:') else 'prueba', regla)


def test_la_lista_cubre_las_44_reglas_retiradas():
    # 44 reglas; `/auth/login` admite GET y POST: 45 pares.
    assert len({regla for _, regla in RUTAS_RETIRADAS}) == 44
    assert len(RUTAS_RETIRADAS) == 45


@pytest.mark.parametrize('metodo,regla', RUTAS_RETIRADAS)
@pytest.mark.parametrize('con_sesion', [False, True], ids=['anonimo', 'admin'])
def test_ruta_retirada_responde_404(client, cliente_admin, metodo, regla,
                                    con_sesion):
    cliente = cliente_admin if con_sesion else client

    respuesta = cliente.open(_url(regla), method=metodo)

    assert respuesta.status_code == 404, (metodo, regla)


def test_fuera_de_api_v1_no_queda_ninguna_ruta(app):
    otras = sorted(
        (metodo, regla.rule)
        for regla in app.url_map.iter_rules()
        for metodo in regla.methods - METODOS_IMPLICITOS
        if not regla.rule.startswith(PREFIJO_API))
    assert not otras, otras


def test_el_modulo_decorators_ya_no_existe():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('app.decorators')


def test_acceso_denegado_de_un_decorador_responde_403_json(app):
    """`_deny` ya no redirige a una ruta heredada: siempre JSON 403, también fuera de /api/."""
    from app.authz import admin_required

    @admin_required
    def vista():
        return 'ok'

    with app.test_request_context('/ejemplo',
                                  headers={'Accept': 'text/html'}):
        respuesta, codigo = vista()
    assert codigo == 403
    assert respuesta.get_json()['status'] == 'error'
