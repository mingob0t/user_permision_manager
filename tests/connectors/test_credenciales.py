"""Resolvedor de credenciales: fuente por entorno, caché breve y sin valores
en logs ni representaciones (FNC-050, ADR-005)."""
import logging

import pytest

from app.modules.connectors import credenciales
from app.modules.connectors.credenciales import (Credencial,
                                                CredencialNoEncontrada,
                                                GestorNoConfigurado,
                                                ProveedorSecretosEntorno,
                                                ProveedorSecretosVaultwarden,
                                                ResolvedorCredenciales,
                                                nombre_variable,
                                                proveedor_de_secretos)
from tests.connectors.conftest import (REFERENCIA, SECRETO_FICTICIO,
                                       VARIABLE_CREDENCIAL)


class Reloj:
    def __init__(self):
        self.ahora = 1000.0

    def __call__(self):
        return self.ahora


class FuenteContada(credenciales.ProveedorDeSecretos):
    fuente = 'contada'

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = 0

    def obtener(self, referencia):
        self.llamadas += 1
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, BaseException):
            raise respuesta
        return respuesta


def test_nombre_de_variable_desde_la_referencia():
    assert nombre_variable(REFERENCIA) == VARIABLE_CREDENCIAL
    assert nombre_variable('erp.contabilidad/api-v2') == (
        'CONNECTOR_CREDENTIAL_ERP_CONTABILIDAD_API_V2')


def test_entorno_resuelve_la_credencial_y_su_usuario_opcional():
    entorno = {VARIABLE_CREDENCIAL: SECRETO_FICTICIO,
               f'{VARIABLE_CREDENCIAL}__USUARIO': 'svc-portal'}
    credencial = ProveedorSecretosEntorno(entorno).obtener(REFERENCIA)
    assert (credencial.secreto, credencial.usuario) == (
        SECRETO_FICTICIO, 'svc-portal')


def test_entorno_sin_la_variable_es_credencial_no_encontrada():
    with pytest.raises(CredencialNoEncontrada):
        ProveedorSecretosEntorno({}).obtener(REFERENCIA)


def test_la_representacion_nunca_muestra_el_secreto():
    credencial = Credencial(secreto=SECRETO_FICTICIO, usuario='svc')
    assert SECRETO_FICTICIO not in repr(credencial)
    assert SECRETO_FICTICIO not in str(credencial)
    assert SECRETO_FICTICIO not in f'{credencial!r} {credencial}'


def test_vaultwarden_es_un_stub_no_configurado_hasta_fnc_068():
    with pytest.raises(GestorNoConfigurado):
        ProveedorSecretosVaultwarden().obtener(REFERENCIA)


@pytest.mark.parametrize('app_env, esperado', [
    ('development', ProveedorSecretosEntorno),
    ('staging', ProveedorSecretosVaultwarden),
    ('production', ProveedorSecretosVaultwarden),
    ('', ProveedorSecretosVaultwarden),
    ('DEVELOPMENT ', ProveedorSecretosEntorno),
])
def test_fuente_segun_el_entorno(app_env, esperado):
    assert isinstance(proveedor_de_secretos({'APP_ENV': app_env}), esperado)


def test_la_cache_reutiliza_hasta_vencer_y_no_guarda_fallos():
    reloj = Reloj()
    fuente = FuenteContada([CredencialNoEncontrada(),
                            Credencial(secreto='a1b2c3d4'),
                            Credencial(secreto='e5f6g7h8')])
    resolvedor = ResolvedorCredenciales(segundos_cache=60, reloj=reloj)

    with pytest.raises(CredencialNoEncontrada):
        resolvedor.resolver(fuente, REFERENCIA)
    assert resolvedor.resolver(fuente, REFERENCIA).secreto == 'a1b2c3d4'
    reloj.ahora += 59
    assert resolvedor.resolver(fuente, REFERENCIA).secreto == 'a1b2c3d4'
    reloj.ahora += 2
    assert resolvedor.resolver(fuente, REFERENCIA).secreto == 'e5f6g7h8'
    assert fuente.llamadas == 3


def test_cache_en_cero_no_guarda_nada():
    fuente = FuenteContada([Credencial(secreto='a1b2c3d4'),
                            Credencial(secreto='a1b2c3d4')])
    resolvedor = ResolvedorCredenciales(segundos_cache=0, reloj=Reloj())
    resolvedor.resolver(fuente, REFERENCIA)
    resolvedor.resolver(fuente, REFERENCIA)
    assert fuente.llamadas == 2


def test_resolver_no_registra_el_valor_en_logs(monkeypatch, caplog):
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.setenv(VARIABLE_CREDENCIAL, SECRETO_FICTICIO)
    caplog.set_level(logging.DEBUG)
    credencial = credenciales.resolver_credencial(REFERENCIA)
    assert credencial.secreto == SECRETO_FICTICIO
    assert SECRETO_FICTICIO not in caplog.text
