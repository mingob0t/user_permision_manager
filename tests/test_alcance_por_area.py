"""Alcance por área y escalada de privilegios (FNC-021).

Escenario con dos áreas (A y B), una plataforma en cada una y cinco actores:
superadmin, admin de A, admin de B, usuario de A y usuario de B.

FNC-063 (P4): un usuario ve una plataforma por un acceso `activo`, no por
pertenecer al área; por eso cada usuario tiene un acceso activo a la
plataforma de su área. Los casos sin acceso están en
`tests/authz/test_visibilidad_por_accesos.py`.

Cada actor solo debe ver y modificar lo de su alcance. Lo que hoy la app hace
mal se prueba con el resultado correcto y `xfail(strict=True)` con el hallazgo
y la tarea que lo corrige.
"""

from dataclasses import dataclass

import pytest
from flask import g

from app import db
from app.authz import (ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER,
                       can_access_platform, can_manage_area,
                       can_manage_platform, can_manage_user, managed_area_ids,
                       scoped_areas, scoped_platforms, scoped_users)
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from tests import fabricas
from tests.matriz_proteccion import CONTRASENA_FICTICIA

A = '/api/v1'
CONTRASENA_NUEVA = 'otra-clave-ficticia-de-prueba'
VISITAS_A = 3
VISITAS_B = 7

SUPERADMIN = 'superadmin'
ADMIN_A = 'admin_a'
ADMIN_B = 'admin_b'
USUARIO_A = 'usuario_a'
USUARIO_B = 'usuario_b'
ACTORES = (SUPERADMIN, ADMIN_A, ADMIN_B, USUARIO_A, USUARIO_B)
ADMINS_DE_AREA = (ADMIN_A, ADMIN_B)
USUARIOS = (USUARIO_A, USUARIO_B)

# Actor -> área propia ('A' o 'B'); el superadmin no tiene.
AREA_DE = {ADMIN_A: 'A', ADMIN_B: 'B', USUARIO_A: 'A', USUARIO_B: 'B'}
OTRA = {'A': 'B', 'B': 'A'}


@dataclass
class Alcance:
    """IDs del escenario de dos áreas."""
    area: dict
    plataforma: dict
    actor: dict


@pytest.fixture
def alcance(app):
    area_a = fabricas.crear_area('Área A')
    area_b = fabricas.crear_area('Área B')
    plataforma_a = fabricas.crear_plataforma(area_a, 'Plataforma A',
                                             visits=VISITAS_A)
    plataforma_b = fabricas.crear_plataforma(area_b, 'Plataforma B',
                                             visits=VISITAS_B)
    actores = {
        SUPERADMIN: fabricas.crear_usuario(ROLE_ADMIN),
        # Como en `POST /users`, el admin_area también es miembro de su área.
        ADMIN_A: fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_a],
                                        areas_administradas=[area_a]),
        ADMIN_B: fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_b],
                                        areas_administradas=[area_b]),
        USUARIO_A: fabricas.crear_usuario(ROLE_USER, areas=[area_a]),
        USUARIO_B: fabricas.crear_usuario(ROLE_USER, areas=[area_b]),
    }
    fabricas.crear_acceso(actores[USUARIO_A], plataforma_a)
    fabricas.crear_acceso(actores[USUARIO_B], plataforma_b)
    return Alcance(
        area={'A': area_a.id, 'B': area_b.id},
        plataforma={'A': plataforma_a.id, 'B': plataforma_b.id},
        actor={nombre: u.id for nombre, u in actores.items()},
    )


def _usuario(user_id):
    db.session.expire_all()
    return db.session.get(User, user_id)


def _como(cliente_como, esc, actor):
    return cliente_como(_usuario(esc.actor[actor]))


def _ids(respuesta):
    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    return {item['id'] for item in respuesta.get_json()}


def _assert_denegado(respuesta, codigos=(403, 404)):
    assert respuesta.status_code in codigos, respuesta.get_data(as_text=True)
    datos = respuesta.get_json()
    assert datos is not None and datos.get('status') == 'error'


# --------------------------------------------------------------------------- #
# Funciones de app/authz.py
# --------------------------------------------------------------------------- #

def test_authz_scoped_por_actor(alcance):
    esc = alcance
    esperado = {
        SUPERADMIN: ({'A', 'B'}, {'A', 'B'}),
        ADMIN_A: ({'A'}, {'A'}),
        ADMIN_B: ({'B'}, {'B'}),
        USUARIO_A: ({'A'}, {'A'}),
        USUARIO_B: ({'B'}, {'B'}),
    }
    for actor, (areas, plataformas) in esperado.items():
        usuario = _usuario(esc.actor[actor])
        assert {a.id for a in scoped_areas(usuario)} == \
            {esc.area[x] for x in areas}, actor
        assert {p.id for p in scoped_platforms(usuario)} == \
            {esc.plataforma[x] for x in plataformas}, actor


def test_authz_scoped_users(alcance):
    esc = alcance
    todos = set(esc.actor.values())
    esperado = {
        SUPERADMIN: todos,
        # FNC-044: solo cuentas `usuario` de sus áreas (ni él mismo).
        ADMIN_A: {esc.actor[USUARIO_A]},
        ADMIN_B: {esc.actor[USUARIO_B]},
        USUARIO_A: {esc.actor[USUARIO_A]},
        USUARIO_B: {esc.actor[USUARIO_B]},
    }
    for actor, ids in esperado.items():
        usuario = _usuario(esc.actor[actor])
        assert {u.id for u in scoped_users(usuario)} == ids, actor


def test_authz_can_manage_y_acceso(alcance):
    esc = alcance
    plataforma = {x: db.session.get(Platform, esc.plataforma[x]) for x in 'AB'}
    for actor in ACTORES:
        usuario = _usuario(esc.actor[actor])
        for x in 'AB':
            propia = actor == SUPERADMIN or AREA_DE[actor] == x
            administra = propia and actor not in USUARIOS
            assert can_manage_area(esc.area[x], usuario) is administra
            assert can_manage_platform(plataforma[x], usuario) is administra
            assert can_access_platform(plataforma[x], usuario) is propia
    admin_a = _usuario(esc.actor[ADMIN_A])
    assert managed_area_ids(admin_a) == [esc.area['A']]
    assert managed_area_ids(_usuario(esc.actor[USUARIO_A])) == []
    assert can_manage_user(_usuario(esc.actor[USUARIO_A]), admin_a)
    for ajeno in (USUARIO_B, ADMIN_B, SUPERADMIN):
        assert not can_manage_user(_usuario(esc.actor[ajeno]), admin_a), ajeno
    assert not can_manage_area(None, admin_a)
    assert not can_manage_platform(None, admin_a)
    assert not can_access_platform(None, admin_a)


# --------------------------------------------------------------------------- #
# Áreas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor', ACTORES)
def test_listado_de_areas_filtrado(alcance, cliente_como, actor):
    esc = alcance
    areas = {'A', 'B'} if actor == SUPERADMIN else {AREA_DE[actor]}
    respuesta = _como(cliente_como, esc, actor).get(f'{A}/areas')
    assert _ids(respuesta) == {esc.area[x] for x in areas}


@pytest.mark.parametrize('actor', ADMINS_DE_AREA)
@pytest.mark.parametrize('metodo,sufijo,cuerpo', [
    ('GET', '', None),
    ('PUT', '', {'description': 'Editada desde otra área'}),
    ('DELETE', '', None),
    ('PUT', '/users', {'user_ids': []}),
])
def test_admin_area_no_toca_area_ajena(alcance, cliente_como, actor, metodo,
                                       sufijo, cuerpo):
    esc = alcance
    ajena = esc.area[OTRA[AREA_DE[actor]]]
    respuesta = _como(cliente_como, esc, actor).open(
        f'{A}/areas/{ajena}{sufijo}', method=metodo, json=cuerpo)
    _assert_denegado(respuesta)
    area = db.session.get(Area, ajena)
    assert area is not None and area.description != 'Editada desde otra área'


def test_admin_area_no_mete_usuarios_ajenos_en_su_area(alcance, cliente_como):
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).put(
        f"{A}/areas/{esc.area['A']}/users",
        json={'user_ids': [esc.actor[USUARIO_A], esc.actor[USUARIO_B]]})
    _assert_denegado(respuesta, (403,))
    assert [a.id for a in _usuario(esc.actor[USUARIO_B]).areas] == \
        [esc.area['B']]


# --------------------------------------------------------------------------- #
# Plataformas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor', ACTORES)
def test_listado_de_plataformas_filtrado(alcance, cliente_como, actor):
    esc = alcance
    cliente = _como(cliente_como, esc, actor)
    plataformas = {'A', 'B'} if actor == SUPERADMIN else {AREA_DE[actor]}
    assert _ids(cliente.get(f'{A}/platforms')) == \
        {esc.plataforma[x] for x in plataformas}
    if actor != SUPERADMIN:
        ajena = esc.area[OTRA[AREA_DE[actor]]]
        assert _ids(cliente.get(f'{A}/platforms?area_id={ajena}')) == set()


@pytest.mark.parametrize('actor', ADMINS_DE_AREA)
@pytest.mark.parametrize('metodo,sufijo,cuerpo', [
    ('PUT', '', {'description': 'Editada desde otra área'}),
    ('DELETE', '', None),
    ('PUT', '/users', {'user_ids': []}),
])
def test_admin_area_no_toca_plataforma_ajena(alcance, cliente_como, actor,
                                             metodo, sufijo, cuerpo):
    esc = alcance
    ajena = esc.plataforma[OTRA[AREA_DE[actor]]]
    respuesta = _como(cliente_como, esc, actor).open(
        f'{A}/platforms/{ajena}{sufijo}', method=metodo, json=cuerpo)
    _assert_denegado(respuesta)
    plataforma = db.session.get(Platform, ajena)
    assert plataforma is not None
    assert plataforma.description != 'Editada desde otra área'


def test_admin_area_no_crea_plataforma_en_area_ajena(alcance, cliente_como):
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).post(
        f'{A}/platforms', json={'name': 'Intrusa', 'area_id': esc.area['B']})
    # FNC-046: área ajena = inexistente → 404 (contrato plataformas-integracion).
    _assert_denegado(respuesta, (404,))
    assert Platform.query.filter_by(name='Intrusa').first() is None


def test_admin_area_no_mueve_plataforma_a_area_ajena(alcance, cliente_como):
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).put(
        f"{A}/platforms/{esc.plataforma['A']}", json={'area_id': esc.area['B']})
    _assert_denegado(respuesta, (404,))
    db.session.expire_all()
    assert db.session.get(Platform, esc.plataforma['A']).area_id == \
        esc.area['A']


def test_admin_area_no_da_su_plataforma_a_usuario_ajeno(alcance, cliente_como):
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).put(
        f"{A}/platforms/{esc.plataforma['A']}/users",
        json={'user_ids': [esc.actor[USUARIO_B]]})
    _assert_denegado(respuesta, (403,))
    assert _usuario(esc.actor[USUARIO_B]).platforms == []


# --------------------------------------------------------------------------- #
# Usuarios
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor', ADMINS_DE_AREA)
def test_listado_de_usuarios_filtrado(alcance, cliente_como, actor):
    esc = alcance
    propio = AREA_DE[actor]
    ids = _ids(_como(cliente_como, esc, actor).get(f'{A}/users'))
    assert esc.actor[USUARIO_A if propio == 'A' else USUARIO_B] in ids
    for ajeno in (SUPERADMIN, ADMIN_B if propio == 'A' else ADMIN_A,
                  USUARIO_B if propio == 'A' else USUARIO_A):
        assert esc.actor[ajeno] not in ids, ajeno


def test_superadmin_lista_a_todos(alcance, cliente_como):
    esc = alcance
    ids = _ids(_como(cliente_como, esc, SUPERADMIN).get(f'{A}/users'))
    assert set(esc.actor.values()) <= ids


@pytest.mark.parametrize('objetivo', (USUARIO_B, ADMIN_B, SUPERADMIN))
@pytest.mark.parametrize('metodo,sufijo,cuerpo', [
    ('PUT', '', {'name': 'Editado desde otra área'}),
    ('PUT', '', {'password': CONTRASENA_NUEVA}),
    ('PUT', '', {'is_active': False}),
    ('DELETE', '', None),
    ('PUT', '/areas', {'area_ids': []}),
    ('PUT', '/platforms', {'platform_ids': []}),
])
def test_admin_a_no_toca_cuentas_ajenas(alcance, cliente_como, objetivo,
                                        metodo, sufijo, cuerpo):
    esc = alcance
    antes = _usuario(esc.actor[objetivo])
    hash_antes = antes.password_hash
    areas_antes = {a.id for a in antes.areas}
    plataformas_antes = {p.id for p in antes.platforms}
    respuesta = _como(cliente_como, esc, ADMIN_A).open(
        f'{A}/users/{esc.actor[objetivo]}{sufijo}', method=metodo, json=cuerpo)
    _assert_denegado(respuesta)
    cuenta = _usuario(esc.actor[objetivo])
    assert cuenta is not None and cuenta.is_active
    assert cuenta.nombre != 'Editado desde otra área'
    assert cuenta.password_hash == hash_antes
    assert {a.id for a in cuenta.areas} == areas_antes
    assert {p.id for p in cuenta.platforms} == plataformas_antes


@pytest.mark.parametrize('actor', USUARIOS)
@pytest.mark.parametrize('metodo,cuerpo', [
    ('PUT', {'name': 'Editado por un usuario'}),
    ('DELETE', None),
])
def test_usuario_no_toca_otras_cuentas(alcance, cliente_como, actor, metodo,
                                       cuerpo):
    esc = alcance
    otro = USUARIO_B if actor == USUARIO_A else USUARIO_A
    respuesta = _como(cliente_como, esc, actor).open(
        f'{A}/users/{esc.actor[otro]}', method=metodo, json=cuerpo)
    _assert_denegado(respuesta, (403,))
    assert _usuario(esc.actor[otro]).nombre != 'Editado por un usuario'


# --------------------------------------------------------------------------- #
# Escalada de privilegios con ids fuera de alcance
# --------------------------------------------------------------------------- #

def test_no_asigna_area_ajena_a_usuario_propio(alcance, cliente_como):
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).put(
        f'{A}/users/{esc.actor[USUARIO_A]}/areas',
        json={'area_ids': [esc.area['A'], esc.area['B']]})
    _assert_denegado(respuesta, (403,))
    assert [a.id for a in _usuario(esc.actor[USUARIO_A]).areas] == \
        [esc.area['A']]


def test_no_asigna_plataforma_ajena_a_usuario_propio(alcance, cliente_como):
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).put(
        f'{A}/users/{esc.actor[USUARIO_A]}/platforms',
        json={'platform_ids': [esc.plataforma['B']]})
    _assert_denegado(respuesta, (403,))
    assert _usuario(esc.actor[USUARIO_A]).platforms == []


def test_crear_usuario_no_le_da_area_ajena(alcance, cliente_como):
    """Hoy el área ajena se descarta en silencio: la cuenta no la recibe."""
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).post(f'{A}/users', json={
        'email': 'nuevo@pruebas.local', 'role': ROLE_USER,
        'area_ids': [esc.area['A'], esc.area['B']]})
    if respuesta.status_code != 201:
        _assert_denegado(respuesta, (403,))
        return
    nuevo = _usuario(respuesta.get_json()['id'])
    assert [a.id for a in nuevo.areas] == [esc.area['A']]


def test_managed_area_ids_ajeno_no_se_asigna(alcance, cliente_como):
    esc = alcance
    _como(cliente_como, esc, ADMIN_A).put(
        f'{A}/users/{esc.actor[USUARIO_A]}',
        json={'managed_area_ids': [esc.area['B']]})
    assert esc.area['B'] not in \
        [a.id for a in _usuario(esc.actor[USUARIO_A]).managed_areas]


@pytest.mark.parametrize('area', ('A', 'B'))
def test_admin_area_no_asigna_managed_area_ids(alcance, cliente_como, area):
    """SEG-09 (FNC-044, antes xfail): `managed_area_ids` ya no se acepta en
    `PUT /users/<id>` (contrato: `400 campo_no_permitido`)."""
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).put(
        f'{A}/users/{esc.actor[USUARIO_A]}',
        json={'managed_area_ids': [esc.area[area]]})
    _assert_denegado(respuesta, (400,))
    assert respuesta.get_json()['code'] == 'campo_no_permitido'
    assert _usuario(esc.actor[USUARIO_A]).managed_areas == []


def test_admin_a_no_toca_al_admin_de_otra_area(alcance, cliente_como):
    """Admin de B sin membresía en A: fuera de alcance, 404 (SEC-AUTHZ-04)."""
    esc = alcance
    hash_antes = _usuario(esc.actor[ADMIN_B]).password_hash
    respuesta = _como(cliente_como, esc, ADMIN_A).put(
        f'{A}/users/{esc.actor[ADMIN_B]}',
        json={'password': CONTRASENA_NUEVA, 'role': ROLE_USER})
    _assert_denegado(respuesta, (404,))
    cuenta = _usuario(esc.actor[ADMIN_B])
    assert cuenta.role == ROLE_AREA_ADMIN
    assert cuenta.password_hash == hash_antes


@pytest.fixture
def admin_b_miembro_de_a(alcance):
    """Admin de B que además es miembro de A (caso de SEG-05)."""
    area_a = db.session.get(Area, alcance.area['A'])
    area_b = db.session.get(Area, alcance.area['B'])
    cuenta = fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_a, area_b],
                                    areas_administradas=[area_b],
                                    contrasena=CONTRASENA_FICTICIA)
    return cuenta.id


@pytest.mark.parametrize('metodo,cuerpo', [
    ('PUT', {'password': CONTRASENA_NUEVA}),
    ('PUT', {'role': ROLE_USER}),
    ('PUT', {'is_active': False}),
    ('DELETE', None),
])
def test_admin_area_no_toma_cuenta_de_otro_admin_area(
        alcance, cliente_como, admin_b_miembro_de_a, metodo, cuerpo):
    """SEG-05 (FNC-044, antes xfail): otro admin, aunque sea miembro del área,
    queda fuera de alcance: 404 (contrato areas-y-roles.md)."""
    esc = alcance
    respuesta = _como(cliente_como, esc, ADMIN_A).open(
        f'{A}/users/{admin_b_miembro_de_a}', method=metodo, json=cuerpo)
    _assert_denegado(respuesta, (404,))
    cuenta = _usuario(admin_b_miembro_de_a)
    assert cuenta is not None and cuenta.is_active
    assert cuenta.role == ROLE_AREA_ADMIN
    assert cuenta.check_password(CONTRASENA_FICTICIA)


# --------------------------------------------------------------------------- #
# Favoritos y visitas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('accion', ('favorite', 'visit'))
@pytest.mark.parametrize('actor', (ADMIN_A, ADMIN_B, USUARIO_A, USUARIO_B))
def test_no_marca_ni_visita_plataforma_ajena(alcance, cliente_como, actor,
                                             accion):
    esc = alcance
    ajena = OTRA[AREA_DE[actor]]
    respuesta = _como(cliente_como, esc, actor).post(
        f'{A}/platforms/{esc.plataforma[ajena]}/{accion}')
    _assert_denegado(respuesta, (404,))
    db.session.expire_all()
    plataforma = db.session.get(Platform, esc.plataforma[ajena])
    assert plataforma.visits == (VISITAS_A if ajena == 'A' else VISITAS_B)
    assert _usuario(esc.actor[actor]).favorites == []


def test_visita_y_favorito_en_plataforma_propia(alcance, cliente_como):
    esc = alcance
    cliente = _como(cliente_como, esc, USUARIO_A)
    propia = esc.plataforma['A']
    visita = cliente.post(f'{A}/platforms/{propia}/visit')
    assert visita.status_code == 200
    assert visita.get_json()['visits'] == VISITAS_A + 1
    assert cliente.post(f'{A}/platforms/{propia}/favorite').status_code == 200
    assert _ids(cliente.get(f'{A}/favorites')) == {propia}


def test_favorito_fuera_de_alcance_no_se_lista(alcance, cliente_como):
    """Un favorito que quedó fuera de alcance (p. ej. cambió de área) se oculta."""
    esc = alcance
    usuario_a = _usuario(esc.actor[USUARIO_A])
    usuario_a.favorites = [db.session.get(Platform, esc.plataforma['A']),
                           db.session.get(Platform, esc.plataforma['B'])]
    db.session.commit()
    respuesta = _como(cliente_como, esc, USUARIO_A).get(f'{A}/favorites')
    assert _ids(respuesta) == {esc.plataforma['A']}


# --------------------------------------------------------------------------- #
# Estadísticas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor', ACTORES)
def test_estadisticas_filtradas(alcance, cliente_como, actor):
    esc = alcance
    respuesta = _como(cliente_como, esc, actor).get(f'{A}/stats')
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    if actor == SUPERADMIN:
        areas, visitas = {'A', 'B'}, VISITAS_A + VISITAS_B
    else:
        areas = {AREA_DE[actor]}
        visitas = VISITAS_A if AREA_DE[actor] == 'A' else VISITAS_B
    assert datos['areas'] == len(areas)
    assert datos['platforms'] == len(areas)
    assert datos['visits'] == visitas
    assert {p['id'] for p in datos['most_visited']} == \
        {esc.plataforma[x] for x in areas}
    assert {g['area'] for g in datos['platforms_by_area']} == \
        {f'Área {x}' for x in areas}
    if actor in USUARIOS:
        assert 'users' not in datos
    elif actor in ADMINS_DE_AREA:
        assert datos['users'] == 1  # el usuario de su área (FNC-044)
    else:
        assert datos['users'] == len(ACTORES)


# --------------------------------------------------------------------------- #
# Auditoría
# --------------------------------------------------------------------------- #

def _registrar(cuenta, area_id, accion='ACCIÓN DE PRUEBA'):
    db.session.add(AuditLog(user=cuenta.email, actor_id=cuenta.id,
                            area_id=area_id, action=accion, module='Pruebas'))
    db.session.commit()


@pytest.fixture
def auditoria(alcance):
    """Un registro por actor en su área (el del superadmin, sin área);
    devuelve actor -> correo (FNC-060: el admin ve por área afectada)."""
    correos = {}
    for actor, uid in alcance.actor.items():
        cuenta = _usuario(uid)
        area = AREA_DE.get(actor)
        _registrar(cuenta, alcance.area[area] if area else None)
        correos[actor] = cuenta.email
    return correos


@pytest.mark.parametrize('actor,visibles', [
    (SUPERADMIN, ACTORES),
    (ADMIN_A, (ADMIN_A, USUARIO_A)),
    (ADMIN_B, (ADMIN_B, USUARIO_B)),
    (USUARIO_A, (USUARIO_A,)),
    (USUARIO_B, (USUARIO_B,)),
])
def test_auditoria_filtrada(alcance, auditoria, cliente_como, actor, visibles):
    respuesta = _como(cliente_como, alcance, actor).get(f'{A}/audit')
    assert respuesta.status_code == 200
    usuarios = {r['user'] for r in respuesta.get_json()}
    assert usuarios == {auditoria[v] for v in visibles}


def test_admin_area_no_ve_eventos_de_otra_area_de_un_usuario_compartido(
        alcance, cliente_como):
    """SEG-16 (FNC-060): un usuario de A que también es de B actúa en B; el
    admin de A no ve ese registro (antes filtraba por actor, no por área)."""
    esc = alcance
    compartido = fabricas.crear_usuario(
        ROLE_USER, areas=[db.session.get(Area, esc.area['A']),
                          db.session.get(Area, esc.area['B'])])
    _registrar(compartido, esc.area['B'], accion='EN B')
    _registrar(compartido, esc.area['A'], accion='EN A')
    respuesta = _como(cliente_como, esc, ADMIN_A).get(f'{A}/audit')
    assert respuesta.status_code == 200
    assert [r['action'] for r in respuesta.get_json()
            if r['user'] == compartido.email] == ['EN A']


def test_admin_area_no_ve_auditoria_de_otra_area(alcance, cliente_como,
                                                 admin_b_miembro_de_a):
    """SEG-16 (FNC-060, antes xfail): el admin de B (miembro de A) edita su
    plataforma de B: el admin de A no ve ese registro."""
    esc = alcance
    edicion = cliente_como(_usuario(admin_b_miembro_de_a)).put(
        f"{A}/platforms/{esc.plataforma['B']}",
        json={'description': 'Editada en B'})
    assert edicion.status_code == 200
    # Las peticiones comparten el app context de la prueba: sin esto,
    # Flask-Login reutiliza el usuario de la petición anterior (`g`).
    g.pop('_login_user', None)
    respuesta = _como(cliente_como, esc, ADMIN_A).get(f'{A}/audit')
    assert respuesta.status_code == 200
    assert not [r for r in respuesta.get_json()
                if r['module'] == 'Plataformas'
                and r['target'] == 'Plataforma B'], respuesta.get_json()
