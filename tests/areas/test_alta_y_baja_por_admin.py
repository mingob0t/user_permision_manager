"""Alta, edición y baja de áreas por el admin (FNC-045, contrato areas-y-roles.md).

- `POST /areas`: superadmin y admin de área; el admin queda en `area_admins`
  del área nueva en la misma transacción; auditoría `area_creada`.
- `PUT` y `DELETE /areas/<id>`: admin (sus áreas) o superadmin; área ajena o
  inexistente → 404; usuario → 403.
- `DELETE`: `409 area_con_plataformas` o `409 area_con_accesos`; auditoría
  `area_eliminada` (P11).
- Lista blanca (400 `campo_no_permitido`), validación (422 `validacion`) y
  nombre único sin distinguir mayúsculas (409 `area_duplicada`).

La matriz por rol está en `tests/matriz_proteccion.py`.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit import services as auditoria
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.core.models import Area
from tests import fabricas

A = '/api/v1'


@pytest.fixture
def escena(app):
    """Áreas A y B, un admin de cada una, un usuario de A y el superadmin."""
    area_a = fabricas.crear_area('Área A')
    area_b = fabricas.crear_area('Área B')
    return {
        'A': area_a.id,
        'B': area_b.id,
        'admin_a': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                          email='admin-a@pruebas.local',
                                          areas_administradas=[area_a]),
        'admin_b': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                          areas_administradas=[area_b]),
        'usuario': fabricas.crear_usuario(ROLE_USER, areas=[area_a]),
        'super': fabricas.crear_usuario(ROLE_ADMIN,
                                        email='super@pruebas.local'),
    }


@pytest.fixture
def como(escena, cliente_como):
    return lambda actor: cliente_como(escena[actor])


def _codigo(respuesta, http, code):
    assert respuesta.status_code == http, respuesta.get_data(as_text=True)
    datos = respuesta.get_json()
    assert datos['status'] == 'error' and datos['message']
    assert datos['code'] == code
    return datos


def _area(area_id):
    db.session.expire_all()
    return db.session.get(Area, area_id)


def _eventos(accion):
    return AuditLog.query.filter_by(action=accion).all()


# --------------------------------------------------------------------------- #
# POST /areas
# --------------------------------------------------------------------------- #

def test_admin_area_crea_area_y_queda_como_su_admin(escena, como):
    respuesta = como('admin_a').post(f'{A}/areas', json={
        'name': 'Finanzas', 'description': 'Sistemas contables',
        'icon': 'wallet', 'color': '#2563eb', 'status': 'Activo'})

    assert respuesta.status_code == 201, respuesta.get_json()
    datos = respuesta.get_json()
    assert datos['status'] == 'success'
    area = datos['area']
    assert (area['name'], area['icon'], area['color']) == \
        ('Finanzas', 'wallet', '#2563eb')
    admin = db.session.get(User, escena['admin_a'].id)
    db.session.refresh(admin)
    assert area['id'] in {a.id for a in admin.managed_areas}


def test_admin_area_administra_el_area_que_creo(escena, como):
    cliente = como('admin_a')
    nueva = cliente.post(f'{A}/areas', json={'name': 'Nueva'}).get_json()

    respuesta = cliente.put(f"{A}/areas/{nueva['area']['id']}",
                            json={'description': 'Editada'})

    assert respuesta.status_code == 200, respuesta.get_json()
    me = cliente.get(f'{A}/me').get_json()
    assert nueva['area']['id'] in {a['id'] for a in me['managed_areas']}


def test_alta_audita_area_creada_con_actor_y_area(escena, como):
    respuesta = como('admin_a').post(f'{A}/areas', json={'name': 'Auditada'})

    area_id = respuesta.get_json()['area']['id']
    registro, = _eventos('area_creada')
    assert registro.actor_id == escena['admin_a'].id
    assert registro.user == 'admin-a@pruebas.local'
    assert registro.area_id == area_id
    assert registro.target == 'Auditada'
    assert registro.after_state['name'] == 'Auditada'


def test_superadmin_crea_area_sin_quedar_en_area_admins(escena, como):
    respuesta = como('super').post(f'{A}/areas', json={'name': 'Global'})

    assert respuesta.status_code == 201
    area = _area(respuesta.get_json()['area']['id'])
    assert area.admins == []
    assert len(_eventos('area_creada')) == 1


def test_usuario_no_crea_areas(escena, como):
    respuesta = como('usuario').post(f'{A}/areas', json={'name': 'No'})

    assert respuesta.status_code == 403
    assert Area.query.filter_by(name='No').first() is None
    assert _eventos('area_creada') == []


@pytest.mark.parametrize('nombre', ['Área A', 'área a', '  ÁREA A  '])
def test_nombre_duplicado_da_409(escena, como, nombre):
    respuesta = como('admin_a').post(f'{A}/areas', json={'name': nombre})

    _codigo(respuesta, 409, 'area_duplicada')
    assert Area.query.count() == 2


@pytest.mark.parametrize('cuerpo,campo', [
    ({}, 'name'),
    ({'name': ''}, 'name'),
    ({'name': 'x'}, 'name'),
    ({'name': 'x' * 101}, 'name'),
    ({'name': 12}, 'name'),
    ({'name': 'Válida', 'description': 'd' * 501}, 'description'),
    ({'name': 'Válida', 'description': 5}, 'description'),
    ({'name': 'Válida', 'icon': 'i' * 51}, 'icon'),
    ({'name': 'Válida', 'icon': '<svg>'}, 'icon'),
    ({'name': 'Válida', 'color': 'red'}, 'color'),
    ({'name': 'Válida', 'color': '#12345'}, 'color'),
    ({'name': 'Válida', 'status': 'Borrada'}, 'status'),
])
def test_alta_con_datos_invalidos_da_422(escena, como, cuerpo, campo):
    respuesta = como('admin_a').post(f'{A}/areas', json=cuerpo)

    datos = _codigo(respuesta, 422, 'validacion')
    assert campo in datos['fields']
    assert Area.query.count() == 2


@pytest.mark.parametrize('campo', ['id', 'admins', 'role', 'is_active',
                                   'area_ids'])
def test_alta_con_campo_no_permitido_da_400(escena, como, campo):
    respuesta = como('admin_a').post(f'{A}/areas',
                                     json={'name': 'Válida', campo: 1})

    _codigo(respuesta, 400, 'campo_no_permitido')
    assert Area.query.count() == 2


def test_alta_con_cuerpo_que_no_es_objeto_da_400(escena, como):
    respuesta = como('admin_a').post(f'{A}/areas', json=['Válida'])

    _codigo(respuesta, 400, 'cuerpo_invalido')


def test_si_falla_la_auditoria_no_se_crea_el_area(escena, como, monkeypatch):
    def _falla(*args, **kwargs):
        raise RuntimeError('auditoría caída (simulada)')
    monkeypatch.setattr(auditoria, 'limpiar_detalle', _falla)

    cliente = como('admin_a')
    with pytest.raises(RuntimeError):
        cliente.post(f'{A}/areas', json={'name': 'A medias'})

    db.session.rollback()
    assert Area.query.filter_by(name='A medias').first() is None
    admin = db.session.get(User, escena['admin_a'].id)
    assert {a.id for a in admin.managed_areas} == {escena['A']}


# --------------------------------------------------------------------------- #
# PUT /areas/<id>
# --------------------------------------------------------------------------- #

def test_admin_edita_su_area_y_audita(escena, como):
    respuesta = como('admin_a').put(f"{A}/areas/{escena['A']}",
                                    json={'description': 'Nueva descripción'})

    assert respuesta.status_code == 200
    assert _area(escena['A']).description == 'Nueva descripción'
    registro, = _eventos('area_editada')
    assert registro.area_id == escena['A']
    assert registro.actor_id == escena['admin_a'].id
    assert registro.after_state['description'] == 'Nueva descripción'


@pytest.mark.parametrize('metodo', ['PUT', 'DELETE'])
def test_admin_sobre_area_ajena_da_404(escena, como, metodo):
    respuesta = como('admin_a').open(f"{A}/areas/{escena['B']}", method=metodo,
                                     json={'description': 'Ajena'})

    _codigo(respuesta, 404, 'no_encontrado')
    area = _area(escena['B'])
    assert area is not None and area.description != 'Ajena'


@pytest.mark.parametrize('metodo', ['PUT', 'DELETE'])
def test_area_inexistente_da_404(escena, como, metodo):
    respuesta = como('super').open(f'{A}/areas/99999', method=metodo,
                                   json={'description': 'x'})

    _codigo(respuesta, 404, 'no_encontrado')


@pytest.mark.parametrize('metodo', ['PUT', 'DELETE'])
def test_usuario_no_edita_ni_borra_areas(escena, como, metodo):
    respuesta = como('usuario').open(f"{A}/areas/{escena['A']}", method=metodo,
                                     json={'description': 'Usuario'})

    assert respuesta.status_code == 403
    area = _area(escena['A'])
    assert area is not None and area.description != 'Usuario'


def test_renombrar_a_un_nombre_existente_da_409(escena, como):
    respuesta = como('super').put(f"{A}/areas/{escena['A']}",
                                  json={'name': 'área b'})

    _codigo(respuesta, 409, 'area_duplicada')
    assert _area(escena['A']).name == 'Área A'


def test_edicion_con_datos_invalidos_da_422(escena, como):
    respuesta = como('admin_a').put(f"{A}/areas/{escena['A']}",
                                    json={'color': 'azul'})

    datos = _codigo(respuesta, 422, 'validacion')
    assert 'color' in datos['fields']


def test_edicion_con_campo_no_permitido_da_400(escena, como):
    respuesta = como('admin_a').put(f"{A}/areas/{escena['A']}",
                                    json={'id': 7})

    _codigo(respuesta, 400, 'campo_no_permitido')


def test_reenviar_un_valor_sin_cambios_no_se_valida(escena, como):
    """Un área heredada con un color fuera de formato se puede seguir editando."""
    area = _area(escena['A'])
    area.color = 'indigo'
    db.session.commit()

    respuesta = como('admin_a').put(f"{A}/areas/{escena['A']}", json={
        'name': 'Área A', 'color': 'indigo', 'description': 'Editada'})

    assert respuesta.status_code == 200, respuesta.get_json()


# --------------------------------------------------------------------------- #
# DELETE /areas/<id> (P11)
# --------------------------------------------------------------------------- #

@pytest.fixture
def sin_miembros(escena):
    """Quita al usuario de A: así A queda sin accesos vigentes."""
    usuario = db.session.get(User, escena['usuario'].id)
    usuario.areas = []
    db.session.commit()
    return escena


def test_admin_da_de_baja_su_area_y_audita(sin_miembros, como):
    escena = sin_miembros
    respuesta = como('admin_a').delete(f"{A}/areas/{escena['A']}")

    assert respuesta.status_code == 200, respuesta.get_json()
    assert respuesta.get_json() == {'status': 'success'}
    assert _area(escena['A']) is None
    registro, = _eventos('area_eliminada')
    assert registro.actor_id == escena['admin_a'].id
    assert registro.target == 'Área A'
    assert registro.before_state['name'] == 'Área A'
    admin = db.session.get(User, escena['admin_a'].id)
    assert admin.managed_areas == []


def test_superadmin_da_de_baja_cualquier_area(escena, como):
    respuesta = como('super').delete(f"{A}/areas/{escena['B']}")

    assert respuesta.status_code == 200
    assert _area(escena['B']) is None


def test_baja_con_plataformas_da_409(sin_miembros, como):
    fabricas.crear_plataforma(_area(sin_miembros['A']))

    respuesta = como('admin_a').delete(f"{A}/areas/{sin_miembros['A']}")

    _codigo(respuesta, 409, 'area_con_plataformas')
    assert _area(sin_miembros['A']) is not None
    assert _eventos('area_eliminada') == []


def test_baja_con_accesos_vigentes_da_409(escena, como):
    """El usuario de A la alcanza (`user_areas`): es un acceso vigente."""
    respuesta = como('super').delete(f"{A}/areas/{escena['A']}")

    _codigo(respuesta, 409, 'area_con_accesos')
    assert _area(escena['A']) is not None


def test_si_falla_la_auditoria_no_se_da_de_baja(sin_miembros, como,
                                               monkeypatch):
    def _falla(*args, **kwargs):
        raise RuntimeError('auditoría caída (simulada)')
    monkeypatch.setattr(auditoria, 'limpiar_detalle', _falla)

    with pytest.raises(RuntimeError):
        como('admin_a').delete(f"{A}/areas/{sin_miembros['A']}")

    db.session.rollback()
    assert _area(sin_miembros['A']) is not None
