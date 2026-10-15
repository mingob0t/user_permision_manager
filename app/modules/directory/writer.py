"""Escritura en OpenLDAP: membresía de grupos y alta de cuentas (FNC-041).

- Usa el cliente único de FNC-040 (`ClienteDirectorio`) con una conexión de
  escritura; TLS, tiempos de espera y registro de errores son los del cliente.
- Solo escribe bajo las bases configuradas: grupos bajo `LDAP_GROUPS_BASE_DN`
  y cuentas bajo `LDAP_USERS_BASE_DN`, comparando RDN normalizados
  (SEC-LDAP-04). Que el grupo esté registrado en una plataforma lo valida el
  llamador (FNC-049).
- Membresía: solo `MODIFY_ADD` y `MODIFY_DELETE` de un valor del atributo de
  membresía; nunca `REPLACE` (SEC-LDAP-07). Idempotente: un miembro existente
  o ausente da `YA_ESTABA` (SEC-LDAP-08).
- Último miembro de un grupo que exige uno (`groupOfNames`,
  `groupOfUniqueNames`): con `LDAP_GROUP_PLACEHOLDER_MEMBER` se agrega el
  relleno y se quita al usuario en la misma operación; sin él, no se quita y
  el resultado es `ERROR_PERMANENTE` (`ultimo_miembro`).
- Alta de cuentas sin contraseña (P8: la maneja Authelia); el identificador se
  escapa al formar el DN (SEC-LDAP-06). No hay borrado de cuentas en v1.
- Nunca lanza por fallos del directorio: devuelve `ResultadoEscritura`.
"""
import logging
import re
from dataclasses import dataclass

from ldap3 import BASE, MODIFY_ADD, MODIFY_DELETE, SUBTREE
from ldap3.core.exceptions import (LDAPAttributeOrValueExistsResult,
                                   LDAPEntryAlreadyExistsResult,
                                   LDAPException, LDAPInvalidDnError,
                                   LDAPNoSuchAttributeResult,
                                   LDAPNoSuchObjectResult,
                                   LDAPSizeLimitExceededResult)
from ldap3.utils.dn import parse_dn

from app.modules.directory.errors import (MOTIVO_DATOS_INCOMPLETOS,
                                          MOTIVO_DIRECTORIO,
                                          MOTIVO_FUERA_DE_BASE,
                                          MOTIVO_GRUPO_INEXISTENTE,
                                          MOTIVO_ULTIMO_MIEMBRO,
                                          MOTIVO_USUARIO_INEXISTENTE,
                                          Resultado, ResultadoEscritura,
                                          clasificar_error)
from app.modules.directory.ldap_client import (
    ATRIBUTOS_MIEMBRO_POR_IDENTIFICADOR, ClienteDirectorio, ErrorDirectorio,
    escapar_filtro, escapar_valor_dn)

logger = logging.getLogger(__name__)

# Clases de grupo cuyo atributo de membresía es obligatorio (≥ 1 valor).
CLASES_GRUPO_CON_MIEMBRO_OBLIGATORIO = frozenset({'groupofnames',
                                                  'groupofuniquenames'})

# Atributos de inetOrgPerson que se llenan en el alta (ADR-004).
ATRIBUTO_NOMBRE_COMPLETO = 'cn'
ATRIBUTO_APELLIDO = 'sn'
ATRIBUTO_NOMBRE = 'givenName'
ATRIBUTO_CORREO = 'mail'

# `\` seguido de dos dígitos hexadecimales o de un carácter (RFC 4514).
_ESCAPE_DN = re.compile(r'\\([0-9a-fA-F]{2}|.)')


@dataclass(frozen=True)
class DatosCuenta:
    """Datos de una cuenta nueva; sin contraseña (P8)."""

    identificador: str
    nombre: str
    apellido: str
    correo: str


def _desescapar(valor):
    def reemplazo(coincidencia):
        texto = coincidencia.group(1)
        return chr(int(texto, 16)) if len(texto) == 2 else texto
    return _ESCAPE_DN.sub(reemplazo, valor)


def _normalizar_dn(dn):
    """RDN como tuplas `(atributo, valor)` en minúsculas; `None` si no es DN."""
    if not dn:
        return None
    try:
        partes = parse_dn(dn)
    except LDAPInvalidDnError:
        return None
    return tuple((atributo.strip().lower(), _desescapar(valor).strip().lower())
                 for atributo, valor, _ in partes)


def _bajo_base(dn, base):
    """`True` si `dn` está estrictamente debajo de `base` (RDN normalizados)."""
    rdns, rdns_base = _normalizar_dn(dn), _normalizar_dn(base)
    if not rdns or not rdns_base or len(rdns) <= len(rdns_base):
        return False
    return rdns[-len(rdns_base):] == rdns_base


def _leer_grupo(conexion, cfg, dn):
    """Entrada del grupo con su atributo de membresía; `None` si no existe."""
    try:
        conexion.search(dn, f'(objectClass={cfg.clase_grupo})', BASE,
                        attributes=[cfg.atributo_miembro])
    except LDAPNoSuchObjectResult:
        return None
    return conexion.entries[0] if conexion.entries else None


def _valores_miembro(entrada, atributo):
    if atributo not in entrada:
        return []
    return [str(valor) for valor in entrada[atributo].values]


def _existe(conexion, dn):
    try:
        conexion.search(dn, '(objectClass=*)', BASE, attributes=[])
    except LDAPNoSuchObjectResult:
        return False
    return bool(conexion.entries)


class EscritorDirectorio:
    """Escritura idempotente con la cuenta de servicio (SEC-LDAP-03)."""

    def __init__(self, cliente=None):
        self.cliente = cliente or ClienteDirectorio()
        self.configuracion = self.cliente.configuracion

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #

    def _por_identificador(self):
        return (self.configuracion.atributo_miembro.lower()
                in ATRIBUTOS_MIEMBRO_POR_IDENTIFICADOR)

    def _valor_miembro(self, usuario):
        return usuario.identificador if self._por_identificador() else usuario.dn

    def _coincide(self, guardado, valor):
        if self._por_identificador():
            return guardado == valor
        return _normalizar_dn(guardado) == _normalizar_dn(valor)

    def _fuera_de_base(self, group_dn, usuario):
        cfg = self.configuracion
        return not (_bajo_base(group_dn, cfg.grupos_base_dn)
                    and _bajo_base(usuario.dn, cfg.usuarios_base_dn)
                    and self._valor_miembro(usuario))

    def _ejecutar(self, operacion, dn, accion):
        """Corre `accion(conexion)` y convierte cualquier fallo en resultado."""
        try:
            with self.cliente.conexion_servicio(solo_lectura=False) as conexion:
                resultado = accion(conexion)
        except ErrorDirectorio as exc:  # conexión: el cliente ya lo registró
            resultado = ResultadoEscritura(clasificar_error(exc.causa), dn,
                                           MOTIVO_DIRECTORIO)
        except LDAPException as exc:
            self.cliente._error(operacion, exc)
            resultado = ResultadoEscritura(clasificar_error(exc), dn,
                                           MOTIVO_DIRECTORIO)
        logger.info('Directorio: %s → %s', operacion,
                    resultado.resultado.value)
        return resultado

    # ------------------------------------------------------------------ #
    # Membresía
    # ------------------------------------------------------------------ #

    def add_member(self, group_dn, user):
        """Agrega `user` (`UsuarioDirectorio`) al grupo `group_dn`."""
        if self._fuera_de_base(group_dn, user):
            return ResultadoEscritura(Resultado.ERROR_PERMANENTE, group_dn,
                                      MOTIVO_FUERA_DE_BASE)
        atributo = self.configuracion.atributo_miembro
        valor = self._valor_miembro(user)

        def agregar(conexion):
            entrada = _leer_grupo(conexion, self.configuracion, group_dn)
            if entrada is None:
                return ResultadoEscritura(Resultado.NO_EXISTE, group_dn,
                                          MOTIVO_GRUPO_INEXISTENTE)
            if not _existe(conexion, user.dn):
                return ResultadoEscritura(Resultado.NO_EXISTE, group_dn,
                                          MOTIVO_USUARIO_INEXISTENTE)
            if any(self._coincide(guardado, valor)
                   for guardado in _valores_miembro(entrada, atributo)):
                return ResultadoEscritura(Resultado.YA_ESTABA, group_dn)
            try:
                conexion.modify(group_dn, {atributo: [(MODIFY_ADD, [valor])]})
            except LDAPAttributeOrValueExistsResult:
                return ResultadoEscritura(Resultado.YA_ESTABA, group_dn)
            return ResultadoEscritura(Resultado.HECHO, group_dn)

        return self._ejecutar('alta de miembro', group_dn, agregar)

    def remove_member(self, group_dn, user):
        """Quita `user` (`UsuarioDirectorio`) del grupo `group_dn`."""
        if self._fuera_de_base(group_dn, user):
            return ResultadoEscritura(Resultado.ERROR_PERMANENTE, group_dn,
                                      MOTIVO_FUERA_DE_BASE)
        cfg = self.configuracion
        atributo = cfg.atributo_miembro
        valor = self._valor_miembro(user)

        def quitar(conexion):
            entrada = _leer_grupo(conexion, cfg, group_dn)
            if entrada is None:
                return ResultadoEscritura(Resultado.NO_EXISTE, group_dn,
                                          MOTIVO_GRUPO_INEXISTENTE)
            guardados = _valores_miembro(entrada, atributo)
            del_usuario = [g for g in guardados if self._coincide(g, valor)]
            if not del_usuario:
                return ResultadoEscritura(Resultado.YA_ESTABA, group_dn)
            cambios = [(MODIFY_DELETE, del_usuario)]
            restantes = [g for g in guardados if g not in del_usuario]
            if (cfg.clase_grupo.lower() in CLASES_GRUPO_CON_MIEMBRO_OBLIGATORIO
                    and not restantes):
                if not cfg.miembro_relleno:
                    logger.error('Directorio: no se quita el último miembro '
                                 'de %s; falta LDAP_GROUP_PLACEHOLDER_MEMBER',
                                 group_dn)
                    return ResultadoEscritura(Resultado.ERROR_PERMANENTE,
                                              group_dn, MOTIVO_ULTIMO_MIEMBRO)
                # Una sola operación: el grupo nunca queda sin miembros.
                cambios.insert(0, (MODIFY_ADD, [cfg.miembro_relleno]))
            try:
                conexion.modify(group_dn, {atributo: cambios})
            except LDAPNoSuchAttributeResult:
                return ResultadoEscritura(Resultado.YA_ESTABA, group_dn)
            return ResultadoEscritura(Resultado.HECHO, group_dn)

        return self._ejecutar('baja de miembro', group_dn, quitar)

    # ------------------------------------------------------------------ #
    # Alta de cuentas
    # ------------------------------------------------------------------ #

    def create_user(self, datos):
        """Crea la cuenta en `LDAP_USERS_BASE_DN`, sin contraseña."""
        cfg = self.configuracion
        if not all(str(campo or '').strip() for campo in (
                datos.identificador, datos.nombre, datos.apellido,
                datos.correo)):
            return ResultadoEscritura(Resultado.ERROR_PERMANENTE,
                                      cfg.usuarios_base_dn,
                                      MOTIVO_DATOS_INCOMPLETOS)
        dn = (f'{cfg.atributo_usuario}='
              f'{escapar_valor_dn(datos.identificador)},{cfg.usuarios_base_dn}')
        atributos = {
            ATRIBUTO_NOMBRE_COMPLETO: f'{datos.nombre} {datos.apellido}',
            ATRIBUTO_APELLIDO: datos.apellido,
            ATRIBUTO_NOMBRE: datos.nombre,
            ATRIBUTO_CORREO: datos.correo,
            cfg.atributo_usuario: datos.identificador,
        }
        filtro = (f'({cfg.atributo_usuario}='
                  f'{escapar_filtro(datos.identificador)})')

        def crear(conexion):
            try:
                conexion.search(cfg.usuarios_base_dn, filtro, SUBTREE,
                                attributes=[], size_limit=1)
            except LDAPSizeLimitExceededResult:
                return ResultadoEscritura(Resultado.YA_ESTABA, dn)
            if conexion.entries:
                return ResultadoEscritura(Resultado.YA_ESTABA,
                                          conexion.entries[0].entry_dn)
            try:
                conexion.add(dn, list(cfg.clases_usuario), atributos)
            except LDAPEntryAlreadyExistsResult:
                return ResultadoEscritura(Resultado.YA_ESTABA, dn)
            return ResultadoEscritura(Resultado.HECHO, dn)

        return self._ejecutar('alta de cuenta', dn, crear)
