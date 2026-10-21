"""Conector tipo API HTTP (FNC-051): plantillas sin inyección, estados HTTP,
destino seguro y registro del tipo. Sin red: resolución y transporte falsos."""
import json
import socket
import ssl
from types import MappingProxyType
from urllib.parse import parse_qs, urlsplit

import pytest

from app.modules.connectors import registry
from app.modules.connectors.api_http import (TIPO, ConectorApi,
                                             validar_params)
from app.modules.connectors.base import Destino, SolicitudConector
from app.modules.connectors.credenciales import Credencial
from app.modules.connectors.http_transporte import (ErrorConexion,
                                                    RespuestaHttp)
from app.modules.connectors.tipos import TIPO_API
from app.modules.connectors.validacion import validar_configuracion
from app.modules.provisioning.saneo import MENSAJES
from app.modules.provisioning.tipos import (RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)

HOST = 'erp.pruebas.local'
SECRETO = 'Cr3dencial-Ficticia-De-Prueba'
PUBLICA = '.'.join(('8', '8', '8', '8'))
PRIVADA = '.'.join(('10', '0', '0', '5'))

PARAMS = {
    'base_path': '/api/v1',
    'auth': {'esquema': 'bearer'},
    'otorgar': {'metodo': 'POST', 'ruta': '/usuarios',
                'cuerpo': {'email': '{correo}', 'rol': '{nivel}',
                           'plataforma': '{plataforma}'}},
    'revocar': {'metodo': 'DELETE', 'ruta': '/usuarios/{correo}'},
    'consultar': {'metodo': 'GET', 'ruta': '/usuarios',
                  'consulta': {'email': '{correo}'}},
}


def params(**cambios):
    valores = json.loads(json.dumps(PARAMS))
    valores.update(cambios)
    return valores


def solicitud(cuenta='ana.ruiz@pruebas.local', nivel='usuario'):
    return SolicitudConector(id_operacion='1', clave_idempotencia='c-1',
                             operacion='otorgar', nivel=nivel,
                             plataforma_id=7, cuenta=cuenta)


def dns(*direcciones):
    def getaddrinfo(host, puerto, **_):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (d, puerto))
                for d in direcciones]
    return getaddrinfo


class TransporteFalso:
    """Registra las llamadas y responde con estados o fallas programadas."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def enviar(self, ip, host, puerto, metodo, ruta, cabeceras, cuerpo,
               tiempo_espera, contexto):
        self.llamadas.append({'ip': ip, 'host': host, 'puerto': puerto,
                              'metodo': metodo, 'ruta': ruta,
                              'cabeceras': cabeceras, 'cuerpo': cuerpo,
                              'tiempo_espera': tiempo_espera,
                              'contexto': contexto})
        respuesta = self.respuestas.pop(0) if self.respuestas else 200
        if isinstance(respuesta, BaseException):
            raise respuesta
        return RespuestaHttp(respuesta)


def conector(*respuestas, valores=None, credencial=None, direcciones=(PUBLICA,),
             archivo_ca=None):
    transporte = TransporteFalso(*respuestas)
    destino = Destino(host=HOST, puerto=443, tiempo_espera=7,
                      params=MappingProxyType(valores or params()))
    api = ConectorApi(destino, credencial or Credencial(SECRETO),
                      transporte=transporte, getaddrinfo=dns(*direcciones),
                      archivo_ca=archivo_ca)
    return api, transporte


# --------------------------------------------------------------------------- #
# Operaciones
# --------------------------------------------------------------------------- #

def test_otorgar_envia_la_plantilla_con_los_campos_permitidos():
    api, transporte = conector(201)
    resultado = api.otorgar(solicitud(nivel='admin'))
    assert resultado.resultado == RESULTADO_EXITOSO
    llamada, = transporte.llamadas
    assert (llamada['metodo'], llamada['ruta']) == ('POST', '/api/v1/usuarios')
    assert json.loads(llamada['cuerpo']) == {
        'email': 'ana.ruiz@pruebas.local', 'rol': 'admin', 'plataforma': '7'}
    assert llamada['cabeceras']['Content-Type'] == 'application/json'
    assert llamada['tiempo_espera'] == 7


def test_conecta_a_la_ip_validada_y_verifica_el_nombre_del_host():
    api, transporte = conector(200)
    api.otorgar(solicitud())
    llamada, = transporte.llamadas
    assert (llamada['ip'], llamada['host'], llamada['puerto']) == (
        PUBLICA, HOST, 443)
    contexto = llamada['contexto']
    assert contexto.verify_mode == ssl.CERT_REQUIRED
    assert contexto.check_hostname is True
    assert contexto.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_revocar_codifica_el_correo_en_la_ruta():
    api, transporte = conector(204)
    assert api.revocar(solicitud()).resultado == RESULTADO_EXITOSO
    llamada, = transporte.llamadas
    assert llamada['metodo'] == 'DELETE'
    assert llamada['ruta'] == '/api/v1/usuarios/ana.ruiz%40pruebas.local'
    assert llamada['cuerpo'] is None


def test_revocar_404_cuenta_como_ya_revocado():
    api, _ = conector(404)
    assert api.revocar(solicitud()).resultado == RESULTADO_SIN_CAMBIOS


def test_revocar_410_cuenta_como_ya_revocado():
    api, _ = conector(410)
    assert api.revocar(solicitud()).resultado == RESULTADO_SIN_CAMBIOS


def test_otorgar_404_es_permanente():
    api, _ = conector(404)
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE


def test_otorgar_409_es_permanente_salvo_que_se_configure():
    api, _ = conector(409)
    assert api.otorgar(solicitud()).resultado == RESULTADO_ERROR_PERMANENTE
    valores = params()
    valores['otorgar']['sin_cambios'] = [409]
    api, _ = conector(409, valores=valores)
    assert api.otorgar(solicitud()).resultado == RESULTADO_SIN_CAMBIOS


def test_consultar_200_presente_y_404_ausente():
    api, transporte = conector(200, 404)
    assert api.consultar(solicitud()).presente is True
    resultado = api.consultar(solicitud())
    assert resultado.resultado == RESULTADO_EXITOSO
    assert resultado.presente is False
    llamada = transporte.llamadas[0]
    partes = urlsplit(llamada['ruta'])
    assert partes.path == '/api/v1/usuarios'
    assert parse_qs(partes.query) == {'email': ['ana.ruiz@pruebas.local']}


def test_consultar_sin_plantilla_es_permanente_como_la_base():
    valores = params()
    del valores['consultar']
    api, transporte = conector(valores=valores)
    resultado = api.consultar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'consulta_no_disponible'
    assert transporte.llamadas == []


# --------------------------------------------------------------------------- #
# Autenticación
# --------------------------------------------------------------------------- #

def test_bearer_va_en_authorization():
    api, transporte = conector(200)
    api.otorgar(solicitud())
    assert transporte.llamadas[0]['cabeceras']['Authorization'] == (
        f'Bearer {SECRETO}')


def test_basica_usa_usuario_y_secreto():
    valores = params(auth={'esquema': 'basic'})
    api, transporte = conector(200, valores=valores,
                               credencial=Credencial(SECRETO, 'servicio'))
    api.otorgar(solicitud())
    # base64("servicio:" + secreto)
    esperado = 'Basic c2VydmljaW86Q3IzZGVuY2lhbC1GaWN0aWNpYS1EZS1QcnVlYmE='
    assert transporte.llamadas[0]['cabeceras']['Authorization'] == esperado


def test_basica_sin_usuario_es_permanente_sin_llamar():
    api, transporte = conector(valores=params(auth={'esquema': 'basic'}))
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'credencial_no_encontrada'
    assert transporte.llamadas == []


def test_cabecera_propia_lleva_el_secreto_en_ese_nombre():
    valores = params(auth={'esquema': 'cabecera', 'nombre': 'X-Api-Token'})
    api, transporte = conector(200, valores=valores)
    api.otorgar(solicitud())
    cabeceras = transporte.llamadas[0]['cabeceras']
    assert cabeceras['X-Api-Token'] == SECRETO
    assert 'Authorization' not in cabeceras


def test_secreto_con_salto_de_linea_no_se_envia():
    api, transporte = conector(credencial=Credencial('abc\r\nX-Evil: 1'))
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'credencial_no_encontrada'
    assert transporte.llamadas == []


# --------------------------------------------------------------------------- #
# Inyección
# --------------------------------------------------------------------------- #

MALICIOSAS = ['a"b@x.mx', "a'b@x.mx", 'a;b@x.mx', 'a\r\nHost: evil@x.mx',
              'a\nb@x.mx', 'a/b@x.mx', 'a?x=1&y=2@x.mx',
              'a#b@x.mx', '{nivel}@x.mx', '%0d%0a@x.mx', 'a b@x.mx',
              'x"}, "rol": "admin", "z": {"@x.mx']


@pytest.mark.parametrize('cuenta', MALICIOSAS)
def test_entrada_maliciosa_no_altera_la_ruta_ni_el_cuerpo(cuenta):
    api, transporte = conector(200, 200, 200)
    api.otorgar(solicitud(cuenta=cuenta))
    api.revocar(solicitud(cuenta=cuenta))
    api.consultar(solicitud(cuenta=cuenta))
    otorgar, revocar, consultar = transporte.llamadas
    cuerpo = json.loads(otorgar['cuerpo'])
    assert cuerpo == {'email': cuenta, 'rol': 'usuario', 'plataforma': '7'}
    assert otorgar['ruta'] == '/api/v1/usuarios'
    # el valor queda en un solo segmento de la ruta, sin caracteres de control
    assert revocar['ruta'].startswith('/api/v1/usuarios/')
    assert revocar['ruta'].count('/') == 4
    assert all(c.isalnum() or c in '/%._~-' for c in revocar['ruta'])
    partes = urlsplit(consultar['ruta'])
    assert partes.path == '/api/v1/usuarios'
    assert parse_qs(partes.query) == {'email': [cuenta]}
    assert not any(c in consultar['ruta'] for c in '\r\n ;"')


@pytest.mark.parametrize('cuenta', ['..', '.', '@', 'sin-arroba', 'a/../..',
                                    '../x@y.mx', 'a\\..\\b@x.mx', ''])
def test_valores_que_recorren_la_ruta_o_sin_arroba_se_rechazan(cuenta):
    api, transporte = conector()
    for operacion in (api.otorgar, api.revocar, api.consultar):
        resultado = operacion(solicitud(cuenta=cuenta))
        assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
        assert resultado.motivo == 'valor_no_valido'
    assert transporte.llamadas == []


@pytest.mark.parametrize('nivel', ['..', '.', 'a/../b', ''])
def test_nivel_con_segmento_de_recorrido_se_rechaza(nivel):
    api, transporte = conector()
    resultado = api.revocar(solicitud(nivel=nivel))
    assert resultado.motivo == 'valor_no_valido'
    assert transporte.llamadas == []


def test_el_nivel_y_la_plataforma_tambien_se_codifican():
    valores = params(revocar={'metodo': 'DELETE',
                              'ruta': '/p/{plataforma}/n/{nivel}/{correo}'})
    api, transporte = conector(200, valores=valores)
    api.revocar(solicitud(nivel='a b/c'))
    assert transporte.llamadas[0]['ruta'] == (
        '/api/v1/p/7/n/a%20b%2Fc/ana.ruiz%40pruebas.local')


def test_la_plantilla_no_ejecuta_formato_ni_expresiones():
    valores = params()
    valores['otorgar']['cuerpo'] = {'x': '{correo.__class__}',
                                    'y': '{0}', 'z': '${correo}'}
    api, transporte = conector(valores=valores)
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert transporte.llamadas == []


# --------------------------------------------------------------------------- #
# Estados HTTP
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('estado', [408, 425, 429, 500, 502, 503, 504])
def test_estados_transitorios(estado):
    api, _ = conector(estado)
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_TRANSITORIO
    assert resultado.motivo == 'http_transitorio'
    assert resultado.detalle == f'HTTP {estado}'


@pytest.mark.parametrize('estado', [400, 401, 403, 404, 409, 422, 501])
def test_estados_permanentes(estado):
    api, _ = conector(estado)
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'http_rechazado'
    assert resultado.detalle == f'HTTP {estado}'


@pytest.mark.parametrize('estado', [301, 302, 303, 307, 308])
def test_no_sigue_redirecciones(estado):
    api, transporte = conector(estado)
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'redireccion_no_permitida'
    assert len(transporte.llamadas) == 1


@pytest.mark.parametrize('estado', [200, 201, 202, 204])
def test_estados_de_exito(estado):
    api, _ = conector(estado)
    assert api.otorgar(solicitud()).resultado == RESULTADO_EXITOSO


# --------------------------------------------------------------------------- #
# Destino y red
# --------------------------------------------------------------------------- #

def test_host_que_resuelve_a_ip_privada_no_se_llama():
    api, transporte = conector(direcciones=(PRIVADA,))
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'destino_no_permitido'
    assert transporte.llamadas == []


def test_dns_caido_es_transitorio():
    def falla(*_, **__):
        raise socket.gaierror('sin dns')
    api, transporte = conector()
    api._getaddrinfo = falla
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_TRANSITORIO
    assert resultado.motivo == 'red_no_disponible'
    assert transporte.llamadas == []


def test_conexion_rechazada_prueba_la_siguiente_ip_validada():
    otra = '.'.join(('1', '1', '1', '1'))
    api, transporte = conector(ErrorConexion(), 200,
                               direcciones=(PUBLICA, otra))
    assert api.otorgar(solicitud()).resultado == RESULTADO_EXITOSO
    assert [c['ip'] for c in transporte.llamadas] == [PUBLICA, otra]


@pytest.mark.parametrize('falla', [TimeoutError(), ConnectionResetError(),
                                   OSError('x')])
def test_tras_enviar_la_peticion_no_se_reintenta_en_otra_ip(falla):
    otra = '.'.join(('1', '1', '1', '1'))
    api, transporte = conector(falla, 200, direcciones=(PUBLICA, otra))
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_TRANSITORIO
    assert len(transporte.llamadas) == 1


def test_tiempo_agotado_y_red_son_transitorios():
    for falla in (TimeoutError(), ConnectionResetError(), OSError('x')):
        api, _ = conector(falla)
        resultado = api.otorgar(solicitud())
        assert resultado.resultado == RESULTADO_ERROR_TRANSITORIO
        assert resultado.motivo == 'red_no_disponible'


def test_certificado_invalido_es_permanente_y_no_filtra_el_texto():
    falla = ssl.SSLCertVerificationError(1, f'fallo con {SECRETO}')
    api, transporte = conector(falla)
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'tls_no_valido'
    assert resultado.detalle is None
    assert len(transporte.llamadas) == 1


def test_ca_inexistente_es_permanente_sin_llamar(tmp_path):
    api, transporte = conector(archivo_ca=str(tmp_path / 'no-existe.pem'))
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert resultado.motivo == 'tls_no_valido'
    assert transporte.llamadas == []


def test_el_detalle_nunca_lleva_el_cuerpo_ni_la_credencial():
    api, _ = conector(500)
    resultado = api.otorgar(solicitud())
    assert SECRETO not in (resultado.detalle or '')


def test_motivos_nuevos_tienen_mensaje_en_el_catalogo():
    for motivo in ('destino_no_permitido', 'valor_no_valido', 'tls_no_valido', 'http_rechazado',
                   'http_transitorio', 'red_no_disponible',
                   'redireccion_no_permitida'):
        assert motivo in MENSAJES


# --------------------------------------------------------------------------- #
# Esquema de parámetros
# --------------------------------------------------------------------------- #

def test_los_params_de_ejemplo_son_validos():
    assert validar_params(params()) == {}


def test_params_minimos_validos():
    assert validar_params({'auth': {'esquema': 'bearer'},
                           'otorgar': {'metodo': 'PUT', 'ruta': '/a'},
                           'revocar': {'metodo': 'DELETE', 'ruta': '/a'}}) == {}


@pytest.mark.parametrize('cambio, campo', [
    ({'auth': None}, 'auth'),
    ({'auth': {'esquema': 'otro'}}, 'auth.esquema'),
    ({'auth': {'esquema': 'cabecera'}}, 'auth.nombre'),
    ({'auth': {'esquema': 'cabecera', 'nombre': 'Host'}}, 'auth.nombre'),
    ({'auth': {'esquema': 'cabecera', 'nombre': 'X\r\nA'}}, 'auth.nombre'),
    ({'auth': {'esquema': 'bearer', 'nombre': 'X-A'}}, 'auth.nombre'),
    ({'base_path': 'sin-barra'}, 'base_path'),
    ({'base_path': '/a/../b'}, 'base_path'),
    ({'base_path': '/a?x=1'}, 'base_path'),
    ({'base_path': '/{correo}'}, 'base_path'),
    ({'extra': 1}, 'extra'),
    ({'otorgar': None}, 'otorgar'),
    ({'otorgar': {'metodo': 'TRACE', 'ruta': '/a'}}, 'otorgar.metodo'),
    ({'otorgar': {'metodo': 'POST', 'ruta': 'a'}}, 'otorgar.ruta'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a/{otro}'}}, 'otorgar.ruta'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a/{correo'}}, 'otorgar.ruta'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a/..'}}, 'otorgar.ruta'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a b'}}, 'otorgar.ruta'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a%2e%2e'}}, 'otorgar.ruta'),
    ({'otorgar': {'metodo': 'GET', 'ruta': '/a', 'cuerpo': {}}},
     'otorgar.cuerpo'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a', 'cuerpo': 'texto'}},
     'otorgar.cuerpo'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a',
                  'cuerpo': {'x': '{raro}'}}}, 'otorgar.cuerpo'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a',
                  'cuerpo': {'{correo}': 'x'}}}, 'otorgar.cuerpo'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a', 'sin_cambios': [200]}},
     'otorgar.sin_cambios'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a', 'sin_cambios': 'x'}},
     'otorgar.sin_cambios'),
    ({'otorgar': {'metodo': 'POST', 'ruta': '/a', 'x': 1}}, 'otorgar.x'),
    ({'consultar': {'metodo': 'GET', 'ruta': '/a',
                    'consulta': {'A b': '{correo}'}}}, 'consultar.consulta'),
])
def test_params_invalidos(cambio, campo):
    valores = params()
    for clave, valor in cambio.items():
        if valor is None:
            valores.pop(clave, None)
        else:
            valores[clave] = valor
    errores = validar_params(valores)
    assert campo in errores
    assert all(isinstance(m, str) and m for m in errores.values())


@pytest.mark.parametrize('cambio', [
    {'auth': {'esquema': 'bearer'}, 'otorgar': {}},
])
def test_params_faltantes_se_reportan(cambio):
    assert validar_params(cambio)


def test_params_con_cuerpo_muy_profundo_se_rechazan():
    cuerpo = {'a': 'x'}
    for _ in range(10):
        cuerpo = {'a': cuerpo}
    valores = params()
    valores['otorgar']['cuerpo'] = cuerpo
    assert 'otorgar.cuerpo' in validar_params(valores)


def test_en_ejecucion_se_revalidan_los_params_de_la_bd():
    valores = params(otorgar={'metodo': 'TRACE', 'ruta': '/a'})
    api, transporte = conector(valores=valores)
    resultado = api.otorgar(solicitud())
    assert resultado.resultado == RESULTADO_ERROR_PERMANENTE
    assert transporte.llamadas == []


# --------------------------------------------------------------------------- #
# Registro y configuración
# --------------------------------------------------------------------------- #

def test_el_tipo_api_queda_registrado(app):
    assert registry.obtener_tipo(TIPO_API) is TIPO
    assert TIPO_API in registry.tipos_disponibles()


def test_validar_configuracion_acepta_api_con_params_validos(app, monkeypatch):
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS', HOST)
    limpio, errores = validar_configuracion({
        'type': 'api', 'host': HOST, 'port': 443, 'params': params(),
        'credential_ref': 'pokemon/erp-api'})
    assert errores == {}
    assert limpio['type'] == 'api'


def test_validar_configuracion_reporta_los_params_del_tipo(app, monkeypatch):
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS', HOST)
    _, errores = validar_configuracion({
        'type': 'api', 'host': HOST, 'port': 443,
        'params': {'base_path': 'x'}, 'credential_ref': 'pokemon/erp-api'})
    assert 'params.base_path' in errores
    assert 'params.auth' in errores
