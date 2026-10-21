"""Proveedor `conector` del ejecutor (FNC-049) con el conector `noop` y
resolvedores simulados (FNC-050)."""
import logging

import pytest

from app import db
from app.modules.audit.models import AuditLog
from app.modules.connectors import credenciales, registry
from app.modules.connectors.base import Conector
from app.modules.connectors.credenciales import (CredencialNoEncontrada,
                                                GestorNoDisponible)
from app.modules.connectors.provider import ProveedorConector
from app.modules.connectors.registry import TipoConector
from app.modules.platforms.tipos import NIVEL_USUARIO, TIPO_LDAP
from app.modules.provisioning import providers, queue
from app.modules.provisioning.ejecucion import ejecutar_trabajo
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.providers import (Operacion, ResultadoProveedor,
                                                obtener_proveedor)
from app.modules.provisioning.tipos import (ESTADO_EXITOSO, ESTADO_FALLIDO,
                                            ESTADO_REINTENTANDO,
                                            OPERACION_OTORGAR,
                                            OPERACION_REVOCAR,
                                            PROVEEDOR_CONECTOR,
                                            RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)
from tests import fabricas
from tests.connectors.conftest import REFERENCIA, SECRETO_FICTICIO


def trabajo(trabajo_id):
    return db.session.get(ProvisioningJob, trabajo_id, populate_existing=True)


def encolar(plataforma, usuario, operacion, clave):
    t = queue.encolar(operacion, usuario.id, plataforma, NIVEL_USUARIO, clave)
    db.session.commit()
    return t.id


def operacion(plataforma, usuario, nombre=OPERACION_OTORGAR):
    return Operacion(id_operacion='1', clave_idempotencia='c-1',
                     operacion=nombre, nivel=NIVEL_USUARIO,
                     plataforma_id=plataforma.id, usuario_id=usuario.id)


def test_el_proveedor_conector_queda_registrado(app):
    assert isinstance(obtener_proveedor(PROVEEDOR_CONECTOR), ProveedorConector)


def test_noop_recorre_otorgar_y_revocar_con_el_ejecutor(conector_noop):
    plataforma, _, usuario = conector_noop
    proveedor = ProveedorConector()

    otorgar = encolar(plataforma, usuario, OPERACION_OTORGAR, 'noop-1')
    assert ejecutar_trabajo(otorgar) == ESTADO_EXITOSO
    assert trabajo(otorgar).attempts[0].result == RESULTADO_EXITOSO
    assert proveedor.consultar(operacion(plataforma, usuario)).presente is True

    revocar = encolar(plataforma, usuario, OPERACION_REVOCAR, 'noop-2')
    assert ejecutar_trabajo(revocar) == ESTADO_EXITOSO
    assert trabajo(revocar).attempts[0].result == RESULTADO_EXITOSO
    assert proveedor.consultar(operacion(plataforma, usuario)).presente is False

    # Idempotente: revocar otra vez no cambia nada.
    otra = encolar(plataforma, usuario, OPERACION_REVOCAR, 'noop-3')
    assert ejecutar_trabajo(otra) == ESTADO_EXITOSO
    assert trabajo(otra).attempts[0].result == RESULTADO_SIN_CAMBIOS


def test_referencia_inexistente_es_permanente_sin_detalles(conector_noop,
                                                            monkeypatch):
    plataforma, configuracion, usuario = conector_noop
    configuracion.credential_ref = 'pokemon/no-existe-en-el-gestor'
    db.session.commit()

    class SinCredencial(credenciales.ProveedorDeSecretos):
        fuente = 'simulada'

        def obtener(self, referencia):
            raise CredencialNoEncontrada(f'no hay {referencia} en el gestor')

    monkeypatch.setattr(credenciales, 'proveedor_de_secretos',
                        lambda entorno=None: SinCredencial())
    t = encolar(plataforma, usuario, OPERACION_OTORGAR, 'ref-1')

    assert ejecutar_trabajo(t) == ESTADO_FALLIDO
    intento = trabajo(t).attempts[0]
    assert intento.result == RESULTADO_ERROR_PERMANENTE
    assert intento.error == ('La credencial del conector no existe en el '
                             'gestor de secretos.')
    assert 'no-existe' not in intento.error
    assert trabajo(t).attempts_count == 1  # sin reintentos


def test_gestor_caido_es_transitorio(conector_noop, monkeypatch):
    plataforma, _, usuario = conector_noop

    class Caido(credenciales.ProveedorDeSecretos):
        fuente = 'simulada'

        def obtener(self, referencia):
            raise GestorNoDisponible('timeout hacia el gestor')

    monkeypatch.setattr(credenciales, 'proveedor_de_secretos',
                        lambda entorno=None: Caido())
    t = encolar(plataforma, usuario, OPERACION_OTORGAR, 'caido-1')
    assert ejecutar_trabajo(t) == ESTADO_REINTENTANDO
    intento = trabajo(t).attempts[0]
    assert (intento.result, intento.error) == (
        RESULTADO_ERROR_TRANSITORIO, 'El gestor de secretos no respondió.')


def test_fuera_de_dev_sin_vaultwarden_es_permanente(conector_noop,
                                                     monkeypatch):
    plataforma, _, usuario = conector_noop
    monkeypatch.setenv('APP_ENV', 'production')
    t = encolar(plataforma, usuario, OPERACION_OTORGAR, 'prod-1')
    assert ejecutar_trabajo(t) == ESTADO_FALLIDO
    assert trabajo(t).attempts[0].error == (
        'El gestor de secretos no está configurado.')


@pytest.mark.parametrize('cambio, mensaje', [
    ({'active': False}, 'El conector de la plataforma no está disponible.'),
    ({'type': 'api'}, 'El conector de la plataforma no está disponible.'),
    ({'host': 'ajeno.pruebas.local'},
     'El host del conector no está autorizado.'),
])
def test_configuracion_no_utilizable_es_permanente(conector_noop, cambio,
                                                   mensaje):
    plataforma, configuracion, usuario = conector_noop
    for campo, valor in cambio.items():
        setattr(configuracion, campo, valor)
    db.session.commit()
    resultado = ProveedorConector().otorgar(operacion(plataforma, usuario))
    assert (resultado.resultado, resultado.motivo is not None) == (
        RESULTADO_ERROR_PERMANENTE, True)
    t = encolar(plataforma, usuario, OPERACION_OTORGAR, f'no-{cambio}')
    assert ejecutar_trabajo(t) == ESTADO_FALLIDO
    assert trabajo(t).attempts[0].error == mensaje


def test_sin_configuracion_o_plataforma_ldap_es_permanente(conector_noop):
    _, _, usuario = conector_noop
    area = fabricas.crear_area()
    ldap = fabricas.crear_plataforma(area, integration_type=TIPO_LDAP)
    resultado = ProveedorConector().otorgar(operacion(ldap, usuario))
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE


class ConectorQueFiltra(Conector):
    """Conector que devuelve la credencial en su detalle o en una excepción."""

    def otorgar(self, solicitud):
        return ResultadoProveedor(
            RESULTADO_ERROR_PERMANENTE, 'inesperado',
            f'rechazado con {self.credencial.secreto} para {solicitud.cuenta}')

    def revocar(self, solicitud):
        raise RuntimeError(f'fallo con password={self.credencial.secreto}')


@pytest.fixture
def tipo_que_filtra(conector_noop):
    plataforma, configuracion, usuario = conector_noop
    registry.registrar_tipo(TipoConector('filtra', ConectorQueFiltra,
                                         lambda params: {}))
    configuracion.type = 'filtra'
    db.session.commit()
    yield plataforma, usuario
    registry.quitar_tipo('filtra')


def test_la_credencial_no_aparece_en_bitacora_auditoria_ni_logs(
        tipo_que_filtra, caplog):
    plataforma, usuario = tipo_que_filtra
    caplog.set_level(logging.DEBUG)

    otorgar = encolar(plataforma, usuario, OPERACION_OTORGAR, 'filtra-1')
    assert ejecutar_trabajo(otorgar) == ESTADO_FALLIDO
    revocar = encolar(plataforma, usuario, OPERACION_REVOCAR, 'filtra-2')
    assert ejecutar_trabajo(revocar) == ESTADO_REINTENTANDO

    errores = [i.error for t in (otorgar, revocar) for i in trabajo(t).attempts]
    assert all(e for e in errores)
    assert not any(SECRETO_FICTICIO in e for e in errores)
    assert '[omitido]' in errores[0]
    for registro in AuditLog.query.all():
        texto = ' '.join(str(v) for v in (registro.detail,
                                          registro.before_state,
                                          registro.after_state))
        assert SECRETO_FICTICIO not in texto
    assert SECRETO_FICTICIO not in caplog.text


def test_resultado_que_no_es_del_contrato_es_transitorio(conector_noop):
    plataforma, configuracion, usuario = conector_noop

    class Raro(Conector):
        def otorgar(self, solicitud):
            return 'ok'

        def revocar(self, solicitud):
            return None

    registry.registrar_tipo(TipoConector('raro', Raro, lambda p: {}))
    try:
        configuracion.type = 'raro'
        db.session.commit()
        resultado = ProveedorConector().otorgar(operacion(plataforma, usuario))
        assert resultado.resultado == RESULTADO_ERROR_TRANSITORIO
    finally:
        registry.quitar_tipo('raro')


def test_consultar_sin_soporte_del_tipo_es_permanente(conector_noop):
    plataforma, configuracion, usuario = conector_noop

    class SoloEscribe(Conector):
        def otorgar(self, solicitud):
            return ResultadoProveedor(RESULTADO_EXITOSO)

        def revocar(self, solicitud):
            return ResultadoProveedor(RESULTADO_EXITOSO)

    registry.registrar_tipo(TipoConector('escribe', SoloEscribe, lambda p: {}))
    try:
        configuracion.type = 'escribe'
        db.session.commit()
        resultado = ProveedorConector().consultar(
            operacion(plataforma, usuario))
        assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    finally:
        registry.quitar_tipo('escribe')


def test_el_conector_recibe_solo_datos_del_servidor(conector_noop):
    plataforma, configuracion, usuario = conector_noop
    recibido = {}

    class Espia(Conector):
        def otorgar(self, solicitud):
            recibido['solicitud'] = solicitud
            recibido['destino'] = self.destino
            return ResultadoProveedor(RESULTADO_EXITOSO)

        def revocar(self, solicitud):
            return ResultadoProveedor(RESULTADO_EXITOSO)

    registry.registrar_tipo(TipoConector('espia', Espia, lambda p: {}))
    try:
        configuracion.type = 'espia'
        db.session.commit()
        ProveedorConector().otorgar(operacion(plataforma, usuario))
    finally:
        registry.quitar_tipo('espia')
    solicitud, destino = recibido['solicitud'], recibido['destino']
    assert (solicitud.cuenta, solicitud.nivel, solicitud.operacion) == (
        'ana.ruiz@pruebas.local', NIVEL_USUARIO, OPERACION_OTORGAR)
    assert (destino.host, destino.puerto, destino.tiempo_espera) == (
        configuracion.host, configuracion.port, 10)
    assert REFERENCIA not in repr(destino)


def test_b1_el_destino_lleva_el_host_normalizado(conector_noop):
    """Regresión B1 (auditor-seguridad): el host crudo de la BD no llega al tipo."""
    plataforma, configuracion, usuario = conector_noop
    recibido = {}

    class Espia(Conector):
        def otorgar(self, solicitud):
            recibido['host'] = self.destino.host
            return ResultadoProveedor(RESULTADO_EXITOSO)

        def revocar(self, solicitud):
            return ResultadoProveedor(RESULTADO_EXITOSO)

    registry.registrar_tipo(TipoConector('espia_host', Espia, lambda p: {}))
    try:
        configuracion.type = 'espia_host'
        configuracion.host = ' NOOP.Pruebas.LOCAL '
        db.session.commit()
        resultado = ProveedorConector().otorgar(operacion(plataforma, usuario))
    finally:
        registry.quitar_tipo('espia_host')
    assert resultado.resultado == RESULTADO_EXITOSO
    assert recibido['host'] == 'noop.pruebas.local'


def test_b3_referencia_que_colisiona_con_otra_es_permanente(conector_noop):
    """Regresión B3: dos referencias distintas con la misma variable de dev."""
    plataforma, configuracion, usuario = conector_noop
    area = fabricas.crear_area()
    otra = fabricas.crear_plataforma(area, integration_type='conector')
    from tests.connectors.conftest import crear_conector
    crear_conector(otra, credential_ref='pokemon/pruebas_noop')
    resultado = ProveedorConector().otorgar(operacion(plataforma, usuario))
    assert (resultado.resultado, resultado.motivo) == (
        RESULTADO_ERROR_PERMANENTE, 'credencial_no_encontrada')
