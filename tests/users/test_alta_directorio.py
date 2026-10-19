"""Alta de cuentas en OpenLDAP desde el portal (FNC-064).

Contrato `POST /users/directory` (`docs/contratos/usuarios-directorio.md`):
- P2: superadmin y admins (solo sus áreas, solo rol `usuario`).
- P8: sin contraseña; `password` → `400 campo_no_permitido` (regresión SEG-02).
- 409 por uid o correo duplicados (directorio o portal); 503 si el directorio
  falla, sin crear nada en la BD; fallo parcial auditado.

La matriz por rol (401/403/201) está en `tests/matriz_proteccion.py`.
"""

import pytest
from ldap3 import ALL_ATTRIBUTES, BASE
from ldap3.core.exceptions import LDAPNoSuchObjectResult, LDAPSocketOpenError

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.directory import ldap_client
from app.modules.users import directory_accounts
from tests import fabricas
from tests.directorio_falso import instalar_directorio
from tests.directory.conftest import dn_persona

URL = '/api/v1/users/directory'
EVENTO = 'cuenta_directorio_creada'


@pytest.fixture
def escena(app):
    area_a = fabricas.crear_area('Área A')
    area_b = fabricas.crear_area('Área B')
    return {
        'A': area_a.id,
        'B': area_b.id,
        'super': fabricas.crear_usuario(ROLE_ADMIN),
        'admin_a': fabricas.crear_usuario(ROLE_AREA_ADMIN, areas=[area_a],
                                          areas_administradas=[area_a]),
    }


@pytest.fixture
def directorio(monkeypatch, app):
    return instalar_directorio(monkeypatch)


def _cuerpo(**cambios):
    datos = {'uid': 'ana.ruiz', 'email': 'ana@pruebas.local',
             'given_name': 'Ana', 'surname': 'Ruiz', 'area_ids': []}
    datos.update(cambios)
    return datos


def _entrada(directorio, uid):
    """Atributos de la entrada `uid=<uid>` del directorio, o `None`."""
    with ldap_client.ClienteDirectorio().conexion_servicio() as conexion:
        try:
            conexion.search(dn_persona(uid), '(objectClass=*)', BASE,
                            attributes=ALL_ATTRIBUTES)
        except LDAPNoSuchObjectResult:
            return None
        if not conexion.entries:
            return None
        return conexion.entries[0].entry_attributes_as_dict


def _cuenta(correo):
    db.session.expire_all()
    return User.query.filter_by(email=correo).first()


def _error(respuesta, http, code):
    assert respuesta.status_code == http, respuesta.get_data(as_text=True)
    datos = respuesta.get_json()
    assert datos['status'] == 'error' and datos['message']
    assert datos['code'] == code
    return datos


def _eventos(status=None):
    consulta = AuditLog.query.filter_by(action=EVENTO)
    if status:
        consulta = consulta.filter_by(status=status)
    return consulta.order_by(AuditLog.id).all()


# --------------------------------------------------------------------------- #
# Alta correcta
# --------------------------------------------------------------------------- #

def test_superadmin_crea_la_entrada_y_la_cuenta_sin_contrasena(
        escena, directorio, cliente_como):
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(area_ids=[escena['B']]))

    assert respuesta.status_code == 201, respuesta.get_data(as_text=True)
    datos = respuesta.get_json()
    assert datos['status'] == 'success'
    usuario = datos['user']
    assert usuario['email'] == 'ana@pruebas.local'
    assert usuario['name'] == 'Ana Ruiz'
    assert usuario['role'] == ROLE_USER
    assert usuario['auth_source'] == 'ldap'
    assert usuario['is_active'] is True
    assert usuario['areas'] == [{'id': escena['B'], 'name': 'Área B'}]
    assert usuario['managed_areas'] == []
    assert usuario['last_login_at'] is None

    entrada = _entrada(directorio, 'ana.ruiz')
    assert entrada is not None
    assert entrada['mail'] == ['ana@pruebas.local']
    assert entrada['givenName'] == ['Ana'] and entrada['sn'] == ['Ruiz']
    assert 'userPassword' not in entrada

    cuenta = _cuenta('ana@pruebas.local')
    assert cuenta.auth_source == 'ldap'
    assert cuenta.password_hash is None


def test_el_alta_se_audita_con_el_actor(escena, directorio, cliente_como):
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())
    assert respuesta.status_code == 201
    cuenta = _cuenta('ana@pruebas.local')

    [evento] = _eventos('success')
    assert evento.actor_id == escena['super'].id
    assert evento.user == escena['super'].email
    assert evento.target_user_id == cuenta.id
    assert evento.after_state['uid'] == 'ana.ruiz'
    assert evento.after_state['auth_source'] == 'ldap'
    assert 'password' not in str(evento.after_state)


def test_admin_de_area_crea_en_su_area(escena, directorio, cliente_como):
    respuesta = cliente_como(escena['admin_a']).post(
        URL, json=_cuerpo(area_ids=[escena['A']]))

    assert respuesta.status_code == 201, respuesta.get_data(as_text=True)
    assert respuesta.get_json()['user']['role'] == ROLE_USER
    assert [a.id for a in _cuenta('ana@pruebas.local').areas] == [escena['A']]
    assert _entrada(directorio, 'ana.ruiz') is not None


def test_superadmin_puede_crear_sin_areas(escena, directorio, cliente_como):
    respuesta = cliente_como(escena['super']).post(
        URL, json={k: v for k, v in _cuerpo().items() if k != 'area_ids'})
    assert respuesta.status_code == 201
    assert respuesta.get_json()['user']['areas'] == []


# --------------------------------------------------------------------------- #
# Permisos (P2)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('areas', [['B'], ['A', 'B'], [999]])
def test_admin_con_area_ajena_o_inexistente_recibe_404(
        escena, directorio, cliente_como, areas):
    ids = [escena[a] if isinstance(a, str) else a for a in areas]
    respuesta = cliente_como(escena['admin_a']).post(
        URL, json=_cuerpo(area_ids=ids))

    _error(respuesta, 404, 'no_encontrado')
    assert _entrada(directorio, 'ana.ruiz') is None
    assert _cuenta('ana@pruebas.local') is None


@pytest.mark.parametrize('cuerpo', [
    _cuerpo(area_ids=[]),
    {k: v for k, v in _cuerpo().items() if k != 'area_ids'},
])
def test_admin_debe_indicar_al_menos_un_area(escena, directorio,
                                             cliente_como, cuerpo):
    respuesta = cliente_como(escena['admin_a']).post(URL, json=cuerpo)
    datos = _error(respuesta, 422, 'validacion')
    assert 'area_ids' in datos['fields']
    assert _entrada(directorio, 'ana.ruiz') is None


def test_superadmin_con_area_inexistente_recibe_422(escena, directorio,
                                                    cliente_como):
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(area_ids=[999]))
    assert 'area_ids' in _error(respuesta, 422, 'validacion')['fields']


def test_usuario_normal_recibe_403(escena, directorio, cliente_como):
    usuario = fabricas.crear_usuario(ROLE_USER)
    respuesta = cliente_como(usuario).post(URL, json=_cuerpo())
    assert respuesta.status_code == 403
    assert _entrada(directorio, 'ana.ruiz') is None


# --------------------------------------------------------------------------- #
# Lista blanca y contraseña (P8, regresión SEG-02)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('campo, valor', [
    ('password', 'clave-ficticia'),
    ('role', ROLE_AREA_ADMIN),
    ('role', ROLE_USER),
    ('auth_source', 'local'),
    ('password_hash', 'x'),
    ('is_active', False),
    ('managed_area_ids', [1]),
    ('desconocido', 1),
])
def test_campos_fuera_de_la_lista_blanca_dan_400(escena, directorio,
                                                 cliente_como, campo, valor):
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(**{campo: valor}))
    _error(respuesta, 400, 'campo_no_permitido')
    assert _entrada(directorio, 'ana.ruiz') is None
    assert _cuenta('ana@pruebas.local') is None


@pytest.mark.parametrize('cuerpo', [[1, 2], 'texto', 3])
def test_cuerpo_que_no_es_objeto_da_400(escena, directorio, cliente_como,
                                        cuerpo):
    respuesta = cliente_como(escena['super']).post(URL, json=cuerpo)
    _error(respuesta, 400, 'cuerpo_invalido')


# --------------------------------------------------------------------------- #
# Validación
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('campo, valor', [
    ('uid', 'Ana'),            # mayúsculas
    ('uid', 'ab'),             # corto
    ('uid', 'a' * 65),         # largo
    ('uid', '1ana'),           # primer carácter
    ('uid', 'ana*'),           # comodín de filtro
    ('uid', 'a)(uid=*'),       # inyección de filtro
    ('uid', 'ana,ou=x'),       # inyección de DN
    ('uid', 'ana ruiz'),
    ('uid', 5),
    ('uid', ''),
    ('email', 'sin-arroba'),
    ('email', 'a@b'),
    ('email', 'a' * 120 + '@pruebas.local'),
    ('email', None),
    ('given_name', ''),
    ('given_name', '   '),
    ('given_name', 'A' * 101),
    ('given_name', 'Ana\nRuiz'),
    ('surname', ''),
    ('surname', 'R' * 101),
    ('surname', ['Ruiz']),
    ('area_ids', 'uno'),
    ('area_ids', [True]),
])
def test_valores_invalidos_dan_422_sin_escribir(escena, directorio,
                                                cliente_como, campo, valor):
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(**{campo: valor}))
    datos = _error(respuesta, 422, 'validacion')
    assert campo in datos['fields']
    # Ninguna conexión al directorio: se valida antes de escribir.
    assert directorio.filtros == []


def test_faltan_campos_obligatorios(escena, directorio, cliente_como):
    respuesta = cliente_como(escena['super']).post(URL, json={})
    datos = _error(respuesta, 422, 'validacion')
    assert set(datos['fields']) == {'uid', 'email', 'given_name', 'surname'}


def test_uid_con_punto_guion_y_guion_bajo_se_acepta(escena, directorio,
                                                    cliente_como):
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(uid='ana.ruiz-2_b'))
    assert respuesta.status_code == 201
    assert _entrada(directorio, 'ana.ruiz-2_b') is not None


def test_correo_se_normaliza_a_minusculas(escena, directorio, cliente_como):
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(email='  Ana@Pruebas.Local '))
    assert respuesta.status_code == 201
    assert respuesta.get_json()['user']['email'] == 'ana@pruebas.local'


# --------------------------------------------------------------------------- #
# Duplicados (409)
# --------------------------------------------------------------------------- #

def test_uid_existente_en_el_directorio_da_409(escena, directorio,
                                               cliente_como):
    directorio.agregar('ana.ruiz', 'clave', correo='otra@pruebas.local')
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())

    _error(respuesta, 409, 'uid_duplicado')
    assert _cuenta('ana@pruebas.local') is None
    assert _entrada(directorio, 'ana.ruiz')['mail'] == ['otra@pruebas.local']


def test_correo_existente_en_el_portal_da_409_sin_tocar_el_directorio(
        escena, directorio, cliente_como):
    fabricas.crear_usuario(ROLE_USER, email='ana@pruebas.local')
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())

    _error(respuesta, 409, 'correo_duplicado')
    assert directorio.filtros == []
    assert _entrada(directorio, 'ana.ruiz') is None


def test_correo_existente_en_el_portal_sin_distinguir_mayusculas(
        escena, directorio, cliente_como):
    fabricas.crear_usuario(ROLE_USER, email='Ana@Pruebas.local')
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())
    _error(respuesta, 409, 'correo_duplicado')


def test_correo_existente_en_el_directorio_da_409(escena, directorio,
                                                  cliente_como):
    directorio.agregar('otra.persona', 'clave', correo='ana@pruebas.local')
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())

    _error(respuesta, 409, 'correo_duplicado')
    assert _entrada(directorio, 'ana.ruiz') is None
    assert _cuenta('ana@pruebas.local') is None


def test_correo_del_directorio_se_busca_escapado(escena, directorio,
                                                 cliente_como):
    directorio.agregar('otra.persona', 'clave', correo='ana@pruebas.local')
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(email='*@pruebas.local'))
    # El comodín se busca literal: no coincide con `ana@pruebas.local`.
    assert respuesta.status_code == 201, respuesta.get_data(as_text=True)
    assert any('\\2a' in filtro for filtro in directorio.filtros)


@pytest.mark.parametrize('uid', ['admin'])
def test_uid_reservado_o_de_cuenta_heredada_da_409(escena, directorio,
                                                   cliente_como, uid):
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo(uid=uid))
    _error(respuesta, 409, 'uid_duplicado')
    assert _entrada(directorio, uid) is None


def test_uid_igual_al_identificador_de_una_cuenta_heredada_da_409(
        escena, directorio, cliente_como):
    fabricas.crear_usuario(ROLE_USER, email='heredado')
    respuesta = cliente_como(escena['super']).post(
        URL, json=_cuerpo(uid='heredado'))
    _error(respuesta, 409, 'uid_duplicado')


def test_segunda_alta_igual_da_409(escena, directorio, cliente_como):
    cliente = cliente_como(escena['super'])
    assert cliente.post(URL, json=_cuerpo()).status_code == 201
    _error(cliente.post(URL, json=_cuerpo()), 409, 'correo_duplicado')
    _error(cliente.post(URL, json=_cuerpo(email='otra@pruebas.local')), 409,
           'uid_duplicado')
    assert User.query.filter_by(auth_source='ldap').count() == 1


# --------------------------------------------------------------------------- #
# Fallos del directorio y fallo parcial
# --------------------------------------------------------------------------- #

def test_directorio_no_disponible_da_503_sin_crear_nada(escena, directorio,
                                                        cliente_como):
    directorio.error = LDAPSocketOpenError('detalle interno ldap.servidor')
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())

    datos = _error(respuesta, 503, 'directorio_no_disponible')
    assert 'ldap' not in datos['message'].lower()
    assert _cuenta('ana@pruebas.local') is None
    [evento] = _eventos('error')
    assert evento.actor_id == escena['super'].id


def test_directorio_no_configurado_da_503(escena, cliente_como):
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())
    _error(respuesta, 503, 'directorio_no_disponible')
    assert _cuenta('ana@pruebas.local') is None


def test_fallo_al_escribir_en_el_directorio_da_503(escena, directorio,
                                                   cliente_como, monkeypatch):
    from app.modules.directory.errors import Resultado, ResultadoEscritura
    from app.modules.directory.writer import EscritorDirectorio
    monkeypatch.setattr(
        EscritorDirectorio, 'create_user',
        lambda self, datos: ResultadoEscritura(Resultado.ERROR_PERMANENTE,
                                               'uid=x', 'directorio'))
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())

    _error(respuesta, 503, 'directorio_no_disponible')
    assert _cuenta('ana@pruebas.local') is None
    assert len(_eventos('error')) == 1


def test_fallo_parcial_deshace_la_bd_audita_y_responde_generico(
        escena, directorio, cliente_como, monkeypatch):
    from sqlalchemy.exc import OperationalError

    def _falla(alta):
        raise OperationalError('INSERT', {}, Exception('detalle interno'))

    monkeypatch.setattr(directory_accounts, '_crear_en_portal', _falla)
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())

    datos = _error(respuesta, 500, 'error_interno')
    assert 'detalle' not in datos['message']
    # La entrada quedó en el directorio (sin borrado en v1) y la BD no.
    assert _entrada(directorio, 'ana.ruiz') is not None
    assert _cuenta('ana@pruebas.local') is None
    [evento] = _eventos('warning')
    assert evento.actor_id == escena['super'].id
    assert 'registro_en_portal_fallido' in evento.detail


def test_fallo_parcial_real_en_el_commit(escena, directorio, cliente_como,
                                         monkeypatch):
    """El `commit` de la cuenta falla: no queda la cuenta ni su auditoría."""
    from sqlalchemy.exc import OperationalError
    original = db.session.commit
    llamadas = {'n': 0}

    def _commit_que_falla_una_vez():
        llamadas['n'] += 1
        if llamadas['n'] == 1:
            raise OperationalError('COMMIT', {}, Exception('detalle'))
        return original()

    monkeypatch.setattr(directory_accounts, '_crear_en_portal',
                        _envolver_commit(_commit_que_falla_una_vez,
                                         monkeypatch))
    respuesta = cliente_como(escena['super']).post(URL, json=_cuerpo())

    _error(respuesta, 500, 'error_interno')
    assert _cuenta('ana@pruebas.local') is None
    assert _eventos('success') == []
    assert len(_eventos('warning')) == 1


def _envolver_commit(commit_falso, monkeypatch):
    """`_crear_en_portal` real, con `db.session.commit` reemplazado."""
    real = directory_accounts._crear_en_portal

    def _crear(alta):
        with monkeypatch.context() as m:
            m.setattr(db.session, 'commit', commit_falso)
            return real(alta)
    return _crear
