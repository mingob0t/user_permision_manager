"""API v1 de la identidad del portal (FNC-029, movido de `api/admin.py`).

`GET /settings` lo lee cualquier sesión (la interfaz lo necesita); guardar es
exclusivo del superadmin.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

from app import db
from app.authz import admin_required
from app.modules.api.helpers import error_response, leer_cuerpo
from app.modules.audit.services import add_audit_log
from app.modules.settings.logo import validar_logo
from app.modules.settings.models import SystemConfig

settings_api_bp = Blueprint('api_settings', __name__, url_prefix='/api/v1')


@settings_api_bp.route('/settings')
@login_required
def get_settings():
    """La identidad del portal la lee cualquiera: la interfaz la necesita."""
    config = SystemConfig.query.first()
    if config is None:
        return jsonify(SystemConfig.por_defecto().to_dict())
    return jsonify(config.to_dict())


@settings_api_bp.route('/settings', methods=['PUT'])
@login_required
@admin_required
def save_settings():
    config = SystemConfig.query.first()
    if config is None:
        config = SystemConfig.por_defecto()
        db.session.add(config)

    data, error = leer_cuerpo(None)
    if error is not None:
        return error
    for field in ('portal_name', 'bg_color', 'text_color'):
        if field in data:
            setattr(config, field, data[field])

    if 'portal_identity_type' in data:
        kind = data['portal_identity_type']
        if kind not in ('icon', 'image'):
            return error_response(
                'El tipo de identidad debe ser "icon" o "image".')
        config.portal_identity_type = kind

    if 'portal_icon' in data:
        raw = data['portal_icon']
        if config.portal_identity_type == 'image':
            value, problem = validar_logo(raw)
            if problem:
                return error_response(problem)
            config.portal_icon = value
        else:
            # Para el modo icono se guarda el SVG tal cual.
            config.portal_icon = raw

    db.session.commit()
    add_audit_log('ACTUALIZAR CONFIGURACIÓN', module='Ajustes',
                  status='success')
    return jsonify({'status': 'success', 'settings': config.to_dict()})
