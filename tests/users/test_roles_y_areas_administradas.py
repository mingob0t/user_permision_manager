"""Roles y áreas administradas (FNC-044, contrato areas-y-roles.md).

- Solo el superadmin asigna `admin_area`; nadie asigna `administrador`.
- `managed_area_ids` y `auth_source` -> `400 campo_no_permitido`.
- `POST /users` con `admin_area` ya no copia las áreas a las administradas.
- Un admin de área no gestiona a otros admins (404) ni cambia contraseñas.
- `PUT /users/<id>/managed-areas`: solo superadmin, con auditoría por área en
  la misma transacción.

La matriz por rol del endpoint nuevo está en `tests/matriz_proteccion.py`.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit import services as auditoria
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.core.models import Area
from tests import fabricas
from tests.matriz_proteccion import CONTRASENA_FICTICIA

A = '/api/v1'
CONTRASENA_NUEVA = 'otra-clave-ficticia-de-prueba'


def _cuenta(user_id):
    db.session.expire_all()
    return db.session.get(User, user_id)


def _codigo(respuesta, http, code):
    assert respuesta.status_code == http, respuesta.get_data(as_text=True)
    datos = respuesta.get_json()
    assert datos['status'] == 'error' and datos['message']
    assert datos['code'] == code


def _eventos(accion, target_user_id):
    return (AuditLog.query.filter_by(action=accion,
                                     target_user_id=target_user_id)
            .order_by(AuditLog.id).all())


@pytest.fixture
def escena(app):
    """Área A y B; superadmin, admin de A (miembro de A) y un usuario de A."""
    area_a = fabricas.crear_area('Área A')
    area_b = fabricas.crear_area('Área B')
    return {
        'A': area_a.id,
        'B': area_b.id,
        'super': fabricas.crear_usuario(ROLE_ADMIN).id,
        'admin_a': fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_a],
                                          areas_administradas=[area_a]).id,
        'usuario_a': fabricas.crear_usuario(ROLE_USER, areas=[area_a],
                                            contrasena=CONTRASENA_FICTICIA).id,
    }


@pytest.fixture
def como(cliente_como):
    return lambda user_id: cliente_como(_cuenta(user_id))


# --------------------------------------------------------------------------- #
# POST /users
# --------------------------------------------------------------------------- #

def test_admin_area_nuevo_nace_sin_areas_administradas(escena, como):
    """Antes copiaba `area_ids` a las áreas administradas."""
    respuesta = como(escena['super']).post(f'{A}/users', json={
        'email': 'nuevo.admin@pruebas.local', 'role': ROLE_AREA_ADMIN,
        'area_ids': [escena['A']], 'password': CONTRASENA_FICTICIA})
    assert respuesta.status_code == 201, respuesta.get_data(as_text=True)
    cuenta = _cuenta(respuesta.get_json()['id'])
    assert cuenta.role == ROLE_AREA_ADMIN
    assert [a.id for a in cuenta.areas] == [escena['A']]
    assert cuenta.managed_areas == []


@pytest.mark.parametrize('campo,valor', [
    ('managed_area_ids', [1]),
    ('auth_source', 'ldap'),
    ('password_hash', 'hash'),
])
@pytest.mark.parametrize('actor', ('super', 'admin_a'))
def test_crear_con_campo_no_permitido_da_400(escena, como, actor, campo,
                                             valor):
    respuesta = como(escena[actor]).post(f'{A}/users', json={
        'email': 'nuevo@pruebas.local', 'role': ROLE_USER,
        'area_ids': [escena['A']], campo: valor})
    _codigo(respuesta, 400, 'campo_no_permitido')
    assert User.query.filter_by(email='nuevo@pruebas.local').first() is None


def test_el_servidor_fija_el_origen_local(escena, como):
    respuesta = como(escena['admin_a']).post(f'{A}/users', json={
        'email': 'nuevo@pruebas.local', 'area_ids': [escena['A']],
        'password': CONTRASENA_FICTICIA})
    assert respuesta.status_code == 201
    assert _cuenta(respuesta.get_json()['id']).auth_source == 'local'


@pytest.mark.parametrize('actor,rol', [
    ('super', ROLE_ADMIN),
    ('super', 'rol-inventado'),
    ('admin_a', ROLE_AREA_ADMIN),
    ('admin_a', ROLE_ADMIN),
])
def test_crear_con_rol_reservado_da_403(escena, como, actor, rol):
    respuesta = como(escena[actor]).post(f'{A}/users', json={
        'email': 'nuevo@pruebas.local', 'role': rol,
        'area_ids': [escena['A']], 'password': CONTRASENA_FICTICIA})
    _codigo(respuesta, 403, 'rol_reservado')
    assert User.query.filter_by(email='nuevo@pruebas.local').first() is None


def test_no_existe_un_segundo_superadmin(escena, como):
    como(escena['super']).post(f'{A}/users', json={
        'email': 'otro.super@pruebas.local', 'role': ROLE_ADMIN,
        'password': CONTRASENA_FICTICIA})
    como(escena['super']).put(f"{A}/users/{escena['usuario_a']}",
                              json={'role': ROLE_ADMIN})
    assert User.query.filter(db.func.lower(User.role) == ROLE_ADMIN).count() == 1


# --------------------------------------------------------------------------- #
# PUT /users/<id>: rol
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('campo,valor', [
    ('managed_area_ids', [1]),
    ('auth_source', 'sso'),
])
def test_editar_con_campo_no_permitido_da_400(escena, como, campo, valor):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['admin_a']}", json={campo: valor})
    _codigo(respuesta, 400, 'campo_no_permitido')
    cuenta = _cuenta(escena['admin_a'])
    assert [a.id for a in cuenta.managed_areas] == [escena['A']]
    assert cuenta.auth_source == 'local'


def test_superadmin_eleva_a_admin_area_sin_areas_y_audita(escena, como):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['usuario_a']}", json={'role': ROLE_AREA_ADMIN})
    assert respuesta.status_code == 200
    cuenta = _cuenta(escena['usuario_a'])
    assert cuenta.role == ROLE_AREA_ADMIN
    assert cuenta.managed_areas == []
    [evento] = _eventos('rol_cambiado', escena['usuario_a'])
    assert evento.actor_id == escena['super']


def test_degradar_borra_areas_administradas_y_audita(escena, como):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['admin_a']}", json={'role': ROLE_USER})
    assert respuesta.status_code == 200
    cuenta = _cuenta(escena['admin_a'])
    assert cuenta.role == ROLE_USER
    assert cuenta.managed_areas == []
    [evento] = _eventos('rol_cambiado', escena['admin_a'])
    datos = evento.to_dict()
    assert datos['before'] == {'role': ROLE_AREA_ADMIN,
                               'managed_area_ids': [escena['A']]}
    assert datos['after'] == {'role': ROLE_USER, 'managed_area_ids': []}


def test_nadie_cambia_su_propio_rol(escena, como):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['super']}", json={'role': ROLE_USER})
    _codigo(respuesta, 403, 'operacion_propia')
    assert _cuenta(escena['super']).role == ROLE_ADMIN


def test_enviar_el_mismo_rol_no_es_un_cambio(escena, como):
    """El formulario actual reenvía el rol; el propio sin cambio no falla."""
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['super']}", json={'role': ROLE_ADMIN,
                                               'name': 'Superadmin'})
    assert respuesta.status_code == 200
    assert _cuenta(escena['super']).nombre == 'Superadmin'
    assert _eventos('rol_cambiado', escena['super']) == []


def test_rol_invalido_no_deja_cambios_a_medias(escena, como):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['usuario_a']}",
        json={'name': 'No debe guardarse', 'role': ROLE_ADMIN})
    _codigo(respuesta, 403, 'rol_reservado')
    assert _cuenta(escena['usuario_a']).nombre != 'No debe guardarse'


# --------------------------------------------------------------------------- #
# Admin de área sobre otras cuentas (SEG-05)
# --------------------------------------------------------------------------- #

@pytest.fixture
def otro_admin_miembro_de_a(escena):
    """Admin de B que además es miembro de A, con contraseña local."""
    area_a = db.session.get(Area, escena['A'])
    area_b = db.session.get(Area, escena['B'])
    return fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_a, area_b],
                                  areas_administradas=[area_b],
                                  contrasena=CONTRASENA_FICTICIA).id


@pytest.mark.parametrize('metodo,ruta,cuerpo', [
    ('PUT', '', {'name': 'Tomada'}),
    ('DELETE', '', None),
    ('PUT', '/areas', {'area_ids': []}),
    ('PUT', '/platforms', {'platform_ids': []}),
])
def test_admin_area_no_gestiona_a_otro_admin(escena, como,
                                             otro_admin_miembro_de_a, metodo,
                                             ruta, cuerpo):
    respuesta = como(escena['admin_a']).open(
        f'{A}/users/{otro_admin_miembro_de_a}{ruta}', method=metodo,
        json=cuerpo)
    assert respuesta.status_code in (403, 404)
    cuenta = _cuenta(otro_admin_miembro_de_a)
    assert cuenta is not None and cuenta.nombre != 'Tomada'
    assert {a.id for a in cuenta.areas} == {escena['A'], escena['B']}


def test_admin_area_no_se_gestiona_a_si_mismo(escena, como):
    respuesta = como(escena['admin_a']).put(
        f"{A}/users/{escena['admin_a']}", json={'role': ROLE_USER})
    _codigo(respuesta, 404, 'no_encontrado')


def test_admin_area_cambia_contrasena_local_de_su_usuario(escena, como):
    """Decisión del dueño (2026-10-15): el admin de área sí puede."""
    respuesta = como(escena['admin_a']).put(
        f"{A}/users/{escena['usuario_a']}", json={'password': CONTRASENA_NUEVA})
    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    assert _cuenta(escena['usuario_a']).check_password(CONTRASENA_NUEVA)


def test_admin_area_no_cambia_contrasena_de_cuenta_no_local(escena, como):
    cuenta = _cuenta(escena['usuario_a'])
    cuenta.auth_source = 'ldap'
    db.session.commit()
    respuesta = como(escena['admin_a']).put(
        f"{A}/users/{escena['usuario_a']}", json={'password': CONTRASENA_NUEVA})
    _codigo(respuesta, 400, 'campo_no_permitido')
    assert _cuenta(escena['usuario_a']).check_password(CONTRASENA_FICTICIA)


@pytest.mark.parametrize('origen', ('ldap', 'sso'))
def test_nadie_cambia_la_contrasena_de_cuentas_no_locales(escena, como,
                                                          origen):
    cuenta = _cuenta(escena['usuario_a'])
    cuenta.auth_source = origen
    db.session.commit()
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['usuario_a']}", json={'password': CONTRASENA_NUEVA})
    _codigo(respuesta, 400, 'campo_no_permitido')
    assert _cuenta(escena['usuario_a']).check_password(CONTRASENA_FICTICIA)


def test_superadmin_cambia_contrasena_local(escena, como):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['usuario_a']}", json={'password': CONTRASENA_NUEVA})
    assert respuesta.status_code == 200
    assert _cuenta(escena['usuario_a']).check_password(CONTRASENA_NUEVA)


# --------------------------------------------------------------------------- #
# PUT /users/<id>/managed-areas
# --------------------------------------------------------------------------- #

def _managed(cliente, user_id, cuerpo):
    return cliente.put(f'{A}/users/{user_id}/managed-areas', json=cuerpo)


def test_superadmin_reemplaza_areas_administradas(escena, como):
    respuesta = _managed(como(escena['super']), escena['admin_a'],
                         {'area_ids': [escena['B']]})
    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    datos = respuesta.get_json()
    assert datos['status'] == 'success'
    assert datos['user']['id'] == escena['admin_a']
    assert [a['id'] for a in datos['user']['managed_areas']] == [escena['B']]
    assert set(datos['user']) == {'id', 'email', 'name', 'role', 'is_active',
                                  'auth_source', 'areas', 'managed_areas',
                                  'last_login_at'}
    assert [a.id for a in _cuenta(escena['admin_a']).managed_areas] == \
        [escena['B']]

    [asignado] = _eventos('admin_asignado', escena['admin_a'])
    [retirado] = _eventos('admin_retirado', escena['admin_a'])
    assert (asignado.area_id, retirado.area_id) == (escena['B'], escena['A'])
    assert asignado.actor_id == escena['super']


def test_lista_vacia_retira_todas(escena, como):
    respuesta = _managed(como(escena['super']), escena['admin_a'],
                         {'area_ids': []})
    assert respuesta.status_code == 200
    assert _cuenta(escena['admin_a']).managed_areas == []


def test_misma_lista_no_audita(escena, como):
    respuesta = _managed(como(escena['super']), escena['admin_a'],
                         {'area_ids': [escena['A']]})
    assert respuesta.status_code == 200
    assert _eventos('admin_asignado', escena['admin_a']) == []
    assert _eventos('admin_retirado', escena['admin_a']) == []


@pytest.mark.parametrize('destino', ('usuario_a', 'super'))
def test_destino_que_no_es_admin_area_da_409(escena, como, destino):
    respuesta = _managed(como(escena['super']), escena[destino],
                         {'area_ids': [escena['A']]})
    _codigo(respuesta, 409, 'rol_no_admin')
    assert _cuenta(escena[destino]).managed_areas == []


def test_destino_inexistente_da_404(escena, como):
    respuesta = _managed(como(escena['super']), 99999, {'area_ids': []})
    _codigo(respuesta, 404, 'no_encontrado')


@pytest.mark.parametrize('cuerpo', [
    {},
    {'area_ids': 'A'},
    {'area_ids': [True]},
    {'area_ids': ['1']},
    {'area_ids': [99999]},
    {'area_ids': list(range(1, 52))},
])
def test_area_ids_invalidos_dan_422(escena, como, cuerpo):
    respuesta = _managed(como(escena['super']), escena['admin_a'], cuerpo)
    _codigo(respuesta, 422, 'validacion')
    assert 'area_ids' in respuesta.get_json()['fields']
    assert [a.id for a in _cuenta(escena['admin_a']).managed_areas] == \
        [escena['A']]


def test_area_ids_repetidos_dan_422(escena, como):
    respuesta = _managed(como(escena['super']), escena['admin_a'],
                         {'area_ids': [escena['B'], escena['B']]})
    _codigo(respuesta, 422, 'validacion')


def test_campo_extra_da_400(escena, como):
    respuesta = _managed(como(escena['super']), escena['admin_a'],
                         {'area_ids': [], 'role': ROLE_USER})
    _codigo(respuesta, 400, 'campo_no_permitido')


@pytest.mark.parametrize('actor', ('admin_a', 'usuario_a'))
def test_solo_el_superadmin_asigna_areas_administradas(escena, como, actor):
    respuesta = _managed(como(escena[actor]), escena['admin_a'],
                         {'area_ids': [escena['A'], escena['B']]})
    assert respuesta.status_code == 403
    assert [a.id for a in _cuenta(escena['admin_a']).managed_areas] == \
        [escena['A']]


def test_si_falla_la_auditoria_no_se_guarda_el_cambio(escena, como,
                                                       monkeypatch):
    """SEC-AUD-06: cambio y auditoría en la misma transacción."""
    def _falla(*args, **kwargs):
        raise RuntimeError('fallo simulado de auditoría')
    monkeypatch.setattr(auditoria, 'limpiar_detalle', _falla)

    with pytest.raises(RuntimeError):
        _managed(como(escena['super']), escena['admin_a'],
                 {'area_ids': [escena['B']]})

    assert [a.id for a in _cuenta(escena['admin_a']).managed_areas] == \
        [escena['A']]
    assert _eventos('admin_asignado', escena['admin_a']) == []


def test_si_falla_la_auditoria_no_se_cambia_el_rol(escena, como, monkeypatch):
    def _falla(*args, **kwargs):
        raise RuntimeError('fallo simulado de auditoría')
    monkeypatch.setattr(auditoria, 'limpiar_detalle', _falla)

    with pytest.raises(RuntimeError):
        como(escena['super']).put(f"{A}/users/{escena['admin_a']}",
                                  json={'role': ROLE_USER})

    cuenta = _cuenta(escena['admin_a'])
    assert cuenta.role == ROLE_AREA_ADMIN
    assert [a.id for a in cuenta.managed_areas] == [escena['A']]


# --------------------------------------------------------------------------- #
# Residual de SEG-05: membresías de otros admins (revisión de seguridad)
# --------------------------------------------------------------------------- #

def test_admin_area_no_lista_a_otros_admins(escena, como,
                                           otro_admin_miembro_de_a):
    respuesta = como(escena['admin_a']).get(f'{A}/users')
    assert respuesta.status_code == 200
    ids = {u['id'] for u in respuesta.get_json()}
    assert ids == {escena['usuario_a']}


def test_admin_area_no_saca_a_otro_admin_de_su_area(escena, como,
                                                    otro_admin_miembro_de_a):
    respuesta = como(escena['admin_a']).put(
        f"{A}/areas/{escena['A']}/users", json={'user_ids': [escena['usuario_a']]})
    assert respuesta.status_code == 200
    assert escena['A'] in {a.id for a in _cuenta(otro_admin_miembro_de_a).areas}


def test_admin_area_no_mete_a_otro_admin_en_su_plataforma(
        escena, como, otro_admin_miembro_de_a):
    area_a = db.session.get(Area, escena['A'])
    plataforma = fabricas.crear_plataforma(area_a)
    respuesta = como(escena['admin_a']).put(
        f'{A}/platforms/{plataforma.id}/users',
        json={'user_ids': [otro_admin_miembro_de_a]})
    assert respuesta.status_code == 403
    assert _cuenta(otro_admin_miembro_de_a).platforms == []


def test_admin_area_ve_su_propia_auditoria(escena, como):
    cliente = como(escena['admin_a'])
    cliente.put(f"{A}/areas/{escena['A']}", json={'description': 'Editada'})
    respuesta = cliente.get(f'{A}/audit')
    assert respuesta.status_code == 200
    correo = _cuenta(escena['admin_a']).email
    assert correo in {r['user'] for r in respuesta.get_json()}


# --------------------------------------------------------------------------- #
# PUT /users/<id>/areas y /platforms (revisión de seguridad, Baja)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('ruta,cuerpo', [
    ('/areas', {'area_ids': []}),
    ('/platforms', {'platform_ids': []}),
])
def test_cuenta_fuera_de_alcance_da_404(escena, como, otro_admin_miembro_de_a,
                                        ruta, cuerpo):
    respuesta = como(escena['admin_a']).put(
        f'{A}/users/{otro_admin_miembro_de_a}{ruta}', json=cuerpo)
    _codigo(respuesta, 404, 'no_encontrado')


@pytest.mark.parametrize('ruta,cuerpo', [
    ('/areas', [1]),
    ('/areas', {'area_ids': 'x'}),
    ('/areas', {'area_ids': [[1]]}),
    ('/platforms', [1]),
    ('/platforms', {'platform_ids': 5}),
    ('/platforms', {'platform_ids': [{}]}),
])
def test_cuerpo_no_valido_da_400(escena, como, ruta, cuerpo):
    respuesta = como(escena['super']).put(
        f"{A}/users/{escena['usuario_a']}{ruta}", json=cuerpo)
    _codigo(respuesta, 400, 'cuerpo_invalido')
