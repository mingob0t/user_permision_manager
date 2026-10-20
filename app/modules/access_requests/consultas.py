"""Consultas de solicitudes para otros módulos (FNC-066)."""
from app.modules.access_requests.models import PlatformAccessRequest


def mias(usuario_id):
    """Query de las solicitudes de la cuenta (`GET /access-requests/mine` y
    el resumen del inicio), sin orden."""
    return PlatformAccessRequest.query.filter(
        PlatformAccessRequest.user_id == usuario_id)
