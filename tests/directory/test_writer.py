"""Escritura en OpenLDAP: membresía de grupos y alta de cuentas (FNC-041).

`ldap3` corre con `MOCK_SYNC` (ver `conftest.py`): sin red. Los errores del
servidor se simulan sustituyendo la operación de `ldap3.Connection`.
"""

import inspect

import ldap3
import pytest
from ldap3.core import exceptions as exc_ldap

from app.modules.directory import errors, ldap_client, writer
from app.modules.directory.errors import Resultado, clasificar_error
from app.modules.directory.ldap_client import UsuarioDirectorio
from app.modules.directory.writer import DatosCuenta, EscritorDirectorio
from tests.directory.conftest import (BASE_DN, GRUPOS_BASE_DN,
                                      USUARIOS_BASE_DN, dn_grupo, dn_persona)

RELLENO = f'cn=sin-miembros,{BASE_DN}'


def _usuario(uid):
    return UsuarioDirectorio(dn=dn_persona(uid), identificador=uid)


def _entrada(directorio, dn, atributos=('*',)):
    with directorio.cliente.conexion_servicio() as conexion:
        conexion.search(dn, '(objectClass=*)', ldap3.BASE,
                        attributes=list(atributos))
        return conexion.entries[0] if conexion.entries else None


def _miembros(directorio, dn, atributo='member'):
    entrada = _entrada(directorio, dn, (atributo,))
    if entrada is None or atributo not in entrada:
        return []
    return list(entrada[atributo].values)


@pytest.fixture
def escritor(directorio):
    return EscritorDirectorio(directorio.cliente)


@pytest.fixture
def operaciones(monkeypatch):
    """Doble que registra cada `modify`, `add` y `delete` (SEC-LDAP-07)."""
    registro = []
    for nombre in ('modify', 'add', 'delete'):
        original = getattr(ldap3.Connection, nombre)

        def envoltura(self, *args, _nombre=nombre, _original=original, **kw):
            registro.append((_nombre, self.read_only, args, kw))
            return _original(self, *args, **kw)

        monkeypatch.setattr(ldap3.Connection, nombre, envoltura)
    return registro


def _fallar(monkeypatch, operacion, excepcion):
    def falla(self, *args, **kwargs):
        raise excepcion

    monkeypatch.setattr(ldap3.Connection, operacion, falla)


# --------------------------------------------------------------------------- #
# Agregar miembro
# --------------------------------------------------------------------------- #

def test_agregar_miembro_lo_agrega_con_conexion_de_escritura(
        directorio, escritor, operaciones):
    directorio.persona('ana')
    directorio.persona('beto')
    grupo = directorio.grupo('conta-usuario', [dn_persona('beto')])

    resultado = escritor.add_member(grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.HECHO
    assert resultado.exito is True
    assert resultado.dn == grupo
    assert dn_persona('ana') in _miembros(directorio, grupo)
    assert operaciones == [('modify', False, (grupo, {
        'member': [(ldap3.MODIFY_ADD, [dn_persona('ana')])]}), {})]


def test_agregar_dos_veces_es_idempotente(directorio, escritor, operaciones):
    directorio.persona('ana')
    grupo = directorio.grupo('conta-usuario', [dn_persona('ana')])

    primero = escritor.add_member(grupo, _usuario('ana'))
    segundo = escritor.add_member(grupo, _usuario('ana'))

    assert primero.resultado is Resultado.YA_ESTABA
    assert segundo.resultado is Resultado.YA_ESTABA
    assert primero.exito is True
    assert operaciones == []
    assert _miembros(directorio, grupo) == [dn_persona('ana')]


def test_agregar_compara_el_dn_sin_distinguir_mayusculas(directorio, escritor,
                                                        operaciones):
    directorio.persona('ana')
    guardado = f'UID=ana,OU=Personas,{BASE_DN.upper()}'
    grupo = directorio.grupo('conta-usuario', [guardado])

    resultado = escritor.add_member(grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.YA_ESTABA
    assert operaciones == []


def test_agregar_cuando_el_servidor_dice_que_ya_existe_es_ya_estaba(
        directorio, escritor, monkeypatch):
    directorio.persona('ana')
    grupo = directorio.grupo('conta-usuario', [dn_persona('ana')])
    # Carrera: otro proceso lo agregó entre la lectura y la escritura.
    monkeypatch.setattr(writer, '_valores_miembro', lambda *a: [])
    _fallar(monkeypatch, 'modify', exc_ldap.LDAPAttributeOrValueExistsResult())

    resultado = escritor.add_member(grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.YA_ESTABA


def test_agregar_a_grupo_inexistente_es_no_existe(directorio, escritor,
                                                  operaciones):
    directorio.persona('ana')

    resultado = escritor.add_member(dn_grupo('no-hay'), _usuario('ana'))

    assert resultado.resultado is Resultado.NO_EXISTE
    assert resultado.motivo == errors.MOTIVO_GRUPO_INEXISTENTE
    assert resultado.reintentable is False
    assert operaciones == []


def test_agregar_usuario_inexistente_es_no_existe(directorio, escritor,
                                                  operaciones):
    grupo = directorio.grupo('conta-usuario', [dn_persona('beto')])

    resultado = escritor.add_member(grupo, _usuario('fantasma'))

    assert resultado.resultado is Resultado.NO_EXISTE
    assert resultado.motivo == errors.MOTIVO_USUARIO_INEXISTENTE
    assert operaciones == []


def test_agregar_con_member_uid_usa_el_identificador(crear_directorio,
                                                    operaciones):
    directorio = crear_directorio(LDAP_GROUP_OBJECT_CLASS='posixGroup',
                                  LDAP_GROUP_MEMBER_ATTR='memberUid')
    directorio.persona('ana')
    grupo = directorio.grupo('conta-usuario', [], clase='posixGroup',
                             atributo='memberUid')

    resultado = EscritorDirectorio(directorio.cliente).add_member(
        grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.HECHO
    assert _miembros(directorio, grupo, 'memberUid') == ['ana']


# --------------------------------------------------------------------------- #
# Quitar miembro
# --------------------------------------------------------------------------- #

def test_quitar_miembro_lo_quita_y_dos_veces_es_idempotente(
        directorio, escritor, operaciones):
    directorio.persona('ana')
    directorio.persona('beto')
    grupo = directorio.grupo('conta-usuario',
                             [dn_persona('ana'), dn_persona('beto')])

    primero = escritor.remove_member(grupo, _usuario('ana'))
    segundo = escritor.remove_member(grupo, _usuario('ana'))

    assert primero.resultado is Resultado.HECHO
    assert segundo.resultado is Resultado.YA_ESTABA
    assert segundo.exito is True
    assert _miembros(directorio, grupo) == [dn_persona('beto')]
    assert operaciones == [('modify', False, (grupo, {
        'member': [(ldap3.MODIFY_DELETE, [dn_persona('ana')])]}), {})]


def test_quitar_usa_el_valor_tal_como_esta_guardado(directorio, escritor,
                                                    operaciones):
    guardado = f'UID=ana,OU=Personas,{BASE_DN.upper()}'
    grupo = directorio.grupo('conta-usuario', [guardado, dn_persona('beto')])

    resultado = escritor.remove_member(grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.HECHO
    assert operaciones[0][2][1] == {
        'member': [(ldap3.MODIFY_DELETE, [guardado])]}


def test_quitar_cuando_el_servidor_dice_que_no_esta_es_ya_estaba(
        directorio, escritor, monkeypatch):
    grupo = directorio.grupo('conta-usuario',
                             [dn_persona('ana'), dn_persona('beto')])
    _fallar(monkeypatch, 'modify', exc_ldap.LDAPNoSuchAttributeResult())

    resultado = escritor.remove_member(grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.YA_ESTABA


def test_quitar_de_grupo_inexistente_es_no_existe(escritor):
    resultado = escritor.remove_member(dn_grupo('no-hay'), _usuario('ana'))

    assert resultado.resultado is Resultado.NO_EXISTE


def test_quitar_ultimo_miembro_sin_relleno_no_deja_el_grupo_vacio(
        directorio, escritor, operaciones):
    grupo = directorio.grupo('conta-usuario', [dn_persona('ana')])

    resultado = escritor.remove_member(grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.ERROR_PERMANENTE
    assert resultado.motivo == errors.MOTIVO_ULTIMO_MIEMBRO
    assert operaciones == []
    assert _miembros(directorio, grupo) == [dn_persona('ana')]


def test_quitar_ultimo_miembro_con_relleno_lo_cambia_en_una_operacion(
        crear_directorio, operaciones):
    directorio = crear_directorio(LDAP_GROUP_PLACEHOLDER_MEMBER=RELLENO)
    grupo = directorio.grupo('conta-usuario', [dn_persona('ana')])

    resultado = EscritorDirectorio(directorio.cliente).remove_member(
        grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.HECHO
    assert _miembros(directorio, grupo) == [RELLENO]
    assert operaciones == [('modify', False, (grupo, {'member': [
        (ldap3.MODIFY_ADD, [RELLENO]),
        (ldap3.MODIFY_DELETE, [dn_persona('ana')])]}), {})]


def test_el_relleno_no_cuenta_como_miembro_real(crear_directorio):
    directorio = crear_directorio(LDAP_GROUP_PLACEHOLDER_MEMBER=RELLENO)
    grupo = directorio.grupo('conta-usuario', [RELLENO, dn_persona('ana')])

    resultado = EscritorDirectorio(directorio.cliente).remove_member(
        grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.HECHO
    assert _miembros(directorio, grupo) == [RELLENO]


def test_posix_group_puede_quedar_sin_miembros(crear_directorio):
    directorio = crear_directorio(LDAP_GROUP_OBJECT_CLASS='posixGroup',
                                  LDAP_GROUP_MEMBER_ATTR='memberUid')
    grupo = directorio.grupo('conta-usuario', ['ana'], clase='posixGroup',
                             atributo='memberUid')

    resultado = EscritorDirectorio(directorio.cliente).remove_member(
        grupo, _usuario('ana'))

    assert resultado.resultado is Resultado.HECHO
    assert _miembros(directorio, grupo, 'memberUid') == []


# --------------------------------------------------------------------------- #
# Límites: solo bajo las bases configuradas (SEC-LDAP-04)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('dn', [
    f'cn=admins,{BASE_DN}',                     # fuera de la OU de grupos
    GRUPOS_BASE_DN,                             # la OU misma
    f'cn=x,ou=grupos-falsos,{BASE_DN}',         # nombre parecido
    f'cn=x,{GRUPOS_BASE_DN},dc=otro',           # la base no es sufijo
    'no es un dn',
    '',
])
def test_grupo_fuera_de_la_base_se_rechaza_sin_conectar(escritor, operaciones,
                                                        monkeypatch, dn):
    monkeypatch.setattr(ldap_client, 'Connection',
                        lambda *a, **k: pytest.fail('no debe conectar'))

    for operacion in (escritor.add_member, escritor.remove_member):
        resultado = operacion(dn, _usuario('ana'))
        assert resultado.resultado is Resultado.ERROR_PERMANENTE
        assert resultado.motivo == errors.MOTIVO_FUERA_DE_BASE
    assert operaciones == []


def test_base_se_compara_normalizada(directorio, escritor):
    directorio.persona('ana')
    grupo = directorio.grupo('conta-usuario', [dn_persona('beto')])
    con_otra_forma = grupo.upper()

    resultado = escritor.add_member(con_otra_forma, _usuario('ana'))

    assert resultado.resultado is Resultado.HECHO


def test_usuario_fuera_de_la_base_de_personas_se_rechaza(directorio, escritor,
                                                        operaciones):
    grupo = directorio.grupo('conta-usuario', [dn_persona('beto')])
    intruso = UsuarioDirectorio(dn=f'cn=servicio,{BASE_DN}',
                                identificador='servicio')

    resultado = escritor.add_member(grupo, intruso)

    assert resultado.resultado is Resultado.ERROR_PERMANENTE
    assert resultado.motivo == errors.MOTIVO_FUERA_DE_BASE
    assert operaciones == []


# --------------------------------------------------------------------------- #
# Clasificación de errores
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('excepcion', [
    exc_ldap.LDAPSocketOpenError('red'),
    exc_ldap.LDAPSocketReceiveError('red'),
    exc_ldap.LDAPSessionTerminatedByServerError('corte'),
    exc_ldap.LDAPResponseTimeoutError('espera'),
    exc_ldap.LDAPBusyResult(),
    exc_ldap.LDAPUnavailableResult(),
    exc_ldap.LDAPTimeLimitExceededResult(),
])
def test_errores_transitorios(excepcion):
    resultado = clasificar_error(excepcion)

    assert resultado is Resultado.ERROR_TRANSITORIO
    assert resultado.reintentable is True


@pytest.mark.parametrize('excepcion, esperado', [
    (exc_ldap.LDAPNoSuchObjectResult(), Resultado.NO_EXISTE),
    (exc_ldap.LDAPInsufficientAccessRightsResult(), Resultado.ERROR_PERMANENTE),
    (exc_ldap.LDAPObjectClassViolationResult(), Resultado.ERROR_PERMANENTE),
    (exc_ldap.LDAPConstraintViolationResult(), Resultado.ERROR_PERMANENTE),
    (exc_ldap.LDAPInvalidDNSyntaxResult(), Resultado.ERROR_PERMANENTE),
    (exc_ldap.LDAPInvalidCredentialsResult(), Resultado.ERROR_PERMANENTE),
    (exc_ldap.LDAPUndefinedAttributeTypeResult(), Resultado.ERROR_PERMANENTE),
    (exc_ldap.LDAPStartTLSError('tls'), Resultado.ERROR_PERMANENTE),
    (None, Resultado.ERROR_PERMANENTE),
])
def test_errores_permanentes(excepcion, esperado):
    resultado = clasificar_error(excepcion)

    assert resultado is esperado
    assert resultado.reintentable is False
    assert resultado.exito is False


@pytest.mark.parametrize('excepcion, esperado', [
    (exc_ldap.LDAPBusyResult(), Resultado.ERROR_TRANSITORIO),
    (exc_ldap.LDAPInsufficientAccessRightsResult(), Resultado.ERROR_PERMANENTE),
    (exc_ldap.LDAPObjectClassViolationResult(), Resultado.ERROR_PERMANENTE),
])
def test_error_al_escribir_se_clasifica(directorio, escritor, monkeypatch,
                                        excepcion, esperado):
    directorio.persona('ana')
    grupo = directorio.grupo('conta-usuario', [dn_persona('beto')])
    _fallar(monkeypatch, 'modify', excepcion)

    resultado = escritor.add_member(grupo, _usuario('ana'))

    assert resultado.resultado is esperado
    assert resultado.motivo == errors.MOTIVO_DIRECTORIO


def test_fallo_de_red_al_conectar_es_transitorio(directorio, escritor,
                                                 monkeypatch, caplog):
    _fallar(monkeypatch, 'bind', exc_ldap.LDAPSocketOpenError('sin red'))

    resultado = escritor.add_member(
        directorio.grupo('conta-usuario', [dn_persona('beto')]),
        _usuario('ana'))

    assert resultado.resultado is Resultado.ERROR_TRANSITORIO
    assert 'LDAPSocketOpenError' in caplog.text


def test_permisos_insuficientes_al_crear_es_permanente(escritor, monkeypatch):
    _fallar(monkeypatch, 'add', exc_ldap.LDAPInsufficientAccessRightsResult())

    resultado = escritor.create_user(DatosCuenta('ana', 'Ana', 'Ruiz',
                                                 'ana@pruebas.local'))

    assert resultado.resultado is Resultado.ERROR_PERMANENTE


# --------------------------------------------------------------------------- #
# Alta de cuentas
# --------------------------------------------------------------------------- #

def test_crear_cuenta_sin_contrasena_en_la_ou_de_personas(directorio, escritor,
                                                          operaciones):
    resultado = escritor.create_user(DatosCuenta(
        'ana.ruiz', 'Ana', 'Ruiz', 'ana@pruebas.local'))

    assert resultado.resultado is Resultado.HECHO
    assert resultado.dn == f'uid=ana.ruiz,{USUARIOS_BASE_DN}'
    entrada = _entrada(directorio, resultado.dn)
    assert entrada.uid.value == 'ana.ruiz'
    assert entrada.cn.value == 'Ana Ruiz'
    assert entrada.sn.value == 'Ruiz'
    assert entrada.givenName.value == 'Ana'
    assert entrada.mail.value == 'ana@pruebas.local'
    assert 'inetOrgPerson' in entrada.objectClass.values
    assert 'userPassword' not in entrada
    (_, solo_lectura, args, kwargs), = operaciones
    assert solo_lectura is False
    assert 'userPassword' not in str(args) + str(kwargs)


def test_crear_cuenta_existente_es_ya_estaba(directorio, escritor,
                                             operaciones):
    directorio.persona('ana')

    resultado = escritor.create_user(DatosCuenta('ana', 'Ana', 'Ruiz',
                                                 'ana@pruebas.local'))

    assert resultado.resultado is Resultado.YA_ESTABA
    assert resultado.dn == dn_persona('ana')
    assert operaciones == []


def test_crear_dos_veces_es_idempotente(directorio, escritor):
    datos = DatosCuenta('ana', 'Ana', 'Ruiz', 'ana@pruebas.local')

    assert escritor.create_user(datos).resultado is Resultado.HECHO
    assert escritor.create_user(datos).resultado is Resultado.YA_ESTABA


def test_crear_cuando_el_servidor_dice_que_existe_es_ya_estaba(
        escritor, monkeypatch):
    _fallar(monkeypatch, 'add', exc_ldap.LDAPEntryAlreadyExistsResult())

    resultado = escritor.create_user(DatosCuenta('ana', 'Ana', 'Ruiz',
                                                 'ana@pruebas.local'))

    assert resultado.resultado is Resultado.YA_ESTABA


@pytest.mark.parametrize('uid, rdn', [
    ('ana,ou=admins', r'uid=ana\,ou\=admins'),
    ('a+b', r'uid=a\+b'),
    ('x\\y', r'uid=x\\y'),
    ('*)(uid=*', r'uid=*)(uid\=*'),
    (' borde ', r'uid=\ borde\ '),
])
def test_identificador_se_escapa_al_formar_el_dn(directorio, escritor,
                                                 operaciones, uid, rdn):
    resultado = escritor.create_user(DatosCuenta(uid, 'Ana', 'Ruiz',
                                                 'ana@pruebas.local'))

    assert resultado.resultado is Resultado.HECHO
    assert resultado.dn == f'{rdn},{USUARIOS_BASE_DN}'
    assert operaciones[0][2][0] == resultado.dn


def test_clases_de_la_cuenta_se_leen_de_la_variable(crear_directorio,
                                                    operaciones):
    directorio = crear_directorio(
        LDAP_USER_OBJECT_CLASSES='inetOrgPerson, organizationalPerson')

    EscritorDirectorio(directorio.cliente).create_user(
        DatosCuenta('ana', 'Ana', 'Ruiz', 'ana@pruebas.local'))

    assert operaciones[0][2][1] == ['inetOrgPerson', 'organizationalPerson']


@pytest.mark.parametrize('datos', [
    DatosCuenta('', 'Ana', 'Ruiz', 'ana@pruebas.local'),
    DatosCuenta('ana', ' ', 'Ruiz', 'ana@pruebas.local'),
    DatosCuenta('ana', 'Ana', '', 'ana@pruebas.local'),
    DatosCuenta('ana', 'Ana', 'Ruiz', ''),
])
def test_datos_incompletos_no_crean_nada(escritor, operaciones, datos):
    resultado = escritor.create_user(datos)

    assert resultado.resultado is Resultado.ERROR_PERMANENTE
    assert resultado.motivo == errors.MOTIVO_DATOS_INCOMPLETOS
    assert operaciones == []


# --------------------------------------------------------------------------- #
# Sin borrado de cuentas en v1
# --------------------------------------------------------------------------- #

def test_no_hay_operacion_de_borrado_de_cuentas():
    publicos = {nombre for nombre, _ in
                inspect.getmembers(EscritorDirectorio, inspect.isfunction)
                if not nombre.startswith('_')}

    assert publicos == {'add_member', 'remove_member', 'create_user'}
    fuente = inspect.getsource(writer)
    assert '.delete(' not in fuente
    assert 'MODIFY_REPLACE' not in fuente


def test_la_lectura_sigue_siendo_de_solo_lectura(directorio):
    with directorio.cliente.conexion_servicio() as conexion:
        assert conexion.read_only is True
