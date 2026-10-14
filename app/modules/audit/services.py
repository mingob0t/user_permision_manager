from app import db
from app.modules.audit.events import ACTOR_SISTEMA, Evento
from app.modules.audit.ip_cliente import ip_cliente
from app.modules.audit.models import AuditLog
from app.modules.audit.sanitizar import limpiar_detalle
from flask import has_request_context
from flask_login import current_user

# IP registrada cuando el evento no viene de una petición (procesos internos).
IP_INTERNA = 'INTERNAL'


def _recortar(valor, columna):
    """Recorta al largo de la columna: un INSERT más largo falla en MySQL estricto."""
    if valor is None:
        return None
    return str(valor)[:AuditLog.__table__.c[columna].type.length]


def _actor(as_system):
    """(correo o "sistema", id del actor o None)."""
    if (as_system or not has_request_context()
            or not current_user.is_authenticated):
        return ACTOR_SISTEMA, None
    return current_user.email, current_user.id


def add_audit_log(action, status='info', detail=None, user_override=None,
                  module=None, target=None, *, target_user_id=None,
                  area_id=None, platform_id=None, before=None, after=None,
                  request_id=None, grant_id=None, as_system=False):
    """
    Registra un evento en la tabla de auditoría.

    - Compatible con las llamadas existentes; lo nuevo (FNC-047) es opcional y
      solo por nombre.
    - `action`: un `Evento` del catálogo (`events.py`) o el texto heredado.
    - `as_system=True`: actúa el sistema (`user = "sistema"`, sin actor) aunque
      haya sesión; fuera de una petición o sin sesión también es "sistema".
    - `before`/`after`: estado antes y después; se quitan datos sensibles.
    - Los textos se recortan al largo de su columna (SEG-25).
    """
    try:
        user_name, actor_id = _actor(as_system)
        if user_override:
            user_name, actor_id = user_override, None
        ip = ip_cliente() if has_request_context() else IP_INTERNA
        if isinstance(action, Evento):
            action = action.value

        log = AuditLog(
            user=_recortar(user_name, 'user'),
            action=_recortar(action, 'action'),
            status=status,
            detail=detail,
            module=_recortar(module, 'module'),
            target=_recortar(target, 'target'),
            ip_address=_recortar(ip, 'ip_address'),
            actor_id=actor_id,
            target_user_id=target_user_id,
            area_id=area_id,
            platform_id=platform_id,
            before_state=limpiar_detalle(before),
            after_state=limpiar_detalle(after),
            request_id=request_id,
            grant_id=grant_id,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"❌ Error al escribir en AuditLog: {e}")
        db.session.rollback()
