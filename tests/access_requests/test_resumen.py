"""Resumen de la bandeja: `GET /access-requests/inbox/stats` (FNC-200)."""
from app import db
from app.authz import ROLE_USER
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.tipos import (ESTADO_APROBADA,
                                               ESTADO_PENDIENTE,
                                               ESTADO_RECHAZADA)
from app.modules.provisioning.reloj import ahora
from tests import fabricas
from tests.access_requests.conftest import RUTA

STATS = f'{RUTA}/inbox/stats'


def solicitud(usuario, plataforma, estado=ESTADO_PENDIENTE):
    registro = PlatformAccessRequest(
        user_id=usuario.id, platform_id=plataforma.id, level='usuario',
        status=estado, created_at=ahora())
    registro.sincronizar_slot()
    db.session.add(registro)
    db.session.commit()
    return registro


def test_usuario_no_ve_el_resumen(escena, cliente_como):
    assert cliente_como(escena['usuario']).get(STATS).status_code == 403


def test_sin_datos_devuelve_las_tres_claves_en_cero(escena, cliente_como):
    cuerpo = cliente_como(escena['super']).get(STATS).get_json()

    assert cuerpo == {'total': 0,
                      'by_status': {'pendiente': 0, 'aprobada': 0,
                                    'rechazada': 0},
                      'by_area': [], 'by_platform': [],
                      'pending_by_area': [],
                      'pending_by_platform': []}


def test_admin_de_area_cuenta_solo_sus_areas_y_no_las_propias(
        escena, cliente_como):
    solicitud(escena['usuario'], escena['plataforma'])
    solicitud(escena['usuario'], escena['plataforma'], ESTADO_APROBADA)
    solicitud(escena['ajeno'], escena['de_otra'])
    # Otro administrador de área (admin_otra) no entra en su alcance.
    solicitud(escena['admin_otra'], escena['plataforma'])

    cuerpo = cliente_como(escena['admin']).get(STATS).get_json()

    assert cuerpo['total'] == 2
    assert cuerpo['by_status'] == {'pendiente': 1, 'aprobada': 1,
                                   'rechazada': 0}
    assert cuerpo['by_area'] == [
        {'area_id': escena['area'].id, 'area': 'Finanzas', 'count': 2}]


def test_superadmin_cuenta_todas_con_agregados_y_orden(escena, cliente_como):
    otro = fabricas.crear_usuario(ROLE_USER, areas=[escena['area']])
    nueva = fabricas.crear_plataforma(escena['area'], 'Activos')
    solicitud(escena['usuario'], escena['plataforma'])
    solicitud(otro, escena['plataforma'], ESTADO_RECHAZADA)
    solicitud(escena['usuario'], nueva)
    solicitud(escena['ajeno'], escena['de_otra'], ESTADO_APROBADA)
    # Cuenta como solicitante la propia del superadmin: no cuenta.
    solicitud(escena['super'], escena['de_otra'])

    cuerpo = cliente_como(escena['super']).get(STATS).get_json()

    assert cuerpo['total'] == 4
    assert cuerpo['by_status'] == {'pendiente': 2, 'aprobada': 1,
                                   'rechazada': 1}
    assert cuerpo['by_area'] == [
        {'area_id': escena['area'].id, 'area': 'Finanzas', 'count': 3},
        {'area_id': escena['otra'].id, 'area': 'Ventas', 'count': 1}]
    # count desc; a igual número, nombre asc (Activos antes que CRM).
    assert cuerpo['by_platform'] == [
        {'platform_id': escena['plataforma'].id, 'platform': 'Contabilidad',
         'area': 'Finanzas', 'count': 2},
        {'platform_id': nueva.id, 'platform': 'Activos', 'area': 'Finanzas',
         'count': 1},
        {'platform_id': escena['de_otra'].id, 'platform': 'CRM',
         'area': 'Ventas', 'count': 1}]


def test_pendientes_por_area_cuenta_solo_las_pendientes(escena, cliente_como):
    """FNC-212: la tarjeta de área muestra cuántas hay por aprobar."""
    otro = fabricas.crear_usuario(ROLE_USER, areas=[escena['area']])
    solicitud(escena['usuario'], escena['plataforma'])
    solicitud(otro, escena['plataforma'])
    solicitud(escena['usuario'], escena['plataforma'], ESTADO_APROBADA)
    solicitud(escena['ajeno'], escena['de_otra'], ESTADO_RECHAZADA)

    cuerpo = cliente_como(escena['super']).get(STATS).get_json()

    # Ventas no tiene pendientes: no aparece.
    assert cuerpo['pending_by_area'] == [
        {'area_id': escena['area'].id, 'area': 'Finanzas', 'count': 2}]


def test_pendientes_por_area_respeta_el_alcance_del_admin(
        escena, cliente_como):
    solicitud(escena['usuario'], escena['plataforma'])
    solicitud(escena['ajeno'], escena['de_otra'])

    cuerpo = cliente_como(escena['admin']).get(STATS).get_json()

    assert cuerpo['pending_by_area'] == [
        {'area_id': escena['area'].id, 'area': 'Finanzas', 'count': 1}]


def test_pendientes_por_plataforma_cuenta_solo_pendientes_y_ordena(
        escena, cliente_como):
    """FNC-219: pendientes por plataforma; sin filas en cero."""
    otro = fabricas.crear_usuario(ROLE_USER, areas=[escena['area']])
    nueva = fabricas.crear_plataforma(escena['area'], 'Activos')
    solicitud(escena['usuario'], escena['plataforma'])
    solicitud(otro, escena['plataforma'])
    solicitud(escena['usuario'], nueva)
    solicitud(otro, nueva, ESTADO_APROBADA)
    solicitud(escena['ajeno'], escena['de_otra'], ESTADO_RECHAZADA)

    cuerpo = cliente_como(escena['super']).get(STATS).get_json()

    area = {'area_id': escena['area'].id, 'area': 'Finanzas'}
    assert cuerpo['pending_by_platform'] == [
        {'platform_id': escena['plataforma'].id, 'platform': 'Contabilidad',
         **area, 'count': 2},
        {'platform_id': nueva.id, 'platform': 'Activos', **area, 'count': 1}]


def test_pendientes_por_plataforma_respeta_el_alcance_del_admin(
        escena, cliente_como):
    solicitud(escena['usuario'], escena['plataforma'])
    solicitud(escena['ajeno'], escena['de_otra'])

    cuerpo = cliente_como(escena['admin']).get(STATS).get_json()

    assert [f['platform_id'] for f in cuerpo['pending_by_platform']] == [
        escena['plataforma'].id]


def test_pendientes_por_plataforma_del_superadmin_ve_todas(
        escena, cliente_como):
    solicitud(escena['usuario'], escena['plataforma'])
    solicitud(escena['ajeno'], escena['de_otra'])

    cuerpo = cliente_como(escena['super']).get(STATS).get_json()

    assert {f['platform_id'] for f in cuerpo['pending_by_platform']} == {
        escena['plataforma'].id, escena['de_otra'].id}
