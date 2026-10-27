"""Crea los datos demo que faltan (FNC-131), sin duplicar los existentes.

Usa los modelos y servicios del portal; no hace `commit` (lo hace el comando
para dejar todo o nada). Devuelve un informe: qué se creó y qué ya existía.
"""
from app import db
from app.authz import ROLE_AREA_ADMIN
from app.modules.access_requests import catalogo, services as solicitudes
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from app.modules.demo import datos
from app.modules.platforms.tipos import (CAMPO_DN_ADMIN, CAMPO_DN_USUARIO,
                                         NIVEL_ADMIN, NIVEL_USUARIO)
from app.modules.users.areas_administradas import asignar_areas_administradas
from app.modules.users.roles import ORIGEN_LOCAL

CREADO = 'creado'
EXISTIA = 'ya existía'


def correos_nuevos():
    """Correos demo que aún no existen (los únicos que necesitan contraseña)."""
    existentes = {c for (c,) in db.session.query(User.email).filter(
        User.email.in_([c.correo for c in datos.CUENTAS]))}
    return [c.correo for c in datos.CUENTAS if c.correo not in existentes]


def _area(definicion):
    area = Area.query.filter_by(name=definicion.nombre).first()
    if area is not None:
        return area, EXISTIA
    area = Area(name=definicion.nombre, description=definicion.descripcion)
    db.session.add(area)
    db.session.flush()
    return area, CREADO


def _plataforma(definicion, area):
    plataforma = Platform.query.filter_by(name=definicion.nombre,
                                          area_id=area.id).first()
    if plataforma is not None:
        return plataforma, EXISTIA
    plataforma = Platform(
        name=definicion.nombre, description=definicion.descripcion,
        area_id=area.id,
        **{CAMPO_DN_USUARIO: datos.dn_de_grupo(definicion, NIVEL_USUARIO),
           CAMPO_DN_ADMIN: datos.dn_de_grupo(definicion, NIVEL_ADMIN)})
    db.session.add(plataforma)
    db.session.flush()
    return plataforma, CREADO


def _cuenta(definicion, area, contrasenas):
    cuenta = User.query.filter_by(email=definicion.correo).first()
    if cuenta is not None:
        return cuenta, EXISTIA
    cuenta = User(email=definicion.correo, nombre=definicion.nombre,
                  role=definicion.rol, auth_source=ORIGEN_LOCAL,
                  is_active=True)
    cuenta.set_password(contrasenas[definicion.correo])
    if definicion.rol != ROLE_AREA_ADMIN:
        cuenta.areas = [area]
    db.session.add(cuenta)
    db.session.flush()
    if definicion.rol == ROLE_AREA_ADMIN:
        # Los accesos automáticos de P6 salen del servicio, con su auditoría.
        asignar_areas_administradas(cuenta, [area.id])
    return cuenta, CREADO


def _solicitud(cuentas, plataformas):
    definicion = datos.SOLICITUD
    actor = cuentas[definicion.correo]
    plataforma = plataformas[definicion.plataforma]
    estado = catalogo.estado(actor.id, plataforma.id)
    if estado.pendiente is not None or estado.vigentes:
        return EXISTIA
    solicitudes.crear(actor, plataforma.id, definicion.nivel,
                      definicion.justificacion)
    return CREADO


def cargar(contrasenas):
    """Crea lo que falta; `contrasenas` = {correo: texto} de las cuentas nuevas.

    Devuelve `{'areas': [(nombre, estado)], 'plataformas': [...],
    'cuentas': [(definición, estado)], 'solicitud': estado}`.
    """
    informe = {'areas': [], 'plataformas': [], 'cuentas': []}
    areas = {}
    for definicion in datos.AREAS:
        areas[definicion.nombre], estado = _area(definicion)
        informe['areas'].append((definicion.nombre, estado))
    plataformas = {}
    for definicion in datos.PLATAFORMAS:
        plataformas[definicion.nombre], estado = _plataforma(
            definicion, areas[definicion.area])
        informe['plataformas'].append((definicion.nombre, estado))
    cuentas = {}
    for definicion in datos.CUENTAS:
        cuentas[definicion.correo], estado = _cuenta(
            definicion, areas[definicion.area], contrasenas)
        informe['cuentas'].append((definicion, estado))
    informe['solicitud'] = _solicitud(cuentas, plataformas)
    return informe
