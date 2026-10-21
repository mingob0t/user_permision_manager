"""Validación de `VAULTWARDEN_*` (FNC-068)."""
import pytest

from app.modules.secretos.configuracion import (ErrorConfiguracionSecretos,
                                                cargar_configuracion,
                                                validar_al_arrancar)
from tests.secretos import vaultwarden_falso as vf

# IPv4 en forma decimal (equivale a una dirección de loopback): el host debe
# ser un nombre, nunca una IP en ninguna forma.
HOST_NUMERICO = '2130706433'


def test_configuracion_valida():
    cfg = cargar_configuracion({**vf.ENTORNO,
                                'VAULTWARDEN_URL': vf.URL + '/vault/'})
    assert cfg.url == vf.URL + '/vault'
    assert cfg.tiempo_espera == 5
    assert cfg.coleccion_id == vf.COLECCION
    for valor in (vf.CLIENT_SECRET, vf.CONTRASENA_MAESTRA, vf.CORREO):
        assert valor not in repr(cfg)


@pytest.mark.parametrize('variable, valor', [
    ('VAULTWARDEN_URL', 'http://vault.pruebas.invalid'),
    ('VAULTWARDEN_URL', f'https://{HOST_NUMERICO}'),
    ('VAULTWARDEN_URL', 'https://u:p@vault.pruebas.invalid'),
    ('VAULTWARDEN_URL', 'https://vault.pruebas.invalid/?x=1'),
    ('VAULTWARDEN_URL', 'https://vault.pruebas.invalid:99999'),
    ('VAULTWARDEN_CLIENT_ID',
     'organization.11111111-2222-4333-8444-555555555555'),
    ('VAULTWARDEN_CLIENT_SECRET', ''),
    ('VAULTWARDEN_MASTER_PASSWORD', '  '),
    ('VAULTWARDEN_EMAIL', 'sin-arroba'),
    ('VAULTWARDEN_COLLECTION_ID', 'portal'),
    ('VAULTWARDEN_TIMEOUT_SECONDS', '0'),
    ('VAULTWARDEN_TIMEOUT_SECONDS', '31'),
    ('VAULTWARDEN_CA_CERT_FILE', '/no/existe.pem'),
])
def test_valores_inseguros_o_incompletos_se_rechazan(variable, valor):
    with pytest.raises(ErrorConfiguracionSecretos) as error:
        cargar_configuracion({**vf.ENTORNO, variable: valor})
    assert variable in str(error.value)
    if len(valor.strip()) > 2:  # "0" aparece en el rango del mensaje
        assert valor not in str(error.value)


def test_al_arrancar_dev_o_sin_variables_no_valida():
    assert validar_al_arrancar({'APP_ENV': 'development',
                                'VAULTWARDEN_URL': 'http://x'}) is None
    assert validar_al_arrancar({'APP_ENV': 'production'}) is None


def test_al_arrancar_fuera_de_dev_con_variables_incompletas_falla():
    with pytest.raises(ErrorConfiguracionSecretos):
        validar_al_arrancar({'APP_ENV': 'production',
                             'VAULTWARDEN_URL': vf.URL})
    assert validar_al_arrancar({'APP_ENV': 'staging', **vf.ENTORNO}) is not None
