"""Higiene de cuentas: purga de usuarios inactivos (D-05, FNC-030).

Única implementación: la API (`api/crud.py`) valida el periodo y delega aquí.
Sustituye a `purge_inactive_users` de `auth/services.py` (heredada, sin uso,
con un criterio que dejaba fuera a las cuentas que nunca iniciaron sesión).
"""

from datetime import datetime, timedelta

from app import db
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.users.roles import MODULO_AUDITORIA

# Periodo mínimo: un umbral bajo borraría cuentas recién creadas.
PURGE_MIN_DAYS = 7
# Correos que se listan en el detalle de la auditoría.
PURGE_MAX_AUDITADOS = 20


def usuarios_inactivos(days):
    """Cuentas candidatas a purga por inactividad.

    Incluye las que nunca han iniciado sesión y son más antiguas que el
    umbral: comparar `last_login_at < cutoff` descarta los nulos, y eran
    justo las más claras. Nunca se purga a un superadmin.
    """
    cutoff = datetime.now() - timedelta(days=days)
    return User.query.filter(
        db.func.lower(db.func.coalesce(User.role, '')) != 'administrador',
        db.or_(
            User.last_login_at < cutoff,
            db.and_(User.last_login_at.is_(None), User.created_at < cutoff),
        ),
    )


def purgar_inactivos(days):
    """Elimina las cuentas inactivas, audita y devuelve sus correos."""
    users = usuarios_inactivos(days).all()
    purged = [u.email for u in users]
    for user in users:
        db.session.delete(user)
    db.session.commit()

    if purged:
        add_audit_log(
            f'PURGAR CUENTAS INACTIVAS ({len(purged)})',
            module=MODULO_AUDITORIA, status='warning',
            detail=(f"Inactividad > {days} días: "
                    f"{', '.join(purged[:PURGE_MAX_AUDITADOS])}"))
    return purged
