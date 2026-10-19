"""
API v1 — la interfaz que consume el frontend Next.js.

Cada endpoint devuelve JSON y aplica el alcance multitenant de `app.authz`, de
modo que un admin de área solo recibe los datos de las áreas que administra.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import (any_admin_required, area_admin_required, can_manage_area,
                       can_manage_user, is_admin, is_area_admin, scoped_areas,
                       scoped_platforms, scoped_users)
from app.modules.api.helpers import (CUERPO_INVALIDO, NO_ENCONTRADO,
                                     error_response, is_id_list, json_object)
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from app.modules.platforms.validacion import url_segura
from app.modules.users.serializacion import usuario_gestionado

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


# --------------------------------------------------------------------------- #
# Sesión
# --------------------------------------------------------------------------- #

@api_bp.route('/me')
@login_required
def me():
    """Identidad y permisos del usuario actual.

    El frontend usa `permissions` para decidir qué menús y acciones muestra; el
    backend vuelve a comprobarlo en cada endpoint.
    """
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.nombre or current_user.email,
        'role': current_user.role,
        'auth_source': current_user.auth_source,
        'areas': [{'id': a.id, 'name': a.name} for a in (current_user.areas or [])],
        'managed_areas': [{'id': a.id, 'name': a.name}
                          for a in (current_user.managed_areas or [])],
        'permissions': {
            'is_admin': is_admin(),
            'is_area_admin': is_area_admin(),
            'can_manage_areas': is_admin(),
            'can_manage_system': is_admin(),
        },
        'preferences': {
            'notifications': current_user.pref_notifications,
            'email_notifications': current_user.pref_email_notifications,
            'refresh_interval': current_user.pref_refresh_interval,
            'tour_enabled': current_user.pref_tour_enabled,
        },
    })


# --------------------------------------------------------------------------- #
# Áreas
# --------------------------------------------------------------------------- #

@api_bp.route('/areas')
@login_required
def list_areas():
    """Áreas visibles para el usuario."""
    areas = scoped_areas().order_by(Area.name).all()
    return jsonify([{
        **a.to_dict(),
        'platforms_count': len(a.platforms or []),
        'users_count': len(a.area_users or []),
    } for a in areas])


@api_bp.route('/areas/<int:area_id>')
@login_required
@area_admin_required('area_id')
def get_area(area_id):
    area = Area.query.get_or_404(area_id)
    return jsonify(area.to_dict())


# --------------------------------------------------------------------------- #
# Plataformas (catálogo de enlaces)
# --------------------------------------------------------------------------- #

def _platform_payload(p, favorite_ids):
    return {
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'area_id': p.area_id,
        'area_name': p.area.name if p.area else None,
        'area_color': p.area.color if p.area else '#6366f1',
        'area_icon': p.area.icon if p.area else 'box',
        # FNC-046: una URL guardada que no es https sale como null.
        'direct_link': url_segura(p.direct_link),
        'icon': p.icon,
        'logo_url': url_segura(p.logo_url),
        'bg_color': p.bg_color,
        'text_color': p.text_color,
        'status': p.status,
        'visits': p.visits or 0,
        'is_favorite': p.id in favorite_ids,
    }


@api_bp.route('/platforms')
@login_required
def list_platforms():
    """Catálogo de plataformas visibles, con marca de favorito."""
    favorite_ids = {p.id for p in (current_user.favorites or [])}
    query = scoped_platforms()

    area_id = request.args.get('area_id', type=int)
    if area_id:
        query = query.filter(Platform.area_id == area_id)
    search = (request.args.get('q') or '').strip()
    if search:
        query = query.filter(Platform.name.ilike(f'%{search}%'))

    platforms = query.order_by(Platform.name).all()
    return jsonify([_platform_payload(p, favorite_ids) for p in platforms])


@api_bp.route('/platforms/<int:platform_id>/visit', methods=['POST'])
@login_required
def register_visit(platform_id):
    """Cuenta una visita al abrir el enlace de una plataforma."""
    platform = scoped_platforms().filter(Platform.id == platform_id).first()
    if platform is None:
        return jsonify({'status': 'error', 'message': 'Plataforma no disponible.'}), 404
    platform.visits = (platform.visits or 0) + 1
    db.session.commit()
    return jsonify({'status': 'success', 'visits': platform.visits})


@api_bp.route('/platforms/<int:platform_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(platform_id):
    platform = scoped_platforms().filter(Platform.id == platform_id).first()
    if platform is None:
        return jsonify({'status': 'error', 'message': 'Plataforma no disponible.'}), 404
    if platform in current_user.favorites:
        current_user.favorites.remove(platform)
        is_favorite = False
    else:
        current_user.favorites.append(platform)
        is_favorite = True
    db.session.commit()
    return jsonify({'status': 'success', 'is_favorite': is_favorite})


@api_bp.route('/favorites')
@login_required
def list_favorites():
    """Favoritos del usuario, limitados a lo que aún puede ver."""
    visible_ids = {p.id for p in scoped_platforms().all()}
    favorites = [p for p in (current_user.favorites or []) if p.id in visible_ids]
    return jsonify([_platform_payload(p, visible_ids & {p.id}) for p in favorites])


# --------------------------------------------------------------------------- #
# Usuarios
# --------------------------------------------------------------------------- #

@api_bp.route('/users')
@login_required
@any_admin_required
def list_users():
    """Usuarios que el solicitante puede administrar."""
    users = scoped_users().order_by(User.email).all()
    return jsonify([usuario_gestionado(u) for u in users])


@api_bp.route('/users/<int:user_id>/areas', methods=['PUT'])
@login_required
@any_admin_required
def set_user_areas(user_id):
    """Reasigna las áreas de un usuario, dentro del alcance del solicitante."""
    target = User.query.get_or_404(user_id)
    if not can_manage_user(target):
        return error_response(*NO_ENCONTRADO)

    requested = json_object()
    area_ids = (requested or {}).get('area_ids') or []
    if requested is None or not is_id_list(area_ids):
        return error_response(*CUERPO_INVALIDO)

    # Solo áreas que el solicitante administra
    allowed = {a.id for a in scoped_areas().all()}
    rejected = [i for i in area_ids if i not in allowed]
    if rejected:
        return jsonify({'status': 'error',
                        'message': 'Hay áreas fuera de tu alcance.',
                        'rejected': rejected}), 403

    # Conserva las áreas del usuario que el solicitante no administra
    kept = [a for a in (target.areas or []) if a.id not in allowed]
    target.areas = kept + Area.query.filter(Area.id.in_(area_ids)).all()
    db.session.commit()
    return jsonify({'status': 'success',
                    'areas': [{'id': a.id, 'name': a.name} for a in target.areas]})


# --------------------------------------------------------------------------- #
# Panel y auditoría
# --------------------------------------------------------------------------- #

@api_bp.route('/stats')
@login_required
def stats():
    """Contadores del panel, ya filtrados por alcance."""
    areas_q = scoped_areas()
    platforms_q = scoped_platforms()

    # MySQL no soporta NULLS LAST: coalesce a 0 para ordenar de forma portable.
    top = (platforms_q.order_by(db.func.coalesce(Platform.visits, 0).desc())
           .limit(5).all())

    payload = {
        'areas': areas_q.count(),
        'platforms': platforms_q.count(),
        'visits': sum((p.visits or 0) for p in platforms_q.all()),
        'most_visited': [{'id': p.id, 'name': p.name, 'visits': p.visits or 0}
                         for p in top],
        'platforms_by_area': [
            {'area': a.name, 'color': a.color,
             'count': sum(1 for p in (a.platforms or []))}
            for a in areas_q.all()
        ],
    }
    if is_admin() or is_area_admin():
        payload['users'] = scoped_users().count()
    return jsonify(payload)


@api_bp.route('/audit')
@login_required
def list_audit():
    """Registros de auditoría dentro del alcance del solicitante."""
    if is_admin():
        query = AuditLog.query
    elif is_area_admin():
        # Las cuentas que administra, más sus propios eventos.
        emails = [u.email for u in scoped_users().all()] + [current_user.email]
        query = AuditLog.query.filter(AuditLog.user.in_(emails))
    else:
        query = AuditLog.query.filter_by(user=current_user.email)

    limit = min(request.args.get('limit', 100, type=int), 500)
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return jsonify([log.to_dict() for log in logs])
