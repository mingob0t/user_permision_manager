"""Cuerpo validado y enlace de bienvenida (FNC-119).

- Los endpoints de escritura que antes de FNC-029 vivían en `crud.py` y
  `admin.py` leen el cuerpo con `leer_cuerpo`: un cuerpo que no es objeto
  responde `400 cuerpo_invalido`, no 500.
- El aviso de bienvenida del login de directorio enlaza a `/login`.
"""

import pytest

from tests.directorio_falso import instalar_directorio
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import iniciar_sesion_api

A = '/api/v1'
CUERPOS_NO_OBJETO = ([1, 2], 'texto', 5)

# (método, ruta con `{area}` / `{usuario}`)
ENDPOINTS = [
    ('PUT', '/areas/{area}/users'),
    ('POST', '/users'),
    ('PUT', '/users/{usuario}'),
    ('POST', '/users/purge'),
    ('PUT', '/me/preferences'),
    ('PUT', '/settings'),
    ('PUT', '/smtp'),
    ('POST', '/smtp/test'),
    ('PUT', '/templates/aviso'),
    ('POST', '/notifications/read'),
]


@pytest.mark.parametrize('cuerpo', CUERPOS_NO_OBJETO)
@pytest.mark.parametrize('metodo,ruta', ENDPOINTS)
def test_cuerpo_que_no_es_objeto_da_400_cuerpo_invalido(
        cliente_admin, crear_area, crear_usuario, metodo, ruta, cuerpo):
    area = crear_area()
    usuario = crear_usuario()
    url = A + ruta.format(area=area.id, usuario=usuario.id)

    respuesta = cliente_admin.open(url, method=metodo, json=cuerpo)

    assert respuesta.status_code == 400, respuesta.get_data(as_text=True)
    assert respuesta.get_json()['code'] == 'cuerpo_invalido'


def test_lista_de_usuarios_de_area_que_no_es_lista_de_enteros_da_400(
        cliente_admin, crear_area):
    area = crear_area()

    respuesta = cliente_admin.put(f'{A}/areas/{area.id}/users',
                                  json={'user_ids': 'todos'})

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'cuerpo_invalido'


def test_cuerpo_objeto_sigue_funcionando(cliente_admin):
    respuesta = cliente_admin.put(f'{A}/settings',
                                  json={'portal_name': 'Portal FNC-119'})

    assert respuesta.status_code == 200


def test_enlace_de_bienvenida_apunta_a_login(app, client, monkeypatch):
    """El alta por login de directorio enlaza a la pantalla vigente."""
    from app.modules.auth import services

    monkeypatch.setenv('BASE_URL', 'https://portal.pruebas.local/')
    avisos = []
    monkeypatch.setattr(services, 'avisar_usuario_creado',
                        lambda *args: avisos.append(args))
    directorio = instalar_directorio(monkeypatch)
    directorio.agregar('jperez', CONTRASENA_FICTICIA, nombre='Juan Pérez')

    respuesta = iniciar_sesion_api(client, 'jperez', CONTRASENA_FICTICIA,
                                   metodo='directory')

    assert respuesta.status_code == 200
    assert len(avisos) == 1
    correo, nombre, base_url, enlace = avisos[0]
    assert base_url == 'https://portal.pruebas.local'
    assert enlace == 'https://portal.pruebas.local/login'


def test_settings_con_logo_valido_guarda_y_da_200(cliente_admin):
    """Regresión de FNC-029: `validar_logo` perdió su `return` y daba 500."""
    logo = ('data:image/png;base64,'
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')

    respuesta = cliente_admin.put(f'{A}/settings', json={
        'portal_identity_type': 'image', 'portal_icon': logo})

    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    assert cliente_admin.get(f'{A}/settings').get_json()['portal_icon'] == logo
