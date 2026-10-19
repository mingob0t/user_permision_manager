"""Forma `ManagedUser` de los contratos (`GET /users` y escrituras)."""


def usuario_gestionado(cuenta):
    """Cuenta administrable tal como la devuelve la API."""
    return {
        'id': cuenta.id,
        'email': cuenta.email,
        'name': cuenta.nombre or cuenta.email,
        'role': cuenta.role,
        'is_active': cuenta.is_active,
        'auth_source': cuenta.auth_source,
        'areas': [{'id': a.id, 'name': a.name} for a in (cuenta.areas or [])],
        'managed_areas': [{'id': a.id, 'name': a.name}
                          for a in (cuenta.managed_areas or [])],
        'last_login_at': (cuenta.last_login_at.isoformat()
                          if cuenta.last_login_at else None),
    }
