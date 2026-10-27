"""Valores por defecto del portal en la API (FNC-121).

Sin registro de configuración, `GET /settings` entrega los valores por
defecto con nombre del módulo `settings`, nunca `null` en esos campos.
"""

from app import db
from app.modules.settings import valores_por_defecto as vpd
from app.modules.settings.models import SystemConfig

CAMPOS = ('portal_name', 'portal_identity_type', 'bg_color', 'text_color')
ESPERADOS = {
    'portal_name': 'Nexus Core AI',
    'portal_identity_type': 'icon',
    'bg_color': '#0f172a',
    'text_color': '#ffffff',
}


def test_sin_registro_entrega_los_valores_por_defecto(app, cliente_usuario):
    cliente = cliente_usuario
    with app.app_context():
        assert SystemConfig.query.first() is None
    cuerpo = cliente.get('/api/v1/settings').get_json()
    for campo in CAMPOS:
        assert cuerpo[campo] is not None, campo
    assert {c: cuerpo[c] for c in CAMPOS} == ESPERADOS


def test_las_constantes_son_las_que_usa_el_modelo(app):
    assert vpd.PORTAL_NAME_POR_DEFECTO == ESPERADOS['portal_name']
    assert vpd.PORTAL_IDENTITY_TYPE_POR_DEFECTO == ESPERADOS['portal_identity_type']
    assert vpd.BG_COLOR_POR_DEFECTO == ESPERADOS['bg_color']
    assert vpd.TEXT_COLOR_POR_DEFECTO == ESPERADOS['text_color']
    with app.app_context():
        db.session.add(SystemConfig())
        db.session.commit()
        guardado = SystemConfig.query.first().to_dict()
    assert {c: guardado[c] for c in CAMPOS} == ESPERADOS


def test_con_registro_entrega_lo_guardado(app, cliente_usuario):
    cliente = cliente_usuario
    with app.app_context():
        db.session.add(SystemConfig(portal_name='Mi portal'))
        db.session.commit()
    cuerpo = cliente.get('/api/v1/settings').get_json()
    assert cuerpo['portal_name'] == 'Mi portal'
    assert cuerpo['bg_color'] == ESPERADOS['bg_color']
