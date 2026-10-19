"""Log detallado de `ldap3` con `DEBUG_LDAP=true` (movido de `auth/services.py`
en FNC-043 para que solo este paquete importe `ldap3`, SEC-LDAP-01).

Mismo comportamiento que antes: nivel `EXTENDED` en `logs/ldap_debug.log` y
en la consola. `ldap3` oculta las contraseñas de bind en su log.
"""
import logging
import os

from ldap3.utils.log import EXTENDED, set_library_log_detail_level

VAR_DEBUG = 'DEBUG_LDAP'
CARPETA_LOG = 'logs'
ARCHIVO_LOG = 'ldap_debug.log'


def activar_si_se_pide(entorno=None):
    """Activa el log detallado si `DEBUG_LDAP` vale `true`."""
    entorno = os.environ if entorno is None else entorno
    if entorno.get(VAR_DEBUG) != 'true':
        return False
    set_library_log_detail_level(EXTENDED)
    registro = logging.getLogger('ldap3')
    registro.setLevel(logging.DEBUG)
    if not registro.handlers:
        carpeta = os.path.join(os.getcwd(), CARPETA_LOG)
        os.makedirs(carpeta, exist_ok=True)
        archivo = logging.FileHandler(os.path.join(carpeta, ARCHIVO_LOG))
        archivo.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'))
        registro.addHandler(archivo)
        registro.addHandler(logging.StreamHandler())
    return True
