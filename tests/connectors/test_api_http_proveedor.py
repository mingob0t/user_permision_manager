"""Conector `api` de punta a punta con el proveedor y el ejecutor (FNC-051),
sin red: transporte y DNS falsos."""
import socket

import pytest

from app import db
from app.modules.connectors import api_http
from app.modules.connectors.http_transporte import RespuestaHttp
from app.modules.connectors.provider import ProveedorConector
from app.modules.connectors.tipos import TIPO_API
from app.modules.provisioning.providers import Operacion
from app.modules.provisioning.tipos import (OPERACION_OTORGAR,
                                            OPERACION_REVOCAR,
                                            RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)
from app.modules.platforms.tipos import NIVEL_USUARIO
from tests.connectors.conftest import SECRETO_FICTICIO
from tests.connectors.test_api_http import PARAMS, PRIVADA, PUBLICA, params


class Transporte:
    llamadas = []
    estados = []

    def enviar(self, ip, host, puerto, metodo, ruta, cabeceras, cuerpo,
               tiempo_espera, contexto):
        Transporte.llamadas.append((ip, host, metodo, ruta, dict(cabeceras)))
        return RespuestaHttp(Transporte.estados.pop(0))


@pytest.fixture
def api_configurada(conector_noop, monkeypatch):
    plataforma, configuracion, usuario = conector_noop
    configuracion.type = TIPO_API
    configuracion.params = params()
    db.session.commit()
    Transporte.llamadas, Transporte.estados = [], []
    monkeypatch.setattr(api_http, 'TransporteHttps', Transporte)
    monkeypatch.setattr(api_http.socket, 'getaddrinfo', lambda h, p, **_: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', (PUBLICA, p))])
    return plataforma, configuracion, usuario


def operacion(plataforma, usuario, nombre):
    return Operacion(id_operacion='1', clave_idempotencia='c-1',
                     operacion=nombre, nivel=NIVEL_USUARIO,
                     plataforma_id=plataforma.id, usuario_id=usuario.id)


def test_otorga_y_revoca_con_la_credencial_del_gestor(api_configurada):
    plataforma, _, usuario = api_configurada
    Transporte.estados = [201, 404]
    proveedor = ProveedorConector()
    otorgar = proveedor.otorgar(operacion(plataforma, usuario,
                                          OPERACION_OTORGAR))
    revocar = proveedor.revocar(operacion(plataforma, usuario,
                                          OPERACION_REVOCAR))
    assert otorgar.resultado == RESULTADO_EXITOSO
    assert revocar.resultado == RESULTADO_SIN_CAMBIOS
    (ip, host, metodo, ruta, cabeceras), _ = Transporte.llamadas
    assert (ip, host, metodo, ruta) == (PUBLICA, 'noop.pruebas.local', 'POST',
                                        '/api/v1/usuarios')
    assert cabeceras['Authorization'] == f'Bearer {SECRETO_FICTICIO}'


def test_el_host_sale_de_la_configuracion_y_no_de_params(api_configurada):
    plataforma, configuracion, usuario = api_configurada
    configuracion.params = {**params(), 'host': 'evil.pruebas.local'}
    db.session.commit()
    resultado = ProveedorConector().otorgar(
        operacion(plataforma, usuario, OPERACION_OTORGAR))
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert Transporte.llamadas == []


def test_host_que_resuelve_a_ip_interna_no_se_llama(api_configurada,
                                                    monkeypatch):
    plataforma, _, usuario = api_configurada
    monkeypatch.setattr(api_http.socket, 'getaddrinfo', lambda h, p, **_: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', (PRIVADA, p))])
    resultado = ProveedorConector().otorgar(
        operacion(plataforma, usuario, OPERACION_OTORGAR))
    assert resultado.motivo == 'destino_no_permitido'
    assert Transporte.llamadas == []


def test_el_detalle_hacia_la_bitacora_no_lleva_el_secreto(api_configurada):
    plataforma, _, usuario = api_configurada
    Transporte.estados = [403]
    resultado = ProveedorConector().otorgar(
        operacion(plataforma, usuario, OPERACION_OTORGAR))
    assert resultado.detalle == 'HTTP 403'
    assert SECRETO_FICTICIO not in repr(resultado)
