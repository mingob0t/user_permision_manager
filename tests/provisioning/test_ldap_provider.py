"""Proveedor LDAP sobre el escritor de FNC-041 con un directorio `MOCK_SYNC`."""
import pytest

from app import db
from app.modules.platforms.tipos import NIVEL_ADMIN, NIVEL_USUARIO
from app.modules.provisioning.ldap_provider import ProveedorLdap
from app.modules.provisioning.providers import Operacion
from app.modules.provisioning.tipos import (RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)
from tests import fabricas
from tests.directory.conftest import (GRUPOS_BASE_DN, ENTORNO_VALIDO,
                                      DirectorioMock, dn_grupo)

OTRO = 'uid=otro,ou=personas,dc=pruebas,dc=local'


@pytest.fixture
def directorio(monkeypatch):
    return DirectorioMock(monkeypatch)


@pytest.fixture
def escenario(app, directorio):
    """Persona `ana` en el directorio, grupo de usuario con otro miembro."""
    directorio.persona('otro')
    dn_ana = directorio.persona('ana', correo='Ana@Pruebas.local')
    grupo = directorio.grupo('wiki-usuario', [OTRO])
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(
        area, integration_type='ldap', ldap_group_user_dn=grupo,
        ldap_group_admin_dn=dn_grupo('wiki-admin'))
    usuario = fabricas.crear_usuario(email='ana@pruebas.local')
    proveedor = ProveedorLdap(cliente=directorio.cliente)
    return proveedor, plataforma, usuario, grupo, dn_ana


def operacion(plataforma, usuario, nivel=NIVEL_USUARIO):
    return Operacion(id_operacion='1', clave_idempotencia='k',
                     operacion='otorgar', nivel=nivel,
                     plataforma_id=plataforma.id, usuario_id=usuario.id)


def miembros(directorio, grupo):
    entrada = directorio.servidor.dit[grupo]
    return [v.decode() if isinstance(v, bytes) else str(v)
            for v in entrada['member']]


def test_otorgar_y_revocar_son_idempotentes(escenario, directorio):
    proveedor, plataforma, usuario, grupo, dn_ana = escenario
    op = operacion(plataforma, usuario)

    assert proveedor.otorgar(op).resultado == RESULTADO_EXITOSO
    assert dn_ana in miembros(directorio, grupo)
    assert proveedor.otorgar(op).resultado == RESULTADO_SIN_CAMBIOS
    assert proveedor.consultar(op).presente is True

    assert proveedor.revocar(op).resultado == RESULTADO_EXITOSO
    assert dn_ana not in miembros(directorio, grupo)
    assert proveedor.revocar(op).resultado == RESULTADO_SIN_CAMBIOS
    assert proveedor.consultar(op).presente is False


def test_grupo_inexistente_es_permanente(escenario):
    proveedor, plataforma, usuario, *_ = escenario
    resultado = proveedor.otorgar(operacion(plataforma, usuario, NIVEL_ADMIN))

    assert (resultado.resultado, resultado.motivo) == (
        RESULTADO_ERROR_PERMANENTE, 'grupo_inexistente')


def test_solo_escribe_en_el_grupo_registrado_y_bajo_la_base(escenario,
                                                            directorio):
    """SEC-LDAP-04: un DN fuera de `LDAP_GROUPS_BASE_DN` no se toca."""
    proveedor, plataforma, usuario, *_ = escenario
    ajeno = directorio.grupo('ajeno', [OTRO])
    fuera = 'cn=root,ou=sistema,dc=pruebas,dc=local'
    directorio.agregar(fuera, objectClass='groupOfNames', cn='root',
                       member=[OTRO])
    plataforma.ldap_group_user_dn = fuera
    db.session.commit()

    resultado = proveedor.otorgar(operacion(plataforma, usuario))

    assert (resultado.resultado, resultado.motivo) == (
        RESULTADO_ERROR_PERMANENTE, 'fuera_de_base')
    assert miembros(directorio, fuera) == [OTRO]
    assert miembros(directorio, ajeno) == [OTRO]


def test_plataforma_sin_grupo_del_nivel(escenario):
    proveedor, plataforma, usuario, *_ = escenario
    plataforma.ldap_group_user_dn = None
    db.session.commit()

    assert proveedor.otorgar(operacion(plataforma, usuario)).motivo == (
        'grupo_no_configurado')


def test_plataforma_que_ya_no_es_ldap(escenario):
    proveedor, plataforma, usuario, *_ = escenario
    plataforma.integration_type = 'conector'
    db.session.commit()

    assert proveedor.otorgar(operacion(plataforma, usuario)).motivo == (
        'tipo_integracion')


def test_persona_por_correo_exacto(escenario, directorio):
    """`ana@…` no se confunde con `juana@…` (búsqueda por subcadena)."""
    proveedor, plataforma, _, grupo, _ = escenario
    directorio.persona('juana', correo='juana@pruebas.local')
    sin_cuenta = fabricas.crear_usuario(email='na@pruebas.local')

    resultado = proveedor.otorgar(operacion(plataforma, sin_cuenta))

    assert (resultado.resultado, resultado.motivo) == (
        RESULTADO_ERROR_PERMANENTE, 'usuario_inexistente')
    assert miembros(directorio, grupo) == [OTRO]


def test_correo_repetido_en_el_directorio_es_ambiguo(escenario, directorio):
    proveedor, plataforma, usuario, *_ = escenario
    directorio.persona('ana2', correo='ana@pruebas.local')

    assert proveedor.otorgar(operacion(plataforma, usuario)).motivo == (
        'persona_ambigua')


def test_directorio_inactivo_es_permanente(app):
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(
        area, ldap_group_user_dn=f'cn=x,{GRUPOS_BASE_DN}')
    usuario = fabricas.crear_usuario()

    resultado = ProveedorLdap().otorgar(operacion(plataforma, usuario))

    assert resultado.motivo == 'directorio_no_configurado'


def test_directorio_caido_es_transitorio(escenario, monkeypatch):
    from ldap3.core.exceptions import LDAPSocketOpenError
    from app.modules.directory import ldap_client

    def _caido(*args, **kwargs):
        raise LDAPSocketOpenError('sin red')
    monkeypatch.setattr(ldap_client, 'Connection', _caido)
    proveedor, plataforma, usuario, *_ = escenario

    resultado = proveedor.otorgar(operacion(plataforma, usuario))

    assert (resultado.resultado, resultado.motivo) == (
        'error_transitorio', 'directorio')


def test_entorno_de_prueba_es_el_del_directorio():
    assert ENTORNO_VALIDO['LDAP_GROUPS_BASE_DN'] == GRUPOS_BASE_DN


def test_de_punta_a_punta_encolar_commit_worker_y_ldap(app, monkeypatch,
                                                       cola_falsa):
    """Encolar → commit → mensaje RQ (síncrono) → proveedor LDAP registrado."""
    from tests.directorio_falso import instalar_directorio
    from app.modules.provisioning.queue import encolar

    directorio_falso = instalar_directorio(monkeypatch)
    dn_ana = directorio_falso.agregar('ana', 'clave-ficticia',
                                      correo='ana@pruebas.local')
    grupo = dn_grupo('wiki-usuario')
    directorio_falso._agregar(grupo, objectClass='groupOfNames',
                              cn='wiki-usuario', member=[OTRO])
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(area, ldap_group_user_dn=grupo)
    usuario = fabricas.crear_usuario(email='ana@pruebas.local')

    encolar('otorgar', usuario.id, plataforma, NIVEL_USUARIO, 'k-e2e')
    db.session.commit()

    assert cola_falsa.procesar() == ['exitoso']
    entrada = directorio_falso.servidor.dit[grupo]
    assert dn_ana.encode() in entrada['member']
