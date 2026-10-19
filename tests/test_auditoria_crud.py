"""Auditoría de las acciones CRUD y casos límite del CRUD (FNC-023).

Cada acción de escritura principal deja un registro con quién la hizo (actor),
qué hizo (acción) y sobre qué (objetivo). El alcance de `GET /audit` por rol
ya se prueba en `test_alcance_por_area.py` (FNC-021); aquí solo su límite.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.core.models import Area
from tests import fabricas

A = '/api/v1'
LIMITE_AUDITORIA = 500


@pytest.fixture
def datos(app):
    """Un área con plataforma y un usuario; el superadmin es el actor."""
    area = fabricas.crear_area('Área auditada')
    plataforma = fabricas.crear_plataforma(area, 'Plataforma auditada')
    objetivo = fabricas.crear_usuario(ROLE_USER, email='objetivo@pruebas.local',
                                      areas=[area])
    actor = fabricas.crear_usuario(ROLE_ADMIN, email='actor@pruebas.local')
    return {'area': area.id, 'plataforma': plataforma.id,
            'objetivo': objetivo.id, 'actor': actor}


# (método, ruta, cuerpo, acción esperada, módulo, objetivo esperado)
ACCIONES = [
    ('POST', '/areas', {'name': 'Área nueva'},
     'area_creada', 'Áreas', 'Área nueva'),
    ('PUT', '/areas/{area}', {'description': 'Editada'},
     'area_editada', 'Áreas', 'Área auditada'),
    ('PUT', '/areas/{area}/users', {'user_ids': []},
     'ACTUALIZAR USUARIOS DE ÁREA: Área auditada', 'Áreas', 'Área auditada'),
    ('POST', '/platforms', {'name': 'Plataforma nueva', 'area_id': '{area}'},
     'CREAR PLATAFORMA: Plataforma nueva', 'Plataformas', 'Plataforma nueva'),
    ('PUT', '/platforms/{plataforma}', {'description': 'Editada'},
     'EDITAR PLATAFORMA: Plataforma auditada', 'Plataformas',
     'Plataforma auditada'),
    ('DELETE', '/platforms/{plataforma}', None,
     'ELIMINAR PLATAFORMA: Plataforma auditada', 'Plataformas',
     'Plataforma auditada'),
    ('PUT', '/platforms/{plataforma}/users', {'user_ids': []},
     'ACTUALIZAR ACCESO: Plataforma auditada', 'Plataformas',
     'Plataforma auditada'),
    ('POST', '/users', {'email': 'nuevo@pruebas.local'},
     'CREAR USUARIO: nuevo@pruebas.local', 'Usuarios', 'nuevo@pruebas.local'),
    ('PUT', '/users/{objetivo}', {'name': 'Editado'},
     'EDITAR USUARIO: objetivo@pruebas.local', 'Usuarios',
     'objetivo@pruebas.local'),
    ('DELETE', '/users/{objetivo}', None,
     'ELIMINAR USUARIO: objetivo@pruebas.local', 'Usuarios',
     'objetivo@pruebas.local'),
    ('PUT', '/users/{objetivo}/platforms', {'platform_ids': []},
     'ACTUALIZAR ACCESOS: objetivo@pruebas.local', 'Usuarios',
     'objetivo@pruebas.local'),
]


def _sustituir(valor, ids):
    if isinstance(valor, str) and valor.startswith('{'):
        return ids[valor.strip('{}')]
    return valor


@pytest.mark.parametrize('metodo,ruta,cuerpo,accion,modulo,objetivo', ACCIONES,
                         ids=[a[3].split(':')[0] for a in ACCIONES])
def test_accion_crud_registra_actor_accion_y_objetivo(
        datos, cliente_como, metodo, ruta, cuerpo, accion, modulo, objetivo):
    ids = {k: v for k, v in datos.items() if k != 'actor'}
    peticion = {}
    if cuerpo is not None:
        peticion['json'] = {k: _sustituir(v, ids) for k, v in cuerpo.items()}

    respuesta = cliente_como(datos['actor']).open(
        A + ruta.format(**ids), method=metodo, **peticion)

    assert respuesta.status_code in (200, 201), respuesta.get_json()
    registro = AuditLog.query.filter_by(action=accion).one()
    assert registro.user == 'actor@pruebas.local'
    assert registro.module == modulo
    assert registro.target == objetivo
    assert registro.status in ('success', 'warning')


def test_borrar_area_registra_evento(app, cliente_admin):
    area = fabricas.crear_area('Área a borrar')

    respuesta = cliente_admin.delete(f'{A}/areas/{area.id}')

    assert respuesta.status_code == 200
    registro = AuditLog.query.filter_by(action='area_eliminada').one()
    assert (registro.module, registro.target, registro.status) == \
        ('Áreas', 'Área a borrar', 'warning')


def test_el_actor_es_el_admin_de_area_que_actua(app, cliente_como):
    area = fabricas.crear_area('Área del admin')
    admin_area = fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                        email='admin-area@pruebas.local',
                                        areas_administradas=[area])

    cliente_como(admin_area).put(f'{A}/areas/{area.id}',
                                 json={'description': 'Editada'})

    registro = AuditLog.query.filter_by(
        action='area_editada').one()
    assert registro.user == 'admin-area@pruebas.local'


def test_accion_rechazada_no_registra_evento(app, cliente_usuario):
    respuesta = cliente_usuario.post(f'{A}/areas', json={'name': 'No permitida'})

    assert respuesta.status_code == 403
    assert AuditLog.query.count() == 0


# --------------------------------------------------------------------------- #
# GET /audit: límite de registros
# --------------------------------------------------------------------------- #

def _llenar_auditoria(n):
    db.session.add_all(AuditLog(user='otro@pruebas.local', action=f'ACCIÓN {i}')
                       for i in range(n))
    db.session.commit()


@pytest.mark.parametrize('limite,esperados', [
    (None, 100), ('3', 3), (str(LIMITE_AUDITORIA + 100), LIMITE_AUDITORIA),
    ('no-numero', 100),
])
def test_limite_de_auditoria(app, cliente_admin, limite, esperados):
    _llenar_auditoria(LIMITE_AUDITORIA + 10)
    ruta = f'{A}/audit' + (f'?limit={limite}' if limite else '')

    respuesta = cliente_admin.get(ruta)

    assert respuesta.status_code == 200
    assert len(respuesta.get_json()) == esperados


# --------------------------------------------------------------------------- #
# Casos límite del CRUD
# --------------------------------------------------------------------------- #

def test_area_con_nombre_repetido_da_409(app, cliente_admin):
    fabricas.crear_area('Repetida')

    respuesta = cliente_admin.post(f'{A}/areas', json={'name': 'Repetida'})

    assert respuesta.status_code == 409
    assert Area.query.filter_by(name='Repetida').count() == 1


def test_renombrar_area_a_un_nombre_existente_da_409(app, cliente_admin):
    fabricas.crear_area('Primera')
    segunda = fabricas.crear_area('Segunda')

    respuesta = cliente_admin.put(f'{A}/areas/{segunda.id}',
                                  json={'name': 'Primera'})

    assert respuesta.status_code == 409


def test_correo_repetido_da_409_sin_distinguir_mayusculas(app, cliente_admin):
    fabricas.crear_usuario(ROLE_USER, email='repetido@pruebas.local')

    respuesta = cliente_admin.post(f'{A}/users',
                                   json={'email': 'REPETIDO@pruebas.local'})

    assert respuesta.status_code == 409
    assert User.query.filter(
        db.func.lower(User.email) == 'repetido@pruebas.local').count() == 1


def test_borrar_area_con_plataformas_da_409(app, cliente_admin):
    area = fabricas.crear_area()
    fabricas.crear_plataforma(area)

    respuesta = cliente_admin.delete(f'{A}/areas/{area.id}')

    assert respuesta.status_code == 409
    assert db.session.get(Area, area.id) is not None


def test_no_se_borra_la_propia_cuenta(app, cliente_de_rol):
    cliente, admin = cliente_de_rol(ROLE_ADMIN)

    respuesta = cliente.delete(f'{A}/users/{admin.id}')

    assert respuesta.status_code == 409
    assert db.session.get(User, admin.id) is not None


@pytest.mark.parametrize('ruta', ['/areas/99999', '/platforms/99999',
                                  '/users/99999'])
def test_editar_inexistente_da_404(app, cliente_admin, ruta):
    respuesta = cliente_admin.put(A + ruta, json={'description': 'x'})

    assert respuesta.status_code == 404
    assert respuesta.get_json()['status'] == 'error'


def test_purga_con_menos_del_minimo_de_dias_da_400(app, cliente_admin):
    respuesta = cliente_admin.post(f'{A}/users/purge', json={'days': 3})

    assert respuesta.status_code == 400


def test_purga_nunca_borra_superadmins(app, cliente_admin):
    from datetime import datetime, timedelta
    antiguo = datetime.now() - timedelta(days=400)
    viejo_admin = fabricas.crear_usuario(ROLE_ADMIN)
    viejo_usuario = fabricas.crear_usuario(ROLE_USER)
    for usuario in (viejo_admin, viejo_usuario):
        usuario.created_at = antiguo
    db.session.commit()
    ids = (viejo_admin.id, viejo_usuario.id)

    respuesta = cliente_admin.post(f'{A}/users/purge', json={'days': 30})

    assert respuesta.status_code == 200
    db.session.expire_all()
    assert db.session.get(User, ids[0]) is not None
    assert db.session.get(User, ids[1]) is None


@pytest.mark.parametrize('pedido,guardado', [(1, 15), (99999, 3600), (60, 60)])
def test_intervalo_de_refresco_se_acota(app, cliente_usuario, pedido,
                                        guardado):
    respuesta = cliente_usuario.put(f'{A}/me/preferences',
                                    json={'refresh_interval': pedido})

    assert respuesta.status_code == 200
    assert respuesta.get_json()['preferences']['refresh_interval'] == guardado
