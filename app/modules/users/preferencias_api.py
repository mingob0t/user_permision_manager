"""API v1 de las preferencias propias (FNC-029, movido de `api/crud.py`)."""

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app import db
from app.modules.api.helpers import error_response, leer_cuerpo

preferences_api_bp = Blueprint('api_preferences', __name__,
                               url_prefix='/api/v1')


@preferences_api_bp.route('/me/preferences', methods=['PUT'])
@login_required
def save_preferences():
    """Cada usuario edita solo sus propias preferencias."""
    data, error = leer_cuerpo(None)
    if error is not None:
        return error
    if 'notifications' in data:
        current_user.pref_notifications = bool(data['notifications'])
    if 'email_notifications' in data:
        current_user.pref_email_notifications = bool(data['email_notifications'])
    if 'tour_enabled' in data:
        current_user.pref_tour_enabled = bool(data['tour_enabled'])
    if 'refresh_interval' in data:
        try:
            # Acotado para que un valor bajo no genere un bucle de peticiones.
            interval = int(data['refresh_interval'])
            current_user.pref_refresh_interval = max(15, min(interval, 3600))
        except (TypeError, ValueError):
            return error_response('Intervalo no válido.')

    db.session.commit()
    return jsonify({'status': 'success', 'preferences': {
        'notifications': current_user.pref_notifications,
        'email_notifications': current_user.pref_email_notifications,
        'refresh_interval': current_user.pref_refresh_interval,
        'tour_enabled': current_user.pref_tour_enabled,
    }})
