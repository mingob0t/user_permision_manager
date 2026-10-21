"""Contraseña de bind LDAP desde Vaultwarden con `LDAP_BIND_PASSWORD_REF`
fuera de dev; dev sigue con `LDAP_BIND_PASSWORD` (FNC-068)."""
import logging

import pytest
from ldap3.core.exceptions import LDAPCommunicationError

from app.modules.connectors import credenciales
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 cargar_configuracion)
from app.modules.directory.ldap_client import ErrorDirectorio
from app.modules.secretos import vaultwarden
from tests.directory.conftest import ENTORNO_VALIDO, DirectorioMock
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.secretos import vaultwarden_falso as vf

REFERENCIA_BIND = 'pokemon/produccion/LDAP_BIND_PASSWORD'
SIN_CONTRASENA = {**ENTORNO_VALIDO, 'LDAP_BIND_PASSWORD': ''}
CON_REFERENCIA = {**SIN_CONTRASENA, 'LDAP_BIND_PASSWORD_REF': REFERENCIA_BIND,
                  'APP_ENV': 'production', **vf.ENTORNO}


@pytest.fixture
def gestor(monkeypatch):
    falso = vf.VaultwardenFalso()
    for clave, valor in CON_REFERENCIA.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setattr(vaultwarden, 'TransporteHttps', lambda cfg: falso)
    vaultwarden.reiniciar_cliente()
    credenciales.limpiar_cache()
    yield falso
    vaultwarden.reiniciar_cliente()
    credenciales.limpiar_cache()


def test_dev_sigue_con_la_contrasena_del_entorno():
    cfg = cargar_configuracion({**ENTORNO_VALIDO, 'APP_ENV': 'development'})
    assert cfg.bind_password == CONTRASENA_FICTICIA
    assert cfg.bind_password_ref is None


def test_fuera_de_dev_acepta_la_referencia_sin_contrasena():
    cfg = cargar_configuracion(CON_REFERENCIA)
    assert cfg.bind_password_ref == REFERENCIA_BIND
    assert cfg.bind_password == ''


@pytest.mark.parametrize('entorno', [
    {**CON_REFERENCIA, 'LDAP_BIND_PASSWORD': CONTRASENA_FICTICIA},  # ambas
    {**CON_REFERENCIA, 'APP_ENV': 'development'},  # referencia en dev
    {**CON_REFERENCIA, 'LDAP_BIND_PASSWORD_REF': 'pokemon/../x y'},
    {**SIN_CONTRASENA, 'LDAP_BIND_PASSWORD_REF': REFERENCIA_BIND,
     'APP_ENV': 'production'},  # sin VAULTWARDEN_*
])
def test_combinaciones_invalidas_detienen_el_arranque(entorno):
    with pytest.raises(ErrorConfiguracionDirectorio):
        cargar_configuracion(entorno)


def test_bind_usa_la_contrasena_del_gestor(monkeypatch, gestor, caplog):
    gestor.item(REFERENCIA_BIND, CONTRASENA_FICTICIA)
    directorio = DirectorioMock(monkeypatch, **CON_REFERENCIA)
    caplog.set_level(logging.DEBUG)
    with directorio.cliente.conexion_servicio() as conexion:
        assert conexion.bound
    assert CONTRASENA_FICTICIA not in caplog.text


def test_sin_item_en_el_gestor_es_error_generico(monkeypatch, gestor, caplog):
    directorio = DirectorioMock(monkeypatch, **CON_REFERENCIA)
    caplog.set_level(logging.DEBUG)
    with pytest.raises(ErrorDirectorio):
        with directorio.cliente.conexion_servicio():
            pass
    assert 'CredencialNoEncontrada' in caplog.text
    assert REFERENCIA_BIND not in caplog.text


def test_gestor_caido_es_error_transitorio(monkeypatch, gestor):
    """El ejecutor reintenta si Vaultwarden no responde (no es permanente)."""
    gestor.estado_forzado[vaultwarden.RUTA_TOKEN] = 503
    directorio = DirectorioMock(monkeypatch, **CON_REFERENCIA)
    with pytest.raises(ErrorDirectorio) as error:
        with directorio.cliente.conexion_servicio():
            pass
    assert isinstance(error.value.causa, LDAPCommunicationError)


def test_arranque_fuera_de_dev_con_vaultwarden_incompleto_falla(monkeypatch):
    from app.modules.secretos.configuracion import ErrorConfiguracionSecretos
    from app import create_app
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('VAULTWARDEN_URL', vf.URL)
    with pytest.raises(ErrorConfiguracionSecretos):
        create_app()
