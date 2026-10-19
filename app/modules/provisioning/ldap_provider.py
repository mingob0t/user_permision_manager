"""Proveedor LDAP: membresía del grupo de la plataforma (FNC-049 sobre FNC-041).

- El grupo sale de la plataforma (`ldap_group_user_dn` o `ldap_group_admin_dn`
  según el nivel): el ejecutor solo escribe en grupos registrados en una
  plataforma y debajo de `LDAP_GROUPS_BASE_DN` (SEC-LDAP-04; el escritor
  vuelve a validar la base).
- La persona se identifica por el correo de su cuenta del portal, igual que el
  login de directorio (FNC-042): búsqueda con el cliente único y coincidencia
  **exacta** de `mail`. Ninguna o más de una → error permanente.
- Traduce `ResultadoEscritura`: `hecho` → `exitoso`, `ya_estaba` →
  `sin_cambios`, `error_transitorio` se reintenta, `no_existe` y
  `error_permanente` no.
"""
from app import db
from app.modules.auth.models import User
from app.modules.core.models import Platform
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 cargar_configuracion,
                                                 directorio_activo)
from app.modules.directory.dn import mismo_dn
from app.modules.directory.errors import (MOTIVO_DIRECTORIO,
                                          MOTIVO_FUERA_DE_BASE,
                                          MOTIVO_USUARIO_INEXISTENTE,
                                          Resultado, clasificar_error)
from app.modules.directory.ldap_client import ClienteDirectorio, ErrorDirectorio
from app.modules.directory.writer import EscritorDirectorio
from app.modules.platforms.grupos import dn_en_base
from app.modules.platforms.tipos import CAMPOS_DN, TIPO_LDAP
from app.modules.provisioning.providers import (Provisioner,
                                                ResultadoProveedor, permanente,
                                                transitorio)
from app.modules.provisioning.saneo import (MOTIVO_DATOS_INCOMPLETOS,
                                            MOTIVO_DIRECTORIO_NO_CONFIGURADO,
                                            MOTIVO_GRUPO_NO_CONFIGURADO,
                                            MOTIVO_PERSONA_AMBIGUA,
                                            MOTIVO_TIPO_INTEGRACION)
from app.modules.provisioning.tipos import (RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)

ATRIBUTO_CORREO = 'mail'

_RESULTADOS = {
    Resultado.HECHO: RESULTADO_EXITOSO,
    Resultado.YA_ESTABA: RESULTADO_SIN_CAMBIOS,
    Resultado.ERROR_TRANSITORIO: RESULTADO_ERROR_TRANSITORIO,
    Resultado.NO_EXISTE: RESULTADO_ERROR_PERMANENTE,
    Resultado.ERROR_PERMANENTE: RESULTADO_ERROR_PERMANENTE,
}


class _Fallo(Exception):
    """Corta la preparación con un resultado ya decidido."""

    def __init__(self, resultado):
        super().__init__(resultado.motivo)
        self.resultado = resultado


def _normalizar(correo):
    return (correo or '').strip().lower()


def _error_directorio(exc):
    tipo = clasificar_error(exc.causa) if exc.causa is not None else None
    if tipo is Resultado.ERROR_TRANSITORIO:
        return transitorio(MOTIVO_DIRECTORIO)
    return permanente(MOTIVO_DIRECTORIO)


class ProveedorLdap(Provisioner):

    def __init__(self, cliente=None, escritor=None):
        self._cliente = cliente
        self._escritor = escritor

    # ------------------------------------------------------------------ #
    # Preparación
    # ------------------------------------------------------------------ #

    def _cliente_y_escritor(self):
        if self._cliente is None:
            if not directorio_activo():
                raise _Fallo(permanente(MOTIVO_DIRECTORIO_NO_CONFIGURADO))
            try:
                self._cliente = ClienteDirectorio(cargar_configuracion())
            except ErrorConfiguracionDirectorio:
                raise _Fallo(permanente(MOTIVO_DIRECTORIO_NO_CONFIGURADO)) from None
        if self._escritor is None:
            self._escritor = EscritorDirectorio(self._cliente)
        return self._cliente, self._escritor

    def _grupo(self, operacion, configuracion):
        plataforma = (db.session.get(Platform, operacion.plataforma_id)
                      if operacion.plataforma_id else None)
        if plataforma is None or operacion.nivel not in CAMPOS_DN:
            raise _Fallo(permanente(MOTIVO_DATOS_INCOMPLETOS))
        if plataforma.integration_type != TIPO_LDAP:
            raise _Fallo(permanente(MOTIVO_TIPO_INTEGRACION))
        dn = getattr(plataforma, CAMPOS_DN[operacion.nivel])
        if not dn:
            raise _Fallo(permanente(MOTIVO_GRUPO_NO_CONFIGURADO))
        if not dn_en_base(configuracion, dn):
            raise _Fallo(permanente(MOTIVO_FUERA_DE_BASE))
        return dn

    def _persona(self, operacion, cliente):
        usuario = (db.session.get(User, operacion.usuario_id)
                   if operacion.usuario_id else None)
        correo = _normalizar(usuario.email if usuario else None)
        if not correo:
            raise _Fallo(permanente(MOTIVO_DATOS_INCOMPLETOS))
        try:
            candidatas = cliente.buscar_personas(correo)
        except ErrorDirectorio as exc:
            raise _Fallo(_error_directorio(exc)) from None
        exactas = [p for p in candidatas
                   if _normalizar(p.atributos.get(ATRIBUTO_CORREO)) == correo]
        if not exactas:
            raise _Fallo(permanente(MOTIVO_USUARIO_INEXISTENTE))
        if len(exactas) > 1:
            raise _Fallo(permanente(MOTIVO_PERSONA_AMBIGUA))
        return exactas[0]

    def _preparar(self, operacion):
        cliente, escritor = self._cliente_y_escritor()
        grupo = self._grupo(operacion, cliente.configuracion)
        persona = self._persona(operacion, cliente)
        return cliente, escritor, grupo, persona

    # ------------------------------------------------------------------ #
    # Operaciones
    # ------------------------------------------------------------------ #

    def _membresia(self, operacion, accion):
        try:
            _, escritor, grupo, persona = self._preparar(operacion)
        except _Fallo as fallo:
            return fallo.resultado
        escritura = getattr(escritor, accion)(grupo, persona)
        resultado = _RESULTADOS[escritura.resultado]
        motivo = None if escritura.exito else escritura.motivo
        return ResultadoProveedor(resultado, motivo)

    def otorgar(self, operacion):
        return self._membresia(operacion, 'add_member')

    def revocar(self, operacion):
        return self._membresia(operacion, 'remove_member')

    def consultar(self, operacion):
        try:
            cliente, _, grupo, persona = self._preparar(operacion)
            grupos = cliente.grupos_de_usuario(persona)
        except _Fallo as fallo:
            return fallo.resultado
        except ErrorDirectorio as exc:
            return _error_directorio(exc)
        presente = any(mismo_dn(grupo, g) for g in grupos)
        return ResultadoProveedor(RESULTADO_EXITOSO, presente=presente)
