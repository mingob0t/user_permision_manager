"""Proveedor `conector` del ejecutor de aprovisionamiento (FNC-050 sobre FNC-049).

Por cada operación:
1. Plataforma `conector` con configuración activa de un tipo registrado; si
   no, error permanente (`tipo_integracion` o `conector_no_disponible`).
2. Host en `CONNECTOR_ALLOWED_HOSTS` (se revalida en cada ejecución,
   SEC-CON-07); si no, permanente `host_no_autorizado`.
3. Cuenta: correo de la cuenta del portal (dato del servidor, SEC-CON-03).
4. Referencia sin `__` en su variable y sin equivalente en otra plataforma
   (B3); si no, permanente `credencial_no_encontrada`.
   Credencial desde la fuente del despliegue (ADR-005): no encontrada o
   gestor sin configurar → permanente; gestor caído → transitorio.
5. Llamada al tipo con el `Destino` (host normalizado, B1) y la `Credencial`. El detalle que devuelva
   se limpia del valor de la credencial antes de llegar a la bitácora (que
   además lo sanea, SEC-CON-10). Una excepción del tipo cuenta como
   transitoria sin guardar su texto; el tiempo de espera de RQ sigue hasta el
   ejecutor.
"""
import logging
from types import MappingProxyType

from rq.timeouts import JobTimeoutException

from app import db
from app.modules.audit.sanitizar import VALOR_OMITIDO
from app.modules.auth.models import User
from app.modules.connectors import credenciales
from app.modules.connectors.base import Destino, SolicitudConector
from app.modules.connectors.configuracion import (cargar_configuracion,
                                                  host_permitido,
                                                  normalizar_host)
from app.modules.connectors.consultas import (configuracion_de,
                                              referencias_de_otras)
from app.modules.connectors.credenciales import (CredencialNoEncontrada,
                                                 ErrorDeCredencial,
                                                 GestorNoConfigurado,
                                                 GestorNoDisponible,
                                                 ReferenciaInvalida,
                                                 referencia_valida,
                                                 referencias_en_conflicto)
from app.modules.connectors.registry import obtener_tipo
from app.modules.core.models import Platform
from app.modules.platforms.tipos import CAMPOS_DN, TIPO_CONECTOR
from app.modules.provisioning.providers import (Provisioner,
                                                ResultadoProveedor, permanente,
                                                transitorio)
from app.modules.provisioning.saneo import (LARGO_MINIMO_SECRETO,
                                            MOTIVO_CONECTOR_NO_DISPONIBLE,
                                            MOTIVO_CREDENCIAL_NO_ENCONTRADA,
                                            MOTIVO_DATOS_INCOMPLETOS,
                                            MOTIVO_GESTOR_NO_CONFIGURADO,
                                            MOTIVO_GESTOR_NO_DISPONIBLE,
                                            MOTIVO_HOST_NO_AUTORIZADO,
                                            MOTIVO_INESPERADO,
                                            MOTIVO_TIPO_INTEGRACION)

logger = logging.getLogger(__name__)

_RESULTADOS_CREDENCIAL = {
    CredencialNoEncontrada: (permanente, MOTIVO_CREDENCIAL_NO_ENCONTRADA),
    ReferenciaInvalida: (permanente, MOTIVO_CREDENCIAL_NO_ENCONTRADA),
    GestorNoConfigurado: (permanente, MOTIVO_GESTOR_NO_CONFIGURADO),
    GestorNoDisponible: (transitorio, MOTIVO_GESTOR_NO_DISPONIBLE),
}


class _Fallo(Exception):
    """Corta la preparación con un resultado ya decidido."""

    def __init__(self, resultado):
        super().__init__(resultado.motivo)
        self.resultado = resultado


def _sin_credencial(resultado, credencial):
    """El mismo resultado sin el valor de la credencial en su detalle."""
    secreto = credencial.secreto or ''
    if (not resultado.detalle or len(secreto) < LARGO_MINIMO_SECRETO
            or secreto not in resultado.detalle):
        return resultado
    return ResultadoProveedor(resultado.resultado, resultado.motivo,
                              resultado.detalle.replace(secreto, VALOR_OMITIDO),
                              resultado.presente)


class ProveedorConector(Provisioner):

    # ------------------------------------------------------------------ #
    # Preparación
    # ------------------------------------------------------------------ #

    def _configuracion(self, operacion):
        plataforma = (db.session.get(Platform, operacion.plataforma_id)
                      if operacion.plataforma_id else None)
        if plataforma is None or operacion.nivel not in CAMPOS_DN:
            raise _Fallo(permanente(MOTIVO_DATOS_INCOMPLETOS))
        if plataforma.integration_type != TIPO_CONECTOR:
            raise _Fallo(permanente(MOTIVO_TIPO_INTEGRACION))
        configuracion = configuracion_de(plataforma.id)
        tipo = obtener_tipo(configuracion.type) if configuracion else None
        if configuracion is None or not configuracion.active or tipo is None:
            raise _Fallo(permanente(MOTIVO_CONECTOR_NO_DISPONIBLE))
        return configuracion, tipo

    def _destino(self, configuracion):
        cfg = cargar_configuracion()
        if not host_permitido(configuracion.host, cfg):
            raise _Fallo(permanente(MOTIVO_HOST_NO_AUTORIZADO))
        return Destino(host=normalizar_host(configuracion.host),
                       puerto=configuracion.port,
                       params=MappingProxyType(dict(configuracion.params or {})),
                       tiempo_espera=cfg.tiempo_espera)

    def _solicitud(self, operacion):
        usuario = (db.session.get(User, operacion.usuario_id)
                   if operacion.usuario_id else None)
        cuenta = (usuario.email if usuario else '') or ''
        cuenta = cuenta.strip().lower()
        if not cuenta:
            raise _Fallo(permanente(MOTIVO_DATOS_INCOMPLETOS))
        return SolicitudConector(
            id_operacion=operacion.id_operacion,
            clave_idempotencia=operacion.clave_idempotencia,
            operacion=operacion.operacion, nivel=operacion.nivel,
            plataforma_id=operacion.plataforma_id, cuenta=cuenta)

    def _credencial(self, configuracion):
        referencia = configuracion.credential_ref
        if not referencia_valida(referencia) or referencias_en_conflicto(
                referencia, referencias_de_otras(configuracion.platform_id)):
            logger.warning('Conector: referencia ambigua en la plataforma %s.',
                           configuracion.platform_id)
            raise _Fallo(permanente(MOTIVO_CREDENCIAL_NO_ENCONTRADA))
        if credenciales.referencia_reservada(referencia):
            # La del bind LDAP nunca va a un conector (B3 de FNC-068).
            logger.warning('Conector: referencia reservada en la plataforma %s.',
                           configuracion.platform_id)
            raise _Fallo(permanente(MOTIVO_CREDENCIAL_NO_ENCONTRADA))
        try:
            return credenciales.resolver_credencial(configuracion.credential_ref)
        except ErrorDeCredencial as exc:
            fabrica, motivo = _RESULTADOS_CREDENCIAL.get(
                type(exc), (transitorio, MOTIVO_INESPERADO))
            logger.warning('Conector: credencial de la plataforma %s sin '
                           'resolver (%s).', configuracion.platform_id, motivo)
            raise _Fallo(fabrica(motivo)) from None

    def _preparar(self, operacion):
        configuracion, tipo = self._configuracion(operacion)
        destino = self._destino(configuracion)
        solicitud = self._solicitud(operacion)
        credencial = self._credencial(configuracion)
        return tipo.fabrica(destino, credencial), solicitud, credencial

    # ------------------------------------------------------------------ #
    # Operaciones
    # ------------------------------------------------------------------ #

    def _ejecutar(self, operacion, accion):
        try:
            conector, solicitud, credencial = self._preparar(operacion)
        except _Fallo as fallo:
            return fallo.resultado
        try:
            resultado = getattr(conector, accion)(solicitud)
        except JobTimeoutException:
            raise
        except Exception as exc:  # solo el tipo: el texto puede traer secretos
            logger.error('Conector: error inesperado al %s en la plataforma '
                         '%s (%s).', accion, operacion.plataforma_id,
                         type(exc).__name__)
            return transitorio(MOTIVO_INESPERADO)
        if not isinstance(resultado, ResultadoProveedor):
            logger.error('Conector: resultado fuera del contrato al %s en la '
                         'plataforma %s.', accion, operacion.plataforma_id)
            return transitorio(MOTIVO_INESPERADO)
        return _sin_credencial(resultado, credencial)

    def otorgar(self, operacion):
        return self._ejecutar(operacion, 'otorgar')

    def revocar(self, operacion):
        return self._ejecutar(operacion, 'revocar')

    def consultar(self, operacion):
        return self._ejecutar(operacion, 'consultar')
