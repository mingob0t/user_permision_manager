"""Variables `CONNECTOR_*` validadas al arrancar (FNC-050)."""
import pytest

from app import create_app
from app.modules.connectors.configuracion import (
    ErrorConfiguracionConectores, cargar_configuracion, host_permitido)


def test_valores_por_defecto_son_los_mas_seguros():
    cfg = cargar_configuracion({})
    assert cfg.hosts_permitidos == frozenset()
    assert (cfg.tiempo_espera, cfg.segundos_cache) == (10, 60)
    assert host_permitido('erp.ejemplo.local', cfg) is False


def test_lista_blanca_normaliza_y_compara_sin_mayusculas():
    cfg = cargar_configuracion(
        {'CONNECTOR_ALLOWED_HOSTS': ' ERP.ejemplo.local , wiki.ejemplo.local'})
    assert cfg.hosts_permitidos == frozenset(
        {'erp.ejemplo.local', 'wiki.ejemplo.local'})
    assert host_permitido('Erp.Ejemplo.Local', cfg) is True
    assert host_permitido('otro.ejemplo.local', cfg) is False


# IP: IPv6 de documentación (RFC 3849) y formas abreviadas de IPv4; los
# lineamientos prohíben IPv4 de 4 octetos también en pruebas.
@pytest.mark.parametrize('entorno', [
    {'CONNECTOR_ALLOWED_HOSTS': '2001:db8::1'},
    {'CONNECTOR_ALLOWED_HOSTS': '10.1.2'},
    {'CONNECTOR_ALLOWED_HOSTS': 'erp.ejemplo.local,::1'},
    {'CONNECTOR_ALLOWED_HOSTS': 'https://erp.ejemplo.local'},
    {'CONNECTOR_ALLOWED_HOSTS': 'erp ejemplo'},
    {'CONNECTOR_TIMEOUT_SECONDS': 'diez'},
    {'CONNECTOR_TIMEOUT_SECONDS': '0'},
    {'CONNECTOR_TIMEOUT_SECONDS': '60'},  # no menor que el intento (60)
    {'CONNECTOR_CREDENTIAL_CACHE_SECONDS': '-1'},
    {'CONNECTOR_CREDENTIAL_CACHE_SECONDS': '9999'},
])
def test_valores_invalidos_fallan(entorno):
    with pytest.raises(ErrorConfiguracionConectores):
        cargar_configuracion(entorno)


def test_tiempo_de_espera_menor_que_el_del_intento():
    cfg = cargar_configuracion({'CONNECTOR_TIMEOUT_SECONDS': '100',
                                'PROVISIONING_ATTEMPT_TIMEOUT_SECONDS': '120'})
    assert cfg.tiempo_espera == 100


def test_la_app_no_arranca_con_una_ip_en_la_lista_blanca(monkeypatch,
                                                          tmp_path):
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS', '2001:db8::1')
    with pytest.raises(ErrorConfiguracionConectores):
        create_app({'SQLALCHEMY_DATABASE_URI':
                    f"sqlite:///{tmp_path / 'x.db'}"})
