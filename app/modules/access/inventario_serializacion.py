"""Forma `Access` del contrato `accesos.md` para el inventario (FNC-059).

Provisional: FNC-058 trae `access/serializacion.py` (`accesos_publicos`), que
aún no está en develop. Al integrarse ambas, el inventario pasa a usarla y
este archivo se elimina (FNC-095). Fechas con `access_requests.serializacion
.fecha` (ISO 8601 en UTC con `Z`).
"""
from app.modules.access_requests.serializacion import fecha
from app.modules.auth.models import User


def _nombre(cuenta):
    return (cuenta.nombre or '').strip() or cuenta.email


def _actores(accesos):
    """`{id: {id, name}}` de quienes otorgaron o revocaron, en una consulta."""
    ids = {i for a in accesos for i in (a.granted_by, a.revoked_by) if i}
    if not ids:
        return {}
    return {c.id: {'id': c.id, 'name': _nombre(c)}
            for c in User.query.filter(User.id.in_(ids))}


def _acceso(acceso, actores):
    usuario, plataforma = acceso.user, acceso.platform
    area = plataforma.area
    return {
        'id': acceso.id,
        'status': acceso.status,
        'level': acceso.level,
        'origin': acceso.origin,
        'user': {'id': usuario.id, 'name': _nombre(usuario),
                 'email': usuario.email},
        'platform': {'id': plataforma.id, 'name': plataforma.name,
                     'integration_type': plataforma.integration_type},
        'area': {'id': area.id, 'name': area.name},
        'request_id': acceso.request_id,
        'granted_by': actores.get(acceso.granted_by),
        'granted_at': fecha(acceso.granted_at),
        'revoked_by': actores.get(acceso.revoked_by),
        'revoked_at': fecha(acceso.revoked_at),
        'revoke_reason': acceso.revoke_reason,
        'last_job_id': acceso.last_job_id,
    }


def accesos_publicos(accesos):
    actores = _actores(accesos)
    return [_acceso(a, actores) for a in accesos]
