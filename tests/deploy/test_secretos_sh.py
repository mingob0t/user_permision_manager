"""`deploy/secretos.sh` con `.env` SINTÉTICOS (FNC-068): nunca lee el real."""
import subprocess
from pathlib import Path

import pytest

from tests.secretos import vaultwarden_falso as vf

SCRIPT = Path(__file__).resolve().parents[2] / 'deploy' / 'secretos.sh'
# Valor ficticio que no debe salir nunca en la salida.
MARCA = 'Valor-Ficticio-Que-No-Se-Imprime'
COMPLETO = {**vf.ENTORNO, 'VAULTWARDEN_CLIENT_SECRET': MARCA,
            'VAULTWARDEN_MASTER_PASSWORD': MARCA, 'APP_ENV': 'production'}


def _revisar(tmp_path, variables):
    env = tmp_path / '.env'
    env.write_text(''.join(f'{k}={v}\n' for k, v in variables.items()))
    resultado = subprocess.run(
        ['bash', '-c', f'. "{SCRIPT}"; revisar_vaultwarden "$1"', '_',
         str(env)], capture_output=True, text=True, timeout=10)
    assert MARCA not in resultado.stdout + resultado.stderr
    return resultado.returncode, resultado.stdout


def test_completo_pasa(tmp_path):
    codigo, salida = _revisar(tmp_path, COMPLETO)
    assert codigo == 0, salida
    assert 'FALTA' not in salida


def test_dev_no_exige_vaultwarden(tmp_path):
    codigo, _ = _revisar(tmp_path, {'APP_ENV': 'development'})
    assert codigo == 0


def test_sin_vaultwarden_fuera_de_dev_es_aviso(tmp_path):
    codigo, salida = _revisar(tmp_path, {'APP_ENV': 'staging'})
    assert codigo == 0 and 'AVISO' in salida


@pytest.mark.parametrize('cambio, texto', [
    ({'VAULTWARDEN_CLIENT_SECRET': '""'}, 'VAULTWARDEN_CLIENT_SECRET'),
    ({'VAULTWARDEN_URL': 'http://vault.pruebas.invalid'}, 'https'),
    ({'VAULTWARDEN_URL': 'https://2130706433'}, 'IP'),
    ({'VAULTWARDEN_CLIENT_ID': 'organization.x'}, 'VAULTWARDEN_CLIENT_ID'),
    ({'LDAP_URL': 'ldaps://ldap.pruebas.invalid'}, 'LDAP_BIND_PASSWORD_REF'),
    ({'LDAP_URL': 'ldaps://ldap.pruebas.invalid', 'LDAP_BIND_PASSWORD': MARCA,
      'LDAP_BIND_PASSWORD_REF': 'pokemon/prod/LDAP'}, 'no ambas'),
])
def test_faltas(tmp_path, cambio, texto):
    codigo, salida = _revisar(tmp_path, {**COMPLETO, **cambio})
    assert codigo == 1
    assert any(l.startswith('FALTA') and texto in l
               for l in salida.splitlines()), salida


def test_bind_desde_referencia_es_ok(tmp_path):
    codigo, salida = _revisar(tmp_path, {
        **COMPLETO, 'LDAP_URL': 'ldaps://ldap.pruebas.invalid',
        'LDAP_BIND_PASSWORD_REF': 'pokemon/prod/LDAP_BIND_PASSWORD'})
    assert codigo == 0 and 'LDAP_BIND_PASSWORD_REF' in salida
