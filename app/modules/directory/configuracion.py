"""Configuración del directorio OpenLDAP leída de variables de entorno (ADR-004).

El directorio está activo cuando `LDAP_URL` tiene valor. Activo, toda la
configuración se valida al arrancar (`validar_al_arrancar`): si falta algo o
no hay TLS, la app no arranca y el mensaje dice qué variable corregir.

TLS es obligatorio: `ldaps://` o `ldap://` con StartTLS; no hay modo sin
cifrar. El certificado del servidor se valida siempre (CA del sistema o la de
`LDAP_CA_CERT_FILE`).
"""
import ipaddress
import os
import re
from dataclasses import dataclass, field
from string import Formatter
from urllib.parse import urlsplit

from ldap3.core.exceptions import LDAPInvalidDnError
from ldap3.utils.dn import parse_dn

from app.modules.directory.dn import bajo_base

# Nombres de las variables (registradas en docs/configuracion/VARIABLES.md).
VAR_URL = 'LDAP_URL'
VAR_CA_CERT_FILE = 'LDAP_CA_CERT_FILE'
VAR_BIND_DN = 'LDAP_BIND_DN'
VAR_BIND_PASSWORD = 'LDAP_BIND_PASSWORD'
VAR_USUARIOS_BASE_DN = 'LDAP_USERS_BASE_DN'
VAR_GRUPOS_BASE_DN = 'LDAP_GROUPS_BASE_DN'
VAR_ATRIBUTO_USUARIO = 'LDAP_USER_ATTR'
VAR_CLASE_GRUPO = 'LDAP_GROUP_OBJECT_CLASS'
VAR_ATRIBUTO_MIEMBRO = 'LDAP_GROUP_MEMBER_ATTR'
VAR_TIEMPO_ESPERA = 'LDAP_TIMEOUT_SECONDS'
VAR_CLASES_USUARIO = 'LDAP_USER_OBJECT_CLASSES'
VAR_MIEMBRO_RELLENO = 'LDAP_GROUP_PLACEHOLDER_MEMBER'
VAR_PLANTILLA_GRUPO = 'LDAP_PLATFORM_GROUP_TEMPLATE'

# Valores por defecto: esquema estándar de OpenLDAP (inetOrgPerson y
# groupOfNames), no datos de un directorio real.
ATRIBUTO_USUARIO_POR_DEFECTO = 'uid'
CLASE_GRUPO_POR_DEFECTO = 'groupOfNames'
ATRIBUTO_MIEMBRO_POR_DEFECTO = 'member'
TIEMPO_ESPERA_POR_DEFECTO = 5  # segundos; el mismo que usaba el código heredado
# Clases de una cuenta creada por el portal (FNC-041); separadas por coma.
CLASES_USUARIO_POR_DEFECTO = ('inetOrgPerson',)

# Esquema de la URL → (TLS desde la conexión, puerto por defecto).
# `ldap://` siempre negocia StartTLS antes del bind.
ESQUEMAS_PERMITIDOS = {'ldaps': (True, 636), 'ldap': (False, 389)}

# Nombre de atributo o clase (RFC 4512: descriptor) u OID numérico. Se valida
# porque estos valores se insertan en filtros sin escapar.
# Formas abreviadas, decimales u octales/hexadecimales de IPv4 (`inet_aton`
# las resuelve aunque `ipaddress` no): un "host" solo con números se rechaza.
_IPV4_NUMERICA = re.compile(r'^(?:0x[0-9a-f]+|\d+)(?:\.(?:0x[0-9a-f]+|\d+))*\.?$',
                            re.IGNORECASE)

_NOMBRE_ATRIBUTO = re.compile(r'^(?:[A-Za-z][A-Za-z0-9-]*|\d+(?:\.\d+)+)$')

# Plantilla del DN de grupo de una plataforma, relativa a LDAP_GROUPS_BASE_DN
# (FNC-046, ADR-004 P3): marcadores permitidos y obligatorios. `{nivel}` hace
# distintos los grupos de usuario y admin.
MARCADORES_PLANTILLA_GRUPO = frozenset({'plataforma', 'area', 'nivel'})
MARCADORES_OBLIGATORIOS_GRUPO = frozenset({'plataforma', 'nivel'})
VALOR_MUESTRA_PLANTILLA = 'muestra'


class ErrorConfiguracionDirectorio(RuntimeError):
    """La configuración del directorio está incompleta o es insegura."""


@dataclass(frozen=True)
class ConfiguracionDirectorio:
    """Configuración validada del directorio. La contraseña no sale en `repr`."""

    url: str
    host: str
    puerto: int
    usa_ldaps: bool
    ca_cert_file: str | None
    bind_dn: str
    bind_password: str = field(repr=False)
    usuarios_base_dn: str = ''
    grupos_base_dn: str = ''
    atributo_usuario: str = ATRIBUTO_USUARIO_POR_DEFECTO
    clase_grupo: str = CLASE_GRUPO_POR_DEFECTO
    atributo_miembro: str = ATRIBUTO_MIEMBRO_POR_DEFECTO
    tiempo_espera: int = TIEMPO_ESPERA_POR_DEFECTO
    clases_usuario: tuple = CLASES_USUARIO_POR_DEFECTO
    # Miembro que ocupa un grupo que exige al menos uno (FNC-041); None = sin él.
    miembro_relleno: str | None = None
    # Plantilla del DN de grupo de plataforma (FNC-046); None = no se deriva.
    plantilla_grupo: str | None = None


def _leer(entorno, nombre):
    return (entorno.get(nombre) or '').strip()


def directorio_activo(entorno=None):
    """`True` si `LDAP_URL` tiene valor."""
    entorno = os.environ if entorno is None else entorno
    return bool(_leer(entorno, VAR_URL))


def es_ip_literal(host):
    """`True` si `host` es una IP (v4, v6 o formas numéricas abreviadas)."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return bool(_IPV4_NUMERICA.match(host))


def _validar_url(url):
    partes = urlsplit(url)
    esquema = partes.scheme.lower()
    if esquema not in ESQUEMAS_PERMITIDOS:
        raise ErrorConfiguracionDirectorio(
            f'{VAR_URL} debe empezar con ldaps:// o ldap:// (con StartTLS); '
            'no se permite el directorio sin TLS.')
    host = partes.hostname
    if not host:
        raise ErrorConfiguracionDirectorio(f'{VAR_URL} no tiene nombre de host.')
    if es_ip_literal(host):
        raise ErrorConfiguracionDirectorio(
            f'{VAR_URL} debe usar un nombre de host, no una dirección IP '
            '(el certificado se valida contra el nombre).')
    if partes.path not in ('', '/') or partes.query or partes.fragment \
            or partes.username or partes.password:
        raise ErrorConfiguracionDirectorio(
            f'{VAR_URL} solo admite esquema, host y puerto.')
    try:
        puerto = partes.port
    except ValueError:
        raise ErrorConfiguracionDirectorio(
            f'{VAR_URL} tiene un puerto inválido.') from None
    usa_ldaps, puerto_por_defecto = ESQUEMAS_PERMITIDOS[esquema]
    return host, puerto or puerto_por_defecto, usa_ldaps


def _requerida(entorno, nombre):
    valor = _leer(entorno, nombre)
    if not valor:
        raise ErrorConfiguracionDirectorio(
            f'Falta {nombre} (obligatoria con {VAR_URL} definida).')
    return valor


def _dn(entorno, nombre):
    valor = _requerida(entorno, nombre)
    try:
        parse_dn(valor)
    except LDAPInvalidDnError:
        raise ErrorConfiguracionDirectorio(
            f'{nombre} no es un DN válido.') from None
    return valor


def _nombre_atributo(entorno, nombre, por_defecto):
    valor = _leer(entorno, nombre) or por_defecto
    if not _NOMBRE_ATRIBUTO.match(valor):
        raise ErrorConfiguracionDirectorio(
            f'{nombre} debe ser un nombre de atributo o clase de LDAP.')
    return valor


def _tiempo_espera(entorno):
    valor = _leer(entorno, VAR_TIEMPO_ESPERA)
    if not valor:
        return TIEMPO_ESPERA_POR_DEFECTO
    try:
        segundos = int(valor)
    except ValueError:
        segundos = 0
    if segundos <= 0:
        raise ErrorConfiguracionDirectorio(
            f'{VAR_TIEMPO_ESPERA} debe ser un entero de segundos mayor que 0.')
    return segundos


def _clases_usuario(entorno):
    valor = _leer(entorno, VAR_CLASES_USUARIO)
    if not valor:
        return CLASES_USUARIO_POR_DEFECTO
    clases = tuple(clase.strip() for clase in valor.split(','))
    if not all(_NOMBRE_ATRIBUTO.match(clase) for clase in clases):
        raise ErrorConfiguracionDirectorio(
            f'{VAR_CLASES_USUARIO} debe ser una lista de clases de LDAP '
            'separadas por coma.')
    return clases


def _miembro_relleno(entorno, usuarios_base_dn):
    """DN de relleno: una entrada sin login ni contraseña, nunca una persona."""
    if not _leer(entorno, VAR_MIEMBRO_RELLENO):
        return None
    relleno = _dn(entorno, VAR_MIEMBRO_RELLENO)
    if bajo_base(relleno, usuarios_base_dn, incluir_base=True):
        raise ErrorConfiguracionDirectorio(
            f'{VAR_MIEMBRO_RELLENO} no puede estar bajo {VAR_USUARIOS_BASE_DN} '
            '(debe ser una entrada sin login ni contraseña).')
    return relleno


def _plantilla_grupo(entorno):
    """Plantilla de RDN como `cn={plataforma}-{nivel},ou={area}`; None si vacía."""
    plantilla = _leer(entorno, VAR_PLANTILLA_GRUPO)
    if not plantilla:
        return None
    error = ErrorConfiguracionDirectorio(
        f'{VAR_PLANTILLA_GRUPO} debe ser un DN relativo con {{plataforma}} y '
        '{nivel} (y opcionalmente {area}), sin otros marcadores.')
    try:
        partes = list(Formatter().parse(plantilla))
    except ValueError:
        raise error from None
    marcadores = set()
    for _, campo, formato, conversion in partes:
        if campo is None:
            continue
        if formato or conversion or campo not in MARCADORES_PLANTILLA_GRUPO:
            raise error
        marcadores.add(campo)
    if not MARCADORES_OBLIGATORIOS_GRUPO <= marcadores:
        raise error
    muestra = plantilla.format(**{m: VALOR_MUESTRA_PLANTILLA
                                  for m in MARCADORES_PLANTILLA_GRUPO})
    try:
        parse_dn(muestra)
    except LDAPInvalidDnError:
        raise error from None
    return plantilla


def _ca_cert_file(entorno):
    ruta = _leer(entorno, VAR_CA_CERT_FILE)
    if not ruta:
        return None  # CA del sistema
    if not os.path.isfile(ruta) or not os.access(ruta, os.R_OK):
        raise ErrorConfiguracionDirectorio(
            f'{VAR_CA_CERT_FILE} no apunta a un archivo legible.')
    return ruta


def cargar_configuracion(entorno=None):
    """Lee y valida la configuración; lanza `ErrorConfiguracionDirectorio`."""
    entorno = os.environ if entorno is None else entorno
    url = _requerida(entorno, VAR_URL)
    host, puerto, usa_ldaps = _validar_url(url)
    usuarios_base_dn = _dn(entorno, VAR_USUARIOS_BASE_DN)
    return ConfiguracionDirectorio(
        url=url,
        host=host,
        puerto=puerto,
        usa_ldaps=usa_ldaps,
        ca_cert_file=_ca_cert_file(entorno),
        bind_dn=_dn(entorno, VAR_BIND_DN),
        bind_password=_requerida(entorno, VAR_BIND_PASSWORD),
        usuarios_base_dn=usuarios_base_dn,
        grupos_base_dn=_dn(entorno, VAR_GRUPOS_BASE_DN),
        atributo_usuario=_nombre_atributo(
            entorno, VAR_ATRIBUTO_USUARIO, ATRIBUTO_USUARIO_POR_DEFECTO),
        clase_grupo=_nombre_atributo(
            entorno, VAR_CLASE_GRUPO, CLASE_GRUPO_POR_DEFECTO),
        atributo_miembro=_nombre_atributo(
            entorno, VAR_ATRIBUTO_MIEMBRO, ATRIBUTO_MIEMBRO_POR_DEFECTO),
        tiempo_espera=_tiempo_espera(entorno),
        clases_usuario=_clases_usuario(entorno),
        miembro_relleno=_miembro_relleno(entorno, usuarios_base_dn),
        plantilla_grupo=_plantilla_grupo(entorno),
    )


def validar_al_arrancar(entorno=None):
    """Con el directorio activo, valida la configuración o detiene el arranque.

    Devuelve la configuración validada, o `None` si el directorio no está
    activo (sin `LDAP_URL`).
    """
    if not directorio_activo(entorno):
        return None
    return cargar_configuracion(entorno)
