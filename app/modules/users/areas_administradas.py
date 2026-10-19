"""Áreas que administra un `admin_area` (tabla `area_admins`, FNC-044).

Contrato: `PUT /users/<id>/managed-areas` en `docs/contratos/areas-y-roles.md`.
Solo el superadmin las asigna (SEC-AUTHZ-05); la ruta vive en `api.py`.
"""

from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.core.models import Area
from app.modules.users.roles import MODULO_AUDITORIA

MAX_AREAS_ADMINISTRADAS = 50
CAMPO_AREAS = 'area_ids'


def validar_area_ids(valor):
    """(ids, None) si `valor` cumple el contrato; si no, (None, mensaje).

    Regla: lista de 0 a 50 enteros sin repetidos, todos de áreas existentes.
    """
    if not isinstance(valor, list):
        return None, 'Debe ser una lista de áreas.'
    if len(valor) > MAX_AREAS_ADMINISTRADAS:
        return None, f'Máximo {MAX_AREAS_ADMINISTRADAS} áreas.'
    # bool es subclase de int: true/false no son identificadores.
    if any(isinstance(i, bool) or not isinstance(i, int) for i in valor):
        return None, 'Cada área debe ser un identificador numérico.'
    if len(set(valor)) != len(valor):
        return None, 'Hay áreas repetidas.'
    existentes = {a.id for a in Area.query.filter(Area.id.in_(valor))}
    if existentes != set(valor):
        return None, 'Hay áreas que no existen.'
    return valor, None


def asignar_areas_administradas(cuenta, area_ids):
    """Reemplaza las áreas administradas de `cuenta` y audita cada cambio.

    No confirma: quien llama guarda el cambio y su auditoría en una sola
    transacción (SEC-AUD-06). Registra `admin_asignado` por área agregada y
    `admin_retirado` por área quitada.
    """
    antes = {a.id: a for a in (cuenta.managed_areas or [])}
    nuevas = Area.query.filter(Area.id.in_(area_ids)).all() if area_ids else []
    despues = {a.id: a for a in nuevas}
    cuenta.managed_areas = nuevas

    for area_id in sorted(set(despues) - set(antes)):
        _auditar(Evento.ADMIN_ASIGNADO, cuenta, despues[area_id])
    for area_id in sorted(set(antes) - set(despues)):
        _auditar(Evento.ADMIN_RETIRADO, cuenta, antes[area_id])


def _auditar(evento, cuenta, area):
    add_audit_log(evento, status='success', module=MODULO_AUDITORIA,
                  target=cuenta.email, target_user_id=cuenta.id,
                  area_id=area.id, detail=f'Área: {area.name}', commit=False)
