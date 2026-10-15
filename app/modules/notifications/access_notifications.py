"""Avisos por correo del gestor de accesos (FNC-048).

- Una función por evento; los módulos de solicitudes, aprobaciones y
  aprovisionamiento solo llaman a la del evento.
- Se llaman **después del commit** de la operación (y dentro de `try` en el
  llamador): un fallo de correo nunca la revierte; queda en el log y en
  auditoría (`notificacion_fallida`).
- Ninguna función pública lanza: datos incompletos (sin área, sin usuario,
  operación desconocida) se registran en el log y devuelven `error`.
- Los destinatarios salen de la BD, nunca de la petición (SEC-MAIL-03), y van
  agrupados en un solo envío por evento.
- El contexto lleva solo las claves de `CLAVES_POR_PLANTILLA` (SEC-MAIL-02); el
  escape HTML lo hace `send_notification_by_slug` (SEC-MAIL-01).
- Envío síncrono: la cola de ADR-003 (FNC-049) aún no existe.
"""

import logging
import os
import re
from functools import wraps

from sqlalchemy import func

from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.notifications import services

logger = logging.getLogger(__name__)

SLUG_SOLICITUD_NUEVA = 'solicitud_nueva'
SLUG_SOLICITUD_APROBADA = 'solicitud_aprobada'
SLUG_SOLICITUD_RECHAZADA = 'solicitud_rechazada'
SLUG_APROVISIONAMIENTO_FALLIDO = 'aprovisionamiento_fallido'

# Lista blanca de variables por plantilla (SEC-MAIL-02).
CLAVES_POR_PLANTILLA = {
    SLUG_SOLICITUD_NUEVA: ('solicitante', 'correo_solicitante', 'nivel',
                           'plataforma', 'area', 'justificacion', 'url'),
    SLUG_SOLICITUD_APROBADA: ('solicitante', 'nivel', 'plataforma', 'area',
                              'url'),
    SLUG_SOLICITUD_RECHAZADA: ('solicitante', 'nivel', 'plataforma', 'area',
                               'motivo', 'url'),
    SLUG_APROVISIONAMIENTO_FALLIDO: ('operacion', 'nivel', 'usuario',
                                     'correo_usuario', 'plataforma', 'area',
                                     'url'),
}

OPERACION_OTORGAR = 'otorgar'
OPERACION_REVOCAR = 'revocar'
OPERACIONES = (OPERACION_OTORGAR, OPERACION_REVOCAR)

# Interruptor de estos avisos; `ENABLE_NOTIFICATIONS` sigue cortando todo.
VARIABLE_INTERRUPTOR = 'NOTIFY_ACCESS_EVENTS'
MODULO_AUDITORIA = 'Notificaciones'
SEPARADOR_DESTINATARIOS = ', '
# Dirección simple: sin espacios, comas ni saltos (no abre otra cabecera).
PATRON_CORREO = re.compile(r'^[^@\s,<>;]+@[^@\s,<>;]+$')

ENVIADO = 'success'
OMITIDO = 'skipped'
FALLIDO = 'error'


# --------------------------------------------------------------------------- #
# Destinatarios
# --------------------------------------------------------------------------- #

def _rol(usuario):
    return (usuario.role or '').lower()


def _quiere_correo(usuario, respetar_preferencia):
    return not respetar_preferencia or usuario.pref_email_notifications is not False


def admins_del_area(area, respetar_preferencia=True, excluir_id=None):
    """Admins de área activos que administran `area` (tabla `area_admins`)."""
    if area is None:
        return []
    return [u for u in area.admins
            if u.is_active and _rol(u) == ROLE_AREA_ADMIN
            and u.id != excluir_id
            and _quiere_correo(u, respetar_preferencia)]


def superadmins(respetar_preferencia=True):
    """Superadmins activos."""
    usuarios = User.query.filter(func.lower(User.role) == ROLE_ADMIN,
                                 User.is_active.is_(True)).all()
    return [u for u in usuarios if _quiere_correo(u, respetar_preferencia)]


def correos(usuarios):
    """Correos válidos, sin repetir y en orden estable."""
    vistos = []
    for usuario in usuarios:
        correo = (usuario.email or '').strip()
        if not PATRON_CORREO.match(correo):
            logger.warning('Correo inválido omitido en un aviso (usuario %s).',
                           usuario.id)
        elif correo not in vistos:
            vistos.append(correo)
    return vistos


# --------------------------------------------------------------------------- #
# Envío
# --------------------------------------------------------------------------- #

def avisos_activos():
    return services._env_flag(VARIABLE_INTERRUPTOR, True)


def _url_portal():
    """Enlace del correo: solo de `BASE_URL`, nunca del `Host` (SEC-MAIL-05)."""
    return (os.getenv('BASE_URL') or '').strip().rstrip('/')


def _nombre(usuario):
    return (usuario.nombre or '').strip() or usuario.email


def _contexto(slug, **valores):
    valores['url'] = _url_portal()
    return {clave: '' if valores.get(clave) is None else str(valores[clave])
            for clave in CLAVES_POR_PLANTILLA[slug]}


def _enviar(slug, destinatarios, contexto, *, area_id=None, platform_id=None,
            target_user_id=None):
    """Envía `slug` a todos los destinatarios; nunca lanza excepción."""
    if not avisos_activos():
        return {'status': OMITIDO, 'recipients': 0}
    if not destinatarios:
        logger.warning("Aviso '%s' sin destinatarios.", slug)
        return {'status': OMITIDO, 'recipients': 0}

    total = len(destinatarios)
    try:
        resultado = services.send_notification_by_slug(
            slug, SEPARADOR_DESTINATARIOS.join(destinatarios), contexto)
    except Exception:
        logger.exception("Error inesperado al enviar el aviso '%s'.", slug)
        resultado = {'status': FALLIDO}

    if resultado.get('status') == ENVIADO:
        return {'status': ENVIADO, 'recipients': total}

    logger.warning("No se envió el aviso '%s' a %d destinatario(s): %s", slug,
                   total, resultado.get('message'))
    add_audit_log(Evento.NOTIFICACION_FALLIDA, status='error',
                  detail=f"No se envió el correo '{slug}' a {total} "
                         'destinatario(s).',
                  module=MODULO_AUDITORIA, target=slug,
                  target_user_id=target_user_id, area_id=area_id,
                  platform_id=platform_id, as_system=True)
    return {'status': FALLIDO, 'recipients': total}


# --------------------------------------------------------------------------- #
# Un aviso por evento
# --------------------------------------------------------------------------- #

class DatosIncompletos(ValueError):
    """Faltan datos para armar el aviso; se registra y no se envía."""


def _sin_excepciones(funcion):
    """El aviso nunca rompe al llamador: registra y devuelve `error`."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except DatosIncompletos as error:
            logger.warning("Aviso '%s' omitido: %s", funcion.__name__, error)
        except Exception:
            logger.exception("Error inesperado al preparar el aviso '%s'.",
                             funcion.__name__)
        return {'status': FALLIDO, 'recipients': 0}
    return envoltura


def _area_de(plataforma):
    area = getattr(plataforma, 'area', None)
    if area is None:
        raise DatosIncompletos('plataforma sin área')
    return area


def _exigir(usuario):
    if usuario is None:
        raise DatosIncompletos('sin usuario')
    return usuario


@_sin_excepciones
def notificar_solicitud_nueva(solicitante, plataforma, nivel, justificacion):
    """A los admins del área de la plataforma (no al solicitante)."""
    _exigir(solicitante)
    area = _area_de(plataforma)
    destinatarios = correos(admins_del_area(area, excluir_id=solicitante.id))
    contexto = _contexto(SLUG_SOLICITUD_NUEVA,
                         solicitante=_nombre(solicitante),
                         correo_solicitante=solicitante.email, nivel=nivel,
                         plataforma=plataforma.name, area=area.name,
                         justificacion=justificacion)
    return _enviar(SLUG_SOLICITUD_NUEVA, destinatarios, contexto,
                   area_id=area.id, platform_id=plataforma.id,
                   target_user_id=solicitante.id)


def _al_solicitante(slug, solicitante, plataforma, nivel, **extra):
    _exigir(solicitante)
    area = _area_de(plataforma)
    activo = solicitante.is_active and _quiere_correo(solicitante, True)
    destinatarios = correos([solicitante]) if activo else []
    contexto = _contexto(slug, solicitante=_nombre(solicitante), nivel=nivel,
                         plataforma=plataforma.name, area=area.name, **extra)
    return _enviar(slug, destinatarios, contexto, area_id=area.id,
                   platform_id=plataforma.id, target_user_id=solicitante.id)


@_sin_excepciones
def notificar_solicitud_aprobada(solicitante, plataforma, nivel):
    """Al solicitante."""
    return _al_solicitante(SLUG_SOLICITUD_APROBADA, solicitante, plataforma,
                           nivel)


@_sin_excepciones
def notificar_solicitud_rechazada(solicitante, plataforma, nivel, motivo):
    """Al solicitante, con el motivo."""
    return _al_solicitante(SLUG_SOLICITUD_RECHAZADA, solicitante, plataforma,
                           nivel, motivo=motivo)


@_sin_excepciones
def notificar_aprovisionamiento_fallido(usuario, plataforma, nivel, operacion):
    """A los admins del área y a los superadmins (P10).

    - Respeta `pref_email_notifications` (respuesta del dueño, 2026-10-15).
    - `operacion`: `otorgar` o `revocar`; otra se registra y no se envía.
    """
    if operacion not in OPERACIONES:
        raise DatosIncompletos(f'operación desconocida: {operacion}')
    _exigir(usuario)
    area = _area_de(plataforma)
    destinatarios = correos(admins_del_area(area) + superadmins())
    contexto = _contexto(SLUG_APROVISIONAMIENTO_FALLIDO, operacion=operacion,
                         nivel=nivel, usuario=_nombre(usuario),
                         correo_usuario=usuario.email,
                         plataforma=plataforma.name, area=area.name)
    return _enviar(SLUG_APROVISIONAMIENTO_FALLIDO, destinatarios, contexto,
                   area_id=area.id, platform_id=plataforma.id,
                   target_user_id=usuario.id)
