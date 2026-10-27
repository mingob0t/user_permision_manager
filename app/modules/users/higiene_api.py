"""API v1 de higiene de cuentas: vista previa y purga de inactivas
(FNC-029, movido de `api/crud.py`). Exclusivo del superadmin.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.authz import admin_required
from app.modules.api.helpers import error_response, leer_cuerpo
from app.modules.auth.models import User
from app.modules.users.services import (PURGE_MIN_DAYS, purgar_inactivos,
                                        usuarios_inactivos)

hygiene_api_bp = Blueprint('api_hygiene', __name__, url_prefix='/api/v1')


@hygiene_api_bp.route('/users/inactive')
@login_required
@admin_required
def list_inactive_users():
    """Vista previa de la purga: qué cuentas se eliminarían."""
    days = max(request.args.get('days', 30, type=int), PURGE_MIN_DAYS)
    users = usuarios_inactivos(days).order_by(User.email).all()
    return jsonify({
        'days': days,
        'count': len(users),
        'users': [{
            'id': u.id,
            'email': u.email,
            'name': u.nombre or u.email,
            'role': u.role,
            'last_login_at': u.last_login_at.isoformat() if u.last_login_at else None,
        } for u in users],
    })


@hygiene_api_bp.route('/users/purge', methods=['POST'])
@login_required
@admin_required
def purge_inactive_users():
    """Elimina las cuentas sin actividad en el periodo indicado."""
    datos, error = leer_cuerpo(None)
    if error is not None:
        return error
    days = datos.get('days', 30)
    try:
        days = int(days)
    except (TypeError, ValueError):
        return error_response('Número de días no válido.')
    if days < PURGE_MIN_DAYS:
        # Un umbral bajo borraría cuentas recién creadas.
        return error_response(f'El periodo mínimo es de {PURGE_MIN_DAYS} días.')

    purged = purgar_inactivos(days)
    return jsonify({'status': 'success', 'count': len(purged), 'purged': purged})
