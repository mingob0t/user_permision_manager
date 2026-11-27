"""Motivo de la solicitud y del rechazo, configurables desde `.env` (FNC-216).

Pedido del dueño (2026-11-27): decidir desde el entorno si se pide motivo al
solicitar y al rechazar. Modifica RF-06 (el rechazo exigía motivo siempre).

- `SOLICITUD_MOTIVO`: `oculto` (por omisión; el campo se descarta), `opcional`
  u `obligatorio`.
- `RECHAZO_MOTIVO`: `obligatorio` (por omisión), `opcional` u `oculto` (el campo
  se descarta).
- Un valor distinto detiene el arranque (`validar_al_arrancar`), sin repetir
  el valor recibido.
"""
import os

MODO_OCULTO = 'oculto'
MODO_OPCIONAL = 'opcional'
MODO_OBLIGATORIO = 'obligatorio'
MODOS = (MODO_OCULTO, MODO_OPCIONAL, MODO_OBLIGATORIO)

VAR_SOLICITUD = 'SOLICITUD_MOTIVO'
VAR_RECHAZO = 'RECHAZO_MOTIVO'
SOLICITUD_POR_OMISION = MODO_OCULTO
RECHAZO_POR_OMISION = MODO_OBLIGATORIO


class ErrorConfiguracionMotivos(RuntimeError):
    """Variable de motivo con un valor no reconocido."""


def _modo(nombre, por_omision):
    valor = (os.getenv(nombre) or '').strip().lower()
    if not valor:
        return por_omision
    if valor not in MODOS:
        raise ErrorConfiguracionMotivos(
            f'{nombre} debe ser {", ".join(MODOS)}.')
    return valor


def modo_solicitud():
    """Modo vigente del motivo al solicitar."""
    return _modo(VAR_SOLICITUD, SOLICITUD_POR_OMISION)


def modo_rechazo():
    """Modo vigente del motivo al rechazar."""
    return _modo(VAR_RECHAZO, RECHAZO_POR_OMISION)


def como_dict():
    """Forma expuesta a la web (`GET /auth/context`, clave `motivos`)."""
    return {'solicitud': modo_solicitud(), 'rechazo': modo_rechazo()}


def validar_al_arrancar():
    """Un valor inválido detiene el arranque con un mensaje claro."""
    modo_solicitud()
    modo_rechazo()
