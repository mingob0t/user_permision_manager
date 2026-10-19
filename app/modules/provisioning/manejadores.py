"""Manejadores del resultado final de un trabajo (FNC-049).

- Quien encola (p. ej. FNC-054, accesos) registra `on_success` y
  `on_failure` para actualizar su estado sin que este módulo dependa de él.
- Se llaman con el `ProvisioningJob` ya en `exitoso` o `fallido`, **dentro de
  la transacción** del resultado (con la auditoría, SEC-AUD-06): no deben
  hacer `commit`. Si uno lanza, se revierte todo y el trabajo queda reservado
  hasta que vence la reserva y se reintenta (las operaciones son idempotentes).
"""

_AL_EXITO = []
_AL_FALLO = []


def registrar_manejador(on_success=None, on_failure=None):
    if on_success is not None and on_success not in _AL_EXITO:
        _AL_EXITO.append(on_success)
    if on_failure is not None and on_failure not in _AL_FALLO:
        _AL_FALLO.append(on_failure)


def quitar_manejadores():
    _AL_EXITO.clear()
    _AL_FALLO.clear()


def avisar_resultado(trabajo, exito):
    for manejador in tuple(_AL_EXITO if exito else _AL_FALLO):
        manejador(trabajo)
