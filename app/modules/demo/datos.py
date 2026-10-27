"""Qué datos demo se crean (FNC-131). Sin contraseñas: las pone el comando."""
from dataclasses import dataclass

from app.authz import ROLE_AREA_ADMIN, ROLE_USER
from app.modules.platforms.tipos import NIVEL_USUARIO

DOMINIO_DEMO = 'demo.local'
# Base ficticia de los grupos LDAP: en local no hay OpenLDAP (el otorgamiento
# falla y se ve como fallido en «Ejecuciones»).
BASE_GRUPOS_DEMO = f'ou=groups,dc=demo,dc={DOMINIO_DEMO.split(".")[-1]}'
LARGO_MINIMO_CONTRASENA = 12
BYTES_CONTRASENA_ALEATORIA = 12  # token_urlsafe(12) -> 16 caracteres


@dataclass(frozen=True)
class AreaDemo:
    nombre: str
    descripcion: str


@dataclass(frozen=True)
class PlataformaDemo:
    nombre: str
    descripcion: str
    area: str
    grupo: str  # base del CN de los grupos de usuario y admin


@dataclass(frozen=True)
class CuentaDemo:
    correo: str
    nombre: str
    rol: str
    area: str  # asignada (usuario) o administrada (admin de área)


@dataclass(frozen=True)
class SolicitudDemo:
    correo: str
    plataforma: str
    nivel: str
    justificacion: str


AREAS = (
    AreaDemo('Demo Infraestructura', 'Área demo con dos plataformas.'),
    AreaDemo('Demo Finanzas', 'Área demo con una plataforma.'),
)

PLATAFORMAS = (
    PlataformaDemo('Demo Wiki', 'Plataforma demo (LDAP).',
                   AREAS[0].nombre, 'demo-wiki'),
    PlataformaDemo('Demo Repositorio', 'Plataforma demo (LDAP).',
                   AREAS[0].nombre, 'demo-repositorio'),
    PlataformaDemo('Demo Reportes', 'Plataforma demo (LDAP).',
                   AREAS[1].nombre, 'demo-reportes'),
)

CUENTAS = (
    CuentaDemo(f'admin.area@{DOMINIO_DEMO}', 'Admin de Área Demo',
               ROLE_AREA_ADMIN, AREAS[0].nombre),
    CuentaDemo(f'usuario1@{DOMINIO_DEMO}', 'Usuario Demo 1',
               ROLE_USER, AREAS[0].nombre),
    CuentaDemo(f'usuario2@{DOMINIO_DEMO}', 'Usuario Demo 2',
               ROLE_USER, AREAS[1].nombre),
)

# Una solicitud pendiente para probar la aprobación del admin de área.
SOLICITUD = SolicitudDemo(CUENTAS[1].correo, PLATAFORMAS[0].nombre,
                          NIVEL_USUARIO, 'Solicitud demo para probar la aprobación.')


def dn_de_grupo(plataforma, nivel):
    return f'cn={plataforma.grupo}-{nivel},{BASE_GRUPOS_DEMO}'
