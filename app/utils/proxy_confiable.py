"""Verificación del proxy autorizado a inyectar cabeceras de identidad.

Lo comparten el SSO (`api/auth.py`) y la IP real del cliente (`audit/ip_cliente.py`).
"""

import os

from flask import request


def es_proxy_confiable():
    """True si la petición viene de un proxy autorizado a inyectar Remote-*.

    Por defecto solo loopback, que es donde escucha Nginx en este despliegue.
    """
    allowed = {p.strip() for p in os.getenv(
        'TRUSTED_PROXIES', '127.0.0.1,::1').split(',') if p.strip()}
    return request.remote_addr in allowed
