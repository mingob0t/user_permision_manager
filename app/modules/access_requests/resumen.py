"""Resumen de la bandeja de solicitudes (FNC-200, contrato `solicitudes.md` 1.3).

Mismo alcance que `approvals.bandeja` (todos los estados) con consultas
agregadas: no se cargan las filas de las solicitudes.
"""
from sqlalchemy import func

from app.modules.access_requests import approvals
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.tipos import ESTADO_PENDIENTE, ESTADOS
from app.modules.core.models import Area, Platform


def _orden(fila):
    """Más solicitudes primero; a igual número, por nombre."""
    return (-fila['count'], fila['nombre'].casefold())


def _por_area(consulta, cuenta):
    """Filas `{area_id, area, count}` con `count > 0`, en el orden de `_orden`."""
    filas = (consulta.join(Area, Area.id == Platform.area_id)
             .with_entities(Area.id, Area.name, cuenta)
             .group_by(Area.id, Area.name).all())
    return sorted(
        ({'area_id': i, 'area': nombre, 'count': int(n), 'nombre': nombre}
         for i, nombre, n in filas if n > 0), key=_orden)


def _por_plataforma(consulta, cuenta, con_area_id=False):
    """Filas `{platform_id, platform, [area_id,] area, count}`, `count > 0`.

    `by_platform` no lleva `area_id` (forma de la 1.3); `pending_by_platform`
    sí (FNC-219).
    """
    filas = (consulta.join(Area, Area.id == Platform.area_id)
             .with_entities(Platform.id, Platform.name, Area.id, Area.name,
                            cuenta)
             .group_by(Platform.id, Platform.name, Area.id, Area.name).all())
    return sorted(
        ({'platform_id': i, 'platform': nombre,
          **({'area_id': area_id} if con_area_id else {}),
          'area': area, 'count': int(n), 'nombre': nombre}
         for i, nombre, area_id, area, n in filas if n > 0), key=_orden)


def resumen(actor):
    """Totales de las solicitudes que `actor` puede decidir."""
    alcance = approvals.bandeja(actor).order_by(None)
    cuenta = func.count(PlatformAccessRequest.id)

    por_estado = dict(alcance.with_entities(
        PlatformAccessRequest.status, cuenta)
        .group_by(PlatformAccessRequest.status).all())
    by_status = {estado: int(por_estado.get(estado, 0)) for estado in ESTADOS}

    by_area = _por_area(alcance, cuenta)
    # Por aprobar en cada área: la tarjeta de área enlaza a la bandeja (FNC-212).
    pending_by_area = _por_area(
        alcance.filter(PlatformAccessRequest.status == ESTADO_PENDIENTE),
        cuenta)

    by_platform = _por_plataforma(alcance, cuenta)
    # Por aprobar en cada plataforma (FNC-219).
    pending_by_platform = _por_plataforma(
        alcance.filter(PlatformAccessRequest.status == ESTADO_PENDIENTE),
        cuenta, con_area_id=True)

    for fila in by_area + pending_by_area + by_platform + pending_by_platform:
        del fila['nombre']
    return {'total': sum(by_status.values()), 'by_status': by_status,
            'by_area': by_area, 'by_platform': by_platform,
            'pending_by_area': pending_by_area,
            'pending_by_platform': pending_by_platform}
