"""Escena de accesos (FNC-054): área con plataforma LDAP, admins, usuario y
superadmin; cola RQ falsa y proveedor simulado del ejecutor (FNC-049)."""
import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.access import manejadores as manejadores_accesos
from app.modules.access.models import PlatformAccessGrant
from app.modules.platforms.tipos import TIPO_LDAP
from app.modules.provisioning import (ejecucion, manejadores, providers,
                                      queue)
from app.modules.provisioning.ldap_provider import ProveedorLdap
from app.modules.provisioning.tipos import PROVEEDOR_CONECTOR, PROVEEDOR_LDAP
from tests import fabricas
from tests.provisioning.conftest import ColaFalsa, ProveedorSimulado

GRUPO_USUARIO = 'cn=conta-usuario,ou=grupos,dc=pruebas,dc=local'
GRUPO_ADMIN = 'cn=conta-admin,ou=grupos,dc=pruebas,dc=local'


@pytest.fixture(autouse=True)
def manejadores_de_accesos(app):
    """Solo los manejadores de accesos (otras pruebas vacían la lista)."""
    manejadores.quitar_manejadores()
    manejadores_accesos.registrar()
    yield
    manejadores.quitar_manejadores()


@pytest.fixture
def cola_falsa(monkeypatch):
    falsa = ColaFalsa()
    monkeypatch.setattr(queue, 'cola', lambda conexion=None, **_: falsa)
    return falsa


@pytest.fixture
def proveedor_simulado():
    simulado = ProveedorSimulado()
    for tipo in (PROVEEDOR_LDAP, PROVEEDOR_CONECTOR):
        providers.registrar_proveedor(tipo, lambda: simulado)
    yield simulado
    providers.quitar_proveedor(PROVEEDOR_CONECTOR)
    providers.registrar_proveedor(PROVEEDOR_LDAP, ProveedorLdap)


@pytest.fixture
def sin_correo(monkeypatch):
    monkeypatch.setattr(ejecucion, 'notificar_aprovisionamiento_fallido',
                        lambda *a, **k: None)


@pytest.fixture
def escena(app):
    area = fabricas.crear_area('Finanzas')
    otra = fabricas.crear_area('Ventas')
    plataforma = fabricas.crear_plataforma(
        area, 'Contabilidad', integration_type=TIPO_LDAP,
        ldap_group_user_dn=GRUPO_USUARIO, ldap_group_admin_dn=GRUPO_ADMIN)
    return {
        'area': area, 'otra': otra, 'plataforma': plataforma,
        'admin': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                        email='admin@pruebas.local',
                                        areas_administradas=[area]),
        'admin2': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                         areas=[area],
                                         areas_administradas=[area]),
        'admin_otra': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                             areas_administradas=[otra]),
        'usuario': fabricas.crear_usuario(ROLE_USER, email='ana@pruebas.local',
                                          areas=[area]),
        'ajeno': fabricas.crear_usuario(ROLE_USER, areas=[otra]),
        'super': fabricas.crear_usuario(ROLE_ADMIN),
    }


def recargar(acceso_id):
    db.session.expire_all()
    return db.session.get(PlatformAccessGrant, acceso_id)
