"""Configuración del ejecutor de aprovisionamiento (FNC-049).

- Variables `PROVISIONING_*` registradas en `docs/configuracion/VARIABLES.md`.
- `validar_al_arrancar()` corre en `create_app()`: un valor inválido o fuera
  de rango detiene el arranque con un mensaje claro.
- Redis (ADR-003): el worker exige `REDIS_PASS` (SEG-29); la app web solo lo
  usa para despertar al worker y, sin él, el trabajo espera al barrido.
"""
import os
import re
from dataclasses import dataclass

from app.modules.directory.configuracion import es_ip_literal

VAR_COLA = 'PROVISIONING_QUEUE_NAME'
VAR_MAX_INTENTOS = 'PROVISIONING_MAX_ATTEMPTS'
VAR_BACKOFF_BASE = 'PROVISIONING_BACKOFF_BASE_SECONDS'
VAR_BACKOFF_MAX = 'PROVISIONING_BACKOFF_MAX_SECONDS'
VAR_TIEMPO_INTENTO = 'PROVISIONING_ATTEMPT_TIMEOUT_SECONDS'
VAR_INTERVALO_BARRIDO = 'PROVISIONING_POLL_INTERVAL_SECONDS'

VAR_REDIS_HOST = 'REDIS_HOST'
VAR_REDIS_PORT = 'REDIS_PORT'
VAR_REDIS_PASS = 'REDIS_PASS'
REDIS_HOST_POR_DEFECTO = 'localhost'
REDIS_PORT_POR_DEFECTO = 6379

COLA_POR_DEFECTO = 'aprovisionamiento'
PATRON_COLA = re.compile(r'[a-z0-9_-]{1,50}')

# (por defecto, mínimo, máximo) de cada entero.
MAX_INTENTOS = (5, 1, 20)
BACKOFF_BASE_SEGUNDOS = (60, 1, 3600)
BACKOFF_MAX_SEGUNDOS = (900, 1, 86400)
TIEMPO_INTENTO_SEGUNDOS = (60, 5, 600)
INTERVALO_BARRIDO_SEGUNDOS = (30, 5, 3600)

# Una reserva vence si el worker no cerró el intento en su tiempo de espera
# más este margen (worker caído a mitad): otro worker la retoma.
MARGEN_RESERVA_SEGUNDOS = 30


class ErrorConfiguracionAprovisionamiento(RuntimeError):
    """Variable `PROVISIONING_*` o de Redis inválida o faltante."""


@dataclass(frozen=True)
class ConfiguracionAprovisionamiento:
    cola: str
    max_intentos: int
    backoff_base: int
    backoff_max: int
    tiempo_intento: int
    intervalo_barrido: int

    @property
    def vencimiento_reserva(self):
        return self.tiempo_intento + MARGEN_RESERVA_SEGUNDOS


@dataclass(frozen=True)
class ConfiguracionRedis:
    host: str
    puerto: int
    contrasena: str | None = None

    def __repr__(self):  # la contraseña nunca sale en logs
        return f'ConfiguracionRedis(host={self.host!r}, puerto={self.puerto})'


def _leer(entorno, nombre):
    return (entorno.get(nombre) or '').strip()


def _entero(entorno, nombre, limites):
    por_defecto, minimo, maximo = limites
    texto = _leer(entorno, nombre)
    if not texto:
        return por_defecto
    try:
        valor = int(texto)
    except ValueError:
        raise ErrorConfiguracionAprovisionamiento(
            f'{nombre} debe ser un entero.') from None
    if not minimo <= valor <= maximo:
        raise ErrorConfiguracionAprovisionamiento(
            f'{nombre} debe estar entre {minimo} y {maximo}.')
    return valor


def cargar_configuracion(entorno=None):
    """Lee y valida `PROVISIONING_*`; lanza `ErrorConfiguracionAprovisionamiento`."""
    entorno = os.environ if entorno is None else entorno
    cola = _leer(entorno, VAR_COLA) or COLA_POR_DEFECTO
    if not PATRON_COLA.fullmatch(cola):
        raise ErrorConfiguracionAprovisionamiento(
            f'{VAR_COLA} solo admite minúsculas, dígitos, "_" y "-" (≤ 50).')
    base = _entero(entorno, VAR_BACKOFF_BASE, BACKOFF_BASE_SEGUNDOS)
    maximo = _entero(entorno, VAR_BACKOFF_MAX, BACKOFF_MAX_SEGUNDOS)
    if maximo < base:
        raise ErrorConfiguracionAprovisionamiento(
            f'{VAR_BACKOFF_MAX} no puede ser menor que {VAR_BACKOFF_BASE}.')
    return ConfiguracionAprovisionamiento(
        cola=cola,
        max_intentos=_entero(entorno, VAR_MAX_INTENTOS, MAX_INTENTOS),
        backoff_base=base,
        backoff_max=maximo,
        tiempo_intento=_entero(entorno, VAR_TIEMPO_INTENTO,
                               TIEMPO_INTENTO_SEGUNDOS),
        intervalo_barrido=_entero(entorno, VAR_INTERVALO_BARRIDO,
                                  INTERVALO_BARRIDO_SEGUNDOS),
    )


def validar_al_arrancar(entorno=None):
    return cargar_configuracion(entorno)


def configuracion_redis(entorno=None):
    """Conexión a Redis desde `REDIS_*`.

    Lanza si falta `REDIS_PASS` (SEG-29) o si `REDIS_HOST` es una IP (solo
    nombres de host).
    """
    entorno = os.environ if entorno is None else entorno
    contrasena = _leer(entorno, VAR_REDIS_PASS) or None
    if not contrasena:
        raise ErrorConfiguracionAprovisionamiento(
            f'{VAR_REDIS_PASS} es obligatoria para la cola de '
            'aprovisionamiento (Redis con contraseña, SEG-29).')
    texto_puerto = _leer(entorno, VAR_REDIS_PORT)
    try:
        puerto = int(texto_puerto) if texto_puerto else REDIS_PORT_POR_DEFECTO
    except ValueError:
        raise ErrorConfiguracionAprovisionamiento(
            f'{VAR_REDIS_PORT} debe ser un entero.') from None
    host = _leer(entorno, VAR_REDIS_HOST) or REDIS_HOST_POR_DEFECTO
    if es_ip_literal(host):
        raise ErrorConfiguracionAprovisionamiento(
            f'{VAR_REDIS_HOST} debe ser un nombre de host, no una IP.')
    return ConfiguracionRedis(host=host, puerto=puerto, contrasena=contrasena)
