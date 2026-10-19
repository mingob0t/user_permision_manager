"""Condiciones para dar de baja un área (FNC-045, P11 del dueño).

`409` si el área tiene plataformas o accesos vigentes
(`docs/contratos/areas-y-roles.md`).
"""

from app import db
from app.authz import is_area_admin
from app.modules.api.helpers import (AREA_CON_ACCESOS, AREA_CON_OTROS_ADMINS,
                                     AREA_CON_PLATAFORMAS)
from app.modules.audit.models import AuditLog


def tiene_accesos_vigentes(area):
    """True si alguna cuenta alcanza el área.

    Decisión del orquestador (FNC-045, pendiente de validar en la prueba de
    concepto): mientras no existan los accesos del gestor (FNC-054/056), un
    acceso vigente es la membresía en `user_areas`. Los admins del área
    (`area_admins`) no cuentan: la baja los retira.
    """
    return bool(area.area_users)


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
    tabla = AuditLog.__table__
    db.session.connection().execute(
        tabla.update().where(tabla.c.area_id == area.id).values(area_id=None))
