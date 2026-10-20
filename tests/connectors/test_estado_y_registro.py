"""`tiene_conector` y registro de tipos (FNC-050)."""
from app import create_app, db
from app.modules.connectors import registry
from app.modules.connectors.registry import TipoConector
from app.modules.connectors.tipos import TIPO_NOOP
from app.modules.platforms.estado import tiene_conector
from app.modules.platforms.tipos import TIPO_LDAP


def test_tiene_conector_con_configuracion_activa(conector_noop):
    plataforma, configuracion, _ = conector_noop
    assert tiene_conector(plataforma) is True
    assert plataforma.to_dict()['has_connector'] is True

    configuracion.active = False
    db.session.commit()
    assert tiene_conector(plataforma) is False


def test_sin_tipo_registrado_no_cuenta_como_conector(conector_noop):
    plataforma, _, _ = conector_noop
    registry.quitar_tipo(TIPO_NOOP)
    assert tiene_conector(plataforma) is False


def test_plataforma_ldap_o_sin_configuracion(conector_noop):
    plataforma, configuracion, _ = conector_noop
    plataforma.integration_type = TIPO_LDAP
    db.session.commit()
    assert tiene_conector(plataforma) is False
    assert tiene_conector(None) is False


def test_registro_de_tipos(app):
    tipo = TipoConector('prueba', fabrica=object, validar_params=lambda p: {})
    registry.registrar_tipo(tipo)
    try:
        assert registry.obtener_tipo('prueba') is tipo
        assert 'prueba' in registry.tipos_disponibles()
    finally:
        registry.quitar_tipo('prueba')
    assert registry.obtener_tipo('prueba') is None


def test_noop_solo_se_registra_en_dev_o_pruebas(monkeypatch, tmp_path):
    uri = f"sqlite:///{tmp_path / 'x.db'}"
    monkeypatch.delenv('APP_ENV', raising=False)
    create_app({'SQLALCHEMY_DATABASE_URI': uri})
    assert registry.obtener_tipo(TIPO_NOOP) is None

    monkeypatch.setenv('APP_ENV', 'development')
    create_app({'SQLALCHEMY_DATABASE_URI': uri})
    assert registry.obtener_tipo(TIPO_NOOP) is not None

    monkeypatch.setenv('APP_ENV', 'production')
    create_app({'SQLALCHEMY_DATABASE_URI': uri, 'TESTING': True})
    assert registry.obtener_tipo(TIPO_NOOP) is not None
