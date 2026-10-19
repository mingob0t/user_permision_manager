"""Directorio OpenLDAP simulado para las pruebas de login (FNC-022, FNC-042).

Desde FNC-042 el login usa el cliente centralizado (`app.modules.directory`).
Este doble activa el directorio con variables `LDAP_*` ficticias y conecta el
cliente a un servidor `ldap3` `MOCK_SYNC` (sin red), el mismo esquema que
`tests/directory/conftest.py`. Registra los filtros de búsqueda que recibe.

Uso:
    directorio = instalar_directorio(monkeypatch)
    directorio.agregar('jperez', 'clave', grupos=[DN_GRUPO])
"""

import ldap3

from app import db
from app.modules.auth.models import AuthConfig
from app.modules.directory import ldap_client
from tests.directory.conftest import (CUENTA_SERVICIO, ENTORNO_VALIDO,
                                      GRUPOS_BASE_DN, USUARIOS_BASE_DN,
                                      dn_persona)
from tests.matriz_proteccion import CONTRASENA_FICTICIA

BASE_DN = 'dc=pruebas,dc=local'
DOMINIO_CORREO = 'pruebas.local'


class DirectorioFalso:
    """Personas y grupos del directorio, y los filtros que pidió el login."""

    def __init__(self, servidor):
        self.servidor = servidor
        self.filtros = []       # filtros de búsqueda recibidos, en orden
        self.error = None       # excepción a lanzar al conectar, si se define
        self._carga = ldap3.Connection(servidor,
                                       client_strategy=ldap3.MOCK_SYNC)
        self._agregar(CUENTA_SERVICIO, objectClass='person', cn='servicio',
                      userPassword=CONTRASENA_FICTICIA)
        for ou in (USUARIOS_BASE_DN, GRUPOS_BASE_DN):
            self._agregar(ou, objectClass='organizationalUnit',
                          ou=ou.split(',')[0].split('=')[1])

    def _agregar(self, dn, **atributos):
        self._carga.strategy.add_entry(dn, atributos)

    def agregar(self, uid, contrasena, correo=None, nombre=None, grupos=()):
        """Persona `inetOrgPerson`; `grupos` son DN de `groupOfNames`.

        `correo=None` usa `<uid>@pruebas.local`; `correo=''`, sin `mail`.
        """
        dn = dn_persona(uid)
        atributos = {'objectClass': 'inetOrgPerson', 'uid': uid, 'cn': uid,
                     'sn': uid, 'displayName': nombre or f'Persona {uid}',
                     'userPassword': contrasena}
        if correo != '':  # `correo=''`: persona sin `mail`
            atributos['mail'] = correo or f'{uid}@{DOMINIO_CORREO}'
        self._agregar(dn, **atributos)
        for grupo in grupos:
            self._agregar(grupo, objectClass='groupOfNames',
                          cn=grupo.split(',')[0].split('=')[1], member=[dn])
        return dn

    def conexion(self):
        """Clase que reemplaza a `ldap3.Connection` en el cliente."""
        directorio = self

        class ConexionRegistrada(ldap3.Connection):
            def __init__(self, *args, **kwargs):
                if directorio.error:
                    raise directorio.error
                super().__init__(*args, **kwargs)

            def search(self, base, filtro, *args, **kwargs):
                directorio.filtros.append(filtro)
                return super().search(base, filtro, *args, **kwargs)

        return ConexionRegistrada


def instalar_directorio(monkeypatch, variables=None, **config):
    """Activa el directorio simulado para el login.

    - `variables`: `LDAP_*` que sobrescriben las de prueba.
    - `config`: si se da, crea `AuthConfig` con esos campos (p. ej.
      `ldap_group_admin` o `ldap_role_mappings`), para probar que el login ya
      no los usa.
    """
    for nombre, valor in {**ENTORNO_VALIDO, **(variables or {})}.items():
        monkeypatch.setenv(nombre, valor)
    if config:
        db.session.add(AuthConfig(**config))
        db.session.commit()

    monkeypatch.setattr(ldap_client, 'ESTRATEGIA', ldap3.MOCK_SYNC)
    cliente = ldap_client.ClienteDirectorio(
        ldap_client.cargar_configuracion())
    directorio = DirectorioFalso(cliente._servidor())
    monkeypatch.setattr(ldap_client.ClienteDirectorio, '_servidor',
                        lambda self: directorio.servidor)
    monkeypatch.setattr(ldap_client, 'Connection', directorio.conexion())
    return directorio
