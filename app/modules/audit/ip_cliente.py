"""IP real del cliente para la auditoría (SEC-AUD-04, SEG-25).

- Si la petición llega de un proxy de `TRUSTED_PROXIES`, se toma la última
  entrada de `X-Forwarded-For` (la que agrega nginx con
  `$proxy_add_x_forwarded_for`; equivale a `ProxyFix(x_for=1)`).
- Si llega de otro origen, `X-Forwarded-For` se ignora y vale `remote_addr`.
- No se aplica `ProxyFix` global: cambiaría `request.remote_addr`, que la
  verificación del SSO compara con `TRUSTED_PROXIES` (`api/auth.py`).
"""

from flask import request

CABECERA_REENVIO = 'X-Forwarded-For'


def ip_cliente():
    """Dirección del cliente de la petición en curso."""
    # Importación diferida: `api/auth.py` importa este módulo vía `services`.
    from app.modules.api.auth import _trusted_proxy

    origen = request.remote_addr
    if not _trusted_proxy():
        return origen
    saltos = [s.strip() for s in request.headers.get(CABECERA_REENVIO, '').split(',')
              if s.strip()]
    return saltos[-1] if saltos else origen
