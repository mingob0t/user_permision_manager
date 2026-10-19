"""Condiciones para dar de baja un área (FNC-045, P11 del dueño).

`409` si el área tiene plataformas o accesos vigentes
(`docs/contratos/areas-y-roles.md`).
"""

from app.modules.api.helpers import AREA_CON_ACCESOS, AREA_CON_PLATAFORMAS


def tiene_accesos_vigentes(area):
    """True si alguna cuenta alcanza el área.

    Decisión del orquestador (FNC-045, pendiente de validar en la prueba de
    concepto): mientras no existan los accesos del gestor (FNC-054/056), un
    acceso vigente es la membresía en `user_areas`. Los admins del área
    (`area_admins`) no cuentan: la baja los retira.
    """
    return bool(area.area_users)


def conflicto_de_baja(area):
    """Error del contrato que impide la baja, o None si se puede borrar."""
    if area.platforms:
        return AREA_CON_PLATAFORMAS
    if tiene_accesos_vigentes(area):
        return AREA_CON_ACCESOS
    return None
