"""Consultas de accesos vigentes para otros módulos (plataformas y áreas)."""
from app import db
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import ESTADOS_VIGENTES, ORIGEN_ADMIN_DE_AREA
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


def contar_vigentes_no_automaticos(plataforma_id):
    """Vigentes que no son `admin_de_area` (FNC-055: esos se resincronizan
    al cambiar el área de la plataforma)."""
    if plataforma_id is None:
        return 0
    return PlatformAccessGrant.query.filter(
        PlatformAccessGrant.platform_id == plataforma_id,
        PlatformAccessGrant.origin != ORIGEN_ADMIN_DE_AREA,
        PlatformAccessGrant.status.in_(ESTADOS_VIGENTES)).count()


def area_tiene_vigentes(area_id):
    """`True` si alguna plataforma del área tiene accesos vigentes."""
    return db.session.query(
        PlatformAccessGrant.query
        .join(Platform, Platform.id == PlatformAccessGrant.platform_id)
        .filter(Platform.area_id == area_id,
                PlatformAccessGrant.status.in_(ESTADOS_VIGENTES)).exists()
    ).scalar()


def de_usuario(usuario_id, estados, area_ids=None):
    """Accesos de una cuenta en `estados`, del más reciente al más antiguo
    (FNC-058). `area_ids`: solo las plataformas de esas áreas (admin de
    área); `None` = sin filtro (superadmin o la propia cuenta)."""
    consulta = PlatformAccessGrant.query.filter(
        PlatformAccessGrant.user_id == usuario_id,
        PlatformAccessGrant.status.in_(estados))
    if area_ids is not None:
        consulta = (consulta
                    .join(Platform, Platform.id == PlatformAccessGrant.platform_id)
                    .filter(Platform.area_id.in_(area_ids)))
    return consulta.order_by(PlatformAccessGrant.granted_at.desc(),
                             PlatformAccessGrant.id.desc())
