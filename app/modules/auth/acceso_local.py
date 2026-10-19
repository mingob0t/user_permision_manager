"""Política del login local y de las contraseñas locales (FNC-077).

Decisión del dueño (2026-10-15): la autenticación es por Authelia o el
directorio. El login local (`method: local`) queda solo para la **cuenta de
emergencia**: rol `administrador` con `auth_source='local'`.

Para la prueba de concepto sin Authelia, `LOGIN_LOCAL_TODAS_LAS_CUENTAS=true`
permite el login local de cualquier cuenta local, pero **solo** si
`APP_ENV=development`; en cualquier otro entorno (o sin `APP_ENV`) se ignora.

Las mismas reglas deciden si el portal fija una contraseña local en
`POST /users` y `PUT /users/<id>`.
"""

import os

from app.authz import ROLE_ADMIN, normalized_role
from app.modules.users.roles import ORIGEN_LOCAL

VAR_LOGIN_LOCAL_TODAS = 'LOGIN_LOCAL_TODAS_LAS_CUENTAS'
VAR_ENTORNO = 'APP_ENV'
ENTORNO_DESARROLLO = 'development'
VALOR_ACTIVO = 'true'

# Motivos solo para la auditoría; el cliente recibe la respuesta única.
MOTIVO_ORIGEN_NO_LOCAL = 'cuenta_no_local'
MOTIVO_SOLO_EMERGENCIA = 'login_local_solo_cuenta_de_emergencia'


def es_origen_local(cuenta):
    """True si la cuenta es local (un origen vacío se trata como local)."""
    return (cuenta.auth_source or ORIGEN_LOCAL) == ORIGEN_LOCAL


def es_cuenta_de_emergencia(cuenta):
    """True si es la cuenta de emergencia: superadmin local."""
    return (cuenta is not None and es_origen_local(cuenta)
            and normalized_role(cuenta) == ROLE_ADMIN)


def _entorno_de_desarrollo():
    return (os.getenv(VAR_ENTORNO) or '').strip().lower() == ENTORNO_DESARROLLO


def login_local_de_todas_habilitado():
    """True solo con la bandera activa y `APP_ENV=development`."""
    bandera = (os.getenv(VAR_LOGIN_LOCAL_TODAS) or '').strip().lower()
    return bandera == VALOR_ACTIVO and _entorno_de_desarrollo()


def motivo_rechazo_login_local(cuenta):
    """Por qué `cuenta` no puede usar el login local, o `None` si puede."""
    if not es_origen_local(cuenta):
        return MOTIVO_ORIGEN_NO_LOCAL
    if es_cuenta_de_emergencia(cuenta) or login_local_de_todas_habilitado():
        return None
    return MOTIVO_SOLO_EMERGENCIA


def contrasena_local_permitida(cuenta=None):
    """True si el portal puede fijar una contraseña local a `cuenta`.

    `cuenta=None` es una cuenta nueva de `POST /users`, que nunca es la de
    emergencia (`administrador` no se asigna por la API).
    """
    if cuenta is not None and not es_origen_local(cuenta):
        return False
    return es_cuenta_de_emergencia(cuenta) or login_local_de_todas_habilitado()
