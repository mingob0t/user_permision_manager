"""Directorio OpenLDAP simulado con `ldap3` `MOCK_SYNC` (sin red) (FNC-040).

`MOCK_SYNC` guarda las entradas en el objeto `Server`; el cliente se fija a un
servidor creado por él mismo (con su TLS real) para que todas sus conexiones
vean las mismas entradas.
"""

import ldap3
import pytest

from app.modules.directory import ldap_client
from app.modules.directory.configuracion import cargar_configuracion
from tests.directorio_falso import (BASE_DN, CUENTA_SERVICIO,  # noqa: F401
                                    ENTORNO_VALIDO, GRUPOS_BASE_DN,
                                    USUARIOS_BASE_DN, ServidorSimulado,
                                    dn_grupo, dn_persona)

# Las constantes y los `dn_*` viven en `tests/directorio_falso.py` (FNC-074);
# se reexportan aquí porque las pruebas del directorio las importan de aquí.


class DirectorioMock(ServidorSimulado):
    """Cliente real ligado a un servidor `MOCK_SYNC` con entradas de prueba."""

    def __init__(self, monkeypatch, **variables):
        monkeypatch.setattr(ldap_client, 'Connection', ldap3.Connection)
        monkeypatch.setattr(ldap_client, 'ESTRATEGIA', ldap3.MOCK_SYNC)
        self.configuracion = cargar_configuracion({**ENTORNO_VALIDO,
                                                   **variables})
        self.cliente = ldap_client.ClienteDirectorio(self.configuracion)
        super().__init__(self.cliente._servidor())
        monkeypatch.setattr(self.cliente, '_servidor', lambda: self.servidor)

    def agregar(self, dn, **atributos):
        self._agregar(dn, **atributos)

    def persona(self, uid, correo=None):
        self.agregar(dn_persona(uid), objectClass='inetOrgPerson', uid=uid,
                     cn=uid, sn=uid, mail=correo or f'{uid}@pruebas.local',
                     displayName=f'Persona {uid}')
        return dn_persona(uid)

    def grupo(self, nombre, miembros, clase='groupOfNames', atributo='member'):
        self.agregar(dn_grupo(nombre), objectClass=clase, cn=nombre,
                     **{atributo: list(miembros)})
        return dn_grupo(nombre)


@pytest.fixture
def directorio(monkeypatch):
    return DirectorioMock(monkeypatch)


@pytest.fixture
def crear_directorio(monkeypatch):
    """Directorio con variables propias (p. ej. `LDAP_GROUP_MEMBER_ATTR`)."""
    return lambda **variables: DirectorioMock(monkeypatch, **variables)
