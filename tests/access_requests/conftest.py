"""Escena de solicitudes (FNC-056): área con plataforma LDAP, admins de área,
usuarios y superadmin; accesos vigentes creados directo en la BD."""
import pytest
from flask import g

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import ORIGEN_SOLICITUD
from app.modules.platforms.tipos import TIPO_LDAP
from tests import fabricas

GRUPO_USUARIO = 'cn=conta-usuario,ou=grupos,dc=pruebas,dc=local'
GRUPO_ADMIN = 'cn=conta-admin,ou=grupos,dc=pruebas,dc=local'
RUTA = '/api/v1/access-requests'


@pytest.fixture
def escena(app):
    area = fabricas.crear_area('Finanzas')
    otra = fabricas.crear_area('Ventas')
    plataforma = fabricas.crear_plataforma(
        area, 'Contabilidad', integration_type=TIPO_LDAP,
        ldap_group_user_dn=GRUPO_USUARIO, ldap_group_admin_dn=GRUPO_ADMIN)
    de_otra = fabricas.crear_plataforma(
        otra, 'CRM', integration_type=TIPO_LDAP,
        ldap_group_user_dn='cn=crm-usuario,ou=grupos,dc=pruebas,dc=local',
        ldap_group_admin_dn='cn=crm-admin,ou=grupos,dc=pruebas,dc=local')
    return {
        'area': area, 'otra': otra, 'plataforma': plataforma,
        'de_otra': de_otra,
        'admin': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                        email='admin@pruebas.local',
                                        areas_administradas=[area]),
        # Admin de Ventas que además pertenece a Finanzas (RF-03).
        'admin_otra': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                             email='admin.otra@pruebas.local',
                                             areas=[area],
                                             areas_administradas=[otra]),
        'usuario': fabricas.crear_usuario(ROLE_USER, email='ana@pruebas.local',
                                          areas=[area]),
        'ajeno': fabricas.crear_usuario(ROLE_USER, areas=[otra]),
        'super': fabricas.crear_usuario(ROLE_ADMIN),
    }


def dar_acceso(usuario, plataforma, nivel, estado='activo'):
    acceso = PlatformAccessGrant(user_id=usuario.id, platform_id=plataforma.id,
                                 level=nivel, origin=ORIGEN_SOLICITUD,
                                 request_id=None, status=estado)
    acceso.sincronizar_slots()
    db.session.add(acceso)
    db.session.commit()
    return acceso


def pedir(cliente, plataforma, nivel='usuario', **extra):
    return cliente.post(RUTA, json={'platform_id': plataforma.id,
                                    'level': nivel, **extra})


def cambiar_de_actor():
    """Las peticiones comparten el contexto de la app de la prueba: se olvida
    el usuario que Flask-Login dejó en `g` antes de usar otro cliente."""
    g.pop('_login_user', None)
