"""Regresión de los hallazgos bajos de auditor-seguridad sobre FNC-068.

- B1: excepciones sin traducir (`http.client.HTTPException`, `UnsupportedAlgorithm`
  de Argon2id, `RecursionError` de `json`, errores inesperados al pedir el bind).
- B2: un ítem ilegible con el mismo nombre que uno legible no lo vuelve ambiguo.
- B3: la referencia del bind LDAP no puede ser la credencial de un conector
  (al ejecutar: `tests/connectors/test_referencia_reservada.py`).
- FNC-108: los secretos de arranque de Vaultwarden se borran de la bitácora.
"""
import http.client

import pytest
from cryptography.exceptions import UnsupportedAlgorithm

from app.modules.connectors import credenciales
from app.modules.connectors import validacion
from app.modules.directory.ldap_client import ErrorDirectorio
from app.modules.provisioning import saneo
from app.modules.secretos import cifrado, vaultwarden
from app.modules.secretos.configuracion import cargar_configuracion
from app.modules.secretos.vaultwarden import (ClienteVaultwarden, GestorCaido,
                                              GestorMalConfigurado, Respuesta,
                                              RUTA_SYNC, TransporteHttps)
from tests.connectors.conftest import HOST_PERMITIDO
from tests.directory.conftest import DirectorioMock
from tests.directory.test_bind_desde_gestor import CON_REFERENCIA, REFERENCIA_BIND
from tests.secretos import vaultwarden_falso as vf
from tests.secretos.test_vaultwarden import REFERENCIA, SECRETO, _cliente


class _Abridor:
    def __init__(self, efecto):
        self.efecto = efecto

    def open(self, peticion, timeout=None):
        raise self.efecto


@pytest.mark.parametrize('efecto', [http.client.IncompleteRead(b'x'),
                                    http.client.BadStatusLine('x'),
                                    http.client.RemoteDisconnected('x')])
def test_b1_http_exception_es_gestor_caido(efecto):
    transporte = TransporteHttps(cargar_configuracion(vf.ENTORNO))
    transporte._abridor = _Abridor(efecto)
    with pytest.raises(GestorCaido):
        transporte('GET', vf.URL, {})


def test_b1_json_demasiado_anidado_es_no_configurado():
    def transporte(metodo, url, cabeceras, cuerpo=None):
        return Respuesta(200, b'[' * 100_000 + b']' * 100_000)

    cliente = ClienteVaultwarden(cargar_configuracion(vf.ENTORNO),
                                 transporte=transporte)
    with pytest.raises(GestorMalConfigurado):
        cliente.leer(REFERENCIA)


def test_b1_argon2_no_soportado_es_error_de_cifrado(monkeypatch):
    def sin_argon2(**kwargs):
        raise UnsupportedAlgorithm('sin argon2')

    monkeypatch.setattr(cifrado, 'Argon2id', sin_argon2)
    with pytest.raises(cifrado.ErrorDeCifrado):
        cifrado.derivar_clave_maestra('x', 'a@b.c', cifrado.KDF_ARGON2ID, 3,
                                      64, 4)


def test_b1_bind_con_error_inesperado_es_error_directorio(monkeypatch):
    falso = vf.VaultwardenFalso()
    falso.item(REFERENCIA_BIND, 'clave-ficticia-de-prueba')
    for clave, valor in CON_REFERENCIA.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(vaultwarden, 'TransporteHttps', lambda cfg: falso)
    vaultwarden.reiniciar_cliente()
    credenciales.limpiar_cache()

    def falla(referencia):
        raise RuntimeError('inesperado')

    monkeypatch.setattr(credenciales, 'resolver_en_gestor', falla)
    directorio = DirectorioMock(monkeypatch, **CON_REFERENCIA)
    with pytest.raises(ErrorDirectorio):
        with directorio.cliente.conexion_servicio():
            pass
    vaultwarden.reiniciar_cliente()


def test_b2_ilegible_y_legible_con_el_mismo_nombre_devuelve_el_legible():
    servidor = vf.VaultwardenFalso()
    roto = servidor.item(REFERENCIA, 'otro-valor-ficticio')
    iv, datos, _ = roto['login']['password'][2:].split('|')
    roto['login']['password'] = f'2.{iv}|{datos}|{"A" * 43}='
    servidor.item(REFERENCIA, SECRETO)
    assert _cliente(servidor).leer(REFERENCIA).secreto == SECRETO


def test_b2_solo_ilegibles_falla_cerrado():
    servidor = vf.VaultwardenFalso()
    roto = servidor.item(REFERENCIA, SECRETO)
    iv, datos, _ = roto['login']['password'][2:].split('|')
    roto['login']['password'] = f'2.{iv}|{datos}|{"A" * 43}='
    with pytest.raises(GestorMalConfigurado):
        _cliente(servidor).leer(REFERENCIA)


def test_b3_validacion_rechaza_la_referencia_del_bind(app):
    entorno = {'APP_ENV': 'production', 'CONNECTOR_ALLOWED_HOSTS':
               HOST_PERMITIDO, 'LDAP_BIND_PASSWORD_REF': REFERENCIA_BIND}
    _, errores = validacion.validar_configuracion(
        {'type': 'noop', 'host': HOST_PERMITIDO, 'port': 443, 'params': {},
         'credential_ref': REFERENCIA_BIND}, entorno)
    assert errores.get('credential_ref') == getattr(
        validacion, 'MENSAJE_REFERENCIA_RESERVADA', 'sin la corrección B3')


@pytest.mark.parametrize('variable', ['VAULTWARDEN_CLIENT_SECRET',
                                      'VAULTWARDEN_MASTER_PASSWORD'])
def test_fnc108_secretos_de_arranque_en_variables_secretas(variable):
    assert variable in saneo.VARIABLES_SECRETAS


def test_sync_sin_cambios_previos(monkeypatch):
    """Control: el flujo normal sigue igual tras las correcciones."""
    servidor = vf.VaultwardenFalso()
    servidor.item(REFERENCIA, SECRETO)
    assert _cliente(servidor).leer(REFERENCIA).secreto == SECRETO
    assert ('GET', RUTA_SYNC) in servidor.peticiones
