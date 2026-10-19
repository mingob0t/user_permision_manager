"""API del directorio (FNC-043): `/auth-config`, su prueba y `/directory/search`.

El directorio corre sobre `ldap3` `MOCK_SYNC` (`tests/directorio_falso.py`):
no hay red. La protección por rol está en la matriz (`matriz_proteccion.py`).
"""

import ldap3
import pytest
from ldap3.operation.search import parse_filter
from sqlalchemy import text

from app import db
from app.modules.audit.models import AuditLog
from app.modules.auth.models import AuthConfig
from app.modules.directory import ldap_client
from tests.directorio_falso import DOMINIO_CORREO, instalar_directorio
from tests.matriz_proteccion import CONTRASENA_FICTICIA, HOST_LDAP_FICTICIO

A = '/api/v1'
CLAVE_EN_BD = 'clave-ldap-heredada-ficticia'
DETALLE_INTERNO = 'detalle-interno-del-servidor-ldap'
HOST_AJENO = 'ldap.ajeno.invalid'


@pytest.fixture
def directorio(app, monkeypatch):
    return instalar_directorio(monkeypatch)


@pytest.fixture
def clave_heredada_en_bd(app):
    """Fila previa a la migración 0004: contraseña de bind guardada en la BD.

    Por SQL directo: el modelo ya no permite escribirla.
    """
    db.session.execute(text(
        'INSERT INTO auth_config (ldap_host, ldap_user, ldap_pass) '
        'VALUES (:host, :usuario, :clave)'),
        {'host': HOST_LDAP_FICTICIO, 'usuario': 'cn=servicio',
         'clave': CLAVE_EN_BD})
    db.session.commit()


def _sin_credenciales(respuesta):
    texto = respuesta.get_data(as_text=True)
    assert CONTRASENA_FICTICIA not in texto
    assert CLAVE_EN_BD not in texto
    assert 'ldap_pass' not in texto
    assert 'password' not in texto.lower()


def _codigo(respuesta):
    return respuesta.get_json().get('code')


# --------------------------------------------------------------------------- #
# GET /auth-config
# --------------------------------------------------------------------------- #

def test_get_sin_directorio_lo_muestra_inactivo(app, cliente_admin):
    respuesta = cliente_admin.get(f'{A}/auth-config')

    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['active'] is False
    assert datos['config'] is None
    assert datos['editable'] is False
    assert datos['source'] == 'env'


def test_get_muestra_la_configuracion_efectiva_y_su_origen(
        directorio, cliente_admin, clave_heredada_en_bd):
    respuesta = cliente_admin.get(f'{A}/auth-config')

    assert respuesta.status_code == 200
    _sin_credenciales(respuesta)
    datos = respuesta.get_json()
    assert datos['active'] is True and datos['error'] is None
    config = datos['config']
    assert config['host'] == HOST_LDAP_FICTICIO
    assert config['tls'] == 'ldaps' and config['port'] == 636
    assert config['ca_cert'] == 'system'
    assert config['user_attr'] == 'uid'
    assert datos['origins']['url'] == 'env'
    assert datos['origins']['user_attr'] == 'default'
    assert datos['variables']['bind_dn'] == 'LDAP_BIND_DN'
    assert 'LDAP_BIND_PASSWORD' not in datos['variables'].values()


def test_get_con_configuracion_invalida_no_expone_el_detalle(
        app, cliente_admin, monkeypatch):
    monkeypatch.setenv('LDAP_URL', f'ldaps://{HOST_LDAP_FICTICIO}')

    respuesta = cliente_admin.get(f'{A}/auth-config')

    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['active'] is True
    assert datos['config'] is None
    assert datos['error'] == 'configuracion_invalida'


# --------------------------------------------------------------------------- #
# PUT /auth-config: sin campos editables (ADR-004)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('cuerpo', [
    {'ldap_pass': CONTRASENA_FICTICIA},
    {'ldap_host': HOST_AJENO},
    {'ldap_host': HOST_AJENO, 'ldap_pass': ''},
    {'bind_password': CONTRASENA_FICTICIA},
    {'url': f'ldaps://{HOST_AJENO}'},
    {'ldap_role_mappings': '{}'},
])
def test_put_rechaza_credenciales_y_cualquier_campo(app, cliente_admin, cuerpo):
    respuesta = cliente_admin.put(f'{A}/auth-config', json=cuerpo)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == 'campo_no_permitido'
    assert AuthConfig.query.count() == 0


def test_put_con_cuerpo_que_no_es_objeto(app, cliente_admin):
    respuesta = cliente_admin.put(f'{A}/auth-config', json=['ldap_pass'])

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == 'cuerpo_invalido'


def test_put_vacio_devuelve_la_configuracion_sin_credencial(
        directorio, cliente_admin):
    respuesta = cliente_admin.put(f'{A}/auth-config', json={})

    assert respuesta.status_code == 200
    _sin_credenciales(respuesta)
    assert respuesta.get_json()['config']['active'] is True


# --------------------------------------------------------------------------- #
# POST /auth-config/test
# --------------------------------------------------------------------------- #

def test_prueba_con_la_configuracion_efectiva(directorio, cliente_admin):
    respuesta = cliente_admin.post(f'{A}/auth-config/test')

    assert respuesta.status_code == 200
    assert respuesta.get_json()['status'] == 'success'
    _sin_credenciales(respuesta)
    assert AuditLog.query.filter_by(action='PRUEBA LDAP',
                                    status='success').count() == 1


def test_prueba_no_acepta_un_host_nuevo_con_la_clave_guardada(
        directorio, cliente_admin, clave_heredada_en_bd):
    """SEG-22: antes se probaba el host del cuerpo con la contraseña guardada."""
    directorio.error = AssertionError('no debe conectar')

    respuesta = cliente_admin.post(f'{A}/auth-config/test',
                                   json={'ldap_host': HOST_AJENO})

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == 'campo_no_permitido'


def test_prueba_sin_directorio_configurado(app, cliente_admin):
    respuesta = cliente_admin.post(f'{A}/auth-config/test')

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == 'directorio_no_configurado'


def test_prueba_fallida_responde_un_mensaje_generico(directorio, cliente_admin):
    """SEG-21: antes devolvía `str(exc)` al cliente."""
    directorio.error = ldap3.core.exceptions.LDAPSocketOpenError(
        f'{DETALLE_INTERNO} {CONTRASENA_FICTICIA}')

    respuesta = cliente_admin.post(f'{A}/auth-config/test')

    assert respuesta.status_code == 503
    assert _codigo(respuesta) == 'directorio_no_disponible'
    texto = respuesta.get_data(as_text=True)
    assert DETALLE_INTERNO not in texto
    _sin_credenciales(respuesta)
    registro = AuditLog.query.filter_by(action='PRUEBA LDAP').one()
    assert registro.status == 'error'
    assert DETALLE_INTERNO not in (registro.detail or '')


# --------------------------------------------------------------------------- #
# GET /directory/search
# --------------------------------------------------------------------------- #

def test_busqueda_por_uid_marca_las_cuentas_existentes(
        directorio, cliente_admin, crear_usuario):
    from app.authz import ROLE_USER
    directorio.agregar('ana.ruiz', CONTRASENA_FICTICIA, nombre='Ana Ruiz')
    directorio.agregar('ana.lopez', CONTRASENA_FICTICIA, nombre='Ana López')
    directorio.agregar('beto', CONTRASENA_FICTICIA)
    crear_usuario(ROLE_USER, email=f'ANA.LOPEZ@{DOMINIO_CORREO}')

    respuesta = cliente_admin.get(f'{A}/directory/search?q=ana')

    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    por_cuenta = {u['account']: u for u in datos['users']}
    assert set(por_cuenta) == {'ana.ruiz', 'ana.lopez'}
    assert datos['count'] == 2
    assert por_cuenta['ana.ruiz'] == {
        'account': 'ana.ruiz', 'name': 'Ana Ruiz',
        'email': f'ana.ruiz@{DOMINIO_CORREO}', 'exists': False}
    assert por_cuenta['ana.lopez']['exists'] is True
    assert '(uid=*ana*)' in directorio.filtros[-1]


@pytest.mark.parametrize('entrada,escapada', [
    ('*)(uid=*', r'\2a\29\28uid=\2a'),
    ('**', r'\2a\2a'),
    ('a)(|(uid=*', r'a\29\28|\28uid=\2a'),
])
def test_busqueda_escapa_la_entrada(directorio, cliente_admin, entrada,
                                    escapada):
    """SEC-LDAP-06. Se revisa el filtro enviado: el `MOCK_SYNC` de `ldap3` no
    sabe comparar valores escapados (el servidor real sí)."""
    cliente_admin.get(f'{A}/directory/search', query_string={'q': entrada})

    filtro = directorio.filtros[-1]
    assert filtro == ('(|' + ''.join(
        f'({atributo}=*{escapada}*)'
        for atributo in ('uid', 'mail', 'cn', 'displayName')) + ')')
    parse_filter(filtro, None, False, False, None, False)  # bien formado


@pytest.mark.parametrize('consulta', ['', 'a', ' a ', 'x' * 65])
def test_busqueda_con_texto_fuera_de_rango(directorio, cliente_admin, consulta):
    respuesta = cliente_admin.get(f'{A}/directory/search',
                                  query_string={'q': consulta})

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == 'parametro_invalido'


def test_busqueda_sin_directorio_configurado(app, cliente_admin):
    respuesta = cliente_admin.get(f'{A}/directory/search?q=ana')

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == 'directorio_no_configurado'


def test_busqueda_fallida_responde_un_mensaje_generico(directorio,
                                                       cliente_admin):
    """SEG-21: antes devolvía `str(exc)` al cliente."""
    directorio.error = ldap3.core.exceptions.LDAPSocketOpenError(
        DETALLE_INTERNO)

    respuesta = cliente_admin.get(f'{A}/directory/search?q=ana')

    assert respuesta.status_code == 503
    assert _codigo(respuesta) == 'directorio_no_disponible'
    assert DETALLE_INTERNO not in respuesta.get_data(as_text=True)


def test_buscar_personas_respeta_el_limite(directorio, monkeypatch):
    """Pide `limite` al servidor y recorta si devuelve más.

    El servidor simulado ignora el límite (el `MOCK_SYNC` no devuelve
    entradas con `sizeLimitExceeded`, el servidor real sí).
    """
    for numero in range(3):
        directorio.agregar(f'persona{numero}', CONTRASENA_FICTICIA)
    pedidos = []
    original = ldap3.Connection.search

    def search(self, *args, size_limit=0, **kwargs):
        pedidos.append(size_limit)
        return original(self, *args, size_limit=0, **kwargs)
    monkeypatch.setattr(ldap3.Connection, 'search', search)

    personas = ldap_client.ClienteDirectorio().buscar_personas('persona',
                                                               limite=2)

    assert pedidos == [2]
    assert len(personas) == 2


# --------------------------------------------------------------------------- #
# Credencial fuera de la BD
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('clave', [CONTRASENA_FICTICIA, ' '])
def test_el_modelo_no_acepta_guardar_la_clave(app, clave):
    with pytest.raises(ValueError):
        AuthConfig(ldap_host=HOST_LDAP_FICTICIO, ldap_pass=clave)


@pytest.mark.parametrize('clave', [None, ''])
def test_el_modelo_acepta_la_clave_vacia(app, clave):
    assert AuthConfig(ldap_pass=clave).ldap_pass is None
