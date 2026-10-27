"""Tema guardado en la cuenta del usuario (FNC-122).

- `PUT /me/preferences` acepta `theme` de la lista de `temas.TEMAS_VALIDOS`.
- `GET /me` lo devuelve en `preferences.theme` ('sistema' si nunca eligió).
- Un valor desconocido responde `422 validacion` con `fields.theme`.
- Cada usuario solo cambia el suyo.
"""

import pytest

from app import db
from app.authz import ROLE_USER
from app.modules.auth.models import User
from app.modules.users.temas import TEMA_POR_DEFECTO, TEMAS_VALIDOS

A = '/api/v1'


def test_lista_de_temas_coincide_con_la_del_frontend():
    assert TEMA_POR_DEFECTO == 'sistema'
    assert set(TEMAS_VALIDOS) == {'sistema', 'claro', 'oscuro', 'esmeralda',
                                  'obsidiana', 'rosa', 'violeta'}


def test_usuario_nuevo_lee_el_tema_por_defecto(cliente_usuario):
    cuerpo = cliente_usuario.get(f'{A}/me').get_json()

    assert cuerpo['preferences']['theme'] == 'sistema'


@pytest.mark.parametrize('tema', sorted(TEMAS_VALIDOS))
def test_guardar_y_leer_el_tema(cliente_de_rol, tema):
    cliente, usuario = cliente_de_rol(ROLE_USER)

    guardado = cliente.put(f'{A}/me/preferences', json={'theme': tema})

    assert guardado.status_code == 200
    assert guardado.get_json()['preferences']['theme'] == tema
    assert cliente.get(f'{A}/me').get_json()['preferences']['theme'] == tema
    db.session.expire_all()
    assert db.session.get(User, usuario.id).pref_theme == tema


@pytest.mark.parametrize('invalido', ['neon', '', 'DARK', 5, None, ['dark']])
def test_tema_desconocido_da_422_y_no_cambia_nada(cliente_de_rol, invalido):
    cliente, usuario = cliente_de_rol(ROLE_USER)
    cliente.put(f'{A}/me/preferences', json={'theme': 'oscuro'})

    respuesta = cliente.put(f'{A}/me/preferences', json={'theme': invalido})

    assert respuesta.status_code == 422, respuesta.get_data(as_text=True)
    cuerpo = respuesta.get_json()
    assert cuerpo['code'] == 'validacion'
    assert 'theme' in cuerpo['fields']
    db.session.expire_all()
    assert db.session.get(User, usuario.id).pref_theme == 'oscuro'


def test_tema_invalido_no_aplica_otras_preferencias_del_mismo_cuerpo(
        cliente_de_rol):
    cliente, usuario = cliente_de_rol(ROLE_USER)

    respuesta = cliente.put(f'{A}/me/preferences',
                            json={'theme': 'neon', 'tour_enabled': False})

    assert respuesta.status_code == 422
    db.session.expire_all()
    assert db.session.get(User, usuario.id).pref_tour_enabled is True


def test_un_usuario_no_cambia_el_tema_de_otro(cliente_de_rol):
    cliente_a, usuario_a = cliente_de_rol(ROLE_USER)
    _, usuario_b = cliente_de_rol(ROLE_USER)

    cliente_a.put(f'{A}/me/preferences',
                  json={'theme': 'violeta', 'user_id': usuario_b.id})

    db.session.expire_all()
    assert db.session.get(User, usuario_a.id).pref_theme == 'violeta'
    assert db.session.get(User, usuario_b.id).pref_theme == 'sistema'


def test_preferencias_sin_tema_no_lo_tocan(cliente_de_rol):
    cliente, usuario = cliente_de_rol(ROLE_USER)
    cliente.put(f'{A}/me/preferences', json={'theme': 'rosa'})

    cliente.put(f'{A}/me/preferences', json={'tour_enabled': False})

    db.session.expire_all()
    assert db.session.get(User, usuario.id).pref_theme == 'rosa'
