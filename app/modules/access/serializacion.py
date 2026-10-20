"""Forma `Access` del contrato `accesos.md` (FNC-058; la reutiliza FNC-059).

- Fechas en UTC sin zona en la BD (`provisioning.reloj.ahora`): se envían en
  ISO 8601 con `Z`.
- `granted_by`/`revoked_by` se resuelven en una sola consulta por página.
- `last_job_id` se omite cuando quien consulta es del rol usuario.
"""
from app.modules.auth.models import User

SUFIJO_UTC = 'Z'


def _fecha_utc(valor):
    return f'{valor.isoformat()}{SUFIJO_UTC}' if valor else None


def _persona(cuenta):
    return {'id': cuenta.id, 'name': cuenta.nombre or cuenta.email}


def _actores(accesos):
    ids = {i for a in accesos for i in (a.granted_by, a.revoked_by) if i}
    if not ids:
        return {}
    return {c.id: _persona(c) for c in User.query.filter(User.id.in_(ids))}


def acceso_publico(acceso, actores, con_trabajo=True):
    usuario, plataforma = acceso.user, acceso.platform
    area = plataforma.area
    datos = {
        'id': acceso.id,
        'status': acceso.status,
        'level': acceso.level,
        'origin': acceso.origin,
        'user': {'id': usuario.id, 'name': usuario.nombre or usuario.email,
                 'email': usuario.email},
        'platform': {'id': plataforma.id, 'name': plataforma.name,
                     'integration_type': plataforma.integration_type},
        'area': {'id': area.id, 'name': area.name} if area else None,
        'request_id': acceso.request_id,
        'granted_by': actores.get(acceso.granted_by),
        'granted_at': _fecha_utc(acceso.granted_at),
        'revoked_by': actores.get(acceso.revoked_by),
        'revoked_at': _fecha_utc(acceso.revoked_at),
        'revoke_reason': acceso.revoke_reason,
    }
    if con_trabajo:
        datos['last_job_id'] = acceso.last_job_id
    return datos


def accesos_publicos(accesos, con_trabajo=True):
    actores = _actores(accesos)
    return [acceso_publico(a, actores, con_trabajo) for a in accesos]
