"""Helpers comunes de `api/helpers.py` y servicios unificados (FNC-030, FNC-082).

- Lista blanca y lista negra de campos, y `leer_cuerpo`.
- `json_payload` (lectura laxa) y `error_response` sin `code`.
- Aviso de usuario creado (D-04) y purga de inactivos (D-05).
"""

from datetime import datetime, timedelta

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_USER
from app.modules.api.helpers import (campos_no_permitidos, campos_prohibidos,
                                     error_response, json_payload,
                                     leer_cuerpo)
from app.modules.auth.models import User
from app.modules.notifications import services
from app.modules.users.services import (PURGE_MIN_DAYS, purgar_inactivos,
                                        usuarios_inactivos)
from tests import fabricas


# --------------------------------------------------------------------------- #
# Listas blanca y negra
# --------------------------------------------------------------------------- #

def test_lista_blanca_devuelve_los_rechazados_ordenados():
    datos = {'z': 1, 'a': 2, 'ok': 3}

    assert campos_no_permitidos(datos, {'ok'}) == ['a', 'z']


def test_lista_blanca_vacia_si_todo_esta_permitido():
    assert campos_no_permitidos({'a': 1}, frozenset({'a', 'b'})) == []


def test_sin_permitidos_cualquier_campo_se_rechaza():
    assert campos_no_permitidos({'x': 1}) == ['x']
    assert campos_no_permitidos({}) == []


def test_lista_negra_devuelve_solo_los_prohibidos_ordenados():
    datos = {'password_hash': 1, 'name': 2, 'auth_source': 3}

    assert campos_prohibidos(
        datos, {'auth_source', 'password_hash', 'managed_area_ids'}
    ) == ['auth_source', 'password_hash']


# --------------------------------------------------------------------------- #
# Lectura del cuerpo
# --------------------------------------------------------------------------- #


def test_leer_cuerpo_sin_cuerpo_es_objeto_vacio(app):
    with app.test_request_context('/', method='POST'):
        assert leer_cuerpo() == ({}, None)


def test_leer_cuerpo_valido_con_campos_permitidos(app):
    with app.test_request_context('/', method='POST', json={'reason': 'x'}):
        assert leer_cuerpo({'reason'}) == ({'reason': 'x'}, None)


@pytest.mark.parametrize('cuerpo', [[1], 'texto', 3])
def test_leer_cuerpo_que_no_es_objeto_da_400_cuerpo_invalido(app, cuerpo):
    with app.test_request_context('/', method='POST', json=cuerpo):
        datos, respuesta = leer_cuerpo()

    assert datos is None
    cuerpo_error, estado = respuesta[0].get_json(), respuesta[1]
    assert estado == 400 and cuerpo_error['code'] == 'cuerpo_invalido'


def test_leer_cuerpo_con_campo_ajeno_da_400_campo_no_permitido(app):
    with app.test_request_context('/', method='POST', json={'otro': 1}):
        datos, respuesta = leer_cuerpo({'reason'})

    assert datos is None
    assert respuesta[1] == 400
    assert respuesta[0].get_json()['code'] == 'campo_no_permitido'


def test_json_payload_laxo_devuelve_vacio_sin_cuerpo(app):
    with app.test_request_context('/', method='POST'):
        assert json_payload() == {}
    with app.test_request_context('/', method='POST', json={'a': 1}):
        assert json_payload() == {'a': 1}


def test_error_response_sin_code_ni_fields_solo_status_y_message(app):
    with app.app_context():
        respuesta, estado = error_response('Falló.', 409)

    assert estado == 409
    assert respuesta.get_json() == {'status': 'error', 'message': 'Falló.'}


# --------------------------------------------------------------------------- #
# Aviso de usuario creado (D-04)
# --------------------------------------------------------------------------- #

@pytest.fixture
def envios(monkeypatch):
    llamadas = []
    monkeypatch.setattr(services, 'send_notification_by_slug',
                        lambda *a, **k: llamadas.append((a, k)))
    return llamadas


def test_aviso_de_usuario_creado_usa_la_plantilla_y_el_contexto(
        app, envios, monkeypatch):
    monkeypatch.setenv('NOTIFY_USER_CREATED', 'true')

    services.avisar_usuario_creado('a@pruebas.local', 'Ana',
                                   'https://portal.invalid', 'https://x/l')

    (args, kwargs), = envios
    assert args == ('usuario_creado', 'a@pruebas.local')
    assert kwargs['context'] == {
        'nombre': 'Ana', 'usuario': 'a@pruebas.local',
        'base_url': 'https://portal.invalid', 'url': 'https://x/l'}


def test_aviso_de_usuario_creado_url_por_omision_es_la_base(
        app, envios, monkeypatch):
    monkeypatch.setenv('NOTIFY_USER_CREATED', 'true')

    services.avisar_usuario_creado('a@pruebas.local', 'Ana', 'https://b.invalid')

    assert envios[0][1]['context']['url'] == 'https://b.invalid'


def test_aviso_de_usuario_creado_apagado_no_envia(app, envios, monkeypatch):
    monkeypatch.setenv('NOTIFY_USER_CREATED', 'false')

    services.avisar_usuario_creado('a@pruebas.local', 'Ana', 'https://b.invalid')

    assert envios == []


def test_aviso_de_usuario_creado_no_propaga_fallos(app, monkeypatch):
    monkeypatch.setenv('NOTIFY_USER_CREATED', 'true')

    def _explota(*args, **kwargs):
        raise RuntimeError('fallo inesperado')
    monkeypatch.setattr(services, 'send_notification_by_slug', _explota)

    services.avisar_usuario_creado('a@pruebas.local', 'Ana', 'https://b.invalid')


# --------------------------------------------------------------------------- #
# Purga de inactivos (D-05)
# --------------------------------------------------------------------------- #

def _antiguo(usuario, dias, ultimo_acceso=None):
    usuario.created_at = datetime.now() - timedelta(days=dias)
    usuario.last_login_at = ultimo_acceso
    return usuario


def test_purga_elimina_inactivos_incluidos_los_que_nunca_entraron(app):
    nunca = _antiguo(fabricas.crear_usuario(ROLE_USER), 100)
    viejo = _antiguo(fabricas.crear_usuario(ROLE_USER), 100,
                     datetime.now() - timedelta(days=60))
    activo = _antiguo(fabricas.crear_usuario(ROLE_USER), 100,
                      datetime.now() - timedelta(days=1))
    reciente = fabricas.crear_usuario(ROLE_USER)
    db.session.commit()
    ids = {u.email: u.id for u in (nunca, viejo, activo, reciente)}

    purgados = purgar_inactivos(30)

    assert sorted(purgados) == sorted([nunca.email, viejo.email])
    db.session.expire_all()
    assert db.session.get(User, ids[activo.email]) is not None
    assert db.session.get(User, ids[reciente.email]) is not None


def test_purga_nunca_toca_superadmins_y_no_audita_si_no_hay_nadie(app):
    admin = _antiguo(fabricas.crear_usuario(ROLE_ADMIN), 400)
    db.session.commit()

    assert usuarios_inactivos(30).all() == []
    assert purgar_inactivos(30) == []
    assert db.session.get(User, admin.id) is not None


def test_periodo_minimo_de_purga_es_de_siete_dias():
    assert PURGE_MIN_DAYS == 7
