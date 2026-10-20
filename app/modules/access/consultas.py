"""Consultas de accesos vigentes para otros módulos (plataformas y áreas)."""
from app import db
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import ESTADOS_VIGENTES
from app.modules.core.models import Platform


def vigentes_de(usuario_id, plataforma_id):
    """Accesos vigentes de un usuario en una plataforma."""
    return PlatformAccessGrant.query.filter(
        PlatformAccessGrant.user_id == usuario_id,
        PlatformAccessGrant.platform_id == plataforma_id,
        PlatformAccessGrant.status.in_(ESTADOS_VIGENTES)).all()


def contar_vigentes_de_plataforma(plataforma_id):
    if plataforma_id is None:
        return 0
    return PlatformAccessGrant.query.filter(
        PlatformAccessGrant.platform_id == plataforma_id,
        PlatformAccessGrant.status.in_(ESTADOS_VIGENTES)).count()


def area_tiene_vigentes(area_id):
    """`True` si alguna plataforma del área tiene accesos vigentes."""
    return db.session.query(
        PlatformAccessGrant.query
        .join(Platform, Platform.id == PlatformAccessGrant.platform_id)
        .filter(Platform.area_id == area_id,
                PlatformAccessGrant.status.in_(ESTADOS_VIGENTES)).exists()
    ).scalar()
