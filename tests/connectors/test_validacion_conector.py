"""Validación de la configuración de un conector (contrato
`conectores-y-ejecuciones.md`, `PUT /platforms/<id>/connector`; FNC-050)."""
import pytest

from app.modules.connectors import registry
from app.modules.connectors.registry import TipoConector
from app.modules.connectors.validacion import (
    MENSAJE_HOST, MENSAJE_PARAMS_PROFUNDOS, MENSAJE_REFERENCIA_EN_CONFLICTO,
    validar_configuracion)
from tests.connectors.conftest import HOST_PERMITIDO, REFERENCIA

ENTORNO = {'APP_ENV': 'development', 'CONNECTOR_ALLOWED_HOSTS': HOST_PERMITIDO}


def datos(**cambios):
    base = {'type': 'noop', 'host': HOST_PERMITIDO, 'port': 443, 'params': {},
            'credential_ref': REFERENCIA}
    base.update(cambios)
    return base


def test_configuracion_valida_se_normaliza(app):
    limpio, errores = validar_configuracion(
        datos(host='NOOP.pruebas.local '), ENTORNO)
    assert errores == {}
    assert limpio == {'type': 'noop', 'host': HOST_PERMITIDO, 'port': 443,
                      'params': {}, 'credential_ref': REFERENCIA,
                      'active': True}


# IP sin IPv4 de 4 octetos (lineamientos): IPv6, abreviada, decimal y hex.
@pytest.mark.parametrize('host', ['2001:db8::1', '::1', '10.1.2', '2130706433',
                                  '0x7f000001',
                                  'otro.pruebas.local', 'https://x.local',
                                  '', None, 5])
def test_host_ajeno_ip_o_invalido(app, host):
    _, errores = validar_configuracion(datos(host=host), ENTORNO)
    assert errores['host'] == MENSAJE_HOST == 'Usa un nombre de host autorizado.'


def test_sin_lista_blanca_ningun_host_es_valido(app):
    _, errores = validar_configuracion(datos(), {'APP_ENV': 'development'})
    assert 'host' in errores


@pytest.mark.parametrize('puerto', [0, 65536, '443', True, None, 4.5])
def test_puerto_fuera_de_rango(app, puerto):
    _, errores = validar_configuracion(datos(port=puerto), ENTORNO)
    assert 'port' in errores


@pytest.mark.parametrize('referencia', ['', None, 'x' * 201, 'con espacio',
                                        '../salir', '/absoluta',
                                        'tiene\nsalto'])
def test_referencia_invalida(app, referencia):
    _, errores = validar_configuracion(datos(credential_ref=referencia),
                                       ENTORNO)
    assert 'credential_ref' in errores


def test_tipo_sin_implementar_o_desconocido(app):
    for tipo in ('otro', None):
        _, errores = validar_configuracion(datos(type=tipo), ENTORNO)
        assert 'type' in errores, tipo


def test_noop_no_se_acepta_fuera_de_dev_y_pruebas(app, monkeypatch):
    registry.quitar_tipo('noop')
    _, errores = validar_configuracion(datos(), ENTORNO)
    assert 'type' in errores


def test_params_debe_ser_objeto_y_sin_secretos(app):
    _, errores = validar_configuracion(datos(params=['a']), ENTORNO)
    assert 'params' in errores
    registry.registrar_tipo(TipoConector('libre', fabrica=object,
                                         validar_params=lambda p: {}))
    try:
        for clave in ('password', 'api_key', 'Token', 'mi_secreto'):
            _, errores = validar_configuracion(
                datos(type='libre', params={clave: 'x'}), ENTORNO)
            assert f'params.{clave}' in errores, clave
        _, errores = validar_configuracion(
            datos(type='libre', params={'base_path': '/usuarios'}), ENTORNO)
        assert errores == {}
    finally:
        registry.quitar_tipo('libre')


def test_params_validados_por_el_esquema_del_tipo(app):
    _, errores = validar_configuracion(datos(params={'base_path': '/x'}),
                                       ENTORNO)
    assert 'params.base_path' in errores  # el noop no admite parámetros


def test_active_debe_ser_booleano(app):
    _, errores = validar_configuracion(datos(active='si'), ENTORNO)
    assert 'active' in errores
    limpio, errores = validar_configuracion(datos(active=False), ENTORNO)
    assert errores == {} and limpio['active'] is False


def _libre():
    registry.registrar_tipo(TipoConector('libre', fabrica=object,
                                         validar_params=lambda p: {}))


def test_b2_secretos_dentro_de_listas(app):
    """Regresión B2: una clave sensible dentro de una lista se detecta."""
    _libre()
    try:
        _, errores = validar_configuracion(
            datos(type='libre',
                  params={'extras': [{'nombre': 'x'}, {'api_key': 'y'}]}),
            ENTORNO)
        assert 'params.extras.1.api_key' in errores
        _, errores = validar_configuracion(
            datos(type='libre', params={'lista': [[{'token': 'z'}]]}), ENTORNO)
        assert 'params.lista.0.0.token' in errores
    finally:
        registry.quitar_tipo('libre')


def test_b2_profundidad_excesiva_es_invalida_sin_recursionerror(app):
    """Regresión B2: un anidado profundo se rechaza, no rompe la validación."""
    _libre()
    profundo = {}
    actual = profundo
    for _ in range(5000):
        actual['n'] = [{}]
        actual = actual['n'][0]
    try:
        _, errores = validar_configuracion(datos(type='libre',
                                                 params=profundo), ENTORNO)
        assert errores['params'] == MENSAJE_PARAMS_PROFUNDOS
        poco = {'a': {'b': [{'c': 1}]}}
        _, errores = validar_configuracion(datos(type='libre', params=poco),
                                           ENTORNO)
        assert errores == {}
    finally:
        registry.quitar_tipo('libre')


@pytest.mark.parametrize('referencia', ['pokemon__erp', 'pokemon/_erp',
                                        'pokemon._erp', 'pokemon/erp_'])
def test_b3_referencia_con_doble_guion_bajo_en_su_variable(app, referencia):
    """Regresión B3: `__` en la variable choca con el sufijo `__USUARIO`."""
    _, errores = validar_configuracion(datos(credential_ref=referencia),
                                       ENTORNO)
    assert 'credential_ref' in errores


def test_b3_referencia_que_colisiona_con_otra_en_uso(app):
    """Regresión B3: misma variable de entorno que otra referencia distinta."""
    for en_uso in (['pokemon/pruebas_noop'], ['POKEMON/PRUEBAS-NOOP'],
                   ['pokemon.pruebas.noop']):
        _, errores = validar_configuracion(datos(), ENTORNO,
                                           referencias_en_uso=en_uso)
        assert errores.get('credential_ref') == MENSAJE_REFERENCIA_EN_CONFLICTO
    _, errores = validar_configuracion(datos(), ENTORNO,
                                       referencias_en_uso=[REFERENCIA])
    assert errores == {}  # la misma referencia (otra plataforma) sí vale
