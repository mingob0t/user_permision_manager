"""Credenciales de conectores desde Vaultwarden fuera de dev (FNC-068)."""
import logging

import pytest

from app.modules.connectors import credenciales
from app.modules.connectors.credenciales import (Credencial,
                                                CredencialNoEncontrada,
                                                GestorNoConfigurado,
                                                GestorNoDisponible,
                                                ProveedorSecretosVaultwarden,
                                                ResolvedorCredenciales)
from app.modules.secretos import vaultwarden
from tests.connectors.conftest import REFERENCIA, SECRETO_FICTICIO
from tests.secretos import vaultwarden_falso as vf


@pytest.fixture
def servidor(monkeypatch):
    """Vaultwarden simulado como transporte del cliente compartido."""
    falso = vf.VaultwardenFalso()
    monkeypatch.setenv('APP_ENV', 'production')
    for clave, valor in vf.ENTORNO.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(vaultwarden, 'TransporteHttps', lambda cfg: falso)
    vaultwarden.reiniciar_cliente()
    yield falso
    vaultwarden.reiniciar_cliente()


class ClienteFijo:
    def __init__(self, efecto):
        self.efecto = efecto

    def leer(self, referencia):
        if isinstance(self.efecto, BaseException):
            raise self.efecto
        return self.efecto


def test_fuera_de_dev_resuelve_desde_vaultwarden(servidor):
    servidor.item(REFERENCIA, SECRETO_FICTICIO, usuario='svc-portal')
    credencial = credenciales.resolver_credencial(REFERENCIA)
    assert (credencial.secreto, credencial.usuario) == (SECRETO_FICTICIO,
                                                        'svc-portal')


def test_b4_limpiar_cache_al_rotar_usa_el_valor_nuevo(servidor):
    """Requisito heredado de FNC-050 (B4): tras rotar, `limpiar_cache()`."""
    servidor.item(REFERENCIA, SECRETO_FICTICIO)
    assert credenciales.resolver_credencial(REFERENCIA).secreto == \
        SECRETO_FICTICIO
    servidor.cambiar_contrasena(0, 'Valor-Rotado-Ficticio')
    assert credenciales.resolver_credencial(REFERENCIA).secreto == \
        SECRETO_FICTICIO  # caché vigente
    credenciales.limpiar_cache()
    assert credenciales.resolver_credencial(REFERENCIA).secreto == \
        'Valor-Rotado-Ficticio'


@pytest.mark.parametrize('efecto, esperado', [
    (vaultwarden.SecretoNoEncontrado('x'), CredencialNoEncontrada),
    (vaultwarden.SecretoAmbiguo('x'), CredencialNoEncontrada),
    (vaultwarden.GestorCaido('x'), GestorNoDisponible),
    (vaultwarden.GestorMalConfigurado('x'), GestorNoConfigurado),
])
def test_mapeo_de_errores_sin_referencia_ni_valor(efecto, esperado):
    proveedor = ProveedorSecretosVaultwarden(cliente=ClienteFijo(efecto))
    with pytest.raises(esperado) as error:
        proveedor.obtener(REFERENCIA)
    assert REFERENCIA not in str(error.value)


def test_item_leido_se_convierte_en_credencial():
    proveedor = ProveedorSecretosVaultwarden(cliente=ClienteFijo(
        vaultwarden.ItemSecreto(secreto=SECRETO_FICTICIO, usuario=None)))
    assert proveedor.obtener(REFERENCIA) == Credencial(secreto=SECRETO_FICTICIO)


def test_sin_variables_falla_cerrado_no_configurado(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    vaultwarden.reiniciar_cliente()
    with pytest.raises(GestorNoConfigurado):
        credenciales.resolver_credencial(REFERENCIA)


def test_vaultwarden_caido_es_no_disponible_y_no_se_guarda(servidor):
    servidor.item(REFERENCIA, SECRETO_FICTICIO)
    servidor.estado_forzado[vaultwarden.RUTA_TOKEN] = 503
    with pytest.raises(GestorNoDisponible):
        credenciales.resolver_credencial(REFERENCIA)
    del servidor.estado_forzado[vaultwarden.RUTA_TOKEN]
    assert credenciales.resolver_credencial(REFERENCIA).secreto == \
        SECRETO_FICTICIO


def test_sin_valores_en_logs(servidor, caplog):
    servidor.item(REFERENCIA, SECRETO_FICTICIO)
    caplog.set_level(logging.DEBUG)
    credenciales.resolver_credencial(REFERENCIA)
    for valor in (SECRETO_FICTICIO, vf.CLIENT_SECRET, vf.CONTRASENA_MAESTRA,
                  vf.TOKEN):
        assert valor not in caplog.text


def test_cache_acotada():
    """La caché no crece sin límite con referencias distintas."""
    resolvedor = ResolvedorCredenciales(segundos_cache=60)

    class Fuente(credenciales.ProveedorDeSecretos):
        fuente = 'fija'

        def obtener(self, referencia):
            return Credencial(secreto='a1b2c3d4')

    for numero in range(credenciales.MAXIMO_EN_CACHE + 25):
        resolvedor.resolver(Fuente(), f'pokemon/ref-{numero}')
    assert len(resolvedor._cache) == credenciales.MAXIMO_EN_CACHE
