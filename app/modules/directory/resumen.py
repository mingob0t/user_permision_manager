"""Configuración efectiva del directorio, sin secretos (FNC-043).

La configuración sale solo de las variables `LDAP_*` (ADR-004); este módulo
arma la vista que devuelve `GET /api/v1/auth-config`: cada valor, la variable
que lo define y su origen (`env` o `default`). La contraseña de bind nunca
sale (SEC-LDAP-11), ni la ruta de la CA (solo si es propia o la del sistema).
"""
import logging
import os

from app.modules.directory import configuracion as cfg_mod
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 cargar_configuracion,
                                                 directorio_activo)

logger = logging.getLogger(__name__)

ORIGEN_ENTORNO = 'env'
ORIGEN_POR_DEFECTO = 'default'
FUENTE = 'env'  # toda la configuración del directorio viene del entorno

TLS_LDAPS = 'ldaps'
TLS_STARTTLS = 'starttls'
CA_PROPIA = 'custom'
CA_SISTEMA = 'system'

# Campo de la respuesta → variable de entorno que lo define.
VARIABLES = {
    'url': cfg_mod.VAR_URL,
    'ca_cert': cfg_mod.VAR_CA_CERT_FILE,
    'bind_dn': cfg_mod.VAR_BIND_DN,
    'users_base_dn': cfg_mod.VAR_USUARIOS_BASE_DN,
    'groups_base_dn': cfg_mod.VAR_GRUPOS_BASE_DN,
    'user_attr': cfg_mod.VAR_ATRIBUTO_USUARIO,
    'group_object_class': cfg_mod.VAR_CLASE_GRUPO,
    'group_member_attr': cfg_mod.VAR_ATRIBUTO_MIEMBRO,
    'timeout_seconds': cfg_mod.VAR_TIEMPO_ESPERA,
    'user_object_classes': cfg_mod.VAR_CLASES_USUARIO,
    'placeholder_member': cfg_mod.VAR_MIEMBRO_RELLENO,
}


def _origenes(entorno):
    return {campo: (ORIGEN_ENTORNO if (entorno.get(variable) or '').strip()
                    else ORIGEN_POR_DEFECTO)
            for campo, variable in VARIABLES.items()}


def _valores(cfg):
    return {
        'url': cfg.url,
        'host': cfg.host,
        'port': cfg.puerto,
        'tls': TLS_LDAPS if cfg.usa_ldaps else TLS_STARTTLS,
        'ca_cert': CA_PROPIA if cfg.ca_cert_file else CA_SISTEMA,
        'bind_dn': cfg.bind_dn,
        'users_base_dn': cfg.usuarios_base_dn,
        'groups_base_dn': cfg.grupos_base_dn,
        'user_attr': cfg.atributo_usuario,
        'group_object_class': cfg.clase_grupo,
        'group_member_attr': cfg.atributo_miembro,
        'timeout_seconds': cfg.tiempo_espera,
        'user_object_classes': list(cfg.clases_usuario),
        'placeholder_member': cfg.miembro_relleno,
    }


def configuracion_publica(entorno=None):
    """Vista sin secretos de la configuración efectiva.

    - `active`: `LDAP_URL` tiene valor.
    - `editable`: siempre `False`; se cambia en el entorno (ADR-004).
    - `config`: valores efectivos, o `None` si está inactivo o es inválido.
    - `error`: `configuracion_invalida` si no se pudo cargar (detalle al log).
    """
    entorno = os.environ if entorno is None else entorno
    vista = {'active': directorio_activo(entorno), 'source': FUENTE,
             'editable': False, 'variables': dict(VARIABLES),
             'origins': _origenes(entorno), 'config': None, 'error': None}
    if not vista['active']:
        return vista
    try:
        vista['config'] = _valores(cargar_configuracion(entorno))
    except ErrorConfiguracionDirectorio as exc:
        # El mensaje nombra la variable, nunca su valor.
        logger.error('Directorio: configuración inválida: %s', exc)
        vista['error'] = 'configuracion_invalida'
    return vista
