"""Conector de prueba `noop` (FNC-050): solo dev y pruebas.

- No se conecta a nada: guarda en memoria del proceso qué cuentas tienen cada
  nivel de cada plataforma, para recorrer otorgar → consultar → revocar con
  el ejecutor. Idempotente (`sin_cambios`).
- No admite parámetros.
"""
import threading

from app.modules.connectors.base import Conector
from app.modules.connectors.registry import TipoConector
from app.modules.connectors.tipos import TIPO_NOOP
from app.modules.provisioning.providers import ResultadoProveedor
from app.modules.provisioning.tipos import (RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)

MENSAJE_SIN_PARAMS = 'El conector de prueba no admite parámetros.'

_CUENTAS = set()
_CANDADO = threading.Lock()


def _clave(solicitud):
    return (solicitud.plataforma_id, solicitud.nivel, solicitud.cuenta)


class ConectorNoop(Conector):

    def otorgar(self, solicitud):
        with _CANDADO:
            if _clave(solicitud) in _CUENTAS:
                return ResultadoProveedor(RESULTADO_SIN_CAMBIOS)
            _CUENTAS.add(_clave(solicitud))
        return ResultadoProveedor(RESULTADO_EXITOSO)

    def revocar(self, solicitud):
        with _CANDADO:
            if _clave(solicitud) not in _CUENTAS:
                return ResultadoProveedor(RESULTADO_SIN_CAMBIOS)
            _CUENTAS.discard(_clave(solicitud))
        return ResultadoProveedor(RESULTADO_EXITOSO)

    def consultar(self, solicitud):
        with _CANDADO:
            presente = _clave(solicitud) in _CUENTAS
        return ResultadoProveedor(RESULTADO_EXITOSO, presente=presente)


def validar_params(params):
    return {str(clave): MENSAJE_SIN_PARAMS for clave in params}


TIPO = TipoConector(TIPO_NOOP, ConectorNoop, validar_params)


def limpiar():
    with _CANDADO:
        _CUENTAS.clear()
