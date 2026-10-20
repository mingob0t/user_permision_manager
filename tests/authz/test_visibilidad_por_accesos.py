"""Mis plataformas según los accesos otorgados (FNC-063, P4).

- Usuario: solo plataformas con un acceso `activo` y de un área a la que
  pertenece (P1).
- Admin de área: las plataformas de las áreas que administra (acceso
  automático, FNC-055) y las de sus accesos `activo`.
- Superadmin: todas (acceso por defecto, P6).
"""
import pytest

from app import db
from app.authz import (ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER,
                       can_access_platform, scoped_platforms)
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO,
                                      ESTADO_FALLIDO, ESTADO_FALLO_REVOCACION,
                                      ESTADO_REVOCADO, ESTADO_REVOCANDO)
from app.modules.auth.models import User
from app.modules.core.models import Platform
from tests import fabricas

A = '/api/v1'
ESTADOS_SIN_VISIBILIDAD = (ESTADO_EN_PROCESO, ESTADO_FALLIDO, ESTADO_REVOCANDO,
                           ESTADO_REVOCADO, ESTADO_FALLO_REVOCACION)


@pytest.fixture
def escena(app):
    area = fabricas.crear_area('Finanzas')
    otra = fabricas.crear_area('Ventas')
    return {
        'area': area,
        'otra': otra,
        'plataforma': fabricas.crear_plataforma(area, 'Contabilidad'),
        'hermana': fabricas.crear_plataforma(area, 'Nómina'),
        'ajena': fabricas.crear_plataforma(otra, 'CRM'),
        'usuario': fabricas.crear_usuario(ROLE_USER, areas=[area]),
    }


def _recargar(usuario):
    db.session.expire_all()
    return db.session.get(User, usuario.id)


def _ids(respuesta):
    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    return {p['id'] for p in respuesta.get_json()}


def _visibles(usuario):
    return {p.id for p in scoped_platforms(_recargar(usuario))}


# --------------------------------------------------------------------------- #
# Usuario
# --------------------------------------------------------------------------- #

def test_usuario_sin_acceso_no_ve_la_plataforma_de_su_area(escena,
                                                           cliente_como):
    usuario = escena['usuario']
    cliente = cliente_como(usuario)
    assert _ids(cliente.get(f'{A}/platforms')) == set()
    assert _visibles(usuario) == set()
    assert not can_access_platform(escena['plataforma'], _recargar(usuario))


def test_usuario_sin_acceso_no_marca_favorito_ni_visita(escena, cliente_como):
    usuario = escena['usuario']
    cliente = cliente_como(usuario)
    pid = escena['plataforma'].id
    assert cliente.post(f'{A}/platforms/{pid}/favorite').status_code == 404
    assert cliente.post(f'{A}/platforms/{pid}/visit').status_code == 404
    assert _recargar(usuario).favorites == []
    assert (db.session.get(Platform, pid).visits or 0) == 0


def test_usuario_con_acceso_activo_ve_solo_esa_plataforma(escena,
                                                          cliente_como):
    usuario = escena['usuario']
    fabricas.crear_acceso(usuario, escena['plataforma'], ESTADO_ACTIVO)
    cliente = cliente_como(_recargar(usuario))
    pid = escena['plataforma'].id
    assert _ids(cliente.get(f'{A}/platforms')) == {pid}
    assert cliente.post(f'{A}/platforms/{pid}/favorite').status_code == 200
    assert cliente.post(f'{A}/platforms/{pid}/visit').status_code == 200
    assert _ids(cliente.get(f'{A}/favorites')) == {pid}
    assert can_access_platform(escena['plataforma'], _recargar(usuario))
    assert not can_access_platform(escena['hermana'], _recargar(usuario))


@pytest.mark.parametrize('estado', ESTADOS_SIN_VISIBILIDAD)
def test_acceso_no_activo_no_da_visibilidad(escena, cliente_como, estado):
    usuario = escena['usuario']
    fabricas.crear_acceso(usuario, escena['plataforma'], estado)
    cliente = cliente_como(_recargar(usuario))
    pid = escena['plataforma'].id
    assert _ids(cliente.get(f'{A}/platforms')) == set()
    assert cliente.post(f'{A}/platforms/{pid}/favorite').status_code == 404
    assert not can_access_platform(escena['plataforma'], _recargar(usuario))


def test_favorito_sin_acceso_activo_no_se_lista(escena, cliente_como):
    """Un favorito de cuando la plataforma era visible deja de listarse."""
    usuario = escena['usuario']
    acceso = fabricas.crear_acceso(usuario, escena['plataforma'],
                                   ESTADO_ACTIVO)
    usuario = _recargar(usuario)
    usuario.favorites = [db.session.get(Platform, escena['plataforma'].id)]
    db.session.commit()
    acceso.status = ESTADO_REVOCADO
    acceso.sincronizar_slots()
    db.session.commit()
    respuesta = cliente_como(_recargar(usuario)).get(f'{A}/favorites')
    assert _ids(respuesta) == set()


def test_acceso_activo_fuera_de_sus_areas_no_da_visibilidad(escena,
                                                            cliente_como):
    """Decisión del orquestador: si la cuenta ya no pertenece al área de la
    plataforma, el acceso activo no la muestra (P1)."""
    usuario = escena['usuario']
    fabricas.crear_acceso(usuario, escena['ajena'], ESTADO_ACTIVO)
    cliente = cliente_como(_recargar(usuario))
    assert _ids(cliente.get(f'{A}/platforms')) == set()
    assert not can_access_platform(escena['ajena'], _recargar(usuario))


def test_accesos_de_otra_cuenta_no_cuentan(escena, cliente_como):
    otra = fabricas.crear_usuario(ROLE_USER, areas=[escena['area']])
    fabricas.crear_acceso(otra, escena['plataforma'], ESTADO_ACTIVO)
    cliente = cliente_como(_recargar(escena['usuario']))
    assert _ids(cliente.get(f'{A}/platforms')) == set()


def test_estadisticas_solo_cuentan_plataformas_con_acceso(escena,
                                                          cliente_como):
    usuario = escena['usuario']
    fabricas.crear_acceso(usuario, escena['plataforma'], ESTADO_ACTIVO)
    datos = cliente_como(_recargar(usuario)).get(f'{A}/stats').get_json()
    assert datos['platforms'] == 1
    assert {p['id'] for p in datos['most_visited']} == \
        {escena['plataforma'].id}


# --------------------------------------------------------------------------- #
# Admin de área y superadmin
# --------------------------------------------------------------------------- #

def test_admin_ve_las_plataformas_de_las_areas_que_administra(escena,
                                                              cliente_como):
    admin = fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[escena['area']],
                                   areas_administradas=[escena['area']])
    esperado = {escena['plataforma'].id, escena['hermana'].id}
    assert _ids(cliente_como(admin).get(f'{A}/platforms')) == esperado
    assert _visibles(admin) == esperado


def test_admin_ve_con_acceso_activo_una_plataforma_de_area_que_no_administra(
        escena, cliente_como):
    admin = fabricas.crear_usuario(
        ROLE_AREA_ADMIN, areas=[escena['area'], escena['otra']],
        areas_administradas=[escena['area']])
    assert escena['ajena'].id not in _visibles(admin)
    fabricas.crear_acceso(admin, escena['ajena'], ESTADO_ACTIVO)
    esperado = {escena['plataforma'].id, escena['hermana'].id,
                escena['ajena'].id}
    assert _ids(cliente_como(_recargar(admin)).get(f'{A}/platforms')) == \
        esperado
    assert can_access_platform(escena['ajena'], _recargar(admin))


def test_superadmin_ve_todas_sin_accesos(escena, cliente_como):
    superadmin = fabricas.crear_usuario(ROLE_ADMIN)
    esperado = {escena[k].id for k in ('plataforma', 'hermana', 'ajena')}
    assert _ids(cliente_como(superadmin).get(f'{A}/platforms')) == esperado


def test_cuenta_inactiva_no_ve_nada(escena):
    usuario = escena['usuario']
    fabricas.crear_acceso(usuario, escena['plataforma'], ESTADO_ACTIVO)
    usuario = _recargar(usuario)
    usuario.is_active = False
    db.session.commit()
    assert _visibles(usuario) == set()


def test_acceso_activo_del_admin_no_le_da_alcance_para_asignar(escena,
                                                               cliente_como):
    """Ver una plataforma por un acceso propio no es administrarla: no la
    asigna por `PUT /users/<id>/platforms` (heredado, FNC-065)."""
    admin = fabricas.crear_usuario(
        ROLE_AREA_ADMIN, areas=[escena['area'], escena['otra']],
        areas_administradas=[escena['area']])
    fabricas.crear_acceso(admin, escena['ajena'], ESTADO_ACTIVO)
    usuario = escena['usuario']
    respuesta = cliente_como(_recargar(admin)).put(
        f'{A}/users/{usuario.id}/platforms',
        json={'platform_ids': [escena['ajena'].id]})
    assert respuesta.status_code == 403, respuesta.get_data(as_text=True)
    assert _recargar(usuario).platforms == []
