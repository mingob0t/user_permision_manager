"""Fábricas de datos de prueba: áreas, plataformas y usuarios por rol.

Cada función crea el registro en la BD de pruebas y lo devuelve ya guardado.
Los nombres se generan únicos para que varias llamadas no choquen.
"""

from itertools import count

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform

ROLES = (ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER)

_secuencia = count(1)


def _siguiente():
    return next(_secuencia)


def crear_area(nombre=None, **campos):
    area = Area(name=nombre or f'Área {_siguiente()}', **campos)
    db.session.add(area)
    db.session.commit()
    return area


def crear_plataforma(area, nombre=None, descripcion='Plataforma de prueba',
                     **campos):
    plataforma = Platform(name=nombre or f'Plataforma {_siguiente()}',
                          description=descripcion, area_id=area.id, **campos)
    db.session.add(plataforma)
    db.session.commit()
    return plataforma


def crear_usuario(rol=ROLE_USER, email=None, areas=(), areas_administradas=(),
                  plataformas=(), activo=True, contrasena=None):
    """Crea un usuario local con el rol indicado.

    - `areas`: áreas asignadas (`user_areas`), lo que ve un usuario normal.
    - `areas_administradas`: áreas que administra (`area_admins`), para el rol
      `admin_area`.
    - `contrasena`: opcional; sin ella el usuario no puede iniciar sesión por
      formulario, solo por la sesión que arma el cliente autenticado.
    """
    if rol not in ROLES:
        raise ValueError(f'Rol desconocido en pruebas: {rol}')
    n = _siguiente()
    usuario = User(email=email or f'{rol}{n}@pruebas.local',
                   nombre=f'{rol} {n}', role=rol, is_active=activo)
    if contrasena:
        usuario.set_password(contrasena)
    usuario.areas = list(areas)
    usuario.managed_areas = list(areas_administradas)
    usuario.platforms = list(plataformas)
    db.session.add(usuario)
    db.session.commit()
    return usuario


def crear_usuario_de_rol(rol):
    """Usuario listo para su rol, con un área propia.

    El `admin_area` administra su área; el `usuario` la tiene asignada; el
    `administrador` no necesita áreas.
    """
    if rol == ROLE_ADMIN:
        return crear_usuario(ROLE_ADMIN)
    area = crear_area()
    if rol == ROLE_AREA_ADMIN:
        return crear_usuario(ROLE_AREA_ADMIN, areas_administradas=[area])
    return crear_usuario(ROLE_USER, areas=[area])
