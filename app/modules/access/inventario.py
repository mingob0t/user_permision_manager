"""Consulta del inventario de permisos con el alcance del solicitante (FNC-059).

Contrato `accesos.md`, `GET /access/inventory` (F-AUD-02). Visibilidad (Anexo
A de `docs/seguridad/LINEAMIENTOS.md`, decisión del dueño):
- superadmin: todo;
- admin de área: los accesos de las plataformas de las áreas que administra;
- usuario: no tiene inventario (usa `/me/access`); la ruta responde 403.

Los filtros se suman (AND) al alcance: un filtro fuera de alcance da una
lista vacía, igual que en la auditoría (`audit.queries.filtrar`).
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import false, func, or_
from sqlalchemy.orm import joinedload

from app.authz import is_admin, is_area_admin, managed_area_ids
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import ESTADOS_VIGENTES
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform

# `status` del filtro que agrupa todos los estados vigentes (contrato).
ESTADO_VIGENTE = 'vigente'


@dataclass(frozen=True)
class FiltrosInventario:
    area_id: Optional[int] = None
    platform_id: Optional[int] = None
    user_id: Optional[int] = None
    level: Optional[str] = None
    origin: Optional[str] = None
    status: str = ESTADO_VIGENTE
    q: Optional[str] = None


def _base():
    return (PlatformAccessGrant.query
            .join(Platform, Platform.id == PlatformAccessGrant.platform_id)
            .join(Area, Area.id == Platform.area_id)
            .join(User, User.id == PlatformAccessGrant.user_id)
            .options(joinedload(PlatformAccessGrant.user),
                     joinedload(PlatformAccessGrant.platform)
                     .joinedload(Platform.area)))


def visibles(usuario):
    """Query de los accesos que `usuario` puede ver en el inventario."""
    consulta = _base()
    if is_admin(usuario):
        return consulta
    if is_area_admin(usuario):
        # in_([]) es SQL falso: sin áreas no ve nada.
        return consulta.filter(Platform.area_id.in_(managed_area_ids(usuario)))
    return consulta.filter(false())


def filtrar(consulta, filtros):
    if filtros.area_id:
        consulta = consulta.filter(Platform.area_id == filtros.area_id)
    if filtros.platform_id:
        consulta = consulta.filter(
            PlatformAccessGrant.platform_id == filtros.platform_id)
    if filtros.user_id:
        consulta = consulta.filter(
            PlatformAccessGrant.user_id == filtros.user_id)
    if filtros.level:
        consulta = consulta.filter(PlatformAccessGrant.level == filtros.level)
    if filtros.origin:
        consulta = consulta.filter(PlatformAccessGrant.origin == filtros.origin)
    if filtros.status == ESTADO_VIGENTE:
        consulta = consulta.filter(
            PlatformAccessGrant.status.in_(ESTADOS_VIGENTES))
    else:
        consulta = consulta.filter(PlatformAccessGrant.status == filtros.status)
    if filtros.q:
        texto = filtros.q.lower()
        consulta = consulta.filter(or_(
            func.lower(User.nombre).contains(texto, autoescape=True),
            func.lower(User.email).contains(texto, autoescape=True)))
    return consulta


def ordenados(consulta):
    """Orden del contrato: área, plataforma, usuario (e `id` para desempatar)."""
    return consulta.order_by(Area.name, Platform.name, User.email,
                             PlatformAccessGrant.id)
