"""Directorio OpenLDAP simulado con `ldap3` `MOCK_SYNC` (sin red) (FNC-040).

`MOCK_SYNC` guarda las entradas en el objeto `Server`; el cliente se fija a un
servidor creado por él mismo (con su TLS real) para que todas sus conexiones
vean las mismas entradas.
"""

import ldap3
import pytest

from app.modules.directory import ldap_client
from app.modules.directory.configuracion import cargar_configuracion
from tests.matriz_proteccion import CONTRASENA_FICTICIA, HOST_LDAP_FICTICIO

BASE_DN = 'dc=pruebas,dc=local'
USUARIOS_BASE_DN = f'ou=personas,{BASE_DN}'
GRUPOS_BASE_DN = f'ou=grupos,{BASE_DN}'
CUENTA_SERVICIO = f'cn=servicio,{BASE_DN}'

ENTORNO_VALIDO = {
    'LDAP_URL': f'ldaps://{HOST_LDAP_FICTICIO}',
    'LDAP_BIND_DN': CUENTA_SERVICIO,
    'LDAP_BIND_PASSWORD': CONTRASENA_FICTICIA,
    'LDAP_USERS_BASE_DN': USUARIOS_BASE_DN,
    'LDAP_GROUPS_BASE_DN': GRUPOS_BASE_DN,
}


def dn_persona(uid):
    return f'uid={uid},{USUARIOS_BASE_DN}'


def dn_grupo(nombre):
    return f'cn={nombre},{GRUPOS_BASE_DN}'


class DirectorioMock:
    """Cliente real ligado a un servidor `MOCK_SYNC` con entradas de prueba."""

    def __init__(self, monkeypatch, **variables):
        monkeypatch.setattr(ldap_client, 'Connection', ldap3.Connection)
        monkeypatch.setattr(ldap_client, 'ESTRATEGIA', ldap3.MOCK_SYNC)
        self.configuracion = cargar_configuracion({**ENTORNO_VALIDO,
                                                   **variables})
        self.cliente = ldap_client.ClienteDirectorio(self.configuracion)
        self.servidor = self.cliente._servidor()
        monkeypatch.setattr(self.cliente, '_servidor', lambda: self.servidor)
        self._carga = ldap3.Connection(self.servidor,
                                       client_strategy=ldap3.MOCK_SYNC)
        self.agregar(CUENTA_SERVICIO, objectClass='person', cn='servicio',
                     userPassword=CONTRASENA_FICTICIA)
        for ou in (USUARIOS_BASE_DN, GRUPOS_BASE_DN):
            self.agregar(ou, objectClass='organizationalUnit',
                         ou=ou.split(',')[0].split('=')[1])

    def agregar(self, dn, **atributos):
        self._carga.strategy.add_entry(dn, atributos)

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
