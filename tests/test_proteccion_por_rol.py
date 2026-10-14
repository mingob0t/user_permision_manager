"""Protección por rol de cada endpoint /api/v1 (FNC-020).

- Matriz ruta × método × rol con el código esperado (401/403/2xx).
- Entradas inválidas -> 400 con el formato estándar de error.
- Rol pedido en el cuerpo: solo el superadmin crea o eleva admins (RF-04).

El alcance por área (scoped_*) es FNC-021; aquí todos los datos están dentro
del alcance del actor.
"""

import pytest

from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from tests.matriz_proteccion import (ANONIMO, CASOS, CASOS_400,
                                     CONTRASENA_FICTICIA, ROLES_MATRIZ,
                                     crear_actor, crear_escenario)

CODIGOS_DENEGADOS = (401, 403)


def _cliente(rol, esc, client, cliente_como):
    if rol == ANONIMO:
        return client
    return cliente_como(crear_actor(rol, esc))


def _assert_error_estandar(respuesta):
    datos = respuesta.get_json()
    assert datos is not None, 'El error debe responderse en JSON'
    assert datos.get('status') == 'error'
    assert datos.get('message')


@pytest.mark.parametrize(
    'caso,rol',
    [(caso, rol) for caso in CASOS for rol in ROLES_MATRIZ],
    ids=lambda v: f'{v.metodo} {v.regla}' if hasattr(v, 'metodo') else v,
)
def test_proteccion_por_rol(app, client, cliente_como, monkeypatch, caso, rol):
    esc = crear_escenario()
    cliente = _cliente(rol, esc, client, cliente_como)
    if caso.preparar:
        caso.preparar(esc, monkeypatch)

    respuesta = cliente.open(caso.ruta(esc), method=caso.metodo,
                             **caso.peticion(esc))

    esperado = caso.esperado[rol]
    assert respuesta.status_code == esperado, respuesta.get_data(as_text=True)
    if esperado in CODIGOS_DENEGADOS:
        _assert_error_estandar(respuesta)


@pytest.mark.parametrize('metodo,ruta,peticion', CASOS_400,
                         ids=[f'{m} {r}' for m, r, _ in CASOS_400])
def test_entrada_invalida_devuelve_400(app, cliente_como, metodo, ruta,
                                       peticion):
    esc = crear_escenario()
    cliente = cliente_como(crear_actor(ROLE_ADMIN, esc))

    respuesta = cliente.open(ruta.format(area_id=esc.area_id), method=metodo,
                             **peticion(esc))

    assert respuesta.status_code == 400, respuesta.get_data(as_text=True)
    _assert_error_estandar(respuesta)


_RF04 = pytest.mark.xfail(
    strict=True,
    reason='SEG-20261013-09 / FNC-007: admin_area puede asignar admin_area '
           '(RF-04: solo el superadmin crea o eleva admins)')


@pytest.mark.parametrize('rol,metodo,rol_pedido,esperado', [
    (ROLE_ADMIN, 'POST', ROLE_AREA_ADMIN, 201),
    (ROLE_ADMIN, 'POST', ROLE_ADMIN, 201),
    (ROLE_ADMIN, 'PUT', ROLE_AREA_ADMIN, 200),
    (ROLE_AREA_ADMIN, 'POST', ROLE_USER, 201),
    (ROLE_AREA_ADMIN, 'POST', ROLE_ADMIN, 403),
    (ROLE_AREA_ADMIN, 'PUT', ROLE_ADMIN, 403),
    pytest.param(ROLE_AREA_ADMIN, 'POST', ROLE_AREA_ADMIN, 403, marks=_RF04),
    pytest.param(ROLE_AREA_ADMIN, 'PUT', ROLE_AREA_ADMIN, 403, marks=_RF04),
])
def test_solo_el_superadmin_crea_o_eleva_admins(app, cliente_como, rol, metodo,
                                                rol_pedido, esperado):
    esc = crear_escenario()
    cliente = cliente_como(crear_actor(rol, esc))
    if metodo == 'POST':
        respuesta = cliente.post('/api/v1/users', json={
            'email': 'elevado@pruebas.local', 'role': rol_pedido,
            'area_ids': [esc.area_id], 'password': CONTRASENA_FICTICIA})
    else:
        respuesta = cliente.put(f'/api/v1/users/{esc.objetivo_id}',
                                json={'role': rol_pedido})

    assert respuesta.status_code == esperado, respuesta.get_data(as_text=True)
    if esperado in CODIGOS_DENEGADOS:
        _assert_error_estandar(respuesta)
