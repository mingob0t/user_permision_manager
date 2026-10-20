"""Consultas de auditoría con el alcance del solicitante (FNC-060).

Visibilidad (Anexo A de `docs/seguridad/LINEAMIENTOS.md`, SEG-16):
- superadmin: todo;
- admin de área: solo eventos con `area_id` en las áreas que administra; los
  eventos sin área solo los ve el superadmin;
- usuario: los propios (actor o usuario afectado).

Toda consulta de auditoría hacia el cliente parte de `visibles()`.
"""

from sqlalchemy import false, or_
from sqlalchemy.orm import selectinload

from app.authz import is_admin, is_area_admin, managed_area_ids
from app.modules.audit.models import AuditLog

ESCAPE_LIKE = '\\'


def de_usuario(usuario_id):
    """Eventos donde la cuenta es actor o usuario afectado, solo por id.

    Sin coincidencia por correo (SEG-060-01): al borrar una cuenta `actor_id`
    queda en NULL y el correo puede pasar a otra persona. Los registros
    anteriores a FNC-047 (sin `actor_id`) solo los ve el superadmin.
    """
    return or_(AuditLog.actor_id == usuario_id,
               AuditLog.target_user_id == usuario_id)


def de_plataforma(plataforma_id):
    """Eventos de una plataforma."""
    return AuditLog.platform_id == plataforma_id


def visibles(usuario):
    """Query de los eventos que `usuario` puede ver."""
    consulta = AuditLog.query.options(
        selectinload(AuditLog.actor), selectinload(AuditLog.target_user),
        selectinload(AuditLog.area), selectinload(AuditLog.platform))
    if is_admin(usuario):
        return consulta
    if is_area_admin(usuario):
        # in_([]) es SQL falso: sin áreas no ve nada.
        return consulta.filter(AuditLog.area_id.in_(managed_area_ids(usuario)))
    if usuario is not None and usuario.is_authenticated:
        return consulta.filter(de_usuario(usuario.id))
    return consulta.filter(false())


def _como_patron(texto):
    escapado = (texto.replace(ESCAPE_LIKE, ESCAPE_LIKE * 2)
                .replace('%', ESCAPE_LIKE + '%').replace('_', ESCAPE_LIKE + '_'))
    return f'%{escapado}%'


def filtrar(consulta, filtros):
    """Aplica los filtros del contrato; fuera de alcance quedan vacíos porque
    se suman (AND) al alcance de `visibles()`."""
    if filtros.action:
        consulta = consulta.filter(AuditLog.action == filtros.action)
    if filtros.result:
        consulta = consulta.filter(AuditLog.status == filtros.result)
    if filtros.area_id:
        consulta = consulta.filter(AuditLog.area_id == filtros.area_id)
    if filtros.platform_id:
        consulta = consulta.filter(AuditLog.platform_id == filtros.platform_id)
    if filtros.user_id:
        consulta = consulta.filter(de_usuario(filtros.user_id))
    if filtros.desde:
        consulta = consulta.filter(AuditLog.timestamp >= filtros.desde)
    if filtros.hasta:
        consulta = consulta.filter(AuditLog.timestamp < filtros.hasta)
    if filtros.q:
        patron = _como_patron(filtros.q)
        consulta = consulta.filter(or_(
            AuditLog.user.ilike(patron, escape=ESCAPE_LIKE),
            AuditLog.target.ilike(patron, escape=ESCAPE_LIKE)))
    return consulta


def ordenados(consulta):
    """Orden fijo del contrato: `time` descendente (y `id` para desempatar)."""
    return consulta.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
