"""Registro de tipos de conector (FNC-050).

- Cada tipo se registra con su fábrica (`fabrica(destino, credencial)` →
  `Conector`) y la validación de sus `params` (`validar_params(params)` →
  `{campo: mensaje}`; vacío si son válidos).
- `noop` lo registra `connectors.registrar()` solo en dev y pruebas; `api`,
  `ssh` y `bd`, FNC-051 a FNC-053. Un tipo sin registrar no se acepta al
  configurar ni se ejecuta (`conector_no_disponible`).
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class TipoConector:
    nombre: str
    fabrica: Callable
    validar_params: Callable


_TIPOS = {}


def registrar_tipo(tipo):
    _TIPOS[tipo.nombre] = tipo


def quitar_tipo(nombre):
    _TIPOS.pop(nombre, None)


def obtener_tipo(nombre):
    """`TipoConector` registrado, o `None`."""
    return _TIPOS.get(nombre) if isinstance(nombre, str) else None


def tipos_disponibles():
    return tuple(sorted(_TIPOS))
