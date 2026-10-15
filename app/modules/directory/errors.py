"""Resultado tipificado de la escritura en el directorio (FNC-041).

El ejecutor (FNC-049) decide con `reintentable` si vuelve a intentar:
- éxito: `HECHO` (se escribió) o `YA_ESTABA` (sin cambios; idempotencia, SEC-LDAP-08);
- `ERROR_TRANSITORIO`: red, tiempo de espera o servidor ocupado; se reintenta;
- `NO_EXISTE` y `ERROR_PERMANENTE`: no se reintentan.
"""
from dataclasses import dataclass
from enum import Enum

from ldap3.core.exceptions import (LDAPAdminLimitExceededResult,
                                   LDAPBusyResult, LDAPCommunicationError,
                                   LDAPMaximumRetriesError,
                                   LDAPNoSuchObjectResult,
                                   LDAPResponseTimeoutError,
                                   LDAPTimeLimitExceededResult,
                                   LDAPUnavailableResult)


class Resultado(str, Enum):
    HECHO = 'hecho'
    YA_ESTABA = 'ya_estaba'
    NO_EXISTE = 'no_existe'
    ERROR_TRANSITORIO = 'error_transitorio'
    ERROR_PERMANENTE = 'error_permanente'

    @property
    def exito(self):
        return self in (Resultado.HECHO, Resultado.YA_ESTABA)

    @property
    def reintentable(self):
        return self is Resultado.ERROR_TRANSITORIO


# Errores de `ldap3` que se reintentan: red, tiempo de espera y servidor
# ocupado o no disponible. El resto (permisos, esquema, DN, credencial, TLS)
# es permanente.
ERRORES_TRANSITORIOS = (
    LDAPCommunicationError,        # socket: abrir, enviar, recibir, sesión cortada
    LDAPResponseTimeoutError,
    LDAPMaximumRetriesError,
    LDAPBusyResult,
    LDAPUnavailableResult,
    LDAPTimeLimitExceededResult,
    LDAPAdminLimitExceededResult,
)

# Motivos (códigos cortos, sin datos de la persona) para el ejecutor y el log.
MOTIVO_FUERA_DE_BASE = 'fuera_de_base'
MOTIVO_GRUPO_INEXISTENTE = 'grupo_inexistente'
MOTIVO_USUARIO_INEXISTENTE = 'usuario_inexistente'
MOTIVO_ULTIMO_MIEMBRO = 'ultimo_miembro'
MOTIVO_DATOS_INCOMPLETOS = 'datos_incompletos'
MOTIVO_DATOS_INVALIDOS = 'datos_invalidos'
MOTIVO_DIRECTORIO = 'directorio'


@dataclass(frozen=True)
class ResultadoEscritura:
    """Resultado de una operación: estado, DN afectado y motivo si falló."""

    resultado: Resultado
    dn: str
    motivo: str | None = None

    @property
    def exito(self):
        return self.resultado.exito

    @property
    def reintentable(self):
        return self.resultado.reintentable


def clasificar_error(excepcion):
    """Tipo de resultado de una excepción de `ldap3` (o `None`: permanente)."""
    if isinstance(excepcion, LDAPNoSuchObjectResult):
        return Resultado.NO_EXISTE
    if isinstance(excepcion, ERRORES_TRANSITORIOS):
        return Resultado.ERROR_TRANSITORIO
    return Resultado.ERROR_PERMANENTE
