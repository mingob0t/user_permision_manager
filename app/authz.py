"""
Autorización centralizada de Nexus (multitenant por área).

Este módulo concentra las reglas de acceso. El resto de la aplicación debe pedir
permisos aquí en lugar de comparar `current_user.role` a mano.

Niveles de acceso (de mayor a menor):

    administrador -> superadmin: todas las áreas y plataformas, y la
                     configuración global del sistema.
    admin_area    -> administra las áreas que tiene asignadas en `area_admins`:
                     sus plataformas, sus usuarios y sus permisos. No ve ni toca
                     nada de otras áreas ni la configuración global.
    usuario       -> solo consulta las plataformas de las áreas que tiene
                     asignadas en `user_areas`.

El área es la unidad de aislamiento (tenant). El aislamiento se aplica por
fila: cada consulta se filtra por las áreas que el usuario alcanza, mediante las
funciones `scoped_*` de este módulo.
"""

from functools import wraps

from flask import abort, flash, jsonify, redirect, request, url_for
from flask_login import current_user

ROLE_ADMIN = 'administrador'
ROLE_AREA_ADMIN = 'admin_area'
ROLE_USER = 'usuario'


# --------------------------------------------------------------------------- #
# Consultas de rol
# --------------------------------------------------------------------------- #

def _role(user):
    """Rol normalizado: llega sin normalizar de LDAP y de Authelia."""
    return (getattr(user, 'role', '') or '').lower()


def normalized_role(user):
    """Rol en minúsculas de cualquier cuenta (no exige sesión)."""
    return _role(user)


def _valid(user):
    return bool(user) and user.is_authenticated


def is_admin(user=None):
    """True si es superadmin global."""
    user = user if user is not None else current_user
    return _valid(user) and _role(user) == ROLE_ADMIN


def is_area_admin(user=None):
    """True si administra una o más áreas (no incluye al superadmin)."""
    user = user if user is not None else current_user
    return _valid(user) and _role(user) == ROLE_AREA_ADMIN


def is_any_admin(user=None):
    """True si administra algo: superadmin o admin de área."""
    return is_admin(user) or is_area_admin(user)


def managed_area_ids(user=None):
    """IDs de las áreas que el usuario administra.

    Vacío para el superadmin: su alcance no se expresa como lista, sino como
    ausencia de filtro. Usa `scoped_*` en lugar de esta función para consultar.
    """
    user = user if user is not None else current_user
    if not is_area_admin(user):
        return []
    return [a.id for a in (user.managed_areas or [])]


def user_area_ids(user=None, only_active=False):
    """IDs de las áreas que el usuario alcanza.

    Un admin de área alcanza las que administra; un usuario, las que le fueron
    asignadas.
    """
    user = user if user is not None else current_user
    if not _valid(user):
        return []
    areas = (user.managed_areas if is_area_admin(user) else user.areas) or []
    if only_active:
        areas = [a for a in areas if a.status == 'Activo']
    return [a.id for a in areas]


# --------------------------------------------------------------------------- #
# Alcance de datos (row-level scoping)
# --------------------------------------------------------------------------- #

def scoped_areas(user=None, only_active=False):
    """Query de las áreas visibles para el usuario."""
    from app.modules.core.models import Area

    user = user if user is not None else current_user
    if is_admin(user):
        query = Area.query
    else:
        ids = user_area_ids(user)
        # in_([]) genera SQL falso, que es justo lo que queremos: sin áreas, no
        # se ve nada.
        query = Area.query.filter(Area.id.in_(ids))
    if only_active:
        query = query.filter(Area.status == 'Activo')
    return query


def scoped_platforms(user=None):
    """Query de las plataformas visibles para el usuario."""
    from app.modules.core.models import Platform

    user = user if user is not None else current_user
    if is_admin(user):
        return Platform.query
    return Platform.query.filter(Platform.area_id.in_(user_area_ids(user)))


def scoped_users(user=None):
    """Query de los usuarios que el usuario puede administrar.

    El superadmin ve a todos. Un admin de área ve a quienes pertenecen a alguna
    de las áreas que administra. Un usuario normal, solo a sí mismo.
    """
    from app import db
    from app.modules.auth.models import User, user_areas

    user = user if user is not None else current_user
    if is_admin(user):
        return User.query
    if is_area_admin(user):
        ids = managed_area_ids(user)
        if not ids:
            return User.query.filter(False)
        # Subconsulta en lugar de JOIN: así la query devuelta mantiene User
        # como única entidad y admite filter_by() encadenado por quien llama.
        member_ids = (db.session.query(user_areas.c.user_id)
                      .filter(user_areas.c.area_id.in_(ids)))
        # Un superadmin puede pertenecer a estas áreas, pero nunca debe quedar
        # bajo la administración de un admin de área.
        return User.query.filter(
            User.id.in_(member_ids),
            db.func.lower(db.func.coalesce(User.role, '')) != ROLE_ADMIN,
        )
    return User.query.filter(User.id == user.id) if _valid(user) else User.query.filter(False)


# --------------------------------------------------------------------------- #
# Permisos sobre objetos concretos
# --------------------------------------------------------------------------- #

def can_access_platform(platform, user=None):
    """True si el usuario puede ver esa plataforma."""
    if platform is None:
        return False
    user = user if user is not None else current_user
    if is_admin(user):
        return True
    return platform.area_id in user_area_ids(user)


def can_manage_area(area_id, user=None):
    """True si el usuario puede administrar el área indicada."""
    user = user if user is not None else current_user
    if is_admin(user):
        return True
    if area_id is None:
        return False
    return int(area_id) in managed_area_ids(user)


def can_manage_platform(platform, user=None):
    """True si el usuario puede crear/editar/borrar esa plataforma."""
    if platform is None:
        return False
    return can_manage_area(platform.area_id, user)


def can_manage_user(target, user=None):
    """True si `user` puede administrar la cuenta `target`.

    Un admin de área solo administra cuentas con rol `usuario` de sus áreas:
    nunca a otro admin de área ni al superadmin (SEC-AUTHZ-06, SEG-05).
    """
    if target is None:
        return False
    user = user if user is not None else current_user
    if is_admin(user):
        return True
    if not is_area_admin(user):
        return False
    if _role(target) != ROLE_USER:
        return False
    managed = set(managed_area_ids(user))
    return bool(managed & {a.id for a in (target.areas or [])})


# --------------------------------------------------------------------------- #
# Decoradores
# --------------------------------------------------------------------------- #

def _wants_json():
    """True si quien llama espera JSON en lugar de una redirección HTML.

    Sin esto, un `fetch()` a una ruta protegida recibe un 302 hacia el dashboard
    y el JS falla al parsear HTML como JSON.
    """
    if request.is_json or '/api/' in request.path or request.path.endswith('-api'):
        return True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    accept = request.accept_mimetypes
    return accept['application/json'] >= accept['text/html']


def _deny(message='Acceso restringido. Se requieren permisos de administrador.'):
    """Respuesta de acceso denegado en el formato que espera quien llama."""
    if _wants_json():
        return jsonify({'status': 'error', 'message': message}), 403
    flash(message, 'warning')
    return redirect(url_for('core.index'))


def admin_required(f):
    """Solo el superadmin global (configuración del sistema, auditoría)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return _deny()
        return f(*args, **kwargs)
    return decorated_function


def any_admin_required(f):
    """Superadmin o admin de área.

    Las vistas que lo usan deben filtrar sus datos con `scoped_*`: este
    decorador concede la entrada, no el alcance.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_any_admin():
            return _deny('Se requieren permisos de administración.')
        return f(*args, **kwargs)
    return decorated_function


def area_admin_required(area_arg='area_id'):
    """Restringe la vista a quien administre el área indicada en la ruta."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not can_manage_area(kwargs.get(area_arg)):
                return _deny('No tienes permisos para administrar esta área.')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def platform_access_required(platform_arg='platform_id'):
    """Restringe la vista a quien tenga acceso a la plataforma de la ruta."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.modules.core.models import Platform

            platform = Platform.query.get(kwargs.get(platform_arg))
            if platform is None:
                abort(404)
            if not can_access_platform(platform):
                return _deny('No tienes acceso a esta plataforma.')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def platform_manage_required(platform_arg='platform_id'):
    """Restringe la vista a quien pueda administrar la plataforma de la ruta."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.modules.core.models import Platform

            platform = Platform.query.get(kwargs.get(platform_arg))
            if platform is None:
                abort(404)
            if not can_manage_platform(platform):
                return _deny('No tienes permisos sobre esta plataforma.')
            return f(*args, **kwargs)
        return decorated_function
    return decorator
