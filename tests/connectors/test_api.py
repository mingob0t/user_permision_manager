"""API de configuración de conectores (FNC-061, contrato
`conectores-y-ejecuciones.md`). La matriz por rol está en
`tests/matriz_proteccion.py`; aquí, las reglas de cada endpoint."""
import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import ESTADO_ACTIVO, ORIGEN_SOLICITUD
from app.modules.audit.models import AuditLog
from app.modules.connectors import api as api_conectores
from app.modules.connectors import noop, registry
from app.modules.connectors.models import PlatformConnector
from app.modules.connectors.registry import TipoConector
from app.modules.connectors.tipos import (CREDENCIAL_NO_ENCONTRADA,
                                          CREDENCIAL_OK,
                                          CREDENCIAL_SIN_VERIFICAR, TIPO_NOOP)
from app.modules.platforms.tipos import (NIVEL_USUARIO, TIPO_CONECTOR,
                                         TIPO_LDAP)
from tests import fabricas
from tests.connectors.conftest import (HOST_PERMITIDO, REFERENCIA,
                                       SECRETO_FICTICIO, VARIABLE_CREDENCIAL,
                                       crear_conector)

A = '/api/v1'
TIPO_OTRO = 'otro-pruebas'
CUERPO_VALIDO = {'type': TIPO_NOOP, 'host': HOST_PERMITIDO, 'port': 443,
                 'params': {}, 'credential_ref': REFERENCIA, 'active': True}


def ruta(plataforma_id, sufijo=''):
    return f'{A}/platforms/{plataforma_id}/connector{sufijo}'


def eventos(accion):
    return AuditLog.query.filter_by(action=accion).all()


@pytest.fixture
def plataforma(app, entorno_conector):
    area = fabricas.crear_area()
    return fabricas.crear_plataforma(area, integration_type=TIPO_CONECTOR,
                                     status='Activo')


@pytest.fixture
def superadmin(cliente_como):
    return cliente_como(fabricas.crear_usuario(ROLE_ADMIN))


@pytest.fixture
def tipo_otro():
    """Segundo tipo registrado, para cambiar el `type`."""
    registry.registrar_tipo(TipoConector(TIPO_OTRO, noop.ConectorNoop,
                                         noop.validar_params))
    yield TIPO_OTRO
    registry.quitar_tipo(TIPO_OTRO)


@pytest.fixture
def espia_cache(monkeypatch):
    llamadas = []
    monkeypatch.setattr(api_conectores, 'limpiar_cache',
                        lambda: llamadas.append(True))
    return llamadas


def acceso_vigente(plataforma):
    usuario = fabricas.crear_usuario()
    acceso = PlatformAccessGrant(user_id=usuario.id, platform_id=plataforma.id,
                                 level=NIVEL_USUARIO, origin=ORIGEN_SOLICITUD,
                                 request_id=1, status=ESTADO_ACTIVO)
    acceso.sincronizar_slots()
    db.session.add(acceso)
    db.session.commit()


# --------------------------------------------------------------------------- #
# Protección
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('rol', [ROLE_USER, ROLE_AREA_ADMIN])
@pytest.mark.parametrize('metodo,sufijo,cuerpo', [
    ('GET', '', None), ('PUT', '', CUERPO_VALIDO), ('DELETE', '', {}),
    ('POST', '/test', {})])
def test_solo_el_superadmin_aunque_administre_el_area(
        plataforma, cliente_como, rol, metodo, sufijo, cuerpo):
    crear_conector(plataforma)
    actor = fabricas.crear_usuario(rol, areas=[plataforma.area],
                                   areas_administradas=[plataforma.area]
                                   if rol == ROLE_AREA_ADMIN else ())
    respuesta = cliente_como(actor).open(ruta(plataforma.id, sufijo),
                                         method=metodo, json=cuerpo)
    assert respuesta.status_code == 403
    assert PlatformConnector.query.count() == 1


@pytest.mark.parametrize('metodo,sufijo,cuerpo', [
    ('PUT', '', CUERPO_VALIDO), ('DELETE', '', {}), ('POST', '/test', {})])
def test_escrituras_solo_desde_el_portal_y_en_json(plataforma, superadmin,
                                                   metodo, sufijo, cuerpo):
    crear_conector(plataforma)
    sin_json = superadmin.open(ruta(plataforma.id, sufijo), method=metodo,
                               data='x')
    ajena = superadmin.open(ruta(plataforma.id, sufijo), method=metodo,
                            json=cuerpo,
                            headers={'Sec-Fetch-Site': 'cross-site'})
    assert sin_json.status_code == 415
    assert ajena.status_code == 403
    assert ajena.get_json()['code'] == 'csrf_invalido'


# --------------------------------------------------------------------------- #
# GET
# --------------------------------------------------------------------------- #

def test_get_devuelve_la_configuracion_sin_el_secreto(plataforma, superadmin):
    crear_conector(plataforma)
    respuesta = superadmin.get(ruta(plataforma.id))
    assert respuesta.status_code == 200
    conector = respuesta.get_json()['connector']
    assert conector['credential_ref'] == REFERENCIA
    assert conector['host'] == HOST_PERMITIDO
    assert SECRETO_FICTICIO not in respuesta.get_data(as_text=True)


@pytest.mark.parametrize('metodo,sufijo,cuerpo', [
    ('GET', '', None), ('DELETE', '', {}), ('POST', '/test', {})])
def test_sin_configuracion_o_plataforma_responde_404(plataforma, superadmin,
                                                     metodo, sufijo, cuerpo):
    for plataforma_id in (plataforma.id, 9999):
        respuesta = superadmin.open(ruta(plataforma_id, sufijo),
                                    method=metodo, json=cuerpo)
        assert respuesta.status_code == 404
        assert respuesta.get_json()['code'] == 'no_encontrado'


# --------------------------------------------------------------------------- #
# PUT
# --------------------------------------------------------------------------- #

def test_put_crea_audita_y_limpia_la_cache(plataforma, superadmin,
                                           espia_cache):
    respuesta = superadmin.put(ruta(plataforma.id), json=CUERPO_VALIDO)

    assert respuesta.status_code == 200, respuesta.get_json()
    datos = respuesta.get_json()
    assert datos['status'] == 'success'
    assert datos['connector']['credential_status'] == CREDENCIAL_SIN_VERIFICAR
    assert SECRETO_FICTICIO not in respuesta.get_data(as_text=True)
    guardada = PlatformConnector.query.filter_by(
        platform_id=plataforma.id).one()
    assert guardada.type == TIPO_NOOP
    [evento] = eventos('conector_configurado')
    assert evento.platform_id == plataforma.id
    assert evento.after_state['host'] == HOST_PERMITIDO
    assert SECRETO_FICTICIO not in str(evento.after_state)
    assert espia_cache == [True]


def test_put_reemplaza_y_audita_solo_lo_que_cambia(plataforma, superadmin):
    crear_conector(plataforma)
    respuesta = superadmin.put(ruta(plataforma.id),
                               json={**CUERPO_VALIDO, 'port': 8443})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['connector']['port'] == 8443
    [evento] = eventos('conector_configurado')
    assert evento.before_state == {'port': 443}
    assert evento.after_state == {'port': 8443}

    # Reenviar lo mismo no audita otra vez.
    superadmin.put(ruta(plataforma.id), json={**CUERPO_VALIDO, 'port': 8443})
    assert len(eventos('conector_configurado')) == 1


def test_put_con_host_nuevo_deja_la_credencial_sin_verificar(plataforma,
                                                             superadmin,
                                                             monkeypatch):
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS',
                       f'{HOST_PERMITIDO},otro.pruebas.local')
    crear_conector(plataforma, credential_status=CREDENCIAL_OK)
    respuesta = superadmin.put(ruta(plataforma.id), json={
        **CUERPO_VALIDO, 'host': 'otro.pruebas.local'})
    assert respuesta.get_json()['connector']['credential_status'] == \
        CREDENCIAL_SIN_VERIFICAR


@pytest.mark.parametrize('cambio,campo', [
    ({'host': 'ajeno.pruebas.local'}, 'host'),
    ({'host': '2001:db8::1'}, 'host'),
    ({'port': 0}, 'port'),
    ({'params': {'base_path': '/x'}}, 'params.base_path'),
    ({'params': {'password': 'x'}}, 'params.password'),
    ({'credential_ref': 'pokemon/con__doble'}, 'credential_ref'),
    ({'type': 'ssh'}, 'type'),
    ({'active': 'si'}, 'active'),
])
def test_put_invalido_responde_422_por_campo(plataforma, superadmin,
                                             espia_cache, cambio, campo):
    respuesta = superadmin.put(ruta(plataforma.id),
                               json={**CUERPO_VALIDO, **cambio})
    assert respuesta.status_code == 422
    datos = respuesta.get_json()
    assert datos['code'] == 'validacion'
    assert campo in datos['fields']
    assert PlatformConnector.query.count() == 0
    assert espia_cache == []


def test_put_rechaza_una_referencia_equivalente_a_otra_en_uso(plataforma,
                                                              superadmin):
    otra = fabricas.crear_plataforma(plataforma.area,
                                     integration_type=TIPO_CONECTOR)
    crear_conector(otra, credential_ref='pokemon/erp-api')
    respuesta = superadmin.put(ruta(plataforma.id), json={
        **CUERPO_VALIDO, 'credential_ref': 'pokemon/erp_api'})
    assert respuesta.status_code == 422
    assert 'credential_ref' in respuesta.get_json()['fields']


@pytest.mark.parametrize('cuerpo', [
    {**CUERPO_VALIDO, 'credential_status': CREDENCIAL_OK},
    {**CUERPO_VALIDO, 'secret': SECRETO_FICTICIO},
    {**CUERPO_VALIDO, 'platform_id': 2},
])
def test_put_con_campos_fuera_de_la_lista_blanca_responde_400(
        plataforma, superadmin, cuerpo):
    respuesta = superadmin.put(ruta(plataforma.id), json=cuerpo)
    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'campo_no_permitido'
    assert SECRETO_FICTICIO not in respuesta.get_data(as_text=True)


def test_put_en_plataforma_sin_conector_responde_409(app, entorno_conector,
                                                     superadmin):
    ldap = fabricas.crear_plataforma(fabricas.crear_area(),
                                     integration_type=TIPO_LDAP)
    respuesta = superadmin.put(ruta(ldap.id), json=CUERPO_VALIDO)
    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'plataforma_sin_conector'


def test_put_en_plataforma_inexistente_responde_404(app, entorno_conector,
                                                    superadmin):
    respuesta = superadmin.put(ruta(9999), json=CUERPO_VALIDO)
    assert respuesta.status_code == 404


def test_cambiar_el_tipo_con_accesos_vigentes_responde_409(plataforma,
                                                           superadmin,
                                                           tipo_otro):
    crear_conector(plataforma)
    acceso_vigente(plataforma)
    respuesta = superadmin.put(ruta(plataforma.id),
                               json={**CUERPO_VALIDO, 'type': tipo_otro})
    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'plataforma_con_accesos'
    assert PlatformConnector.query.one().type == TIPO_NOOP

    # Con accesos vigentes sí se cambia lo demás.
    otra = superadmin.put(ruta(plataforma.id),
                          json={**CUERPO_VALIDO, 'port': 8443})
    assert otra.status_code == 200


def test_cambiar_el_tipo_sin_accesos_se_permite(plataforma, superadmin,
                                                tipo_otro):
    crear_conector(plataforma)
    respuesta = superadmin.put(ruta(plataforma.id),
                               json={**CUERPO_VALIDO, 'type': tipo_otro})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['connector']['type'] == tipo_otro


# --------------------------------------------------------------------------- #
# DELETE
# --------------------------------------------------------------------------- #

def test_delete_borra_audita_y_limpia_la_cache(plataforma, superadmin,
                                               espia_cache):
    crear_conector(plataforma)
    respuesta = superadmin.delete(ruta(plataforma.id), json={})
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {'status': 'success'}
    assert PlatformConnector.query.count() == 0
    [evento] = eventos('conector_eliminado')
    assert evento.before_state['host'] == HOST_PERMITIDO
    assert espia_cache == [True]


def test_delete_con_accesos_vigentes_responde_409(plataforma, superadmin):
    crear_conector(plataforma)
    acceso_vigente(plataforma)
    respuesta = superadmin.delete(ruta(plataforma.id), json={})
    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'plataforma_con_accesos'
    assert PlatformConnector.query.count() == 1


@pytest.mark.parametrize('sufijo', ['', '/test'])
def test_acciones_sin_datos_rechazan_campos(plataforma, superadmin, sufijo):
    crear_conector(plataforma)
    metodo = 'POST' if sufijo else 'DELETE'
    respuesta = superadmin.open(ruta(plataforma.id, sufijo), method=metodo,
                                json={'force': True})
    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'campo_no_permitido'
    assert PlatformConnector.query.count() == 1


# --------------------------------------------------------------------------- #
# Prueba de conexión
# --------------------------------------------------------------------------- #

def test_prueba_correcta_marca_la_credencial_ok(plataforma, superadmin):
    crear_conector(plataforma)
    respuesta = superadmin.post(ruta(plataforma.id, '/test'), json={})
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {'status': 'success', 'result': 'ok',
                                    'message': 'Conexión correcta.'}
    assert SECRETO_FICTICIO not in respuesta.get_data(as_text=True)
    assert PlatformConnector.query.one().credential_status == CREDENCIAL_OK
    [evento] = eventos('conector_probado')
    assert evento.status == 'success'
    # No otorga: la cuenta del superadmin no queda con acceso en el `noop`.
    assert not noop._CUENTAS


def test_prueba_sin_credencial_da_mensaje_generico(plataforma, superadmin,
                                                   monkeypatch):
    crear_conector(plataforma)
    monkeypatch.delenv(VARIABLE_CREDENCIAL)
    respuesta = superadmin.post(ruta(plataforma.id, '/test'), json={})
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        'status': 'success', 'result': 'error',
        'message': 'No se pudo conectar con la plataforma.'}
    assert PlatformConnector.query.one().credential_status == \
        CREDENCIAL_NO_ENCONTRADA
    [evento] = eventos('conector_probado')
    assert evento.status == 'error'


def test_prueba_con_host_fuera_de_la_lista_falla(plataforma, superadmin,
                                                 monkeypatch):
    crear_conector(plataforma)
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS', 'otro.pruebas.local')
    respuesta = superadmin.post(ruta(plataforma.id, '/test'), json={})
    assert respuesta.get_json()['result'] == 'error'
    assert PlatformConnector.query.one().credential_status == \
        CREDENCIAL_SIN_VERIFICAR
