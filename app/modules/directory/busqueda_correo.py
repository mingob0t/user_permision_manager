"""Búsqueda de una persona del directorio por su correo (FNC-064).

- Lectura con la cuenta de servicio del cliente único (`ClienteDirectorio`),
  bajo `LDAP_USERS_BASE_DN` y con el filtro escapado (SEC-LDAP-06).
- Vive aquí y no en `ldap_client.py` para no tocar el cliente compartido;
  `ldap3` sigue confinado al módulo `directory` (SEC-LDAP-01).
- Un fallo se registra sin el mensaje del servidor ni el correo (dato de la
  persona) y se lanza como `ErrorDirectorio`.
"""
from ldap3 import SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPSizeLimitExceededResult

from app.modules.directory.ldap_client import escapar_filtro

ATRIBUTO_CORREO = 'mail'


def correo_en_directorio(cliente, correo):
    """`True` si alguna entrada de la OU de personas tiene ese `mail`."""
    cfg = cliente.configuracion
    filtro = f'({ATRIBUTO_CORREO}={escapar_filtro(correo)})'
    with cliente.conexion_servicio() as conexion:
        try:
            conexion.search(cfg.usuarios_base_dn, filtro, SUBTREE,
                            attributes=[], size_limit=1)
        except LDAPSizeLimitExceededResult:
            return True
        except LDAPException as exc:
            raise cliente.registrar_error('búsqueda de correo', exc,
                                          con_detalle=False) from None
        return bool(conexion.entries)
