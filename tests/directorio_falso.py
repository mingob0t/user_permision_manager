"""Directorio LDAP simulado para las pruebas de autenticación (FNC-022).

Sustituye a `ldap3.Server` y `ldap3.Connection` dentro de
`app.modules.auth.services`, sin red. Guarda las personas del directorio, sus
contraseñas y grupos, y registra los filtros de búsqueda que recibe.

Uso:
    directorio = instalar_directorio(monkeypatch)
    directorio.agregar('jperez', 'clave', grupos=[DN_GRUPO])
"""

import fnmatch
import re

from ldap3.core.exceptions import LDAPBindError

from app import db
from app.modules.auth import services as auth_services
from app.modules.auth.models import AuthConfig
from tests.matriz_proteccion import CONTRASENA_FICTICIA, HOST_LDAP_FICTICIO

BASE_DN = 'dc=pruebas,dc=local'
CUENTA_SERVICIO = f'cn=servicio,{BASE_DN}'
DOMINIO_CORREO = 'pruebas.local'

_FILTRO = re.compile(r'^\((?P<atributo>[^=()]+)=(?P<valor>.*)\)$')


class _Valor:
    """Imita un atributo de `ldap3`: `.value`, iterable y con valor de verdad."""

    def __init__(self, valores):
        self.values = list(valores) if isinstance(valores, (list, tuple)) \
            else [valores]

    @property
    def value(self):
        return self.values[0] if len(self.values) == 1 else self.values

    def __iter__(self):
        return iter(self.values)

    def __bool__(self):
        return bool(self.values)

    def __str__(self):
        return str(self.value)


class EntradaFalsa:
    """Imita una entrada de `conn.entries` (atributos, `in` y `entry_dn`)."""

    def __init__(self, dn, atributos):
        self.entry_dn = dn
        self._atributos = atributos

    def __contains__(self, nombre):
        return nombre in self._atributos

    def __getattr__(self, nombre):
        if nombre.startswith('_'):
            raise AttributeError(nombre)
        try:
            return _Valor(self._atributos[nombre])
        except KeyError:
            raise AttributeError(nombre) from None


class DirectorioFalso:
    """Personas del directorio y registro de lo que pidió el servicio."""

    def __init__(self):
        self.personas = {}      # uid -> (EntradaFalsa, contraseña)
        self.filtros = []       # filtros de búsqueda recibidos, en orden
        self.error = None       # excepción a lanzar al conectar, si se define

    def agregar(self, uid, contrasena, correo=None, nombre=None, grupos=()):
        dn = f'uid={uid},ou=personas,{BASE_DN}'
        atributos = {'sAMAccountName': uid, 'cn': uid,
                     'mail': correo or f'{uid}@{DOMINIO_CORREO}',
                     'displayName': nombre or f'Persona {uid}'}
        if grupos:
            atributos['memberOf'] = list(grupos)
        entrada = EntradaFalsa(dn, atributos)
        self.personas[uid] = (entrada, contrasena)
        return entrada

    def buscar(self, filtro):
        self.filtros.append(filtro)
        coincidencia = _FILTRO.match(filtro)
        if not coincidencia:
            return []
        valor = coincidencia.group('valor')
        # Como un servidor real, `*` sin escapar es comodín.
        return [entrada for uid, (entrada, _) in self.personas.items()
                if fnmatch.fnmatchcase(uid, valor)]

    def validar_bind(self, usuario, contrasena):
        if usuario == CUENTA_SERVICIO:
            return
        for entrada, clave in self.personas.values():
            if entrada.entry_dn == usuario and clave == contrasena:
                return
        raise LDAPBindError('invalidCredentials')

    def conexion(self):
        """Clase que reemplaza a `ldap3.Connection`, ligada a este directorio."""
        directorio = self

        class ConexionFalsa:
            def __init__(self, servidor, user=None, password=None, **kwargs):
                if directorio.error:
                    raise directorio.error
                directorio.validar_bind(user, password)
                self.entries = []

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def search(self, base, filtro, attributes=None, **kwargs):
                self.entries = directorio.buscar(filtro)
                return bool(self.entries)

            def unbind(self):
                return True

        return ConexionFalsa


def instalar_directorio(monkeypatch, **config):
    """Configura el directorio en la BD y simula `ldap3` en el servicio.

    `config` sobrescribe campos de `AuthConfig` (p. ej. `ldap_group_admin` o
    `ldap_role_mappings`).
    """
    campos = {'ldap_host': HOST_LDAP_FICTICIO, 'ldap_base_dn': BASE_DN,
              'ldap_user': CUENTA_SERVICIO, 'ldap_pass': CONTRASENA_FICTICIA,
              'ldap_user_attr': 'sAMAccountName'}
    campos.update(config)
    db.session.add(AuthConfig(**campos))
    db.session.commit()

    directorio = DirectorioFalso()
    monkeypatch.setattr(auth_services, 'Server', lambda *args, **kwargs: None)
    monkeypatch.setattr(auth_services, 'Connection', directorio.conexion())
    return directorio
