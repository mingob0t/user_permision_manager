"""Punta a punta (FNC-054): servicio → cola falsa → worker → proveedor LDAP
real sobre el directorio simulado (`MOCK_SYNC`) → manejador → estado."""
import pytest

from app import db
from app.modules.access import services
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_REVOCADO,
                                      ORIGEN_SOLICITUD)
from app.modules.platforms.tipos import NIVEL_ADMIN, NIVEL_USUARIO
from app.modules.provisioning import providers
from app.modules.provisioning.ldap_provider import ProveedorLdap
from app.modules.provisioning.tipos import PROVEEDOR_LDAP
from tests.access.conftest import GRUPO_ADMIN, GRUPO_USUARIO, recargar
from tests.directory.conftest import DirectorioMock

OTRO = 'uid=otro,ou=personas,dc=pruebas,dc=local'


@pytest.fixture
def directorio(monkeypatch, escena):
    directorio = DirectorioMock(monkeypatch)
    directorio.persona('otro')
    dn_ana = directorio.persona('ana', correo='ana@pruebas.local')
    for grupo in (GRUPO_USUARIO, GRUPO_ADMIN):
        directorio.grupo(grupo.split(',')[0].split('=')[1], [OTRO])
    providers.registrar_proveedor(
        PROVEEDOR_LDAP, lambda: ProveedorLdap(cliente=directorio.cliente))
    yield directorio, dn_ana
    providers.registrar_proveedor(PROVEEDOR_LDAP, ProveedorLdap)


def _miembros(directorio, grupo):
    return [v.decode() if isinstance(v, bytes) else str(v)
            for v in directorio.servidor.dit[grupo]['member']]


def test_otorgar_subir_y_revocar_en_el_directorio(escena, cola_falsa,
                                                 directorio):
    directorio, dn_ana = directorio

    usuario_ = services.otorgar(escena['usuario'], escena['plataforma'],
                                NIVEL_USUARIO, ORIGEN_SOLICITUD,
                                actor=escena['admin'], request_id=1)
    db.session.commit()
    assert cola_falsa.procesar() == ['exitoso']
    assert recargar(usuario_.id).status == ESTADO_ACTIVO
    assert dn_ana in _miembros(directorio, GRUPO_USUARIO)

    # P5: subir a admin saca del grupo de usuario y mete en el de admin.
    admin_ = services.otorgar(escena['usuario'], escena['plataforma'],
                              NIVEL_ADMIN, ORIGEN_SOLICITUD,
                              actor=escena['admin'], request_id=2)
    db.session.commit()
    assert sorted(cola_falsa.procesar()) == ['exitoso', 'exitoso']
    assert recargar(usuario_.id).status == ESTADO_REVOCADO
    assert recargar(admin_.id).status == ESTADO_ACTIVO
    assert dn_ana not in _miembros(directorio, GRUPO_USUARIO)
    assert dn_ana in _miembros(directorio, GRUPO_ADMIN)

    services.revocar(recargar(admin_.id), actor=escena['super'])
    db.session.commit()
    assert cola_falsa.procesar() == ['exitoso']
    assert recargar(admin_.id).status == ESTADO_REVOCADO
    assert dn_ana not in _miembros(directorio, GRUPO_ADMIN)
