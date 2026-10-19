"""Matriz de protección por rol de los endpoints /api/v1 (FNC-020).

Cada `Caso` clasifica una ruta (método + regla tal como aparece en
`app.url_map`) y dice qué código HTTP espera cada rol. La prueba guardia
(`test_guardia_rutas.py`) falla si aparece una ruta /api/v1 sin caso aquí.

Los datos de cada petición son los mínimos válidos para que el 2xx sea real
(la acción se ejecuta); los servicios externos (SMTP, LDAP) se simulan.
"""

import io
import json
import zipfile
from dataclasses import dataclass, field
from typing import Callable, Optional

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.notifications.models import SMTPConfig
from tests import fabricas

ANONIMO = 'anonimo'
ROLES_MATRIZ = (ANONIMO, ROLE_USER, ROLE_AREA_ADMIN, ROLE_ADMIN)

# Valores ficticios de prueba (no son secretos ni hosts reales).
CONTRASENA_FICTICIA = 'clave-ficticia-de-prueba'
HOST_SMTP_FICTICIO = 'smtp.pruebas.invalid'
HOST_LDAP_FICTICIO = 'ldap.pruebas.invalid'
CORREO_SSO_FICTICIO = 'sso@pruebas.local'

# Blueprints heredados: sus 44 rutas responden 410 o redirigen al frontend.
# Se cubren en FNC-023 (y se retiran en FNC-027); aquí solo se excluyen.
BLUEPRINTS_HEREDADOS = frozenset({
    'auth', 'core', 'audit', 'settings', 'notifications', 'users_module',
    'areas_module',
})


# --------------------------------------------------------------------------- #
# Códigos esperados por rol
# --------------------------------------------------------------------------- #

def publica(codigo=200):
    """Sin sesión: todos los roles reciben lo mismo."""
    return {rol: codigo for rol in ROLES_MATRIZ}


def con_sesion(codigo=200):
    """`@login_required`: cualquier rol con sesión."""
    return {ANONIMO: 401, ROLE_USER: codigo, ROLE_AREA_ADMIN: codigo,
            ROLE_ADMIN: codigo}


def administradores(codigo=200):
    """Superadmin y admin de área (sobre su propia área)."""
    return {ANONIMO: 401, ROLE_USER: 403, ROLE_AREA_ADMIN: codigo,
            ROLE_ADMIN: codigo}


def solo_superadmin(codigo=200):
    """`@admin_required`: configuración global y acciones de tenant."""
    return {ANONIMO: 401, ROLE_USER: 403, ROLE_AREA_ADMIN: 403,
            ROLE_ADMIN: codigo}


# --------------------------------------------------------------------------- #
# Escenario de datos
# --------------------------------------------------------------------------- #

@dataclass
class Escenario:
    """IDs de los datos mínimos que usan las peticiones de la matriz."""
    area_id: int
    area_vacia_id: int
    plataforma_id: int
    objetivo_id: int
    cuenta_local_email: str
    admin_objetivo_id: int


def crear_escenario():
    """Un área con plataforma y un usuario objetivo, más un área sin nada.

    El admin de área y el usuario de la matriz pertenecen a `area`, así que
    todo lo que tocan está dentro de su alcance: la matriz mide el rol, no el
    alcance (eso es FNC-021).
    """
    area = fabricas.crear_area()
    area_vacia = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(area)
    objetivo = fabricas.crear_usuario(ROLE_USER, areas=[area])
    # Cuenta de emergencia: la única con login local (FNC-077).
    cuenta_local = fabricas.crear_usuario(ROLE_ADMIN,
                                          contrasena=CONTRASENA_FICTICIA)
    # Admin de área sin áreas: destino de `PUT /users/<id>/managed-areas`.
    admin_objetivo = fabricas.crear_usuario(ROLE_AREA_ADMIN)
    return Escenario(area_id=area.id, area_vacia_id=area_vacia.id,
                     plataforma_id=plataforma.id, objetivo_id=objetivo.id,
                     cuenta_local_email=cuenta_local.email,
                     admin_objetivo_id=admin_objetivo.id)


def crear_actor(rol, esc):
    """Usuario del rol pedido, con el área del escenario en su alcance."""
    from app.modules.core.models import Area

    area = db.session.get(Area, esc.area_id)
    if rol == ROLE_ADMIN:
        return fabricas.crear_usuario(ROLE_ADMIN)
    if rol == ROLE_AREA_ADMIN:
        # También administra el área vacía: destino de `DELETE /areas/<id>`
        # (FNC-045, P11: el admin da de baja sus áreas).
        area_vacia = db.session.get(Area, esc.area_vacia_id)
        return fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                      areas_administradas=[area, area_vacia])
    return fabricas.crear_usuario(ROLE_USER, areas=[area])


# --------------------------------------------------------------------------- #
# Preparaciones: servicios externos simulados
# --------------------------------------------------------------------------- #

def _con_smtp_configurado(esc, monkeypatch):
    from app.modules.notifications import services
    db.session.add(SMTPConfig(server=HOST_SMTP_FICTICIO, port=587,
                              encryption='starttls'))
    db.session.commit()
    monkeypatch.setattr(services, 'send_test_email',
                        lambda **kwargs: {'status': 'success'})


def _con_directorio_simulado(esc, monkeypatch):
    """Directorio activo (`LDAP_*` ficticias) sobre `ldap3` `MOCK_SYNC`."""
    # Import diferido: `directorio_falso` importa constantes de este módulo.
    from tests.directorio_falso import instalar_directorio
    instalar_directorio(monkeypatch)


def _con_sso_activo(esc, monkeypatch):
    # El cliente de pruebas llega desde loopback, que es proxy de confianza
    # por defecto. Las reglas del SSO se prueban en FNC-022.
    monkeypatch.setenv('AUTHELIA_ENABLED', 'true')


# --------------------------------------------------------------------------- #
# Peticiones
# --------------------------------------------------------------------------- #

def _json(datos):
    return lambda esc: {'json': datos}


def _sin_cuerpo(esc):
    return {}


def _zip_respaldo(esc):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archivo:
        archivo.writestr('nexus_config.json', json.dumps({'payload': {}}))
    buffer.seek(0)
    return {'data': {'file': (buffer, 'respaldo.zip')},
            'content_type': 'multipart/form-data'}


def _login_local(esc):
    return {'json': {'email': esc.cuenta_local_email,
                     'password': CONTRASENA_FICTICIA, 'method': 'local'}}


def _cabecera_sso(esc):
    return {'headers': {'Remote-Email': CORREO_SSO_FICTICIO}}


def _nuevo_usuario(esc):
    return {'json': {'email': 'nuevo@pruebas.local', 'role': ROLE_USER,
                     'area_ids': [esc.area_id]}}


def _nueva_cuenta_directorio(esc):
    return {'json': {'uid': 'ana.ruiz', 'email': 'ana.ruiz@pruebas.local',
                     'given_name': 'Ana', 'surname': 'Ruiz',
                     'area_ids': [esc.area_id]}}


@dataclass(frozen=True)
class Caso:
    metodo: str
    regla: str
    ruta: Callable[[Escenario], str]
    esperado: dict
    peticion: Callable[[Escenario], dict] = _sin_cuerpo
    preparar: Optional[Callable] = None
    nota: str = field(default='')

    @property
    def clave(self):
        return (self.metodo, self.regla)


def _fija(ruta):
    return lambda esc: ruta


def _area(sufijo=''):
    return lambda esc: f'/api/v1/areas/{esc.area_id}{sufijo}'


def _plataforma(sufijo=''):
    return lambda esc: f'/api/v1/platforms/{esc.plataforma_id}{sufijo}'


def _objetivo(sufijo=''):
    return lambda esc: f'/api/v1/users/{esc.objetivo_id}{sufijo}'


A = '/api/v1'

CASOS = (
    # ---- Autenticación (públicas, salvo logout) ----
    Caso('GET', f'{A}/auth/context', _fija(f'{A}/auth/context'), publica()),
    Caso('POST', f'{A}/auth/sso', _fija(f'{A}/auth/sso'), publica(),
         _cabecera_sso, _con_sso_activo),
    Caso('POST', f'{A}/auth/login', _fija(f'{A}/auth/login'), publica(),
         _login_local),
    Caso('POST', f'{A}/auth/logout', _fija(f'{A}/auth/logout'), con_sesion()),

    # ---- Lectura (routes.py) ----
    Caso('GET', f'{A}/me', _fija(f'{A}/me'), con_sesion()),
    Caso('GET', f'{A}/areas', _fija(f'{A}/areas'), con_sesion()),
    Caso('GET', f'{A}/areas/<int:area_id>', _area(), administradores()),
    Caso('GET', f'{A}/platforms', _fija(f'{A}/platforms'), con_sesion()),
    Caso('POST', f'{A}/platforms/<int:platform_id>/visit', _plataforma('/visit'),
         con_sesion()),
    Caso('POST', f'{A}/platforms/<int:platform_id>/favorite',
         _plataforma('/favorite'), con_sesion()),
    Caso('GET', f'{A}/favorites', _fija(f'{A}/favorites'), con_sesion()),
    Caso('GET', f'{A}/users', _fija(f'{A}/users'), administradores()),
    Caso('PUT', f'{A}/users/<int:user_id>/areas', _objetivo('/areas'),
         administradores(), lambda esc: {'json': {'area_ids': [esc.area_id]}}),
    Caso('GET', f'{A}/stats', _fija(f'{A}/stats'), con_sesion()),
    Caso('GET', f'{A}/audit', _fija(f'{A}/audit'), con_sesion()),

    # ---- Áreas (areas/api.py) ----
    Caso('POST', f'{A}/areas', _fija(f'{A}/areas'), administradores(201),
         _json({'name': 'Área nueva de prueba'}),
         nota='FNC-045: el admin de área da de alta áreas'),
    Caso('PUT', f'{A}/areas/<int:area_id>', _area(), administradores(),
         _json({'description': 'Descripción editada'})),
    Caso('DELETE', f'{A}/areas/<int:area_id>',
         lambda esc: f'{A}/areas/{esc.area_vacia_id}', administradores(),
         nota='FNC-045 (P11): el admin da de baja sus áreas'),

    # ---- Escritura (crud.py) ----
    Caso('PUT', f'{A}/areas/<int:area_id>/users', _area('/users'),
         administradores(),
         lambda esc: {'json': {'user_ids': [esc.objetivo_id]}}),
    Caso('POST', f'{A}/platforms', _fija(f'{A}/platforms'), administradores(201),
         lambda esc: {'json': {'name': 'Plataforma nueva de prueba',
                               'description': 'Plataforma de prueba',
                               'area_id': esc.area_id,
                               'integration_type': 'conector'}},
         nota='FNC-046: movida a platforms/api.py; contrato plataformas-integracion'),
    # FNC-046: el admin de área recibe 404 fuera de su área (no 403); se
    # prueba en tests/platforms/test_integracion_y_grupos.py.
    Caso('PUT', f'{A}/platforms/<int:platform_id>', _plataforma(),
         administradores(), _json({'description': 'Descripción editada'}),
         nota='FNC-046: movida a platforms/api.py'),
    Caso('DELETE', f'{A}/platforms/<int:platform_id>', _plataforma(),
         administradores()),
    Caso('PUT', f'{A}/platforms/<int:platform_id>/users', _plataforma('/users'),
         administradores(),
         lambda esc: {'json': {'user_ids': [esc.objetivo_id]}}),
    Caso('POST', f'{A}/users', _fija(f'{A}/users'), administradores(201),
         _nuevo_usuario),
    Caso('PUT', f'{A}/users/<int:user_id>', _objetivo(), administradores(),
         _json({'name': 'Nombre editado'})),
    Caso('DELETE', f'{A}/users/<int:user_id>', _objetivo(), administradores()),
    Caso('PUT', f'{A}/users/<int:user_id>/platforms', _objetivo('/platforms'),
         administradores(),
         lambda esc: {'json': {'platform_ids': [esc.plataforma_id]}}),
    Caso('PUT', f'{A}/users/<int:user_id>/managed-areas',
         lambda esc: f'{A}/users/{esc.admin_objetivo_id}/managed-areas',
         solo_superadmin(),
         lambda esc: {'json': {'area_ids': [esc.area_id]}},
         nota='FNC-044: solo el superadmin asigna áreas administradas'),
    Caso('POST', f'{A}/users/directory', _fija(f'{A}/users/directory'),
         administradores(201), _nueva_cuenta_directorio,
         _con_directorio_simulado,
         nota='FNC-064 (P2): superadmin y admins (sus áreas) crean cuentas '
              'en OpenLDAP'),
    Caso('PUT', f'{A}/me/preferences', _fija(f'{A}/me/preferences'),
         con_sesion(), _json({'tour_enabled': False})),
    Caso('GET', f'{A}/users/inactive', _fija(f'{A}/users/inactive'),
         solo_superadmin()),
    Caso('POST', f'{A}/users/purge', _fija(f'{A}/users/purge'),
         solo_superadmin(), _json({'days': 30})),

    # ---- Sistema y notificaciones (admin.py) ----
    Caso('GET', f'{A}/settings', _fija(f'{A}/settings'), con_sesion()),
    Caso('PUT', f'{A}/settings', _fija(f'{A}/settings'), solo_superadmin(),
         _json({'portal_name': 'Portal de prueba'})),
    Caso('GET', f'{A}/smtp', _fija(f'{A}/smtp'), solo_superadmin()),
    Caso('PUT', f'{A}/smtp', _fija(f'{A}/smtp'), solo_superadmin(),
         _json({'server': HOST_SMTP_FICTICIO, 'port': 587})),
    Caso('POST', f'{A}/smtp/test', _fija(f'{A}/smtp/test'), solo_superadmin(),
         _json({'email': 'destino@pruebas.local'}), _con_smtp_configurado),
    Caso('GET', f'{A}/templates', _fija(f'{A}/templates'), solo_superadmin()),
    Caso('PUT', f'{A}/templates/<slug>', _fija(f'{A}/templates/prueba'),
         solo_superadmin(),
         _json({'name': 'Plantilla de prueba', 'subject': 'Asunto'})),
    Caso('GET', f'{A}/notifications', _fija(f'{A}/notifications'), con_sesion()),
    Caso('POST', f'{A}/notifications/read', _fija(f'{A}/notifications/read'),
         con_sesion()),
    Caso('DELETE', f'{A}/notifications', _fija(f'{A}/notifications'),
         con_sesion()),
    Caso('GET', f'{A}/auth-config', _fija(f'{A}/auth-config'),
         solo_superadmin()),
    Caso('PUT', f'{A}/auth-config', _fija(f'{A}/auth-config'),
         solo_superadmin(), _json({}),
         nota='FNC-043: sin campos editables (ADR-004); `{}` no cambia nada'),
    Caso('POST', f'{A}/auth-config/test', _fija(f'{A}/auth-config/test'),
         solo_superadmin(), preparar=_con_directorio_simulado,
         nota='FNC-043: solo la configuración efectiva, sin cuerpo'),
    Caso('GET', f'{A}/backup', _fija(f'{A}/backup'), solo_superadmin()),
    Caso('POST', f'{A}/backup', _fija(f'{A}/backup'), solo_superadmin(),
         _zip_respaldo),
    Caso('GET', f'{A}/directory/search', _fija(f'{A}/directory/search?q=ab'),
         solo_superadmin(), preparar=_con_directorio_simulado),
)

# Entradas inválidas: con un rol que pasa la protección, la validación
# responde 400 con el formato estándar de error.
CASOS_400 = (
    ('POST', f'{A}/auth/login', _json({})),
    # POST y PUT /areas con datos inválidos: 422 `validacion` (FNC-045,
    # tests/areas/).
    # FNC-046: un campo vacío es `422 validacion`; el 400 es la lista blanca.
    ('POST', f'{A}/platforms', _json({'user_ids': []})),
    ('PUT', f'{A}/platforms/{{plataforma_id}}', _json({'visits': 0})),
    ('POST', f'{A}/users', _json({'email': ''})),
    ('POST', f'{A}/users/directory', _json({'password': 'x'})),
    ('PUT', f'{A}/me/preferences', _json({'refresh_interval': 'no-numero'})),
    ('POST', f'{A}/users/purge', _json({'days': 'no-numero'})),
    ('PUT', f'{A}/settings', _json({'portal_identity_type': 'otro'})),
    ('PUT', f'{A}/smtp', _json({'port': 'no-numero'})),
    ('POST', f'{A}/smtp/test', _json({'email': 'sin-arroba'})),
    ('PUT', f'{A}/templates/nueva', _json({'name': ''})),
    ('PUT', f'{A}/auth-config', _json({'ldap_port': 'no-numero'})),
    ('POST', f'{A}/auth-config/test', _json({'ldap_host': HOST_LDAP_FICTICIO})),
    ('POST', f'{A}/backup', _sin_cuerpo),
    ('GET', f'{A}/directory/search?q=a', _sin_cuerpo),
)
