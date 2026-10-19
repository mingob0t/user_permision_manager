"""Variables del ejecutor y de Redis (FNC-049)."""
import pytest

from app import create_app
from app.modules.provisioning.config import (
    ErrorConfiguracionAprovisionamiento, cargar_configuracion,
    configuracion_redis)


def test_valores_por_defecto():
    cfg = cargar_configuracion({})
    assert (cfg.cola, cfg.max_intentos, cfg.backoff_base, cfg.backoff_max,
            cfg.tiempo_intento, cfg.intervalo_barrido) == (
        'aprovisionamiento', 5, 60, 900, 60, 30)
    assert cfg.vencimiento_reserva == 90


@pytest.mark.parametrize('entorno', [
    {'PROVISIONING_MAX_ATTEMPTS': 'cinco'},
    {'PROVISIONING_MAX_ATTEMPTS': '0'},
    {'PROVISIONING_ATTEMPT_TIMEOUT_SECONDS': '9999'},
    {'PROVISIONING_BACKOFF_BASE_SECONDS': '100',
     'PROVISIONING_BACKOFF_MAX_SECONDS': '50'},
    {'PROVISIONING_QUEUE_NAME': 'Cola Con Espacios'},
])
def test_valores_invalidos_fallan(entorno):
    with pytest.raises(ErrorConfiguracionAprovisionamiento):
        cargar_configuracion(entorno)


def test_la_app_no_arranca_con_un_valor_invalido(monkeypatch, tmp_path):
    monkeypatch.setenv('PROVISIONING_POLL_INTERVAL_SECONDS', '-1')
    with pytest.raises(ErrorConfiguracionAprovisionamiento):
        create_app({'SQLALCHEMY_DATABASE_URI':
                    f"sqlite:///{tmp_path / 'x.db'}"})


def test_redis_exige_contrasena():
    with pytest.raises(ErrorConfiguracionAprovisionamiento, match='REDIS_PASS'):
        configuracion_redis({'REDIS_HOST': 'redis.ejemplo.local'})


def test_redis_rechaza_ip_literal():
    # Dirección de documentación (RFC 3849): los lineamientos prohíben IPv4
    # literales también en pruebas.
    with pytest.raises(ErrorConfiguracionAprovisionamiento, match='REDIS_HOST'):
        configuracion_redis({'REDIS_HOST': '2001:db8::1', 'REDIS_PASS': 'x' * 8})


def test_la_contrasena_de_redis_no_sale_en_repr():
    cfg = configuracion_redis({'REDIS_PASS': 'Ficticia-Redis-1'})
    assert 'Ficticia-Redis-1' not in repr(cfg)
    assert (cfg.host, cfg.puerto) == ('localhost', 6379)
