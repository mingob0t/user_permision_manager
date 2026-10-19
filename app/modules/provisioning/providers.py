"""Interfaz de proveedores de aprovisionamiento y su registro (FNC-049).

- Todo proveedor implementa `otorgar`, `revocar` y `consultar` con una
  `Operacion` (lleva el `id_operacion`) y devuelve un `ResultadoProveedor`
  tipado (SEC-CON-01). No debe lanzar: el ejecutor igual convierte cualquier
  excepción en error transitorio sin guardar su texto.
- La `Operacion` lleva solo datos del servidor: ids, nivel y operación
  enumerados; nunca texto del usuario (SEC-CON-03).
- Registro por tipo de integración: `ldap` lo registra este módulo
  (`__init__.py`); los conectores los registra FNC-050. Un tipo sin
  proveedor da `conector_no_disponible` (permanente), sin reintentos.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.modules.provisioning.tipos import (RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADOS, RESULTADOS_EXITO)


@dataclass(frozen=True)
class Operacion:
    """Lo que el proveedor necesita para ejecutar un trabajo."""

    id_operacion: str
    clave_idempotencia: str
    operacion: str
    nivel: str
    plataforma_id: int | None
    usuario_id: int | None
    acceso_id: int | None = None


@dataclass(frozen=True)
class ResultadoProveedor:
    """Resultado de una llamada al proveedor.

    - `motivo`: código corto del catálogo de `saneo.py` si hubo error.
    - `detalle`: texto opcional del proveedor; se guarda saneado.
    - `presente`: solo en `consultar` (si la persona tiene el acceso).
    """

    resultado: str
    motivo: str | None = None
    detalle: str | None = None
    presente: bool | None = None

    def __post_init__(self):
        if self.resultado not in RESULTADOS:
            raise ValueError(f'Resultado desconocido: {self.resultado}')

    @property
    def exito(self):
        return self.resultado in RESULTADOS_EXITO

    @property
    def reintentable(self):
        return self.resultado == RESULTADO_ERROR_TRANSITORIO


def permanente(motivo, detalle=None):
    return ResultadoProveedor(RESULTADO_ERROR_PERMANENTE, motivo, detalle)


def transitorio(motivo, detalle=None):
    return ResultadoProveedor(RESULTADO_ERROR_TRANSITORIO, motivo, detalle)


class Provisioner(ABC):
    """Contrato de un proveedor (LDAP o conector)."""

    @abstractmethod
    def otorgar(self, operacion):
        """Da el acceso; idempotente (ya otorgado = `sin_cambios`)."""

    @abstractmethod
    def revocar(self, operacion):
        """Quita el acceso; idempotente (ya ausente = `sin_cambios`)."""

    @abstractmethod
    def consultar(self, operacion):
        """Consulta sin cambios; `presente` dice si la persona tiene el acceso."""


_PROVEEDORES = {}


def registrar_proveedor(tipo, fabrica):
    """`fabrica()` devuelve un `Provisioner` para el tipo de integración."""
    _PROVEEDORES[tipo] = fabrica


def quitar_proveedor(tipo):
    _PROVEEDORES.pop(tipo, None)


def obtener_proveedor(tipo):
    """Proveedor del tipo, o `None` si no hay ninguno registrado."""
    fabrica = _PROVEEDORES.get(tipo)
    return fabrica() if fabrica else None
