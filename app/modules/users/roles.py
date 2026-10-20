"""Reglas de rol de las cuentas (FNC-044).

Fuente: `docs/contratos/areas-y-roles.md` y `docs/seguridad/LINEAMIENTOS.md`
(SEC-AUTHZ-05, 06, 08 y 09).

- Solo el superadmin asigna `admin_area`; un admin de área solo `usuario`.
- `administrador` no se asigna nunca por la API: hay un solo superadmin.
- Dejar de ser `admin_area` borra las áreas administradas y revoca sus
  accesos automáticos (FNC-055).
"""

from app.authz import (ROLE_AREA_ADMIN, ROLE_USER, is_admin, is_area_admin,
                       normalized_role)
from app.modules.access.area_admin_sync import sincronizar_cuenta
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log

ROLES_DEL_SUPERADMIN = (ROLE_USER, ROLE_AREA_ADMIN)
ROLES_DEL_ADMIN_DE_AREA = (ROLE_USER,)

# Campos que `POST /users` y `PUT /users/<id>` rechazan con
# `400 campo_no_permitido`: las áreas administradas solo se asignan con
# `PUT /users/<id>/managed-areas` y el origen de la cuenta lo fija el servidor.
CAMPOS_NO_PERMITIDOS = frozenset({'managed_area_ids', 'auth_source',
                                  'password_hash'})

# Origen de las cuentas locales (`POST /users` en desarrollo con la bandera de
# FNC-077; si no, `ldap`: `auth/acceso_local.origen_de_alta`).
ORIGEN_LOCAL = 'local'

MODULO_AUDITORIA = 'Usuarios'


def roles_asignables(actor=None):
    """Roles que `actor` puede asignar (vacío si no administra)."""
    if is_admin(actor):
        return ROLES_DEL_SUPERADMIN
    if is_area_admin(actor):
        return ROLES_DEL_ADMIN_DE_AREA
    return ()


def rol_asignable(rol, actor=None):
    """True si `actor` puede asignar `rol` (valor exacto del contrato)."""
    return isinstance(rol, str) and rol in roles_asignables(actor)


def campos_no_permitidos(datos):
    """Campos del cuerpo que el endpoint no acepta, ordenados."""
    return sorted(CAMPOS_NO_PERMITIDOS & set(datos))


def es_el_mismo_rol(cuenta, rol):
    """True si `rol` no cambia el rol actual: no es una asignación."""
    return isinstance(rol, str) and rol.lower() == normalized_role(cuenta)


def _estado_de_rol(cuenta):
    return {'role': normalized_role(cuenta),
            'managed_area_ids': sorted(a.id for a in (cuenta.managed_areas
                                                      or []))}


def cambiar_rol(cuenta, rol):
    """Cambia el rol de `cuenta` y lo audita sin confirmar.

    Quien llama confirma la transacción: el cambio y su auditoría se guardan
    juntos (SEC-AUD-06). Dejar de ser `admin_area` borra sus áreas
    administradas en la misma transacción.
    """
    antes = _estado_de_rol(cuenta)
    cuenta.role = rol
    if rol != ROLE_AREA_ADMIN:
        cuenta.managed_areas = []
    add_audit_log(Evento.ROL_CAMBIADO, status='warning',
                  module=MODULO_AUDITORIA, target=cuenta.email,
                  target_user_id=cuenta.id, before=antes,
                  after=_estado_de_rol(cuenta), commit=False)
    if rol != ROLE_AREA_ADMIN:
        sincronizar_cuenta(cuenta)  # revoca sus automáticos (FNC-055)
