"""Configuración del conector `bd` (FNC-053).

- `CONNECTOR_DB_TIMEOUT_SECONDS`: tiempo máximo de la conexión y de cada
  consulta contra la base de datos de la plataforma. Conectar y consultar
  pueden usar uno cada una: el doble debe ser menor que
  `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS`, para que el conector corte antes que
  RQ.
- `CONNECTOR_DB_CA_FILE`: archivo PEM con la CA que firma el certificado de las
  bases de datos de las plataformas; vacío = CA del sistema. La verificación
  TLS (certificado y nombre del host) es siempre obligatoria.
- `validar_al_arrancar()` corre en `connectors.registrar()` (`create_app()`).
"""
import os
from dataclasses import dataclass

from app.modules.connectors.configuracion import (ErrorConfiguracionConectores,
                                                  _entero, _leer)
from app.modules.provisioning.configuracion import \
    cargar_configuracion as cargar_aprovisionamiento

VAR_TIEMPO_BD = 'CONNECTOR_DB_TIMEOUT_SECONDS'
VAR_CA_BD = 'CONNECTOR_DB_CA_FILE'

# (por defecto, mínimo, máximo).
TIEMPO_BD_SEGUNDOS = (10, 1, 120)
# Conectar y consultar: cada uno puede llegar al tiempo máximo.
ETAPAS_CON_TIEMPO = 2


@dataclass(frozen=True)
class ConfiguracionBd:
    tiempo: int
    archivo_ca: str


def cargar_configuracion_bd(entorno=None):
    """Lee y valida `CONNECTOR_DB_*`; lanza `ErrorConfiguracionConectores`."""
    entorno = os.environ if entorno is None else entorno
    tiempo = _entero(entorno, VAR_TIEMPO_BD, TIEMPO_BD_SEGUNDOS)
    intento = cargar_aprovisionamiento(entorno).tiempo_intento
    if tiempo * ETAPAS_CON_TIEMPO >= intento:
        raise ErrorConfiguracionConectores(
            f'El doble de {VAR_TIEMPO_BD} debe ser menor que '
            f'PROVISIONING_ATTEMPT_TIMEOUT_SECONDS ({intento}).')
    return ConfiguracionBd(tiempo=tiempo,
                           archivo_ca=_leer(entorno, VAR_CA_BD))


def validar_al_arrancar(entorno=None):
    return cargar_configuracion_bd(entorno)
