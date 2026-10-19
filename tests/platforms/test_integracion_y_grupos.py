"""Plataformas: tipo de integración y grupos del directorio por nivel (FNC-046).

Contrato `docs/contratos/plataformas-integracion.md`. El directorio se simula
con `ldap3` `MOCK_SYNC` (`tests/directorio_falso.py`), sin red.
"""

import pytest
from ldap3.core.exceptions import LDAPSocketOpenError

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.models import AuditLog
from app.modules.core.models import Platform
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 cargar_configuracion)
from app.modules.platforms import api as api_plataformas
from tests import fabricas
from tests.directorio_falso import instalar_directorio
from tests.directory.conftest import ENTORNO_VALIDO, GRUPOS_BASE_DN

A = '/api/v1'
PLANTILLA = 'cn={plataforma}-{nivel},ou={area}'
DN_USUARIO = f'cn=conta-usuario,{GRUPOS_BASE_DN}'
DN_ADMIN = f'cn=conta-admin,{GRUPOS_BASE_DN}'


@pytest.fixture
def area(app):
    return fabricas.crear_area('Finanzas')


@pytest.fixture
def superadmin(cliente_como):
    return cliente_como(fabricas.crear_usuario(ROLE_ADMIN,
                                               email='super@pruebas.local'))


@pytest.fixture
def admin_de_area(cliente_como, area):
    return cliente_como(fabricas.crear_usuario(
        ROLE_AREA_ADMIN, email='luis@pruebas.local',
        areas_administradas=[area]))


@pytest.fixture
def directorio(app, monkeypatch):
    return instalar_directorio(monkeypatch)


def _grupo(directorio, dn):
    directorio._agregar(dn, objectClass='groupOfNames',
                        cn=dn.split(',')[0].split('=')[1],
                        member=['cn=relleno,dc=pruebas,dc=local'])


def _alta(area_id, **campos):
    return {'name': 'Contabilidad', 'description': 'ERP contable',
            'area_id': area_id, 'integration_type': 'ldap', **campos}


def _codigo(respuesta):
    return respuesta.get_json().get('code')


# --------------------------------------------------------------------------- #
# Alta: tipo de integración
# --------------------------------------------------------------------------- #

def test_alta_conector_sin_grupos(superadmin, area):
    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, integration_type='conector',
        direct_link='https://conta.pruebas.local'))

    assert respuesta.status_code == 201, respuesta.get_json()
    datos = respuesta.get_json()
    assert datos['warnings'] == []
    plataforma = datos['platform']
    assert plataforma['integration_type'] == 'conector'
    assert plataforma['ldap_group_user_dn'] is None
    assert plataforma['ldap_group_admin_dn'] is None
    assert plataforma['groups_status'] == 'sin_verificar'
    assert plataforma['has_connector'] is False
    assert plataforma['active_grants'] == 0
    assert 'user_ids' not in plataforma


@pytest.mark.parametrize('cuerpo,campo', [
    ({'integration_type': None}, 'integration_type'),
    ({'integration_type': 'ad'}, 'integration_type'),
    ({'name': 'X'}, 'name'),
    ({'description': ''}, 'description'),
    ({'area_id': 'uno'}, 'area_id'),
    ({'area_id': True}, 'area_id'),
    ({'bg_color': 'x' * 21}, 'bg_color'),
])
def test_alta_con_campo_invalido_responde_422(superadmin, area, cuerpo, campo):
    respuesta = superadmin.post(f'{A}/platforms',
                                json={**_alta(area.id), **cuerpo})

    assert respuesta.status_code == 422, respuesta.get_json()
    assert _codigo(respuesta) == 'validacion'
    assert campo in respuesta.get_json()['fields']
    assert Platform.query.count() == 0


@pytest.mark.parametrize('campo', ['user_ids', 'visits', 'groups_status',
                                   'is_active'])
def test_campo_fuera_de_la_lista_blanca_responde_400(superadmin, area, campo):
    respuesta = superadmin.post(f'{A}/platforms',
                                json=_alta(area.id, **{campo: 1}))

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == 'campo_no_permitido'


def test_cuerpo_que_no_es_objeto_responde_400(superadmin):
    respuesta = superadmin.post(f'{A}/platforms', json=[1])

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == 'cuerpo_invalido'


def test_ldap_con_directorio_inactivo_responde_422(superadmin, area):
    respuesta = superadmin.post(f'{A}/platforms', json=_alta(area.id))

    assert respuesta.status_code == 422
    assert 'integration_type' in respuesta.get_json()['fields']


def test_ldap_sin_grupos_ni_convencion_responde_422(superadmin, area,
                                                    directorio):
    """Criterio: alta `ldap` sin grupos → error de validación (422)."""
    respuesta = superadmin.post(f'{A}/platforms', json=_alta(area.id))

    assert respuesta.status_code == 422
    assert set(respuesta.get_json()['fields']) == {'ldap_group_user_dn',
                                                   'ldap_group_admin_dn'}
    assert Platform.query.count() == 0


# --------------------------------------------------------------------------- #
# Alta: DN de grupos
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('dn', [
    'cn=conta-usuario,ou=otra,dc=pruebas,dc=local',
    GRUPOS_BASE_DN,                                    # la base misma
    f'cn=conta-usuario,ou=grupos,dc=pruebas,dc=otro',
    f'cn=conta-usuario,ou=\\ grupos,dc=pruebas,dc=local',
    'no-es-un-dn',
])
def test_dn_fuera_de_la_base_responde_422(superadmin, area, directorio, dn):
    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, ldap_group_user_dn=dn, ldap_group_admin_dn=DN_ADMIN))

    assert respuesta.status_code == 422, respuesta.get_json()
    assert respuesta.get_json()['fields'] == {
        'ldap_group_user_dn': 'El grupo debe estar en la OU de plataformas.'}
    assert Platform.query.count() == 0


def test_dn_existentes_quedan_ok_sin_avisos(superadmin, area, directorio):
    _grupo(directorio, DN_USUARIO)
    _grupo(directorio, DN_ADMIN)

    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, ldap_group_user_dn=DN_USUARIO, ldap_group_admin_dn=DN_ADMIN))

    assert respuesta.status_code == 201, respuesta.get_json()
    datos = respuesta.get_json()
    assert datos['warnings'] == []
    assert datos['platform']['groups_status'] == 'ok'
    assert datos['platform']['ldap_group_user_dn'] == DN_USUARIO


def test_dn_inexistente_se_guarda_con_aviso(superadmin, area, directorio):
    _grupo(directorio, DN_ADMIN)

    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, ldap_group_user_dn=DN_USUARIO, ldap_group_admin_dn=DN_ADMIN))

    assert respuesta.status_code == 201
    datos = respuesta.get_json()
    assert datos['platform']['groups_status'] == 'no_existe'
    assert datos['warnings'] == [{
        'code': 'grupo_no_existe',
        'message': 'El grupo de nivel usuario no existe en el directorio.'}]


def test_directorio_sin_respuesta_guarda_sin_verificar(superadmin, area,
                                                       directorio):
    directorio.error = LDAPSocketOpenError('sin respuesta')

    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, ldap_group_user_dn=DN_USUARIO, ldap_group_admin_dn=DN_ADMIN))

    assert respuesta.status_code == 201
    datos = respuesta.get_json()
    assert datos['platform']['groups_status'] == 'sin_verificar'
    assert [a['code'] for a in datos['warnings']] == \
        ['directorio_no_disponible']


@pytest.mark.parametrize('dn_admin', [
    DN_USUARIO, DN_USUARIO.upper(), f' {DN_USUARIO} '])
def test_grupos_iguales_responde_409(superadmin, area, directorio, dn_admin):
    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, ldap_group_user_dn=DN_USUARIO, ldap_group_admin_dn=dn_admin))

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == 'grupos_iguales'


def test_conector_no_acepta_grupos(superadmin, area):
    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, integration_type='conector', ldap_group_user_dn=DN_USUARIO))

    assert respuesta.status_code == 422
    assert 'ldap_group_user_dn' in respuesta.get_json()['fields']


@pytest.mark.parametrize('campo', ['ldap_group_user_dn', 'ldap_group_admin_dn'])
def test_admin_de_area_no_define_grupos(admin_de_area, area, directorio,
                                        campo):
    respuesta = admin_de_area.post(f'{A}/platforms',
                                   json=_alta(area.id, **{campo: DN_USUARIO}))

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == 'dn_solo_superadmin'
    assert Platform.query.count() == 0


# --------------------------------------------------------------------------- #
# Derivación por la convención (LDAP_PLATFORM_GROUP_TEMPLATE)
# --------------------------------------------------------------------------- #

def test_admin_de_area_crea_ldap_con_grupos_derivados(admin_de_area, area,
                                                      monkeypatch):
    monkeypatch.setenv('LDAP_PLATFORM_GROUP_TEMPLATE', PLANTILLA)
    instalar_directorio(monkeypatch)

    respuesta = admin_de_area.post(f'{A}/platforms', json=_alta(
        area.id, name='Contabilidad General'))

    assert respuesta.status_code == 201, respuesta.get_json()
    plataforma = respuesta.get_json()['platform']
    assert plataforma['ldap_group_user_dn'] == \
        f'cn=contabilidad-general-usuario,ou=finanzas,{GRUPOS_BASE_DN}'
    assert plataforma['ldap_group_admin_dn'] == \
        f'cn=contabilidad-general-admin,ou=finanzas,{GRUPOS_BASE_DN}'
    assert plataforma['groups_status'] == 'no_existe'


def test_derivacion_no_inyecta_rdn(superadmin, monkeypatch):
    """Caracteres especiales del nombre no agregan RDN ni salen de la base."""
    monkeypatch.setenv('LDAP_PLATFORM_GROUP_TEMPLATE', PLANTILLA)
    instalar_directorio(monkeypatch)
    area = fabricas.crear_area('Área, ou=raiz')

    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        area.id, name='Conta,cn=x+uid=y*'))

    assert respuesta.status_code == 201, respuesta.get_json()
    assert respuesta.get_json()['platform']['ldap_group_user_dn'] == \
        f'cn=conta-cn-x-uid-y-usuario,ou=area-ou-raiz,{GRUPOS_BASE_DN}'


def test_admin_de_area_sin_convencion_no_crea_ldap(admin_de_area, area,
                                                   directorio):
    respuesta = admin_de_area.post(f'{A}/platforms', json=_alta(area.id))

    assert respuesta.status_code == 422
    assert Platform.query.count() == 0


@pytest.mark.parametrize('plantilla', [
    'cn={plataforma}',                     # sin {nivel}
    'cn={nivel}',                          # sin {plataforma}
    'cn={plataforma}-{nivel},ou={otro}',   # marcador desconocido
    'cn={plataforma.x}-{nivel}',           # acceso a atributo
    'cn={plataforma!r}-{nivel}',           # conversión
    'cn={plataforma:>5}-{nivel}',          # formato
    '{plataforma}-{nivel}',                # no es DN
    'cn={plataforma-{nivel}',              # llave sin cerrar
])
def test_plantilla_invalida_detiene_el_arranque(plantilla):
    with pytest.raises(ErrorConfiguracionDirectorio):
        cargar_configuracion({**ENTORNO_VALIDO,
                              'LDAP_PLATFORM_GROUP_TEMPLATE': plantilla})


def test_plantilla_vacia_no_deriva():
    assert cargar_configuracion(dict(ENTORNO_VALIDO)).plantilla_grupo is None


# --------------------------------------------------------------------------- #
# Alcance
# --------------------------------------------------------------------------- #

def test_admin_de_area_en_area_ajena_recibe_404(admin_de_area):
    ajena = fabricas.crear_area('Ajena')

    respuesta = admin_de_area.post(f'{A}/platforms', json=_alta(
        ajena.id, integration_type='conector'))

    assert respuesta.status_code == 404
    assert Platform.query.count() == 0


def test_area_inexistente_responde_404(superadmin):
    respuesta = superadmin.post(f'{A}/platforms', json=_alta(
        99999, integration_type='conector'))

    assert respuesta.status_code == 404


def test_usuario_no_crea_plataformas(cliente_como, area):
    cliente = cliente_como(fabricas.crear_usuario(ROLE_USER, areas=[area]))

    respuesta = cliente.post(f'{A}/platforms', json=_alta(
        area.id, integration_type='conector'))

    assert respuesta.status_code == 403


# --------------------------------------------------------------------------- #
# Edición
# --------------------------------------------------------------------------- #

@pytest.fixture
def plataforma_ldap(area):
    return fabricas.crear_plataforma(
        area, 'Conta', integration_type='ldap',
        ldap_group_user_dn=DN_USUARIO, ldap_group_admin_dn=DN_ADMIN,
        groups_status='ok')


@pytest.fixture
def con_accesos(monkeypatch):
    monkeypatch.setattr(api_plataformas, 'accesos_vigentes', lambda p: 1)


@pytest.mark.parametrize('cambio', [
    {'ldap_group_user_dn': f'cn=otro-usuario,{GRUPOS_BASE_DN}'},
    {'integration_type': 'conector'},
    {'area_id': 'otra'},
])
def test_cambio_de_grupos_tipo_o_area_con_accesos_responde_409(
        superadmin, plataforma_ldap, directorio, con_accesos, cambio):
    """Criterio: cambio de grupos con accesos activos → 409 (FNC-054 aporta
    el conteo; aquí se simula su punto de extensión)."""
    if cambio.get('area_id') == 'otra':
        cambio = {'area_id': fabricas.crear_area('Otra').id}

    respuesta = superadmin.put(f'{A}/platforms/{plataforma_ldap.id}',
                               json=cambio)

    assert respuesta.status_code == 409, respuesta.get_json()
    assert _codigo(respuesta) == 'plataforma_con_accesos'
    db.session.expire_all()
    guardada = db.session.get(Platform, plataforma_ldap.id)
    assert (guardada.integration_type, guardada.ldap_group_user_dn) == \
        ('ldap', DN_USUARIO)


def test_con_accesos_se_editan_otros_campos(superadmin, plataforma_ldap,
                                            con_accesos):
    respuesta = superadmin.put(f'{A}/platforms/{plataforma_ldap.id}', json={
        'description': 'Nueva', 'ldap_group_user_dn': DN_USUARIO,
        'area_id': plataforma_ldap.area_id, 'integration_type': 'ldap'})

    assert respuesta.status_code == 200, respuesta.get_json()


def test_superadmin_cambia_grupo_y_queda_auditado(superadmin, plataforma_ldap,
                                                  directorio):
    nuevo = f'cn=conta2-usuario,{GRUPOS_BASE_DN}'
    _grupo(directorio, nuevo)
    _grupo(directorio, DN_ADMIN)

    respuesta = superadmin.put(f'{A}/platforms/{plataforma_ldap.id}',
                               json={'ldap_group_user_dn': nuevo})

    assert respuesta.status_code == 200, respuesta.get_json()
    assert respuesta.get_json()['platform']['groups_status'] == 'ok'
    registro = AuditLog.query.filter_by(action='plataforma_editada').one()
    assert registro.platform_id == plataforma_ldap.id
    assert registro.before_state == {'ldap_group_user_dn': DN_USUARIO}
    assert registro.after_state == {'ldap_group_user_dn': nuevo}


def test_admin_de_area_no_cambia_grupos(admin_de_area, plataforma_ldap):
    respuesta = admin_de_area.put(f'{A}/platforms/{plataforma_ldap.id}',
                                  json={'ldap_group_admin_dn': DN_USUARIO})

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == 'dn_solo_superadmin'


def test_pasar_a_conector_quita_los_grupos(superadmin, plataforma_ldap):
    respuesta = superadmin.put(f'{A}/platforms/{plataforma_ldap.id}',
                               json={'integration_type': 'conector'})

    assert respuesta.status_code == 200
    plataforma = respuesta.get_json()['platform']
    assert plataforma['integration_type'] == 'conector'
    assert plataforma['ldap_group_user_dn'] is None
    assert plataforma['groups_status'] == 'sin_verificar'


def test_plataforma_heredada_sin_grupos_se_edita(admin_de_area, area):
    """Las plataformas migradas quedan `ldap` sin grupos (0005) y se editan."""
    heredada = fabricas.crear_plataforma(area, 'Heredada')

    respuesta = admin_de_area.put(f'{A}/platforms/{heredada.id}',
                                  json={'description': 'Editada'})

    assert respuesta.status_code == 200, respuesta.get_json()
    assert respuesta.get_json()['platform']['integration_type'] == 'ldap'


def test_admin_de_area_edita_plataforma_ajena_recibe_404(admin_de_area):
    ajena = fabricas.crear_plataforma(fabricas.crear_area('Ajena'))

    respuesta = admin_de_area.put(f'{A}/platforms/{ajena.id}',
                                  json={'description': 'Intrusa'})

    assert respuesta.status_code == 404


# --------------------------------------------------------------------------- #
# Auditoría en la misma transacción (SEC-AUD-06)
# --------------------------------------------------------------------------- #

def test_alta_audita_quien_dio_de_alta(admin_de_area, area, monkeypatch):
    respuesta = admin_de_area.post(f'{A}/platforms', json=_alta(
        area.id, integration_type='conector'))

    assert respuesta.status_code == 201
    registro = AuditLog.query.filter_by(action='plataforma_creada').one()
    assert registro.user == 'luis@pruebas.local'
    assert registro.platform_id == respuesta.get_json()['platform']['id']
    assert registro.area_id == area.id
    assert registro.detail == \
        'admin luis@pruebas.local dio de alta la plataforma Contabilidad'
    assert registro.after_state['integration_type'] == 'conector'


def test_si_falla_la_auditoria_no_se_crea_la_plataforma(superadmin, area,
                                                        monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError('auditoría caída')
    monkeypatch.setattr(api_plataformas, 'add_audit_log', falla)

    with pytest.raises(RuntimeError):
        superadmin.post(f'{A}/platforms', json=_alta(
            area.id, integration_type='conector'))

    db.session.rollback()
    assert Platform.query.count() == 0
