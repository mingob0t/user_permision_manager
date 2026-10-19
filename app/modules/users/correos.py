"""Consultas de correos de cuentas del portal (FNC-043)."""
from app import db


def correos_registrados(correos):
    """Los de `correos` (en minúsculas) que ya tienen cuenta en el portal."""
    if not correos:
        return set()
    from app.modules.auth.models import User
    correo = db.func.lower(User.email)
    return {valor for (valor,) in
            db.session.query(correo).filter(correo.in_(correos))}
