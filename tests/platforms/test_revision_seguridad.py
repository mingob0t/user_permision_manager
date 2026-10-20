"""Regresiones de la revisión de FNC-046 (auditor-seguridad y revisor).

- Media: un DN de grupo no puede pertenecer a dos plataformas (`409
  grupo_en_uso`); el admin de área no cambia el tipo (re-derivaría grupos).
- Baja: URL existentes que no son https se devuelven como null.
- Baja: `validar_url` rechaza credenciales, IP literal y DEL.
- Revisor: un PUT sin cambios no audita.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.models import AuditLog
from app.modules.platforms.validacion import validar_url
from tests import fabricas
from tests.directorio_falso import instalar_directorio
from tests.directory.conftest import GRUPOS_BASE_DN

A = '/api/v1'
DN_USUARIO = f'cn=conta-usuario,{GRUPOS_BASE_DN}'
DN_ADMIN = f'cn=conta-admin,{GRUPOS_BASE_DN}'


@pytest.fixture
def superadmin(cliente_como, app):
    return cliente_como(fabricas.crear_usuario(ROLE_ADMIN))


def _alta(area_id, **campos):
    return {'name': 'Conta', 'description': 'ERP', 'area_id': area_id,
            'integration_type': 'ldap', **campos}


def _con_plantilla(monkeypatch, plantilla):
    monkeypatch.setenv('LDAP_PLATFORM_GROUP_TEMPLATE', plantilla)
    instalar_directorio(monkeypatch)


# --------------------------------------------------------------------------- #
# Media: grupo en uso por otra plataforma
# --------------------------------------------------------------------------- #

def test_nombres_con_el_mismo_identificador_en_areas_distintas(
        superadmin, monkeypatch):
    _con_plantilla(monkeypatch, 'cn={plataforma}-{nivel}')
    a, b = fabricas.crear_area('A'), fabricas.crear_area('B')
    assert superadmin.post(f'{A}/platforms', json=_alta(
        a.id, name='Conta')).status_code == 201

    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        b.id, name='CONTA!'))

    assert respuesta.status_code == 409, respuesta.get_json()
    assert respuesta.get_json()['code'] == 'grupo_en_uso'


def test_area_renombrada_no_reutiliza_grupos(superadmin, monkeypatch):
    _con_plantilla(monkeypatch, 'cn={plataforma}-{nivel},ou={area}')
    finanzas = fabricas.crear_area('Finanzas')
    assert superadmin.post(f'{A}/platforms',
                           json=_alta(finanzas.id)).status_code == 201
    finanzas.name = 'Ventas'
    db.session.commit()
    nueva = fabricas.crear_area('Finanzas')

    respuesta = superadmin.post(f'{A}/platforms', json=_alta(nueva.id))

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'grupo_en_uso'


@pytest.mark.parametrize('dn', [DN_USUARIO, DN_USUARIO.upper()])
def test_dn_enviado_de_otra_plataforma_responde_409(superadmin, monkeypatch,
                                                    dn):
    instalar_directorio(monkeypatch)
    area = fabricas.crear_area()
    fabricas.crear_plataforma(area, 'Dueña', ldap_group_user_dn=DN_USUARIO,
                              ldap_group_admin_dn=DN_ADMIN)

    alta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, name='Otra', ldap_group_user_dn=f'cn=x,{GRUPOS_BASE_DN}',
        ldap_group_admin_dn=dn))
    otra = fabricas.crear_plataforma(area, 'Tercera', integration_type='conector')
    edicion = superadmin.put(f'{A}/platforms/{otra.id}', json={
        'integration_type': 'ldap', 'ldap_group_user_dn': dn,
        'ldap_group_admin_dn': f'cn=y,{GRUPOS_BASE_DN}'})

    assert (alta.status_code, alta.get_json()['code']) == (409, 'grupo_en_uso')
    assert (edicion.status_code, edicion.get_json()['code']) == \
        (409, 'grupo_en_uso')


def test_la_propia_plataforma_conserva_sus_grupos(superadmin, monkeypatch):
    instalar_directorio(monkeypatch)
    plataforma = fabricas.crear_plataforma(
        fabricas.crear_area(), 'Conta', ldap_group_user_dn=DN_USUARIO,
        ldap_group_admin_dn=DN_ADMIN)

    respuesta = superadmin.put(f'{A}/platforms/{plataforma.id}', json={
        'ldap_group_admin_dn': f'cn=conta-admin2,{GRUPOS_BASE_DN}'})

    assert respuesta.status_code == 200, respuesta.get_json()


def test_admin_de_area_no_cambia_el_tipo_ida_y_vuelta(cliente_como,
                                                      monkeypatch):
    _con_plantilla(monkeypatch, 'cn={plataforma}-{nivel}')
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(
        area, 'Conta', ldap_group_user_dn=DN_USUARIO,
        ldap_group_admin_dn=DN_ADMIN)
    admin = cliente_como(fabricas.crear_usuario(
        ROLE_AREA_ADMIN, areas_administradas=[area]))

    ida = admin.put(f'{A}/platforms/{plataforma.id}',
                    json={'integration_type': 'conector'})

    assert (ida.status_code, ida.get_json()['code']) == \
        (403, 'dn_solo_superadmin')
    db.session.expire_all()
    assert plataforma.ldap_group_user_dn == DN_USUARIO


def test_superadmin_ida_y_vuelta_rederiva(superadmin, monkeypatch):
    _con_plantilla(monkeypatch, 'cn={plataforma}-{nivel}')
    area = fabricas.crear_area()
    alta = superadmin.post(f'{A}/platforms', json=_alta(area.id))
    pid = alta.get_json()['platform']['id']

    ida = superadmin.put(f'{A}/platforms/{pid}',
                         json={'integration_type': 'conector'})
    vuelta = superadmin.put(f'{A}/platforms/{pid}',
                            json={'integration_type': 'ldap'})

    assert (ida.status_code, vuelta.status_code) == (200, 200)
    assert vuelta.get_json()['platform']['ldap_group_user_dn'] == \
        f'cn=conta-usuario,{GRUPOS_BASE_DN}'


# --------------------------------------------------------------------------- #
# Baja: URL guardadas antes de FNC-046
# --------------------------------------------------------------------------- #

@pytest.fixture
def plataforma_heredada(app):
    area = fabricas.crear_area()
    return fabricas.crear_plataforma(
        area, direct_link='javascript:alert(1)', logo_url='http://x.local/l.png')


def test_url_heredada_no_https_sale_null_en_el_listado(cliente_como,
                                                        plataforma_heredada):
    cuenta = fabricas.crear_usuario(ROLE_USER, areas=[plataforma_heredada.area])
    # FNC-063: el usuario ve la plataforma por un acceso activo.
    fabricas.crear_acceso(cuenta, plataforma_heredada)
    usuario = cliente_como(cuenta)

    listado = usuario.get(f'{A}/platforms').get_json()

    assert (listado[0]['direct_link'], listado[0]['logo_url']) == (None, None)


def test_url_heredada_no_https_sale_null_en_to_dict(superadmin,
                                                     plataforma_heredada):
    edicion = superadmin.put(f'{A}/platforms/{plataforma_heredada.id}',
                             json={'description': 'Nueva'})

    assert edicion.status_code == 200, edicion.get_json()
    datos = edicion.get_json()['platform']
    assert (datos['direct_link'], datos['logo_url']) == (None, None)


# --------------------------------------------------------------------------- #
# Baja: validar_url
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('url', [
    'https://usuario:clave@pruebas.local/',
    'https://usuario@pruebas.local/',
    'https://[2001:db8::1]/',
    'https://0x7f.1/',
    'https://2130706433/',
    'https://127.1/',
    'https://pruebas.local/\x7f',
])
def test_validar_url_rechaza(url):
    assert validar_url(url)[1] is not None


def test_validar_url_acepta_https_con_nombre():
    assert validar_url('https://portal.pruebas.local:8443/ruta?q=1') == \
        ('https://portal.pruebas.local:8443/ruta?q=1', None)


# --------------------------------------------------------------------------- #
# Revisor: PUT sin cambios no audita
# --------------------------------------------------------------------------- #

def test_put_sin_cambios_no_audita(superadmin):
    plataforma = fabricas.crear_plataforma(fabricas.crear_area(), 'Igual',
                                           descripcion='Misma')

    respuesta = superadmin.put(f'{A}/platforms/{plataforma.id}',
                               json={'description': 'Misma'})

    assert respuesta.status_code == 200
    assert AuditLog.query.filter_by(action='plataforma_editada').count() == 0
