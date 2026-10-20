"""API v1 del inicio: resumen por rol (FNC-066, contrato `inicio.md`).

`GET /stats` no cambia: es el panel de contadores y visitas. El resumen por
rol va aparte para no romper su forma (contrato `inicio.md`).
"""
from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.modules.home.services import resumen

home_api_bp = Blueprint('api_home', __name__, url_prefix='/api/v1')


@home_api_bp.route('/home/summary')
@login_required
def home_summary():
    """Sin parámetros; el alcance sale de la sesión."""
    return jsonify(resumen(current_user))
