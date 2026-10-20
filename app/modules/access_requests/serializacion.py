"""Formas `AccessRequest` y entrada del catálogo (contrato `solicitudes.md`)."""
from app.modules.access.models import PlatformAccessGrant
from app.modules.access_requests import catalogo

FORMATO_FECHA = '%Y-%m-%dT%H:%M:%SZ'  # ISO 8601 en UTC con `Z`


def fecha(valor):
    return valor.strftime(FORMATO_FECHA) if valor is not None else None


def _nombre(usuario):
    return (usuario.nombre or '').strip() or usuario.email


def accesos_de(solicitudes):
    """`{request_id: acceso}` de las solicitudes aprobadas, en una consulta."""
    ids = [s.id for s in solicitudes]
    if not ids:
        return {}
    accesos = (PlatformAccessGrant.query
               .filter(PlatformAccessGrant.request_id.in_(ids))
               .order_by(PlatformAccessGrant.id).all())
    return {a.request_id: a for a in accesos}


def solicitud(registro, acceso=None):
    """`AccessRequest`."""
    plataforma, usuario, decisor = (registro.platform, registro.requester,
                                    registro.decider)
    area = plataforma.area
    return {
        'id': registro.id,
        'status': registro.status,
        'level': registro.level,
        'justification': registro.justification,
        'requester': {'id': usuario.id, 'name': _nombre(usuario),
                      'email': usuario.email},
        'platform': {'id': plataforma.id, 'name': plataforma.name},
        'area': {'id': area.id, 'name': area.name} if area else None,
        'current_level': registro.current_level,
        'created_at': fecha(registro.created_at),
        'decided_at': fecha(registro.decided_at),
        'decided_by': ({'id': decisor.id, 'name': _nombre(decisor)}
                       if decisor is not None else None),
        'rejection_reason': registro.rejection_reason,
        'access': ({'id': acceso.id, 'status': acceso.status}
                   if acceso is not None else None),
    }


def entrada_catalogo(actor, plataforma, estado_actor):
    """Una plataforma del catálogo con el estado del actor."""
    acceso = estado_actor.acceso
    niveles = catalogo.niveles_solicitables(actor, plataforma, estado_actor)
    pendiente = estado_actor.pendiente
    area = plataforma.area
    return {
        'platform': {'id': plataforma.id, 'name': plataforma.name,
                     'description': plataforma.description,
                     'icon': plataforma.icon},
        'area': {'id': area.id, 'name': area.name},
        'my_level': acceso.level if acceso is not None else None,
        'my_access_status': acceso.status if acceso is not None else None,
        'pending_request_id': pendiente.id if pendiente is not None else None,
        'can_request': bool(niveles),
        'requestable_levels': niveles,
    }
