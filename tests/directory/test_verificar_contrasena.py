"""Cliente LDAP: verificación de la contraseña de una persona (FNC-042).

`ldap3` corre con `MOCK_SYNC` (ver `conftest.py`): sin red.
"""

import logging

import ldap3
import pytest

from app.modules.directory import ldap_client
from app.modules.directory.ldap_client import (MENSAJE_ERROR, ErrorDirectorio,
                                               UsuarioDirectorio)
from tests.directory.conftest import dn_persona

UID = 'jperez'
CONTRASENA = 'clave-de-la-persona-de-prueba'
CONTRASENA_ERRONEA = 'clave-erronea-de-prueba'


@pytest.fixture
def persona(directorio):
    directorio.agregar(dn_persona(UID), objectClass='inetOrgPerson', uid=UID,
                       cn=UID, sn=UID, userPassword=CONTRASENA)
    return UsuarioDirectorio(dn=dn_persona(UID), identificador=UID)


def test_contrasena_correcta(directorio, persona):
    assert directorio.cliente.verificar_contrasena(persona, CONTRASENA) is True


def test_contrasena_incorrecta(directorio, persona):
    assert directorio.cliente.verificar_contrasena(
        persona, CONTRASENA_ERRONEA) is False


@pytest.mark.parametrize('vacia', ['', None])
def test_contrasena_vacia_no_conecta(directorio, persona, monkeypatch, vacia):
    # Un bind simple sin contraseña es anónimo: no debe llegar al servidor.
    def _no_conectar(*args, **kwargs):
        raise AssertionError('se intentó conectar con contraseña vacía')
    monkeypatch.setattr(ldap_client, 'Connection', _no_conectar)

    assert directorio.cliente.verificar_contrasena(persona, vacia) is False


def test_fallo_del_directorio_es_generico_y_sin_la_contrasena(
        directorio, persona, monkeypatch, caplog):
    class ConexionQueFalla(ldap3.Connection):
        def bind(self, *args, **kwargs):
            raise ldap3.core.exceptions.LDAPSocketOpenError(
                f'fallo con {CONTRASENA}')
    monkeypatch.setattr(ldap_client, 'Connection', ConexionQueFalla)

    with caplog.at_level(logging.ERROR, logger=ldap_client.__name__):
        with pytest.raises(ErrorDirectorio) as error:
            directorio.cliente.verificar_contrasena(persona, CONTRASENA)

    assert str(error.value) == MENSAJE_ERROR
    assert CONTRASENA not in caplog.text
    assert 'verificación de contraseña' in caplog.text


def test_ldap_con_starttls_exige_tls_antes_del_bind(crear_directorio,
                                                    monkeypatch):
    directorio = crear_directorio(LDAP_URL='ldap://ldap.pruebas.invalid')
    directorio.persona(UID)
    usuario = UsuarioDirectorio(dn=dn_persona(UID), identificador=UID)
    pasos = []

    class ConexionSinTls(ldap3.Connection):
        def start_tls(self, *args, **kwargs):
            pasos.append('start_tls')
            return False

        def bind(self, *args, **kwargs):
            pasos.append('bind')
            return super().bind(*args, **kwargs)
    monkeypatch.setattr(ldap_client, 'Connection', ConexionSinTls)

    with pytest.raises(ErrorDirectorio):
        directorio.cliente.verificar_contrasena(usuario, CONTRASENA)

    assert pasos == ['start_tls']
