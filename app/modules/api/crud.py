"""
API v1 — operaciones de escritura.

Separado de `routes.py` (lectura) para que las reglas de permisos de cada
mutación queden juntas y a la vista.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import (admin_required, any_admin_required, area_admin_required,
                       can_manage_user, scoped_areas, scoped_users)
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, CUERPO_INVALIDO,
                                     NO_ENCONTRADO, OPERACION_PROPIA,
                                     ROL_RESERVADO, error_response,
                                     is_id_list, json_object)
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from app.modules.users.roles import (ORIGEN_LOCAL, cambiar_rol,
                                     campos_no_permitidos, es_el_mismo_rol,
                                     rol_asignable)
from app.utils.naming import sanitize_display_name

crud_bp = Blueprint('api_crud', __name__, url_prefix='/api/v1')


def _payload():
    return request.get_json(silent=True) or {}


def _error(message, status=400, code=None):
    return error_response(message, status, code)


# --------------------------------------------------------------------------- #
# Áreas
# --------------------------------------------------------------------------- #

# Alta, edición y baja: `app/modules/areas/api.py` (FNC-045).

@crud_bp.route('/areas/<int:area_id>/users', methods=['PUT'])
@login_required
@area_admin_required('area_id')
def set_area_users(area_id):
    """Define qué usuarios pertenecen al área."""
    area = Area.query.get_or_404(area_id)
    user_ids = _payload().get('user_ids') or []

    # Solo usuarios dentro del alcance de quien administra.
    allowed = {u.id for u in scoped_users().all()}
    rejected = [i for i in user_ids if i not in allowed]
    if rejected:
        return _error('Hay usuarios fuera de tu alcance.', 403)

    current = list(area.area_users or [])
    # Conserva a quien esté fuera del alcance (p. ej. un superadmin).
    keep = [u for u in current if u.id not in allowed]
    area.area_users = keep + User.query.filter(User.id.in_(user_ids)).all()
    db.session.commit()
    add_audit_log(f"ACTUALIZAR USUARIOS DE ÁREA: {area.name}", module='Áreas',
                  target=area.name, status='success')
    return jsonify({'status': 'success',
                    'user_ids': [u.id for u in area.area_users]})


# --------------------------------------------------------------------------- #
# Plataformas: `app/modules/platforms/api.py` (FNC-046)
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Usuarios
# --------------------------------------------------------------------------- #

RESERVED_NAMES = ('admin',)


@crud_bp.route('/users', methods=['POST'])
@login_required
@any_admin_required
def create_user():
    data = _payload()
    email = (data.get('email') or '').strip().lower()
    if not email:
        return _error('El correo es obligatorio.')
    if email in RESERVED_NAMES:
        return _error('Ese identificador está reservado por el sistema.', 403)
    if User.query.filter(db.func.lower(User.email) == email).first():
        return _error('El correo ya está registrado.', 409)
    if campos_no_permitidos(data):
        return _error(*CAMPO_NO_PERMITIDO)

    # Solo el superadmin crea admins de área; nadie crea superadmins (RF-04).
    role = data.get('role') or 'usuario'
    if not rol_asignable(role):
        return _error(*ROL_RESERVADO)

    # Solo áreas dentro del alcance de quien crea.
    allowed = {a.id for a in scoped_areas().all()}
    area_ids = [i for i in (data.get('area_ids') or []) if i in allowed]

    user = User(
        email=email,
        nombre=sanitize_display_name(data.get('name'), fallback=email),
        role=role,
        auth_source=ORIGEN_LOCAL,
        is_active=data.get('is_active', True),
    )
    user.set_password(data.get('password') or 'nexus123')
    # Un admin_area nace sin áreas administradas: se asignan aparte con
    # `PUT /users/<id>/managed-areas` (solo superadmin).
    user.areas = Area.query.filter(Area.id.in_(area_ids)).all()

    db.session.add(user)
    db.session.commit()
    add_audit_log(f"CREAR USUARIO: {email}", module='Usuarios', target=email,
                  status='success')
    return jsonify({'status': 'success', 'id': user.id}), 201


@crud_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@any_admin_required
def update_user(user_id):
    target = User.query.get_or_404(user_id)
    # Fuera de alcance (otra área, otro admin o el superadmin): 404 (SEC-AUTHZ-04).
    if not can_manage_user(target):
        return _error(*NO_ENCONTRADO)

    data = _payload()
    if campos_no_permitidos(data):
        return _error(*CAMPO_NO_PERMITIDO)

    # Enviar el rol que ya tiene no es una asignación: se ignora.
    new_role = data.get('role')
    change_role = 'role' in data and not es_el_mismo_rol(target, new_role)
    if change_role:
        if target.id == current_user.id:
            return _error(*OPERACION_PROPIA)
        if not rol_asignable(new_role):
            return _error(*ROL_RESERVADO)

    # Contraseña: superadmin, o admin de área sobre cuentas `usuario` de sus
    # áreas (ya filtrado por can_manage_user; decisión del dueño 2026-10-15).
    # Nunca de cuentas del directorio o del SSO (SEG-05, P8).
    if data.get('password') and (
            (target.auth_source or ORIGEN_LOCAL) != ORIGEN_LOCAL):
        return _error(*CAMPO_NO_PERMITIDO)

    if change_role:
        cambiar_rol(target, new_role)
    if 'name' in data:
        target.nombre = sanitize_display_name(data['name'], fallback=target.email)
    if 'is_active' in data:
        target.is_active = bool(data['is_active'])
    if data.get('password'):
        target.set_password(data['password'])

    db.session.commit()
    add_audit_log(f"EDITAR USUARIO: {target.email}", module='Usuarios',
                  target=target.email, status='success')
    return jsonify({'status': 'success'})


@crud_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@any_admin_required
def delete_user(user_id):
    target = User.query.get_or_404(user_id)
    if not can_manage_user(target):
        return _error(*NO_ENCONTRADO)
    if target.id == current_user.id:
        return _error('No puedes eliminar tu propia cuenta.', 409)
    if target.email in RESERVED_NAMES:
        return _error('La cuenta maestra no se puede eliminar.', 403)

    email = target.email
    db.session.delete(target)
    db.session.commit()
    add_audit_log(f"ELIMINAR USUARIO: {email}", module='Usuarios', target=email,
                  status='warning')
    return jsonify({'status': 'success'})


@crud_bp.route('/users/<int:user_id>/platforms', methods=['PUT'])
@login_required
@any_admin_required
def set_user_platforms(user_id):
    """Asigna plataformas concretas a un usuario."""
    from app.authz import scoped_platforms

    target = User.query.get_or_404(user_id)
    if not can_manage_user(target):
        return _error(*NO_ENCONTRADO)

    data = json_object()
    platform_ids = (data or {}).get('platform_ids') or []
    if data is None or not is_id_list(platform_ids):
        return _error(*CUERPO_INVALIDO)
    allowed = {p.id for p in scoped_platforms().all()}
    if [i for i in platform_ids if i not in allowed]:
        return _error('Hay plataformas fuera de tu alcance.', 403)

    keep = [p for p in target.platforms if p.id not in allowed]
    target.platforms = keep + Platform.query.filter(
        Platform.id.in_(platform_ids)).all()
    db.session.commit()
    add_audit_log(f"ACTUALIZAR ACCESOS: {target.email}", module='Usuarios',
                  target=target.email, status='success')
    return jsonify({'status': 'success'})


# --------------------------------------------------------------------------- #
# Preferencias propias
# --------------------------------------------------------------------------- #

@crud_bp.route('/me/preferences', methods=['PUT'])
@login_required
def save_preferences():
    """Cada usuario edita solo sus propias preferencias."""
    data = _payload()
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
            return _error('Intervalo no válido.')

    db.session.commit()
    return jsonify({'status': 'success', 'preferences': {
        'notifications': current_user.pref_notifications,
        'email_notifications': current_user.pref_email_notifications,
        'refresh_interval': current_user.pref_refresh_interval,
        'tour_enabled': current_user.pref_tour_enabled,
    }})


# --------------------------------------------------------------------------- #
# Higiene de cuentas
# --------------------------------------------------------------------------- #

PURGE_MIN_DAYS = 7


def _inactive_users(days):
    """Cuentas candidatas a purga por inactividad.

    Incluye las que nunca han iniciado sesión y son más antiguas que el
    umbral: la versión anterior las dejaba fuera, porque comparar
    `last_login_at < cutoff` descarta los nulos, y eran justo las más claras.
    Nunca se purga a un superadmin.
    """
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)
    return User.query.filter(
        db.func.lower(db.func.coalesce(User.role, '')) != 'administrador',
        db.or_(
            User.last_login_at < cutoff,
            db.and_(User.last_login_at.is_(None), User.created_at < cutoff),
        ),
    )


@crud_bp.route('/users/inactive')
@login_required
@admin_required
def list_inactive_users():
    """Vista previa de la purga: qué cuentas se eliminarían."""
    days = max(request.args.get('days', 30, type=int), PURGE_MIN_DAYS)
    users = _inactive_users(days).order_by(User.email).all()
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


@crud_bp.route('/users/purge', methods=['POST'])
@login_required
@admin_required
def purge_inactive_users():
    """Elimina las cuentas sin actividad en el periodo indicado."""
    days = _payload().get('days', 30)
    try:
        days = int(days)
    except (TypeError, ValueError):
        return _error('Número de días no válido.')
    if days < PURGE_MIN_DAYS:
        # Un umbral bajo borraría cuentas recién creadas.
        return _error(f'El periodo mínimo es de {PURGE_MIN_DAYS} días.')

    users = _inactive_users(days).all()
    purged = [u.email for u in users]
    for user in users:
        db.session.delete(user)
    db.session.commit()

    if purged:
        add_audit_log(f'PURGAR CUENTAS INACTIVAS ({len(purged)})',
                      module='Usuarios', status='warning',
                      detail=f"Inactividad > {days} días: {', '.join(purged[:20])}")
    return jsonify({'status': 'success', 'count': len(purged), 'purged': purged})
