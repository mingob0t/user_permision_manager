"""API v1 de cuentas: áreas administradas (FNC-044).

`PUT /api/v1/users/<id>/managed-areas`: solo el superadmin asigna las áreas que
administra un `admin_area` (contrato `docs/contratos/areas-y-roles.md`).
Separado de `api/crud.py` para no hacer crecer ese archivo.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

from app import db
from app.authz import ROLE_AREA_ADMIN, admin_required, normalized_role
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, NO_ENCONTRADO,
                                     ROL_NO_ADMIN, error_response,
                                     json_object, validation_error)
from app.modules.auth.models import User
from app.modules.users.areas_administradas import (CAMPO_AREAS,
                                                   asignar_areas_administradas,
                                                   validar_area_ids)
from app.modules.users.serializacion import usuario_gestionado

users_api_bp = Blueprint('api_users', __name__, url_prefix='/api/v1')


@users_api_bp.route('/users/<int:user_id>/managed-areas', methods=['PUT'])
@login_required
@admin_required
def set_managed_areas(user_id):
    """Reemplaza la lista completa de áreas que administra un `admin_area`."""
    cuenta = db.session.get(User, user_id)
    if cuenta is None:
        return error_response(*NO_ENCONTRADO)

    datos = json_object() or {}
    if set(datos) - {CAMPO_AREAS}:
        return error_response(*CAMPO_NO_PERMITIDO)
    if CAMPO_AREAS not in datos:
        return validation_error({CAMPO_AREAS: 'Es obligatorio.'})
    area_ids, problema = validar_area_ids(datos[CAMPO_AREAS])
    if problema:
        return validation_error({CAMPO_AREAS: problema})

    if normalized_role(cuenta) != ROLE_AREA_ADMIN:
        return error_response(*ROL_NO_ADMIN)

    asignar_areas_administradas(cuenta, area_ids)
    db.session.commit()
    return jsonify({'status': 'success', 'user': usuario_gestionado(cuenta)})
