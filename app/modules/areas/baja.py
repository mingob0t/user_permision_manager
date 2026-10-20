"""Condiciones para dar de baja un área (FNC-045, P11 del dueño).

`409` si el área tiene plataformas o accesos vigentes
(`docs/contratos/areas-y-roles.md`).
"""

from app import db
from app.authz import is_area_admin
from app.modules.api.helpers import (AREA_CON_ACCESOS, AREA_CON_OTROS_ADMINS,
                                     AREA_CON_PLATAFORMAS)
from app.modules.audit.models import AuditLog

# Dialecto donde la FK `ON DELETE SET NULL` de `audit_logs` no se aplica.
DIALECTO_SIN_FK = 'sqlite'


def tiene_accesos_vigentes(area):
    """True si alguna plataforma del área tiene accesos otorgados vigentes
    (FNC-054, definición en `docs/contratos/accesos.md`).

    Sustituye la membresía en `user_areas` que FNC-045 usaba mientras no
    existían los accesos. Defensa en profundidad: hoy un acceso vigente
    implica una plataforma del área, que ya da `area_con_plataformas`.
    """
    from app.modules.access.consultas import area_tiene_vigentes
    return area_tiene_vigentes(area.id)


def tiene_otros_admins(area, actor):
    """True si `area` tiene admins de área además de `actor`."""
    return any(admin.id != actor.id for admin in (area.admins or []))


def conflicto_de_baja(area, actor):
    """Error que impide la baja, o None si se puede borrar.

    Decisión del orquestador (FNC-045, pendiente de validar en la prueba de
    concepto): un admin de área no borra un área que comparte con otros
    admins; el superadmin sí.
    """
    if is_area_admin(actor) and tiene_otros_admins(area, actor):
        return AREA_CON_OTROS_ADMINS
    if area.platforms:
        return AREA_CON_PLATAFORMAS
    if tiene_accesos_vigentes(area):
        return AREA_CON_ACCESOS
    return None


def desligar_auditoria(area):
    """Pone `area_id` en NULL en la auditoría que referencia `area`.

    Hace a mano lo que `ON DELETE SET NULL` hace en MySQL, para no depender
    de la FK (SQLite no la aplica sin `PRAGMA foreign_keys` y reutiliza ids).
    Va por la conexión de la sesión (misma transacción) y no por el ORM, que
    rechaza `UPDATE` en la auditoría (`inmutabilidad.py`); solo cambia la
    referencia, no el contenido del registro.
    """
    conexion = db.session.connection()
    # Solo SQLite: en MySQL la FK ya hace SET NULL y la app no tiene UPDATE en audit_logs (FNC-075).
    if conexion.dialect.name != DIALECTO_SIN_FK:
        return
    tabla = AuditLog.__table__
    conexion.execute(
        tabla.update().where(tabla.c.area_id == area.id).values(area_id=None))
