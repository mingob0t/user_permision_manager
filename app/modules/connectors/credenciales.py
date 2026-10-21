"""Credenciales de los conectores en ejecución (FNC-050, ADR-005).

- La BD guarda solo la **referencia** (`credential_ref`); el valor se pide a
  un `ProveedorDeSecretos` en cada ejecución (SEC-CON-02).
- Fuente según `APP_ENV`: `development` → variables de entorno (`.env` de
  dev); cualquier otro valor o vacío → Vaultwarden (`app.modules.secretos`,
  FNC-068): ítem *login* cuyo nombre es la referencia, en la colección
  `VAULTWARDEN_COLLECTION_ID`. Sin `VAULTWARDEN_*` falla cerrado
  («no configurado»).
- Entorno: la referencia `pokemon/contabilidad-api` se lee de
  `CONNECTOR_CREDENTIAL_POKEMON_CONTABILIDAD_API` (y el usuario opcional de
  `…__USUARIO`).
- Regla de referencias (auditor-seguridad B3): la variable que resulta no
  puede tener `__` ni empezar o terminar en `_` (chocaría con `__USUARIO`), y
  dos referencias distintas no pueden dar la misma variable
  (`pokemon/erp-api` y `pokemon/erp_api`): `referencias_en_conflicto`.
- Caché breve en memoria (`CONNECTOR_CREDENTIAL_CACHE_SECONDS`) por fuente y
  referencia, de a lo más `MAXIMO_EN_CACHE` entradas; los fallos no se
  guardan. Al rotar una credencial: `limpiar_cache()` (por proceso) o esperar
  la vida de la caché (B4 de FNC-050).
- `resolver_en_gestor()`: siempre Vaultwarden (bind LDAP con
  `LDAP_BIND_PASSWORD_REF`, FNC-068).
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
SEPARADOR_DOBLE = '__'
SEPARADOR = '_'
_NO_ALFANUMERICO = re.compile(r'[^A-Z0-9]')

FUENTE_ENTORNO = 'entorno'
FUENTE_VAULTWARDEN = 'vaultwarden'
# Tope de entradas de la caché (una por referencia en uso).
MAXIMO_EN_CACHE = 128


class ErrorDeCredencial(Exception):
    """Base: el texto es solo para el log interno; nunca lleva el valor."""


class CredencialNoEncontrada(ErrorDeCredencial):
    """La referencia no existe en la fuente (permanente)."""


class GestorNoDisponible(ErrorDeCredencial):
    """La fuente no respondió (transitorio)."""


class ReferenciaInvalida(CredencialNoEncontrada):
    """La referencia es ambigua en su variable de dev (permanente)."""


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
    return PREFIJO_VARIABLE + _NO_ALFANUMERICO.sub(SEPARADOR, referencia.upper())


def referencia_valida(referencia):
    """`False` si la variable de la referencia tiene `__` o separadores en los
    extremos (ambigua con `__USUARIO` o con otra referencia)."""
    if not isinstance(referencia, str) or not referencia:
        return False
    sufijo = nombre_variable(referencia)[len(PREFIJO_VARIABLE):]
    return (SEPARADOR_DOBLE not in sufijo and not sufijo.startswith(SEPARADOR)
            and not sufijo.endswith(SEPARADOR))


VAR_REFERENCIA_BIND = 'LDAP_BIND_PASSWORD_REF'


def referencia_reservada(referencia, entorno=None):
    """`True` si `referencia` es la del bind LDAP (`LDAP_BIND_PASSWORD_REF`):
    esa contraseña nunca se entrega a un conector (B3 de FNC-068)."""
    entorno = os.environ if entorno is None else entorno
    reservada = (entorno.get(VAR_REFERENCIA_BIND) or '').strip()
    return bool(reservada) and isinstance(referencia, str) \
        and referencia.strip() == reservada


def referencias_en_conflicto(referencia, otras):
    """Referencias distintas de `referencia` que dan su misma variable."""
    variable = nombre_variable(referencia)
    return sorted({o for o in otras if isinstance(o, str) and o != referencia
                   and nombre_variable(o) == variable})


class ProveedorSecretosEntorno(ProveedorDeSecretos):
    """Solo desarrollo: la credencial sale del entorno (`.env`)."""

    fuente = FUENTE_ENTORNO

    def __init__(self, entorno=None):
        self._entorno = os.environ if entorno is None else entorno

    def obtener(self, referencia):
        if not referencia_valida(referencia):
            raise ReferenciaInvalida('Referencia ambigua para el entorno.')
        nombre = nombre_variable(referencia)
        secreto = self._entorno.get(nombre) or ''
        if not secreto:
            raise CredencialNoEncontrada('Sin variable para la referencia.')
        usuario = (self._entorno.get(nombre + SUFIJO_USUARIO) or '').strip()
        return Credencial(secreto=secreto, usuario=usuario or None)


class ProveedorSecretosVaultwarden(ProveedorDeSecretos):
    """Vaultwarden (ADR-005, alternativa A; FNC-068).

    Sin `cliente`, usa el compartido del proceso (`VAULTWARDEN_*`). Los errores
    del gestor se traducen sin la referencia ni el valor.
    """

    fuente = FUENTE_VAULTWARDEN

    def __init__(self, cliente=None):
        self._cliente = cliente

    def obtener(self, referencia):
        from app.modules.secretos import vaultwarden
        try:
            cliente = self._cliente or vaultwarden.cliente_del_entorno()
            item = cliente.leer(referencia)
        except vaultwarden.SecretoNoEncontrado:
            raise CredencialNoEncontrada(
                'Sin ítem único en Vaultwarden para la referencia.') from None
        except vaultwarden.GestorCaido:
            raise GestorNoDisponible('Vaultwarden no responde.') from None
        except vaultwarden.GestorMalConfigurado as exc:
            raise GestorNoConfigurado(
                f'Vaultwarden no configurado o rechazado: {exc}') from None
        return Credencial(secreto=item.secreto, usuario=item.usuario)


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
                self._acotar(momento)
                self._cache[clave] = (momento + vida, credencial)
        return credencial

    def _acotar(self, momento):
        """Quita las vencidas y, si sigue llena, la que vence antes."""
        for clave in [c for c, (vence, _) in self._cache.items()
                      if vence <= momento]:
            del self._cache[clave]
        while len(self._cache) >= MAXIMO_EN_CACHE:
            del self._cache[min(self._cache, key=lambda c: self._cache[c][0])]

    def limpiar(self):
        with self._candado:
            self._cache.clear()


_RESOLVEDOR = ResolvedorCredenciales()


def resolver_credencial(referencia):
    """Credencial de `referencia` desde la fuente del despliegue."""
    return _RESOLVEDOR.resolver(proveedor_de_secretos(), referencia)


def resolver_en_gestor(referencia):
    """Credencial de `referencia` siempre desde Vaultwarden (con la caché)."""
    return _RESOLVEDOR.resolver(ProveedorSecretosVaultwarden(), referencia)


def limpiar_cache():
    _RESOLVEDOR.limpiar()
