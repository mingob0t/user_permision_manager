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
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, NO_ENCONTRADO,
                                     OPERACION_PROPIA, REEMPLAZO_ASIGNACION,
                                     ROL_RESERVADO, campos_prohibidos,
                                     endpoint_retirado, error_response,
                                     json_payload)
from app.modules.audit.services import add_audit_log
from app.modules.auth.acceso_local import (contrasena_local_permitida,
                                           origen_de_alta)
from app.modules.auth.models import User
from app.modules.core.models import Area
from app.modules.users.roles import (CAMPOS_NO_PERMITIDOS, cambiar_rol,
                                     es_el_mismo_rol, rol_asignable)
from app.modules.users.services import (PURGE_MIN_DAYS, purgar_inactivos,
                                        usuarios_inactivos)
from app.utils.naming import sanitize_display_name

crud_bp = Blueprint('api_crud', __name__, url_prefix='/api/v1')


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
    user_ids = json_payload().get('user_ids') or []

    # Solo usuarios dentro del alcance de quien administra.
    allowed = {u.id for u in scoped_users().all()}
    rejected = [i for i in user_ids if i not in allowed]
    if rejected:
        return error_response('Hay usuarios fuera de tu alcance.', 403)

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
    data = json_payload()
    email = (data.get('email') or '').strip().lower()
    if not email:
        return error_response('El correo es obligatorio.')
    if email in RESERVED_NAMES:
        return error_response(
            'Ese identificador está reservado por el sistema.', 403)
    if User.query.filter(db.func.lower(User.email) == email).first():
        return error_response('El correo ya está registrado.', 409)
    if campos_prohibidos(data, CAMPOS_NO_PERMITIDOS):
        return error_response(*CAMPO_NO_PERMITIDO)
    # Sin contraseña local: la cuenta nace sin clave (FNC-077, SEG-02); solo
    # se acepta en desarrollo con LOGIN_LOCAL_TODAS_LAS_CUENTAS.
    if data.get('password') and not contrasena_local_permitida():
        return error_response(*CAMPO_NO_PERMITIDO)

    # Solo el superadmin crea admins de área; nadie crea superadmins (RF-04).
    role = data.get('role') or 'usuario'
    if not rol_asignable(role):
        return error_response(*ROL_RESERVADO)

    # Solo áreas dentro del alcance de quien crea.
    allowed = {a.id for a in scoped_areas().all()}
    area_ids = [i for i in (data.get('area_ids') or []) if i in allowed]

    user = User(
        email=email,
        nombre=sanitize_display_name(data.get('name'), fallback=email),
        role=role,
        # Cuenta de directorio salvo en desarrollo con la bandera (FNC-077).
        auth_source=origen_de_alta(),
        is_active=data.get('is_active', True),
    )
    if data.get('password'):
        user.set_password(data['password'])
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
        return error_response(*NO_ENCONTRADO)

    data = json_payload()
    if campos_prohibidos(data, CAMPOS_NO_PERMITIDOS):
        return error_response(*CAMPO_NO_PERMITIDO)

    # Enviar el rol que ya tiene no es una asignación: se ignora.
    new_role = data.get('role')
    change_role = 'role' in data and not es_el_mismo_rol(target, new_role)
    if change_role:
        if target.id == current_user.id:
            return error_response(*OPERACION_PROPIA)
        if not rol_asignable(new_role):
            return error_response(*ROL_RESERVADO)

    # Contraseña: solo la cuenta de emergencia (superadmin local) o, en
    # desarrollo con LOGIN_LOCAL_TODAS_LAS_CUENTAS, una cuenta local del
    # alcance (can_manage_user). Nunca del directorio o del SSO (SEG-05, P8,
    # FNC-077).
    if data.get('password') and not contrasena_local_permitida(target):
        return error_response(*CAMPO_NO_PERMITIDO)

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
        return error_response(*NO_ENCONTRADO)
    if target.id == current_user.id:
        return error_response('No puedes eliminar tu propia cuenta.', 409)
    if target.email in RESERVED_NAMES:
        return error_response('La cuenta maestra no se puede eliminar.', 403)

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
    """Retirado (FNC-065): `user_platforms` es obsoleta; ahora se otorga por
    solicitud (`POST /access-requests`)."""
    return endpoint_retirado(REEMPLAZO_ASIGNACION)


# --------------------------------------------------------------------------- #
# Preferencias propias
# --------------------------------------------------------------------------- #

@crud_bp.route('/me/preferences', methods=['PUT'])
@login_required
def save_preferences():
    """Cada usuario edita solo sus propias preferencias."""
    data = json_payload()
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


# --------------------------------------------------------------------------- #
# Higiene de cuentas
# --------------------------------------------------------------------------- #

@crud_bp.route('/users/inactive')
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


@crud_bp.route('/users/purge', methods=['POST'])
@login_required
@admin_required
def purge_inactive_users():
    """Elimina las cuentas sin actividad en el periodo indicado."""
    days = json_payload().get('days', 30)
    try:
        days = int(days)
    except (TypeError, ValueError):
        return error_response('Número de días no válido.')
    if days < PURGE_MIN_DAYS:
        # Un umbral bajo borraría cuentas recién creadas.
        return error_response(f'El periodo mínimo es de {PURGE_MIN_DAYS} días.')

    purged = purgar_inactivos(days)
    return jsonify({'status': 'success', 'count': len(purged), 'purged': purged})
