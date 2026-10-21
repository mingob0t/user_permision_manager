"""`GET /access/inventory`: inventario de permisos por rol (FNC-059)."""
import pytest

from app import db
from app.authz import ROLE_AREA_ADMIN
from app.modules.access.inventario_api import ACCESS_INVENTORY_PAGE_SIZE_MAX
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_REVOCADO,
                                      ORIGEN_ADMIN_DE_AREA, ORIGEN_SOLICITUD)
from app.modules.platforms.tipos import NIVEL_ADMIN, NIVEL_USUARIO
from tests import fabricas

RUTA = '/api/v1/access/inventory'


def _dar(usuario, plataforma, nivel=NIVEL_USUARIO, origen=ORIGEN_SOLICITUD,
         estado=ESTADO_ACTIVO, aprobo=None):
    acceso = PlatformAccessGrant(
        user_id=usuario.id, platform_id=plataforma.id, level=nivel,
        origin=origen, status=estado,
        granted_by=aprobo.id if aprobo is not None else None)
    acceso.sincronizar_slots()
    db.session.add(acceso)
    db.session.commit()
    return acceso


@pytest.fixture
def inventario(escena):
    """Accesos en Finanzas (Contabilidad) y en Ventas (CRM)."""
    crm = fabricas.crear_plataforma(escena['otra'], 'CRM')
    return {
        'ana': _dar(escena['usuario'], escena['plataforma'],
                    aprobo=escena['admin']),
        'auto': _dar(escena['admin'], escena['plataforma'],
                     origen=ORIGEN_ADMIN_DE_AREA),
        'ajeno': _dar(escena['ajeno'], crm, nivel=NIVEL_ADMIN,
                      aprobo=escena['admin_otra']),
        'revocado': _dar(escena['admin2'], escena['plataforma'],
                         estado=ESTADO_REVOCADO),
        'crm': crm,
    }


def _ids(respuesta):
    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    return {a['id'] for a in respuesta.get_json()['items']}


# --------------------------------------------------------------------------- #
# Alcance por rol
# --------------------------------------------------------------------------- #

def test_usuario_no_tiene_inventario(escena, inventario, cliente_como):
    respuesta = cliente_como(escena['usuario']).get(RUTA)

    assert respuesta.status_code == 403


def test_superadmin_ve_todo_lo_vigente(escena, inventario, cliente_como):
    ids = _ids(cliente_como(escena['super']).get(RUTA))

    assert ids == {inventario['ana'].id, inventario['auto'].id,
                   inventario['ajeno'].id}


def test_admin_solo_ve_sus_areas(escena, inventario, cliente_como):
    ids = _ids(cliente_como(escena['admin']).get(RUTA))

    assert ids == {inventario['ana'].id, inventario['auto'].id}


@pytest.mark.parametrize('parametro', ['area_id', 'platform_id', 'user_id'])
def test_admin_no_ve_lo_ajeno_ni_filtrando(escena, inventario, cliente_como,
                                           parametro):
    valor = {'area_id': escena['otra'].id,
             'platform_id': inventario['crm'].id,
             'user_id': escena['ajeno'].id}[parametro]

    respuesta = cliente_como(escena['admin']).get(
        RUTA, query_string={parametro: valor})

    assert _ids(respuesta) == set()
    assert respuesta.get_json()['total'] == 0


def test_admin_sin_areas_no_ve_nada(escena, inventario, cliente_como):
    sin_areas = fabricas.crear_usuario(ROLE_AREA_ADMIN)

    assert _ids(cliente_como(sin_areas).get(RUTA)) == set()


# --------------------------------------------------------------------------- #
# Filtros
# --------------------------------------------------------------------------- #

def test_filtra_por_estado_nivel_y_origen(escena, inventario, cliente_como):
    cliente = cliente_como(escena['super'])

    assert _ids(cliente.get(RUTA, query_string={'status': 'revocado'})) == {
        inventario['revocado'].id}
    assert _ids(cliente.get(RUTA, query_string={'level': 'admin'})) == {
        inventario['ajeno'].id}
    assert _ids(cliente.get(RUTA, query_string={
        'origin': 'admin_de_area'})) == {inventario['auto'].id}
    assert _ids(cliente.get(RUTA, query_string={
        'area_id': escena['area'].id})) == {inventario['ana'].id,
                                            inventario['auto'].id}


def test_busca_por_nombre_o_correo(escena, inventario, cliente_como):
    cliente = cliente_como(escena['super'])

    assert _ids(cliente.get(RUTA, query_string={'q': 'ANA@'})) == {
        inventario['ana'].id}
    # Los comodines de LIKE se buscan literales.
    assert _ids(cliente.get(RUTA, query_string={'q': '%'})) == set()


@pytest.mark.parametrize('consulta', [
    {'status': 'otro'}, {'level': 'otro'}, {'origin': 'heredado'},
    {'area_id': 'x'}, {'q': 'a' * 101}, {'page': '0'},
    {'q': 'a\x00b'}, {'q': 'a\x1bb'},  # SEG-FNC059-01
    {'per_page': str(ACCESS_INVENTORY_PAGE_SIZE_MAX + 1)},
])
def test_parametro_invalido_responde_400(escena, cliente_como, consulta):
    respuesta = cliente_como(escena['super']).get(RUTA, query_string=consulta)

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'parametro_invalido'
    assert set(respuesta.get_json()['fields']) == set(consulta)


# --------------------------------------------------------------------------- #
# Forma, orden y paginación
# --------------------------------------------------------------------------- #

def test_forma_access_con_quien_aprobo(escena, inventario, cliente_como):
    cuerpo = cliente_como(escena['admin']).get(
        RUTA, query_string={'origin': 'solicitud'}).get_json()

    assert cuerpo['page'] == 1 and cuerpo['per_page'] == 25
    assert cuerpo['total'] == 1
    acceso = cuerpo['items'][0]
    admin = escena['admin']
    assert acceso['user']['email'] == 'ana@pruebas.local'
    assert acceso['platform']['name'] == 'Contabilidad'
    assert acceso['area'] == {'id': escena['area'].id, 'name': 'Finanzas'}
    assert acceso['level'] == 'usuario' and acceso['status'] == 'activo'
    assert acceso['granted_by'] == {'id': admin.id,
                                    'name': admin.nombre or admin.email}
    assert acceso['granted_at'].endswith('Z')
    assert {'request_id', 'revoked_by', 'revoked_at', 'revoke_reason',
            'last_job_id'} <= set(acceso)


def test_acceso_automatico_sin_aprobador(escena, inventario, cliente_como):
    cuerpo = cliente_como(escena['super']).get(
        RUTA, query_string={'origin': 'admin_de_area'}).get_json()

    assert cuerpo['items'][0]['granted_by'] is None


def test_orden_area_plataforma_usuario_y_pagina(escena, inventario,
                                                cliente_como):
    cliente = cliente_como(escena['super'])

    orden = [(a['area']['name'], a['platform']['name'])
             for a in cliente.get(RUTA).get_json()['items']]
    segunda = cliente.get(RUTA, query_string={'page': 2, 'per_page': 2})

    assert orden == sorted(orden)
    assert segunda.get_json()['total'] == 3
    assert len(segunda.get_json()['items']) == 1
