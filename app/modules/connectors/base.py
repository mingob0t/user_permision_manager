"""Interfaz común de un tipo de conector (FNC-050, SEC-CON-01).

- Un conector implementa `otorgar` y `revocar`; `consultar` es opcional (sin
  implementarla devuelve un error permanente `consulta_no_disponible`).
- Devuelve el `ResultadoProveedor` tipado del ejecutor (FNC-049): `exitoso`,
  `sin_cambios` (idempotente), `error_transitorio` o `error_permanente`, con
  `permanente(...)`/`transitorio(...)` de `provisioning.providers`.
- Recibe solo datos del servidor (SEC-CON-03): la `SolicitudConector` con ids,
  operación y nivel enumerados y la cuenta del portal; el `Destino` (host de
  la lista blanca, puerto, parámetros validados y tiempo de espera) y la
  `Credencial` ya resuelta. Nunca guarda ni registra la credencial.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import MappingProxyType

from app.modules.provisioning.providers import permanente
from app.modules.provisioning.saneo import MOTIVO_CONSULTA_NO_DISPONIBLE


@dataclass(frozen=True)
class Destino:
    """Adónde se conecta el conector (sin secretos)."""

    host: str
    puerto: int
    params: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))
    tiempo_espera: int = 0


@dataclass(frozen=True)
class SolicitudConector:
    """Lo que el conector necesita para una operación.

    - `cuenta`: correo de la cuenta del portal, normalizado en minúsculas
      (dato del servidor, no del formulario).
    """

    id_operacion: str
    clave_idempotencia: str
    operacion: str
    nivel: str
    plataforma_id: int
    cuenta: str


class Conector(ABC):
    """Base de los tipos `noop`, `api`, `ssh` y `bd`."""

    def __init__(self, destino, credencial):
        self.destino = destino
        self.credencial = credencial

    @abstractmethod
    def otorgar(self, solicitud):
        """Da el acceso; idempotente (ya estaba = `sin_cambios`)."""

    @abstractmethod
    def revocar(self, solicitud):
        """Quita el acceso; idempotente (ya no estaba = `sin_cambios`)."""

    def consultar(self, solicitud):
        """Sin cambios; `presente` dice si la cuenta tiene el acceso."""
        return permanente(MOTIVO_CONSULTA_NO_DISPONIBLE)
