"""Catálogo solicitable (P1) y estado del actor en cada plataforma (FNC-056).

Contrato `solicitudes.md`, `GET /access-requests/catalog`. Las reglas de
nivel (P5) son las de los accesos: `access.rules.acceso_a_reemplazar`.

Decisiones del orquestador (pendientes de validar en la prueba de concepto):
- Áreas del catálogo: las de `user_areas` del actor; un admin de área ve
  además las que administra, solo para ver (`can_request = false`, RF-03). El
  superadmin ve todas, solo para ver.
- Solo plataformas `Activo` de áreas `Activo`.
- Un nivel es solicitable si la plataforma lo tiene integrado: tipo `ldap`
  con el DN de grupo de ese nivel, o tipo `conector` configurado
  (`platforms.estado.tiene_conector`).
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func

from app.authz import is_admin, is_area_admin, managed_area_ids
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.rules import acceso_a_reemplazar
from app.modules.access.tipos import (ESTADOS_OCUPANTES, ESTADOS_VIGENTES,
                                      NIVELES)
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.tipos import ESTADO_PENDIENTE
from app.modules.core.models import Area, Platform
from app.modules.platforms.estado import tiene_conector
from app.modules.platforms.tipos import CAMPOS_DN, TIPO_CONECTOR, TIPO_LDAP

# `status` de un área o plataforma visible en el catálogo.
ESTADO_ACTIVO = 'Activo'


# --------------------------------------------------------------------------- #
# Plataformas del catálogo
# --------------------------------------------------------------------------- #

def areas_del_actor(actor):
    """IDs de las áreas del catálogo; `None` = todas (superadmin)."""
    if is_admin(actor):
        return None
    ids = {a.id for a in (actor.areas or [])}
    ids.update(managed_area_ids(actor))
    return ids


def administra_area(actor, area_id):
    """`True` si el actor es admin de esa área (RF-03: no la solicita)."""
    return is_area_admin(actor) and area_id in managed_area_ids(actor)


def _consulta(actor, solo_activas=True):
    consulta = Platform.query.join(Area, Area.id == Platform.area_id)
    if solo_activas:
        consulta = consulta.filter(Platform.status == ESTADO_ACTIVO,
                                   Area.status == ESTADO_ACTIVO)
    ids = areas_del_actor(actor)
    if ids is not None:
        consulta = consulta.filter(Platform.area_id.in_(ids))
    return consulta


def plataformas(actor, area_id=None, q=None):
    """Plataformas del catálogo, por área y nombre (orden del contrato)."""
    consulta = _consulta(actor)
    if area_id is not None:
        consulta = consulta.filter(Platform.area_id == area_id)
    if q:
        consulta = consulta.filter(
            func.lower(Platform.name).contains(q.lower(), autoescape=True))
    return consulta.order_by(Area.name, Platform.name, Platform.id).all()


def plataforma_en_alcance(actor, plataforma_id):
    """La plataforma si es de un área del catálogo del actor, activa o no;
    si no, `None` (404, igual que inexistente)."""
    return (_consulta(actor, solo_activas=False)
            .filter(Platform.id == plataforma_id).first())


def activa(plataforma):
    area = plataforma.area
    return (plataforma.status == ESTADO_ACTIVO and area is not None
            and area.status == ESTADO_ACTIVO)


def niveles_integrados(plataforma):
    """Niveles que la plataforma puede otorgar hoy (ninguno si está inactiva)."""
    if not activa(plataforma):
        return ()
    if plataforma.integration_type == TIPO_CONECTOR:
        return NIVELES if tiene_conector(plataforma) else ()
    if plataforma.integration_type == TIPO_LDAP:
        return tuple(n for n in NIVELES if getattr(plataforma, CAMPOS_DN[n]))
    return ()


# --------------------------------------------------------------------------- #
# Estado del actor
# --------------------------------------------------------------------------- #

@dataclass
class EstadoDelActor:
    """Accesos vigentes y solicitud pendiente del actor en una plataforma."""
    vigentes: list
    pendiente: Optional[PlatformAccessRequest] = None

    @property
    def acceso(self):
        """El acceso que ocupa el nivel o, si no hay, el que está saliendo."""
        ocupante = next((a for a in self.vigentes
                         if a.status in ESTADOS_OCUPANTES), None)
        return ocupante or (self.vigentes[0] if self.vigentes else None)

    @property
    def nivel_actual(self):
        """Nivel ocupado (P5); `None` si no hay o si solo está saliendo."""
        ocupante = next((a for a in self.vigentes
                         if a.status in ESTADOS_OCUPANTES), None)
        return ocupante.level if ocupante is not None else None


def estados(usuario_id, plataforma_ids):
    """`{plataforma_id: EstadoDelActor}` en dos consultas."""
    resultado = {pid: EstadoDelActor(vigentes=[]) for pid in plataforma_ids}
    if not resultado:
        return resultado
    accesos = PlatformAccessGrant.query.filter(
        PlatformAccessGrant.user_id == usuario_id,
        PlatformAccessGrant.platform_id.in_(resultado),
        PlatformAccessGrant.status.in_(ESTADOS_VIGENTES)).all()
    for acceso in accesos:
        resultado[acceso.platform_id].vigentes.append(acceso)
    pendientes = PlatformAccessRequest.query.filter(
        PlatformAccessRequest.user_id == usuario_id,
        PlatformAccessRequest.platform_id.in_(resultado),
        PlatformAccessRequest.status == ESTADO_PENDIENTE).all()
    for solicitud in pendientes:
        resultado[solicitud.platform_id].pendiente = solicitud
    return resultado


def estado(usuario_id, plataforma_id):
    return estados(usuario_id, [plataforma_id])[plataforma_id]


def nivel_admitido(vigentes, nivel):
    """`True` si P5 permite pedir `nivel` con esos accesos vigentes."""
    try:
        acceso_a_reemplazar(vigentes, nivel)
    except ErrorDeAcceso:
        return False
    return True


def niveles_solicitables(actor, plataforma, estado_actor):
    """`requestable_levels` del contrato (vacío = `can_request` falso)."""
    if (is_admin(actor) or administra_area(actor, plataforma.area_id)
            or estado_actor.pendiente is not None):
        return []
    return [n for n in niveles_integrados(plataforma)
            if nivel_admitido(estado_actor.vigentes, n)]
