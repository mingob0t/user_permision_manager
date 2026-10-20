"""Resumen del inicio por rol (FNC-066, contrato `docs/contratos/inicio.md`).

Solo cuenta; no define alcances propios. Cada contador parte de la consulta
que ya aplica el alcance del rol:
- mis accesos: `access.consultas.de_usuario`;
- mis solicitudes: `access_requests.consultas.mias`;
- pendientes por aprobar: `access_requests.approvals.bandeja` (el mismo
  total que `GET /access-requests/inbox`);
- accesos fallidos y activos: `access.inventario.visibles` (el mismo alcance
  que `GET /access/inventory`);
- áreas: `authz.scoped_areas`.

Alcance (`scope`): `propio` (usuario), `areas` (admin de área), `global`
(superadmin). Los campos que no aplican al rol se omiten.

Decisiones del orquestador (pendientes de validar en la prueba de concepto):
- El superadmin no recibe `my_access` ni `my_requests` (contrato): tiene
  acceso por defecto y no solicita (P6).
- `totals.platforms` del admin: las plataformas de las áreas que administra
  (no las de sus accesos en otras áreas, que no son "sus áreas").
- `totals.areas` y `totals.platforms` cuentan también las inactivas, igual
  que `GET /stats`.
- Solo conteos y una fecha: sin listas ni nombres, para no exponer datos de
  otras cuentas en el inicio.
"""
from sqlalchemy import func

from app.authz import is_admin, is_area_admin, managed_area_ids, scoped_areas
from app.modules.access import consultas as consultas_acceso
from app.modules.access import inventario
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO,
                                      ESTADO_FALLIDO, ESTADO_FALLO_REVOCACION)
from app.modules.access_requests import approvals
from app.modules.access_requests import consultas as consultas_solicitud
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.serializacion import fecha
from app.modules.access_requests.tipos import ESTADO_PENDIENTE, ESTADOS
from app.modules.core.models import Platform

ALCANCE_PROPIO = 'propio'
ALCANCE_AREAS = 'areas'
ALCANCE_GLOBAL = 'global'

# Estados de "mis accesos" (contrato).
ESTADOS_MIS_ACCESOS = (ESTADO_ACTIVO, ESTADO_EN_PROCESO, ESTADO_FALLIDO)
# `failed_access`: el alta o la revocación fallaron (contrato).
ESTADOS_FALLIDOS = (ESTADO_FALLIDO, ESTADO_FALLO_REVOCACION)


def _por_estado(consulta, columna, estados):
    """`{estado: total}` con cero para los estados sin registros."""
    filas = (consulta.order_by(None).with_entities(columna, func.count())
             .group_by(columna).all())
    totales = dict(filas)
    return {estado: totales.get(estado, 0) for estado in estados}


def _propio(usuario):
    accesos = consultas_acceso.de_usuario(usuario.id, ESTADOS_MIS_ACCESOS)
    solicitudes = consultas_solicitud.mias(usuario.id)
    return {
        'my_access': _por_estado(accesos, PlatformAccessGrant.status,
                                 ESTADOS_MIS_ACCESOS),
        'my_requests': _por_estado(solicitudes, PlatformAccessRequest.status,
                                   ESTADOS),
    }


def _contar_accesos(usuario, estados):
    return (inventario.visibles(usuario).order_by(None)
            .filter(PlatformAccessGrant.status.in_(estados)).count())


def _plataformas(usuario):
    if is_admin(usuario):
        return Platform.query
    return Platform.query.filter(
        Platform.area_id.in_(managed_area_ids(usuario)))


def _administracion(usuario):
    pendientes = approvals.bandeja(usuario).filter(
        PlatformAccessRequest.status == ESTADO_PENDIENTE).order_by(None)
    total, mas_antigua = pendientes.with_entities(
        func.count(PlatformAccessRequest.id),
        func.min(PlatformAccessRequest.created_at)).one()
    return {
        'pending_approvals': total,
        'failed_access': _contar_accesos(usuario, ESTADOS_FALLIDOS),
        'oldest_pending_at': fecha(mas_antigua),
        'totals': {
            'areas': scoped_areas(usuario).count(),
            'platforms': _plataformas(usuario).count(),
            'active_access': _contar_accesos(usuario, (ESTADO_ACTIVO,)),
        },
    }


def resumen(usuario):
    """Contadores del inicio con el alcance del rol de `usuario`."""
    if is_admin(usuario):
        return {'scope': ALCANCE_GLOBAL, **_administracion(usuario)}
    if is_area_admin(usuario):
        return {'scope': ALCANCE_AREAS, **_propio(usuario),
                **_administracion(usuario)}
    return {'scope': ALCANCE_PROPIO, **_propio(usuario)}
