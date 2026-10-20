"""Valores enumerados y largos de las solicitudes (contrato `solicitudes.md` v1)."""

ESTADO_PENDIENTE = 'pendiente'
ESTADO_APROBADA = 'aprobada'
ESTADO_RECHAZADA = 'rechazada'
ESTADOS = (ESTADO_PENDIENTE, ESTADO_APROBADA, ESTADO_RECHAZADA)

# Valor de `slot_pendiente` mientras la solicitud está pendiente (NULL al
# decidirse: MySQL y SQLite admiten varios NULL en un índice único).
PENDIENTE = 1

# Justificación: el dueño decidió no pedirla (2026-10-20); si llega, ≤ 500.
ACCESS_REQUEST_JUSTIFICATION_MAX_LENGTH = 500

# Largos de columna.
LARGO_NIVEL = 10
LARGO_ESTADO = 20
LARGO_TEXTO = 500
