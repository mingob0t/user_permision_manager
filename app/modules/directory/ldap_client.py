"""Cliente único de OpenLDAP con TLS validado (FNC-040).

- Conexión de servicio por LDAPS o StartTLS, con `CERT_REQUIRED`, verificación
  del nombre del host y la CA de `LDAP_CA_CERT_FILE` (o la del sistema).
- Tiempos de espera de conexión y de respuesta (`LDAP_TIMEOUT_SECONDS`).
- Todo valor que entra en un filtro se escapa (`escape_filter_chars`); los
  valores para armar un DN se escapan con `escapar_valor_dn`.
- Los errores salen como `ErrorDirectorio` con un mensaje genérico; el detalle
  va al log, nunca con la contraseña de bind.

Las lecturas usan una conexión de solo lectura. La escritura (membresía de
grupos y alta de cuentas, FNC-041) vive en `writer.py` y pide la conexión con
`solo_lectura=False`.
"""
import logging
import ssl
from contextlib import contextmanager
from dataclasses import dataclass, field

from ldap3 import BASE, SUBTREE, SYNC, Connection, Server, Tls
from ldap3.core.exceptions import (LDAPException, LDAPInvalidDnError,
                                   LDAPNoSuchObjectResult,
                                   LDAPSizeLimitExceededResult,
                                   LDAPStartTLSError)
from ldap3.core.exceptions import LDAPInvalidCredentialsResult
from ldap3.utils.conv import escape_filter_chars
from ldap3.utils.dn import escape_rdn, parse_dn

from app.modules.directory.configuracion import cargar_configuracion
from app.modules.directory.depuracion import activar_si_se_pide

logger = logging.getLogger(__name__)

# `DEBUG_LDAP` (antes en `auth/services.py`, al importar; FNC-043).
activar_si_se_pide()

# Estrategia de `ldap3`. Las pruebas la cambian por `MOCK_SYNC` (sin red).
ESTRATEGIA = SYNC

# Atributos de perfil de una persona (inetOrgPerson) que se leen al buscarla.
ATRIBUTOS_PERFIL = ('mail', 'cn', 'displayName')

# Atributos de membresía cuyo valor es el identificador del usuario y no su DN
# (posixGroup). El resto (`member`, `uniqueMember`) guarda el DN.
ATRIBUTOS_MIEMBRO_POR_IDENTIFICADOR = frozenset({'memberuid'})

# Una búsqueda por identificador debe dar a lo sumo una persona; se piden dos
# para detectar duplicados.
LIMITE_BUSQUEDA_USUARIO = 2

# Personas devueltas por la búsqueda libre del alta desde el directorio (FNC-043).
LIMITE_BUSQUEDA_PERSONAS = 50

MENSAJE_ERROR = 'No se pudo consultar el directorio.'
MENSAJE_AMBIGUO = 'El identificador corresponde a más de una persona.'


class ErrorDirectorio(Exception):
    """Fallo controlado del directorio; el mensaje es apto para el cliente.

    `causa` guarda la excepción de `ldap3` para clasificarla (FNC-041); nunca
    se muestra al cliente.
    """

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje)
        self.causa = causa


@dataclass(frozen=True)
class UsuarioDirectorio:
    """Persona encontrada: su DN, su identificador y sus atributos de perfil."""

    dn: str
    identificador: str
    atributos: dict = field(default_factory=dict)


def escapar_filtro(valor):
    """Escapa un valor para un filtro LDAP (RFC 4515): `*`, `(`, `)`, `\\`, NUL."""
    return escape_filter_chars(str(valor))


def escapar_valor_dn(valor):
    """Escapa un valor para un RDN (RFC 4514): `,`, `+`, `"`, `\\`, `<`, `>`, `;`, `=`."""
    return escape_rdn(str(valor))


def valor_de_membresia(configuracion, usuario):
    """Valor que representa a `usuario` en el atributo de membresía:
    el identificador (`memberUid`) o el DN (`member`, `uniqueMember`)."""
    if configuracion.atributo_miembro.lower() in ATRIBUTOS_MIEMBRO_POR_IDENTIFICADOR:
        return usuario.identificador
    return usuario.dn


def _texto(entrada, atributo):
    if atributo not in entrada:
        return ''
    valor = entrada[atributo].value
    if isinstance(valor, list):
        valor = valor[0] if valor else ''
    return '' if valor is None else str(valor)


class ClienteDirectorio:
    """Operaciones de lectura sobre el directorio con la cuenta de servicio."""

    def __init__(self, configuracion=None):
        self.configuracion = configuracion or cargar_configuracion()

    # ------------------------------------------------------------------ #
    # Conexión
    # ------------------------------------------------------------------ #

    def _tls(self):
        cfg = self.configuracion
        # `version=None`: contexto por defecto de Python (TLS 1.2 o superior).
        return Tls(validate=ssl.CERT_REQUIRED, version=None,
                   ca_certs_file=cfg.ca_cert_file, sni=cfg.host)

    def _servidor(self):
        cfg = self.configuracion
        return Server(cfg.host, port=cfg.puerto, use_ssl=cfg.usa_ldaps,
                      tls=self._tls(), connect_timeout=cfg.tiempo_espera)

    def registrar_error(self, operacion, exc, con_detalle=True):
        """Registra el fallo sin la contraseña y devuelve el error genérico.

        `con_detalle=False` (escritura) registra solo el código de resultado,
        sin el mensaje ni el DN, que pueden nombrar a la persona.
        """
        if con_detalle:
            detalle = str(exc)
            contrasena = self.configuracion.bind_password
            if contrasena:
                detalle = detalle.replace(contrasena, '***')
        else:
            detalle = getattr(exc, 'description', None) or '-'
        logger.error('Directorio: fallo en %s (%s): %s', operacion,
                     type(exc).__name__, detalle)
        return ErrorDirectorio(MENSAJE_ERROR, causa=exc)

    @contextmanager
    def conexion_servicio(self, solo_lectura=True):
        """Conexión autenticada con la cuenta de servicio (de solo lectura
        salvo `solo_lectura=False`, que solo usa `writer.py`).

        `ldap://` negocia StartTLS antes de enviar la credencial.
        """
        cfg = self.configuracion
        conexion = None
        try:
            conexion = Connection(
                self._servidor(), user=cfg.bind_dn, password=cfg.bind_password,
                client_strategy=ESTRATEGIA, receive_timeout=cfg.tiempo_espera,
                auto_referrals=False, raise_exceptions=True,
                read_only=solo_lectura)
            conexion.open()
            if not cfg.usa_ldaps:
                conexion.start_tls()
                if not conexion.tls_started:
                    # Sin TLS efectivo la credencial nunca sale en claro.
                    raise LDAPStartTLSError('StartTLS no quedó activo')
            conexion.bind()
        except LDAPException as exc:
            self._cerrar(conexion)
            raise self.registrar_error('conexión', exc) from None
        try:
            yield conexion
        finally:
            self._cerrar(conexion)

    @staticmethod
    def _cerrar(conexion):
        if conexion is None:
            return
        try:
            conexion.unbind()
        except LDAPException:
            pass

    # ------------------------------------------------------------------ #
    # Lecturas
    # ------------------------------------------------------------------ #

    def buscar_usuario(self, identificador):
        """Busca una persona por `LDAP_USER_ATTR`; `None` si no existe.

        El identificador se escapa: `*` o `)(` se buscan literalmente.
        """
        cfg = self.configuracion
        filtro = f'({cfg.atributo_usuario}={escapar_filtro(identificador)})'
        atributos = [cfg.atributo_usuario, *ATRIBUTOS_PERFIL]
        with self.conexion_servicio() as conexion:
            try:
                conexion.search(cfg.usuarios_base_dn, filtro, SUBTREE,
                                attributes=atributos,
                                size_limit=LIMITE_BUSQUEDA_USUARIO)
            except LDAPSizeLimitExceededResult:
                entradas, ambiguo = [], True
            except LDAPException as exc:
                raise self.registrar_error('búsqueda de usuario', exc) from None
            else:
                entradas = list(conexion.entries)
                ambiguo = len(entradas) > 1
        if ambiguo:
            # Sin el identificador: es dato de entrada del usuario.
            logger.error('Directorio: la búsqueda por %s bajo %s corresponde '
                         'a más de una entrada', cfg.atributo_usuario,
                         cfg.usuarios_base_dn)
            raise ErrorDirectorio(MENSAJE_AMBIGUO)
        if not entradas:
            return None
        entrada = entradas[0]
        return self._a_usuario(entrada, respaldo=str(identificador))

    def buscar_personas(self, texto, limite=LIMITE_BUSQUEDA_PERSONAS):
        """Personas cuyo `LDAP_USER_ATTR`, `mail`, `cn` o `displayName`
        contiene `texto` (FNC-043), bajo `LDAP_USERS_BASE_DN`.

        El texto se escapa: `*` o `)(` se buscan literalmente. Si hay más de
        `limite`, se devuelven las primeras `limite`.
        """
        cfg = self.configuracion
        valor = escapar_filtro(texto)
        filtro = '(|{})'.format(''.join(
            f'({atributo}=*{valor}*)'
            for atributo in (cfg.atributo_usuario, *ATRIBUTOS_PERFIL)))
        atributos = [cfg.atributo_usuario, *ATRIBUTOS_PERFIL]
        with self.conexion_servicio() as conexion:
            try:
                conexion.search(cfg.usuarios_base_dn, filtro, SUBTREE,
                                attributes=atributos, size_limit=limite)
            except LDAPSizeLimitExceededResult:
                pass  # se usan las entradas ya recibidas
            except LDAPException as exc:
                raise self.registrar_error('búsqueda de personas', exc) from None
            entradas = list(conexion.entries)[:limite]
        return [self._a_usuario(entrada) for entrada in entradas]

    def _a_usuario(self, entrada, respaldo=''):
        """`UsuarioDirectorio` de una entrada; `respaldo` si no trae el
        atributo de identificador."""
        return UsuarioDirectorio(
            dn=entrada.entry_dn,
            identificador=(_texto(entrada, self.configuracion.atributo_usuario)
                           or respaldo),
            atributos={nombre: _texto(entrada, nombre)
                       for nombre in ATRIBUTOS_PERFIL})

    def grupos_de_usuario(self, usuario):
        """DN de los grupos (`LDAP_GROUP_OBJECT_CLASS`) de los que es miembro.

        Busca bajo `LDAP_GROUPS_BASE_DN`; no depende del overlay `memberOf`.
        """
        cfg = self.configuracion
        valor = valor_de_membresia(cfg, usuario)
        filtro = (f'(&(objectClass={cfg.clase_grupo})'
                  f'({cfg.atributo_miembro}={escapar_filtro(valor)}))')
        with self.conexion_servicio() as conexion:
            try:
                conexion.search(cfg.grupos_base_dn, filtro, SUBTREE,
                                attributes=[])
            except LDAPException as exc:
                raise self.registrar_error('lectura de grupos', exc) from None
            return sorted(entrada.entry_dn for entrada in conexion.entries)

    def existe_dn(self, dn):
        """`True` si la entrada `dn` existe; un DN mal formado da `False`."""
        if not dn:
            return False
        try:
            parse_dn(dn)
        except LDAPInvalidDnError:
            return False
        with self.conexion_servicio() as conexion:
            try:
                conexion.search(dn, '(objectClass=*)', BASE, attributes=[])
            except LDAPNoSuchObjectResult:
                return False
            except LDAPException as exc:
                raise self.registrar_error('comprobación de DN', exc) from None
            return bool(conexion.entries)

    # ------------------------------------------------------------------ #
    # Autenticación de una persona (FNC-042)
    # ------------------------------------------------------------------ #

    def verificar_contrasena(self, usuario, contrasena):
        """`True` si `contrasena` es la de `usuario` (bind simple con su DN).

        - La contraseña vacía da `False` sin conectar: un bind simple sin
          contraseña es anónimo y el servidor lo acepta (SEC-AUTH-09).
        - Misma conexión que la de servicio: TLS validado, StartTLS con
          `ldap://` antes de enviar la contraseña y tiempos de espera.
        - Credenciales inválidas dan `False`; un fallo del directorio,
          `ErrorDirectorio`. La contraseña nunca va al log.
        """
        if not contrasena:
            return False
        cfg = self.configuracion
        conexion = None
        try:
            conexion = Connection(
                self._servidor(), user=usuario.dn, password=contrasena,
                client_strategy=ESTRATEGIA, receive_timeout=cfg.tiempo_espera,
                auto_referrals=False, raise_exceptions=True, read_only=True)
            conexion.open()
            if not cfg.usa_ldaps:
                conexion.start_tls()
                if not conexion.tls_started:
                    raise LDAPStartTLSError('StartTLS no quedó activo')
            conexion.bind()
            return True
        except LDAPInvalidCredentialsResult:
            return False
        except LDAPException as exc:
            logger.error('Directorio: fallo en verificación de contraseña '
                         '(%s): %s', type(exc).__name__,
                         str(exc).replace(contrasena, '***'))
            raise ErrorDirectorio(MENSAJE_ERROR) from None
        finally:
            self._cerrar(conexion)
