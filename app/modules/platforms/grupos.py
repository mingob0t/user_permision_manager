"""Grupos del directorio de una plataforma: validar, derivar y comprobar (FNC-046).

- Todo DN de grupo debe estar debajo de `LDAP_GROUPS_BASE_DN`, comparando RDN
  normalizados (SEC-LDAP-04, `directory/dn.py`).
- Si no llega el DN, se deriva de `LDAP_PLATFORM_GROUP_TEMPLATE` (ADR-004 P3):
  los valores se convierten a un identificador ASCII y se escapan (SEC-LDAP-06).
- La existencia se comprueba con el cliente único (FNC-040). Que el grupo no
  exista o que el directorio no responda no es error: la plataforma se guarda
  con un aviso (los grupos los crea el administrador del directorio en v1).
"""
import re
import unicodedata

from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 cargar_configuracion,
                                                 directorio_activo)
from app.modules.directory.dn import bajo_base
from app.modules.directory.ldap_client import (ClienteDirectorio,
                                               ErrorDirectorio,
                                               escapar_valor_dn)
from app.modules.platforms.tipos import (GRUPOS_NO_EXISTE, GRUPOS_OK,
                                         GRUPOS_SIN_VERIFICAR)

# Avisos de la respuesta (`warnings`).
AVISO_GRUPO_NO_EXISTE = 'grupo_no_existe'
AVISO_DIRECTORIO_NO_DISPONIBLE = 'directorio_no_disponible'
MENSAJE_GRUPO_NO_EXISTE = 'El grupo de nivel {nivel} no existe en el directorio.'
MENSAJE_DIRECTORIO_NO_DISPONIBLE = ('No se pudo comprobar los grupos en el '
                                    'directorio; se guardaron sin verificar.')

_NO_IDENTIFICADOR = re.compile(r'[^a-z0-9]+')
SEPARADOR_IDENTIFICADOR = '-'


def configuracion_directorio():
    """Configuración validada del directorio, o `None` si está inactivo."""
    if not directorio_activo():
        return None
    try:
        return cargar_configuracion()
    except ErrorConfiguracionDirectorio:
        # Con el directorio activo, `validar_al_arrancar` ya la exigió; aquí
        # solo se protege una configuración cambiada en caliente.
        return None


def identificador(texto):
    """`Contabilidad General` → `contabilidad-general` (ASCII, sin acentos)."""
    plano = unicodedata.normalize('NFKD', texto or '')
    plano = plano.encode('ascii', 'ignore').decode('ascii').lower()
    return _NO_IDENTIFICADOR.sub(SEPARADOR_IDENTIFICADOR, plano).strip(
        SEPARADOR_IDENTIFICADOR)


def derivar_dn(configuracion, nivel, plataforma, area):
    """DN del grupo de `nivel` según la plantilla; `None` si no hay plantilla
    o si el nombre de la plataforma no deja un identificador."""
    plantilla = configuracion.plantilla_grupo
    nombre = identificador(plataforma)
    if not plantilla or not nombre:
        return None
    relativo = plantilla.format(plataforma=escapar_valor_dn(nombre),
                                area=escapar_valor_dn(identificador(area)),
                                nivel=escapar_valor_dn(nivel))
    return f'{relativo},{configuracion.grupos_base_dn}'


def dn_en_base(configuracion, dn):
    """`True` si `dn` es un DN válido debajo de la base de grupos."""
    return isinstance(dn, str) and bajo_base(dn, configuracion.grupos_base_dn)


def comprobar_grupos(configuracion, dns_por_nivel):
    """(`groups_status`, avisos) tras buscar cada DN en el directorio."""
    cliente = ClienteDirectorio(configuracion)
    avisos = []
    try:
        for nivel, dn in dns_por_nivel.items():
            if not cliente.existe_dn(dn):
                avisos.append({'code': AVISO_GRUPO_NO_EXISTE,
                               'message': MENSAJE_GRUPO_NO_EXISTE.format(
                                   nivel=nivel)})
    except ErrorDirectorio:
        return GRUPOS_SIN_VERIFICAR, [{
            'code': AVISO_DIRECTORIO_NO_DISPONIBLE,
            'message': MENSAJE_DIRECTORIO_NO_DISPONIBLE}]
    return (GRUPOS_NO_EXISTE if avisos else GRUPOS_OK), avisos
