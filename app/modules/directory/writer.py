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
  el resultado es `ERROR_PERMANENTE` (`ultimo_miembro`). Al agregar un miembro
  real se quita el relleno en la misma operación (decisión del dueño,
  2026-10-15).
- Alta de cuentas sin contraseña (P8: la maneja Authelia); identificador y
  correo validados, y el identificador se escapa al formar el DN
  (SEC-LDAP-06). No hay borrado de cuentas en v1.
- Nunca lanza por fallos del directorio: devuelve `ResultadoEscritura`. El
  log de un fallo de escritura lleva solo el código de resultado, sin el DN
  ni el mensaje del servidor (pueden nombrar a la persona).
"""
import logging
import re
from dataclasses import dataclass

from ldap3 import BASE, MODIFY_ADD, MODIFY_DELETE, SUBTREE
from ldap3.core.exceptions import (LDAPAttributeOrValueExistsResult,
                                   LDAPEntryAlreadyExistsResult,
                                   LDAPException, LDAPNoSuchAttributeResult,
                                   LDAPNoSuchObjectResult,
                                   LDAPSizeLimitExceededResult)

from app.modules.directory.dn import bajo_base, mismo_dn
from app.modules.directory.errors import (MOTIVO_DATOS_INCOMPLETOS,
                                          MOTIVO_DATOS_INVALIDOS,
                                          MOTIVO_DIRECTORIO,
                                          MOTIVO_FUERA_DE_BASE,
                                          MOTIVO_GRUPO_INEXISTENTE,
                                          MOTIVO_ULTIMO_MIEMBRO,
                                          MOTIVO_USUARIO_INEXISTENTE,
                                          Resultado, ResultadoEscritura,
                                          clasificar_error)
from app.modules.directory.ldap_client import (
    ATRIBUTOS_MIEMBRO_POR_IDENTIFICADOR, ClienteDirectorio, ErrorDirectorio,
    escapar_filtro, escapar_valor_dn, valor_de_membresia)

logger = logging.getLogger(__name__)

# Clases de grupo cuyo atributo de membresía es obligatorio (≥ 1 valor).
CLASES_GRUPO_CON_MIEMBRO_OBLIGATORIO = frozenset({'groupofnames',
                                                  'groupofuniquenames'})

# Atributos de inetOrgPerson que se llenan en el alta. Provisionales hasta
# que ADR-004 cierre la lista de atributos de alta (P3).
ATRIBUTO_NOMBRE_COMPLETO = 'cn'
ATRIBUTO_APELLIDO = 'sn'
ATRIBUTO_NOMBRE = 'givenName'
ATRIBUTO_CORREO = 'mail'

# Formatos aceptados en el alta (se usan con `fullmatch`) (auditor-seguridad, 2026-10-15). El contrato
# `usuarios-directorio.md` (FNC-064) agrega largos y primer carácter.
PATRON_IDENTIFICADOR = re.compile(r'[a-z0-9._-]+')
PATRON_CORREO = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')


@dataclass(frozen=True)
class DatosCuenta:
    """Datos de una cuenta nueva; sin contraseña (P8)."""

    identificador: str
    nombre: str
    apellido: str
    correo: str


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

    def _coincide(self, guardado, valor):
        if (self.configuracion.atributo_miembro.lower()
                in ATRIBUTOS_MIEMBRO_POR_IDENTIFICADOR):
            return guardado == valor
        return mismo_dn(guardado, valor)

    def _fuera_de_base(self, group_dn, usuario):
        cfg = self.configuracion
        return not (bajo_base(group_dn, cfg.grupos_base_dn)
                    and bajo_base(usuario.dn, cfg.usuarios_base_dn)
                    and valor_de_membresia(cfg, usuario))

    def _ejecutar(self, operacion, dn, accion):
        """Corre `accion(conexion)` y convierte cualquier fallo en resultado."""
        try:
            with self.cliente.conexion_servicio(solo_lectura=False) as conexion:
                resultado = accion(conexion)
        except ErrorDirectorio as exc:  # conexión: el cliente ya lo registró
            resultado = ResultadoEscritura(clasificar_error(exc.causa), dn,
                                           MOTIVO_DIRECTORIO)
        except LDAPException as exc:
            self.cliente.registrar_error(operacion, exc, con_detalle=False)
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
        cfg = self.configuracion
        atributo = cfg.atributo_miembro
        valor = valor_de_membresia(cfg, user)

        def alta_miembro(conexion):
            entrada = _leer_grupo(conexion, cfg, group_dn)
            if entrada is None:
                return ResultadoEscritura(Resultado.NO_EXISTE, group_dn,
                                          MOTIVO_GRUPO_INEXISTENTE)
            if not _existe(conexion, user.dn):
                return ResultadoEscritura(Resultado.NO_EXISTE, group_dn,
                                          MOTIVO_USUARIO_INEXISTENTE)
            guardados = _valores_miembro(entrada, atributo)
            if any(self._coincide(guardado, valor) for guardado in guardados):
                return ResultadoEscritura(Resultado.YA_ESTABA, group_dn)
            cambios = [(MODIFY_ADD, [valor])]
            rellenos = [g for g in guardados if cfg.miembro_relleno
                        and self._coincide(g, cfg.miembro_relleno)]
            if rellenos:
                # Con un miembro real el relleno sobra; misma operación.
                cambios.append((MODIFY_DELETE, rellenos))
            try:
                conexion.modify(group_dn, {atributo: cambios})
            except LDAPAttributeOrValueExistsResult:
                return ResultadoEscritura(Resultado.YA_ESTABA, group_dn)
            return ResultadoEscritura(Resultado.HECHO, group_dn)

        return self._ejecutar('alta de miembro', group_dn, alta_miembro)

    def remove_member(self, group_dn, user):
        """Quita `user` (`UsuarioDirectorio`) del grupo `group_dn`."""
        if self._fuera_de_base(group_dn, user):
            return ResultadoEscritura(Resultado.ERROR_PERMANENTE, group_dn,
                                      MOTIVO_FUERA_DE_BASE)
        cfg = self.configuracion
        atributo = cfg.atributo_miembro
        valor = valor_de_membresia(cfg, user)

        def baja_miembro(conexion):
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

        return self._ejecutar('baja de miembro', group_dn, baja_miembro)

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
        if not (PATRON_IDENTIFICADOR.fullmatch(datos.identificador)
                and PATRON_CORREO.fullmatch(datos.correo)):
            return ResultadoEscritura(Resultado.ERROR_PERMANENTE,
                                      cfg.usuarios_base_dn,
                                      MOTIVO_DATOS_INVALIDOS)
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

        def alta_cuenta(conexion):
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

        return self._ejecutar('alta de cuenta', dn, alta_cuenta)
