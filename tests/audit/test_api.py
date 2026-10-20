"""Consulta de auditoría por rol e historiales (FNC-060).

Contrato `docs/contratos/auditoria.md`; Anexo A de seguridad: superadmin todo,
admin por área afectada (SEG-16), usuario lo propio (sin `ip`, `before`,
`after`).

Escenario: áreas A y B, plataforma en cada una; `usuario_a` actúa en A y en B
(cuenta compartida, caso SEG-16).
"""

from dataclasses import dataclass
from datetime import datetime

import pytest
from flask import g

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.events import ACTOR_SISTEMA, Evento
from app.modules.audit.models import AuditLog
from app.modules.audit.parametros import (LARGO_MAX_BUSQUEDA, POR_PAGINA_MAX,
                                          RANGO_MAX_DIAS)
from app.modules.auth.models import User
from tests import fabricas

A = '/api/v1'
IP_FICTICIA = 'ip-ficticia-de-prueba'
ESTADO_ANTES = {'status': 'Activo'}
ESTADO_DESPUES = {'status': 'Inactivo'}
ID_INEXISTENTE = 999999


@dataclass
class Escenario:
    cuentas: dict
    area: dict
    plataforma: dict
    evento: dict


def _log(clave, eventos, *, actor=None, user=None, area=None, plataforma=None,
         afectado=None, accion=Evento.PLATAFORMA_EDITADA, status='success',
         target=None, cuando=None):
    registro = AuditLog(
        user=user or (actor.email if actor else ACTOR_SISTEMA),
        actor_id=actor.id if actor else None, action=accion.value,
        status=status, module='Pruebas', target=target or clave,
        ip_address=IP_FICTICIA, area_id=area, platform_id=plataforma,
        target_user_id=afectado.id if afectado else None,
        before_state=ESTADO_ANTES, after_state=ESTADO_DESPUES,
        timestamp=cuando or datetime(2026, 10, 1 + len(eventos), 12, 0, 0))
    db.session.add(registro)
    db.session.commit()
    eventos[clave] = registro.id


@pytest.fixture
def esc(app):
    area_a = fabricas.crear_area('Área A')
    area_b = fabricas.crear_area('Área B')
    plat_a = fabricas.crear_plataforma(area_a, 'Plataforma A')
    plat_b = fabricas.crear_plataforma(area_b, 'Plataforma B')
    cuentas = {
        'superadmin': fabricas.crear_usuario(ROLE_ADMIN),
        'admin_a': fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_a],
                                          areas_administradas=[area_a]),
        'admin_b': fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_b],
                                          areas_administradas=[area_b]),
        'usuario_a': fabricas.crear_usuario(ROLE_USER, areas=[area_a, area_b]),
        'usuario_b': fabricas.crear_usuario(ROLE_USER, areas=[area_b]),
        'admin_sin_areas': fabricas.crear_usuario(ROLE_AREA_ADMIN),
    }
    ua, ub = cuentas['usuario_a'], cuentas['usuario_b']
    ev = {}
    _log('ua_en_a', ev, actor=ua, area=area_a.id, plataforma=plat_a.id,
         accion=Evento.SOLICITUD_CREADA)
    _log('ua_en_b', ev, actor=ua, area=area_b.id, plataforma=plat_b.id,
         accion=Evento.SOLICITUD_CREADA)
    _log('sistema_a_ua', ev, afectado=ua, accion=Evento.ACCESO_ACTIVO,
         status='info')
    _log('ub_en_b', ev, actor=ub, area=area_b.id, plataforma=plat_b.id,
         status='error')
    # Registro anterior a FNC-047: solo el correo, sin actor_id ni área; solo
    # lo ve el superadmin (SEG-060-01).
    _log('heredado_ua', ev, user=ua.email, accion=Evento.AREA_EDITADA)
    return Escenario(cuentas={k: v.id for k, v in cuentas.items()},
                     area={'A': area_a.id, 'B': area_b.id},
                     plataforma={'A': plat_a.id, 'B': plat_b.id}, evento=ev)


@pytest.fixture
def como(esc, cliente_como):
    def _como(nombre):
        # Las peticiones comparten el app context de la prueba: sin esto,
        # Flask-Login reutiliza el usuario de la petición anterior (`g`).
        g.pop('_login_user', None)
        return cliente_como(db.session.get(User, esc.cuentas[nombre]))
    return _como


def _ids(esc, respuesta):
    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    datos = respuesta.get_json()
    items = datos['items'] if isinstance(datos, dict) else datos
    inverso = {v: k for k, v in esc.evento.items()}
    return {inverso[i['id']] for i in items}


def _invalido(respuesta):
    assert respuesta.status_code == 400, respuesta.get_data(as_text=True)
    assert respuesta.get_json()['code'] == 'parametro_invalido'


TODOS = {'ua_en_a', 'ua_en_b', 'sistema_a_ua', 'ub_en_b', 'heredado_ua'}
PROPIOS_UA = {'ua_en_a', 'ua_en_b', 'sistema_a_ua'}


# --------------------------------------------------------------------------- #
# GET /audit: alcance por rol
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor,visibles', [
    ('superadmin', TODOS),
    ('admin_a', {'ua_en_a'}),
    ('admin_b', {'ua_en_b', 'ub_en_b'}),
    ('admin_sin_areas', set()),
    ('usuario_a', PROPIOS_UA),
    ('usuario_b', {'ub_en_b'}),
])
def test_alcance_por_rol(esc, como, actor, visibles):
    assert _ids(esc, como(actor).get(f'{A}/audit')) == visibles


def test_admin_no_ve_eventos_de_otra_area_de_un_usuario_compartido(esc, como):
    """Regresión SEG-16: antes el admin veía todo lo que hacían sus usuarios."""
    ids = _ids(esc, como('admin_a').get(f'{A}/audit'))
    assert 'ua_en_b' not in ids


def test_eventos_sin_area_solo_para_el_superadmin(esc, como):
    for actor in ('admin_a', 'admin_b'):
        ids = _ids(esc, como(actor).get(f'{A}/audit'))
        assert not ids & {'sistema_a_ua', 'heredado_ua'}


def test_usuario_no_recibe_ip_ni_antes_despues(esc, como):
    datos = como('usuario_a').get(f'{A}/audit').get_json()
    assert datos and all(
        (r['ip'], r['before'], r['after']) == (None, None, None) for r in datos)


@pytest.mark.parametrize('actor', ('superadmin', 'admin_a'))
def test_admin_y_superadmin_reciben_ip_y_antes_despues(esc, como, actor):
    datos = como(actor).get(f'{A}/audit').get_json()
    registro = next(r for r in datos if r['id'] == esc.evento['ua_en_a'])
    assert registro['ip'] == IP_FICTICIA
    assert (registro['before'], registro['after']) == (ESTADO_ANTES,
                                                       ESTADO_DESPUES)


# --------------------------------------------------------------------------- #
# Compatibilidad y paginación
# --------------------------------------------------------------------------- #

def test_sin_page_es_arreglo_ordenado_y_respeta_limit(esc, como):
    respuesta = como('superadmin').get(f'{A}/audit?limit=2')
    datos = respuesta.get_json()
    assert isinstance(datos, list) and len(datos) == 2
    assert [r['id'] for r in datos] == [esc.evento['heredado_ua'],
                                        esc.evento['ub_en_b']]


def test_con_page_es_lista_paginada(esc, como):
    respuesta = como('superadmin').get(f'{A}/audit?page=2&per_page=2&limit=1')
    datos = respuesta.get_json()
    assert (datos['page'], datos['per_page'], datos['total']) == (2, 2, 5)
    assert [r['id'] for r in datos['items']] == [esc.evento['sistema_a_ua'],
                                                 esc.evento['ua_en_b']]


def test_paginada_por_defecto(esc, como):
    datos = como('usuario_a').get(f'{A}/audit?page=1').get_json()
    assert (datos['page'], datos['per_page'], datos['total']) == (1, 25, 3)


@pytest.mark.parametrize('consulta', [
    'page=0', 'page=-1', 'page=abc', f'page=1&per_page={POR_PAGINA_MAX + 1}',
    'page=1&per_page=0', 'action=no_existe', 'result=otro', 'area_id=x',
    'platform_id=0', 'user_id=-3', 'from=2026-13-01', 'to=ayer',
    'from=2026-10-05&to=2026-10-01', f'q={"x" * (LARGO_MAX_BUSQUEDA + 1)}',
    'page=1&per_page=9999999999',
])
def test_parametros_invalidos(esc, como, consulta):
    _invalido(como('superadmin').get(f'{A}/audit?{consulta}'))


def test_rango_mayor_al_maximo_es_invalido(esc, como):
    hasta = datetime(2026, 1, 1)
    desde = hasta.replace(year=2024)
    assert (hasta - desde).days > RANGO_MAX_DIAS
    _invalido(como('superadmin').get(
        f'{A}/audit?from={desde.date()}&to={hasta.date()}'))


# --------------------------------------------------------------------------- #
# Filtros
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor,consulta,esperados', [
    ('superadmin', 'action=solicitud_creada', {'ua_en_a', 'ua_en_b'}),
    ('superadmin', 'result=error', {'ub_en_b'}),
    ('superadmin', 'area_id={B}', {'ua_en_b', 'ub_en_b'}),
    ('superadmin', 'platform_id={PA}', {'ua_en_a'}),
    ('superadmin', 'user_id={ua}', PROPIOS_UA),
    ('superadmin', 'q=sistema_a', {'sistema_a_ua'}),
    ('superadmin', 'q=%25', set()),
    ('superadmin', 'from=2026-10-02&to=2026-10-03', {'ua_en_b', 'sistema_a_ua'}),
    ('superadmin', 'to=2026-10-01T12:00:00', {'ua_en_a'}),
    # Fuera de alcance: lista vacía, no error.
    ('admin_a', 'area_id={B}', set()),
    ('admin_a', 'platform_id={PB}', set()),
    ('usuario_b', 'user_id={ua}', set()),
])
def test_filtros(esc, como, actor, consulta, esperados):
    consulta = consulta.format(B=esc.area['B'], PA=esc.plataforma['A'],
                               PB=esc.plataforma['B'],
                               ua=esc.cuentas['usuario_a'])
    assert _ids(esc, como(actor).get(f'{A}/audit?{consulta}')) == esperados


# --------------------------------------------------------------------------- #
# GET /audit/users/<id>
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor,cuenta,esperados', [
    ('superadmin', 'usuario_a', PROPIOS_UA),
    ('admin_a', 'usuario_a', {'ua_en_a'}),
    ('admin_b', 'usuario_a', {'ua_en_b'}),
    ('usuario_a', 'usuario_a', PROPIOS_UA),
    ('admin_a', 'admin_a', set()),
])
def test_historial_de_usuario(esc, como, actor, cuenta, esperados):
    respuesta = como(actor).get(f'{A}/audit/users/{esc.cuentas[cuenta]}')
    assert set(respuesta.get_json()) == {'items', 'page', 'per_page', 'total'}
    assert _ids(esc, respuesta) == esperados


@pytest.mark.parametrize('actor,cuenta', [
    ('usuario_a', 'usuario_b'),
    ('usuario_b', 'admin_b'),
    ('admin_a', 'usuario_b'),
    ('admin_a', 'admin_b'),
    ('admin_a', 'superadmin'),
])
def test_historial_de_usuario_fuera_de_alcance_es_404(esc, como, actor,
                                                      cuenta):
    respuesta = como(actor).get(f'{A}/audit/users/{esc.cuentas[cuenta]}')
    assert respuesta.status_code == 404
    assert respuesta.get_json()['code'] == 'no_encontrado'


def test_historial_de_usuario_inexistente_es_404(esc, como):
    assert como('superadmin').get(
        f'{A}/audit/users/{ID_INEXISTENTE}').status_code == 404


def test_historial_de_usuario_valida_parametros(esc, como):
    _invalido(como('usuario_a').get(
        f"{A}/audit/users/{esc.cuentas['usuario_a']}?per_page=0"))


# --------------------------------------------------------------------------- #
# GET /audit/platforms/<id>
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('actor,plataforma,esperados', [
    ('superadmin', 'B', {'ua_en_b', 'ub_en_b'}),
    ('admin_a', 'A', {'ua_en_a'}),
    ('admin_b', 'B', {'ua_en_b', 'ub_en_b'}),
])
def test_historial_de_plataforma(esc, como, actor, plataforma, esperados):
    respuesta = como(actor).get(
        f'{A}/audit/platforms/{esc.plataforma[plataforma]}?page=1')
    assert _ids(esc, respuesta) == esperados


def test_historial_de_plataforma_de_area_ajena_es_404(esc, como):
    """Contrato y SEC-AUTHZ-04: área ajena = 404 (la ficha decía 403)."""
    respuesta = como('admin_a').get(
        f"{A}/audit/platforms/{esc.plataforma['B']}")
    assert respuesta.status_code == 404


@pytest.mark.parametrize('actor', ('usuario_a', 'usuario_b'))
def test_historial_de_plataforma_usuario_es_403(esc, como, actor):
    respuesta = como(actor).get(f"{A}/audit/platforms/{esc.plataforma['A']}")
    assert respuesta.status_code == 403


def test_historial_de_plataforma_inexistente_es_404(esc, como):
    assert como('superadmin').get(
        f'{A}/audit/platforms/{ID_INEXISTENTE}').status_code == 404


@pytest.mark.parametrize('ruta', ['/audit', '/audit/users/1',
                                  '/audit/platforms/1'])
def test_sin_sesion_es_401(esc, client, ruta):
    assert client.get(f'{A}{ruta}').status_code == 401


# --------------------------------------------------------------------------- #
# Hallazgos de auditor-seguridad
# --------------------------------------------------------------------------- #

def test_correo_reutilizado_no_ve_eventos_de_la_cuenta_borrada(app, como,
                                                              cliente_como):
    """SEG-060-01: al borrar una cuenta, `actor_id` queda en NULL (FK `SET
    NULL`); quien reciba después el mismo correo no ve esos eventos."""
    correo = 'reciclado@pruebas.local'
    anterior = fabricas.crear_usuario(ROLE_USER, email=correo)
    eventos = {}
    _log('de_la_anterior', eventos, actor=anterior, afectado=anterior)
    # Lo que hace la FK en MySQL; SQLite de pruebas no la aplica (fuera del
    # ORM, como `areas/baja.py`).
    db.session.connection().execute(AuditLog.__table__.update()
                       .where(AuditLog.id == eventos['de_la_anterior'])
                       .values(actor_id=None, target_user_id=None))
    db.session.delete(anterior)
    db.session.commit()
    fabricas.crear_usuario(ROLE_USER)  # evita que SQLite reutilice el id
    nueva = fabricas.crear_usuario(ROLE_USER, email=correo)

    g.pop('_login_user', None)
    cliente = cliente_como(nueva)
    assert cliente.get(f'{A}/audit').get_json() == []
    historial = cliente.get(f'{A}/audit/users/{nueva.id}').get_json()
    assert historial['total'] == 0


@pytest.mark.parametrize('consulta', [
    'from=0001-01-01T00:00:00%2B01:00', 'to=9999-12-31',
    'to=9999-12-31T23:59:59.999999',
])
def test_fechas_en_el_limite_no_dan_500(esc, como, consulta):
    """SEG-060-02: OverflowError al convertir o al sumar el día → 400."""
    _invalido(como('superadmin').get(f'{A}/audit?{consulta}'))
