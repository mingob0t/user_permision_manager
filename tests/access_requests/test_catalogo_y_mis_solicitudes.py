"""`GET /access-requests/catalog` y `/mine` (FNC-056)."""
import pytest

from app import db
from app.modules.access_requests.models import PlatformAccessRequest
from tests import fabricas
from tests.access_requests.conftest import (cambiar_de_actor, dar_acceso,
                                            pedir)

CATALOGO = '/api/v1/access-requests/catalog'
MIAS = '/api/v1/access-requests/mine'


def _por_nombre(respuesta):
    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    return {e['platform']['name']: e for e in respuesta.get_json()}


# --------------------------------------------------------------------------- #
# Catálogo
# --------------------------------------------------------------------------- #

def test_usuario_ve_solo_las_plataformas_de_sus_areas(escena, cliente_como):
    catalogo = _por_nombre(cliente_como(escena['usuario']).get(CATALOGO))

    assert set(catalogo) == {'Contabilidad'}
    entrada = catalogo['Contabilidad']
    assert entrada['area'] == {'id': escena['area'].id, 'name': 'Finanzas'}
    assert entrada['can_request'] is True
    assert entrada['requestable_levels'] == ['usuario', 'admin']
    assert entrada['my_level'] is None and entrada['my_access_status'] is None
    assert entrada['pending_request_id'] is None


def test_excluye_plataformas_y_areas_inactivas(escena, cliente_como):
    fabricas.crear_plataforma(escena['area'], 'Apagada', status='Inactivo')
    escena['otra'].status = 'Inactivo'
    db.session.commit()

    catalogo = _por_nombre(cliente_como(escena['admin_otra']).get(CATALOGO))

    assert set(catalogo) == {'Contabilidad'}


def test_admin_ve_sus_areas_sin_poder_solicitar(escena, cliente_como):
    catalogo = _por_nombre(cliente_como(escena['admin_otra']).get(CATALOGO))

    assert catalogo['CRM']['can_request'] is False  # la administra
    assert catalogo['CRM']['requestable_levels'] == []
    assert catalogo['Contabilidad']['can_request'] is True  # área ajena


def test_superadmin_ve_todo_sin_poder_solicitar(escena, cliente_como):
    catalogo = _por_nombre(cliente_como(escena['super']).get(CATALOGO))

    assert set(catalogo) == {'Contabilidad', 'CRM'}
    assert not any(e['can_request'] for e in catalogo.values())


def test_con_pendiente_muestra_la_solicitud(escena, cliente_como):
    cliente = cliente_como(escena['usuario'])
    solicitud_id = pedir(cliente, escena['plataforma']).get_json()['request']['id']

    entrada = _por_nombre(cliente.get(CATALOGO))['Contabilidad']

    assert entrada['pending_request_id'] == solicitud_id
    assert entrada['can_request'] is False


def test_con_usuario_vigente_solo_puede_subir(escena, cliente_como):
    dar_acceso(escena['usuario'], escena['plataforma'], 'usuario')

    entrada = _por_nombre(cliente_como(escena['usuario']).get(CATALOGO))[
        'Contabilidad']

    assert entrada['my_level'] == 'usuario'
    assert entrada['my_access_status'] == 'activo'
    assert entrada['requestable_levels'] == ['admin']


def test_con_admin_vigente_no_puede_solicitar(escena, cliente_como):
    dar_acceso(escena['usuario'], escena['plataforma'], 'admin')

    entrada = _por_nombre(cliente_como(escena['usuario']).get(CATALOGO))[
        'Contabilidad']

    assert entrada['can_request'] is False


def test_filtros_area_y_texto(escena, cliente_como):
    fabricas.crear_plataforma(escena['area'], 'Nómina 100%')
    cliente = cliente_como(escena['super'])

    por_area = _por_nombre(cliente.get(f"{CATALOGO}?area_id={escena['otra'].id}"))
    por_texto = _por_nombre(cliente.get(f'{CATALOGO}?q=conta'))
    comodin = _por_nombre(cliente.get(f'{CATALOGO}?q=%25'))

    assert set(por_area) == {'CRM'}
    assert set(por_texto) == {'Contabilidad'}
    assert set(comodin) == {'Nómina 100%'}  # `%` no es comodín


@pytest.mark.parametrize('consulta', ['area_id=x', 'area_id=0',
                                      f"q={'a' * 101}"])
def test_parametros_invalidos_del_catalogo(escena, cliente_como, consulta):
    respuesta = cliente_como(escena['usuario']).get(f'{CATALOGO}?{consulta}')

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'parametro_invalido'


# --------------------------------------------------------------------------- #
# Mis solicitudes
# --------------------------------------------------------------------------- #

def test_mine_lista_solo_las_propias_paginadas(escena, cliente_como):
    pedir(cliente_como(escena['admin_otra']), escena['plataforma'])
    cambiar_de_actor()
    cliente = cliente_como(escena['usuario'])
    pedir(cliente, escena['plataforma'])

    cuerpo = cliente.get(MIAS).get_json()

    assert cuerpo['total'] == 1 and cuerpo['page'] == 1
    assert cuerpo['per_page'] == 25
    assert cuerpo['items'][0]['requester']['id'] == escena['usuario'].id


def test_mine_ordena_de_la_mas_reciente_y_pagina(escena, cliente_como):
    usuario, plataforma = escena['usuario'], escena['plataforma']
    for _ in range(3):
        db.session.add(PlatformAccessRequest(
            user_id=usuario.id, platform_id=plataforma.id, level='usuario',
            status='rechazada'))
    db.session.commit()
    ids = sorted(s.id for s in PlatformAccessRequest.query.all())

    cuerpo = cliente_como(usuario).get(f'{MIAS}?per_page=2&page=1').get_json()
    segunda = cliente_como(usuario).get(f'{MIAS}?per_page=2&page=2').get_json()

    assert cuerpo['total'] == 3
    assert [i['id'] for i in cuerpo['items']] == [ids[2], ids[1]]
    assert [i['id'] for i in segunda['items']] == [ids[0]]


def test_mine_filtra_por_estado_y_plataforma(escena, cliente_como):
    usuario = escena['usuario']
    cliente = cliente_como(usuario)
    pedir(cliente, escena['plataforma'])
    db.session.add(PlatformAccessRequest(
        user_id=usuario.id, platform_id=escena['plataforma'].id,
        level='usuario', status='rechazada', rejection_reason='No aplica.'))
    db.session.commit()

    pendientes = cliente.get(f'{MIAS}?status=pendiente').get_json()
    de_otra = cliente.get(
        f"{MIAS}?platform_id={escena['de_otra'].id}").get_json()

    assert [i['status'] for i in pendientes['items']] == ['pendiente']
    assert de_otra['total'] == 0


def test_mine_muestra_el_acceso_de_una_aprobada(escena, cliente_como):
    usuario, plataforma = escena['usuario'], escena['plataforma']
    solicitud = PlatformAccessRequest(user_id=usuario.id,
                                      platform_id=plataforma.id,
                                      level='usuario', status='aprobada',
                                      decided_by=escena['admin'].id)
    db.session.add(solicitud)
    db.session.commit()
    acceso = dar_acceso(usuario, plataforma, 'usuario')
    acceso.request_id = solicitud.id
    db.session.commit()

    item = cliente_como(usuario).get(MIAS).get_json()['items'][0]

    assert item['access'] == {'id': acceso.id, 'status': 'activo'}
    assert item['decided_by']['id'] == escena['admin'].id


def test_mine_del_superadmin_esta_vacia(escena, cliente_como):
    cuerpo = cliente_como(escena['super']).get(MIAS).get_json()

    assert cuerpo == {'items': [], 'page': 1, 'per_page': 25, 'total': 0}


@pytest.mark.parametrize('consulta', ['status=otro', 'per_page=101',
                                      'page=0', 'platform_id=x'])
def test_parametros_invalidos_de_mine(escena, cliente_como, consulta):
    respuesta = cliente_como(escena['usuario']).get(f'{MIAS}?{consulta}')

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'parametro_invalido'
