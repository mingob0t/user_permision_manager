"""Credenciales de los conectores en ejecución (FNC-050, ADR-005).

- La BD guarda solo la **referencia** (`credential_ref`); el valor se pide a
  un `ProveedorDeSecretos` en cada ejecución (SEC-CON-02).
- Fuente según `APP_ENV`: `development` → variables de entorno (`.env` de
  dev); cualquier otro valor o vacío → Vaultwarden. Hoy Vaultwarden es un
  *stub* que responde «no configurado»: la API real es FNC-068.
- Entorno: la referencia `pokemon/contabilidad-api` se lee de
  `CONNECTOR_CREDENTIAL_POKEMON_CONTABILIDAD_API` (y el usuario opcional de
  `…__USUARIO`).
- Caché breve en memoria (`CONNECTOR_CREDENTIAL_CACHE_SECONDS`) por fuente y
  referencia; los fallos no se guardan.
- Nunca se registra ni se representa el valor (`repr` lo oculta). Los errores
  no llevan la referencia ni el valor hacia afuera.
"""
import os
import re
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.modules.connectors.configuracion import cargar_configuracion

VAR_ENTORNO = 'APP_ENV'
ENTORNO_DESARROLLO = 'development'
PREFIJO_VARIABLE = 'CONNECTOR_CREDENTIAL_'
SUFIJO_USUARIO = '__USUARIO'
_NO_ALFANUMERICO = re.compile(r'[^A-Z0-9]')

FUENTE_ENTORNO = 'entorno'
FUENTE_VAULTWARDEN = 'vaultwarden'


class ErrorDeCredencial(Exception):
    """Base: el texto es solo para el log interno; nunca lleva el valor."""


class CredencialNoEncontrada(ErrorDeCredencial):
    """La referencia no existe en la fuente (permanente)."""


class GestorNoDisponible(ErrorDeCredencial):
    """La fuente no respondió (transitorio)."""


class GestorNoConfigurado(ErrorDeCredencial):
    """La fuente no está configurada en este despliegue (permanente)."""


@dataclass(frozen=True)
class Credencial:
    secreto: str = field(repr=False)
    usuario: str | None = None

    def __str__(self):
        return repr(self)


class ProveedorDeSecretos(ABC):
    fuente = ''

    @abstractmethod
    def obtener(self, referencia):
        """`Credencial` de la referencia o una `ErrorDeCredencial`."""


def nombre_variable(referencia):
    """Variable de entorno de dev que guarda la credencial de `referencia`."""
    return PREFIJO_VARIABLE + _NO_ALFANUMERICO.sub('_', referencia.upper())


class ProveedorSecretosEntorno(ProveedorDeSecretos):
    """Solo desarrollo: la credencial sale del entorno (`.env`)."""

    fuente = FUENTE_ENTORNO

    def __init__(self, entorno=None):
        self._entorno = os.environ if entorno is None else entorno

    def obtener(self, referencia):
        nombre = nombre_variable(referencia)
        secreto = self._entorno.get(nombre) or ''
        if not secreto:
            raise CredencialNoEncontrada('Sin variable para la referencia.')
        usuario = (self._entorno.get(nombre + SUFIJO_USUARIO) or '').strip()
        return Credencial(secreto=secreto, usuario=usuario or None)


class ProveedorSecretosVaultwarden(ProveedorDeSecretos):
    """Vaultwarden (ADR-005, alternativa A). *Stub* hasta FNC-068."""

    fuente = FUENTE_VAULTWARDEN

    def obtener(self, referencia):
        raise GestorNoConfigurado('Vaultwarden aún no está integrado (FNC-068).')


def proveedor_de_secretos(entorno=None):
    """Fuente de este despliegue: entorno solo en `development`."""
    entorno = os.environ if entorno is None else entorno
    if (entorno.get(VAR_ENTORNO) or '').strip().lower() == ENTORNO_DESARROLLO:
        return ProveedorSecretosEntorno(entorno)
    return ProveedorSecretosVaultwarden()


class ResolvedorCredenciales:
    """Caché en memoria de credenciales por (fuente, referencia)."""

    def __init__(self, segundos_cache=None, reloj=time.monotonic):
        self._segundos = segundos_cache
        self._reloj = reloj
        self._cache = {}
        self._candado = threading.Lock()

    def _vida(self):
        if self._segundos is not None:
            return self._segundos
        return cargar_configuracion().segundos_cache

    def resolver(self, proveedor, referencia):
        clave = (proveedor.fuente, referencia)
        momento = self._reloj()
        with self._candado:
            guardada = self._cache.get(clave)
            if guardada and guardada[0] > momento:
                return guardada[1]
            self._cache.pop(clave, None)
        credencial = proveedor.obtener(referencia)
        vida = self._vida()
        if vida > 0:
            with self._candado:
                self._cache[clave] = (momento + vida, credencial)
        return credencial

    def limpiar(self):
        with self._candado:
            self._cache.clear()


_RESOLVEDOR = ResolvedorCredenciales()


def resolver_credencial(referencia):
    """Credencial de `referencia` desde la fuente del despliegue."""
    return _RESOLVEDOR.resolver(proveedor_de_secretos(), referencia)


def limpiar_cache():
    _RESOLVEDOR.limpiar()
