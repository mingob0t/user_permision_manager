"""Resumen del inicio por rol (FNC-066, contrato `docs/contratos/inicio.md`).

Cada rol recibe solo sus contadores: el usuario los propios, el admin de
área los de sus áreas (sin los de otro admin) y el superadmin los globales.
"""
from datetime import datetime

import pytest
from flask import g

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.access_requests.models import PlatformAccessRequest
from tests import fabricas

RUTA = '/api/v1/home/summary'
CLAVES_PROPIAS = {'my_access', 'my_requests'}
CLAVES_ADMIN = {'pending_approvals', 'failed_access', 'oldest_pending_at',
                'totals'}


def _solicitud(usuario, plataforma, estado='pendiente', creada=None):
    registro = PlatformAccessRequest(
        user_id=usuario.id, platform_id=plataforma.id, level='usuario',
        status=estado, created_at=creada or datetime(2026, 10, 15, 9, 0, 0))
    registro.sincronizar_slot()
    db.session.add(registro)
    db.session.commit()
    return registro


@pytest.fixture
def escena(app):
    finanzas = fabricas.crear_area('Finanzas')
    ventas = fabricas.crear_area('Ventas')
    conta = fabricas.crear_plataforma(finanzas, 'Contabilidad')
    nomina = fabricas.crear_plataforma(finanzas, 'Nómina')
    crm = fabricas.crear_plataforma(ventas, 'CRM')
    admin = fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[finanzas],
                                   areas_administradas=[finanzas])
    # Admin de Ventas que pertenece a Finanzas: el admin de Finanzas no lo
    # administra (SEC-AUTHZ-06), así que sus solicitudes no le cuentan.
    admin_ventas = fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[finanzas],
                                          areas_administradas=[ventas])
    ana = fabricas.crear_usuario(ROLE_USER, areas=[finanzas])
    beto = fabricas.crear_usuario(ROLE_USER, areas=[finanzas])
    ajeno = fabricas.crear_usuario(ROLE_USER, areas=[ventas])
    ceci = fabricas.crear_usuario(ROLE_USER, areas=[ventas])
    superadmin = fabricas.crear_usuario(ROLE_ADMIN)

    # Accesos de Ana: uno por estado (el revocado no cuenta).
    fabricas.crear_acceso(ana, conta, 'activo')
    fabricas.crear_acceso(ana, nomina, 'en_proceso')
    fabricas.crear_acceso(ana, crm, 'fallido')
    # Otros accesos.
    fabricas.crear_acceso(beto, conta, 'activo')
    fabricas.crear_acceso(beto, nomina, 'fallo_revocacion')
    fabricas.crear_acceso(beto, crm, 'revocado')
    fabricas.crear_acceso(ajeno, crm, 'activo')
    fabricas.crear_acceso(ceci, crm, 'fallido')
    fabricas.crear_acceso(admin, conta, 'activo', origen='admin_de_area')

    # Solicitudes de Ana: una por estado.
    _solicitud(ana, conta, 'aprobada')
    _solicitud(ana, nomina, 'pendiente', datetime(2026, 10, 14, 8, 0, 0))
    _solicitud(ana, crm, 'rechazada')
    # Pendientes ajenas.
    _solicitud(beto, nomina, 'pendiente', datetime(2026, 10, 16, 8, 0, 0))
    _solicitud(admin_ventas, nomina, 'pendiente',
               datetime(2026, 10, 10, 8, 0, 0))
    _solicitud(ajeno, crm, 'pendiente', datetime(2026, 10, 1, 8, 0, 0))
    _solicitud(beto, conta, 'aprobada')
    # Del propio admin: no está en su bandeja (solicitud propia).
    _solicitud(admin, crm, 'pendiente', datetime(2026, 10, 2, 8, 0, 0))
    return {'ana': ana, 'admin': admin, 'admin_ventas': admin_ventas,
            'superadmin': superadmin}


def _resumen(cliente_como, usuario):
    # Las peticiones comparten el contexto de la app de la prueba: se olvida
    # el usuario que Flask-Login dejó en `g` antes de usar otro cliente.
    g.pop('_login_user', None)
    respuesta = cliente_como(usuario).get(RUTA)
    assert respuesta.status_code == 200
    return respuesta.get_json()


def test_usuario_recibe_solo_lo_propio(escena, cliente_como):
    datos = _resumen(cliente_como, escena['ana'])
    assert datos == {
        'scope': 'propio',
        'my_access': {'activo': 1, 'en_proceso': 1, 'fallido': 1},
        'my_requests': {'pendiente': 1, 'aprobada': 1, 'rechazada': 1},
    }


def test_admin_recibe_sus_areas_y_lo_propio(escena, cliente_como):
    datos = _resumen(cliente_como, escena['admin'])
    assert datos == {
        'scope': 'areas',
        'my_access': {'activo': 1, 'en_proceso': 0, 'fallido': 0},
        'my_requests': {'pendiente': 1, 'aprobada': 0, 'rechazada': 0},
        # Ana y Beto en Finanzas; no la de admin_ventas, la de Ventas ni la
        # propia.
        'pending_approvals': 2,
        # Fallido de Ana en CRM es de Ventas; solo el fallo_revocacion de Beto.
        'failed_access': 1,
        'oldest_pending_at': '2026-10-14T08:00:00Z',
        'totals': {'areas': 1, 'platforms': 2, 'active_access': 3},
    }


def test_admin_no_ve_lo_de_otro_admin(escena, cliente_como):
    datos = _resumen(cliente_como, escena['admin_ventas'])
    # Ventas: solo la pendiente de `ajeno` (la del admin de Finanzas es de
    # otro admin) y los fallidos de CRM.
    assert datos['pending_approvals'] == 1
    assert datos['oldest_pending_at'] == '2026-10-01T08:00:00Z'
    assert datos['failed_access'] == 2
    assert datos['totals'] == {'areas': 1, 'platforms': 1, 'active_access': 1}


def test_superadmin_recibe_lo_global_sin_lo_propio(escena, cliente_como):
    datos = _resumen(cliente_como, escena['superadmin'])
    assert datos == {
        'scope': 'global',
        'pending_approvals': 5,
        'failed_access': 3,
        'oldest_pending_at': '2026-10-01T08:00:00Z',
        'totals': {'areas': 2, 'platforms': 3, 'active_access': 4},
    }


def test_sin_pendientes_la_mas_antigua_es_null(app, cliente_como):
    admin = fabricas.crear_usuario_de_rol(ROLE_AREA_ADMIN)
    datos = _resumen(cliente_como, admin)
    assert datos['pending_approvals'] == 0
    assert datos['oldest_pending_at'] is None
    assert datos['my_access'] == {'activo': 0, 'en_proceso': 0, 'fallido': 0}


@pytest.mark.parametrize('actor', ['admin', 'admin_ventas', 'superadmin'])
def test_pendientes_coinciden_con_la_bandeja(escena, cliente_como, actor):
    cliente = cliente_como(escena[actor])
    bandeja = cliente.get('/api/v1/access-requests/inbox').get_json()
    assert cliente.get(RUTA).get_json()['pending_approvals'] == \
        bandeja['total']


def test_las_claves_dependen_del_rol(escena, cliente_como):
    usuario = _resumen(cliente_como, escena['ana'])
    admin = _resumen(cliente_como, escena['admin'])
    superadmin = _resumen(cliente_como, escena['superadmin'])
    assert not CLAVES_ADMIN & set(usuario)
    assert CLAVES_ADMIN | CLAVES_PROPIAS <= set(admin)
    assert not CLAVES_PROPIAS & set(superadmin)


def test_sin_sesion_responde_401(client):
    assert client.get(RUTA).status_code == 401
