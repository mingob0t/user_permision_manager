"""Configuración del acceso a Vaultwarden (FNC-068, ADR-005 alternativa A).

Credencial de arranque: la llave de API y la contraseña maestra de una
**cuenta de servicio** de Vaultwarden con acceso de solo lectura a una única
colección. Van en el `.env` del servidor (600, cuenta de servicio; lo carga
systemd con `EnvironmentFile`), los pone una persona y nunca están en el repo.

- `VAULTWARDEN_URL`: `https://<host>[:puerto][/ruta]`; nombre de host, nunca
  IP; sin usuario, consulta ni fragmento.
- `VAULTWARDEN_CA_CERT_FILE`: CA propia (vacía = CA del sistema). TLS 1.2+
  y certificado siempre validados.
- `VAULTWARDEN_CLIENT_ID` (`user.<uuid>`) y `VAULTWARDEN_CLIENT_SECRET`: llave
  de API **personal** de la cuenta de servicio (una de organización no puede
  descifrar ítems).
- `VAULTWARDEN_EMAIL` y `VAULTWARDEN_MASTER_PASSWORD`: derivan la clave que
  descifra la bóveda del lado del cliente.
- `VAULTWARDEN_COLLECTION_ID`: solo se leen ítems de esa colección.
- `VAULTWARDEN_TIMEOUT_SECONDS`: espera de cada operación de red.

Fuera de desarrollo, si alguna `VAULTWARDEN_*` tiene valor se valida todo al
arrancar; sin ninguna, el proveedor falla cerrado al usarse.
"""
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from app.modules.directory.configuracion import es_ip_literal

VAR_URL = 'VAULTWARDEN_URL'
VAR_CA_CERT_FILE = 'VAULTWARDEN_CA_CERT_FILE'
VAR_CLIENT_ID = 'VAULTWARDEN_CLIENT_ID'
VAR_CLIENT_SECRET = 'VAULTWARDEN_CLIENT_SECRET'
VAR_EMAIL = 'VAULTWARDEN_EMAIL'
VAR_MASTER_PASSWORD = 'VAULTWARDEN_MASTER_PASSWORD'
VAR_COLECCION = 'VAULTWARDEN_COLLECTION_ID'
VAR_TIEMPO_ESPERA = 'VAULTWARDEN_TIMEOUT_SECONDS'
PREFIJO = 'VAULTWARDEN_'

VAR_ENTORNO = 'APP_ENV'
ENTORNO_DESARROLLO = 'development'

# (por defecto, mínimo, máximo) en segundos.
TIEMPO_ESPERA_SEGUNDOS = (5, 1, 30)

ESQUEMA = 'https'
_UUID = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
PATRON_UUID = re.compile(_UUID)
PATRON_CLIENT_ID = re.compile(rf'user\.{_UUID}')
PATRON_CORREO = re.compile(r'[^@\s]+@[^@\s]+')


class ErrorConfiguracionSecretos(RuntimeError):
    """Variable `VAULTWARDEN_*` ausente o insegura (el texto nunca lleva su valor)."""


@dataclass(frozen=True)
class ConfiguracionVaultwarden:
    url: str
    ca_cert_file: str | None
    client_id: str
    client_secret: str = field(repr=False)
    correo: str = field(repr=False)
    contrasena_maestra: str = field(repr=False)
    coleccion_id: str = ''
    tiempo_espera: int = TIEMPO_ESPERA_SEGUNDOS[0]


def _leer(entorno, nombre):
    return (entorno.get(nombre) or '').strip()


def es_desarrollo(entorno=None):
    entorno = os.environ if entorno is None else entorno
    return _leer(entorno, VAR_ENTORNO).lower() == ENTORNO_DESARROLLO


def configurado(entorno=None):
    """`True` si alguna variable `VAULTWARDEN_*` tiene valor."""
    entorno = os.environ if entorno is None else entorno
    return any(clave.startswith(PREFIJO) and (valor or '').strip()
               for clave, valor in entorno.items())


def _requerida(entorno, nombre):
    valor = _leer(entorno, nombre)
    if not valor:
        raise ErrorConfiguracionSecretos(f'Falta {nombre}.')
    return valor


def _secreto(entorno, nombre):
    # Sin `strip()`: un secreto puede empezar o terminar en espacio.
    valor = entorno.get(nombre) or ''
    if not valor.strip():
        raise ErrorConfiguracionSecretos(f'Falta {nombre}.')
    return valor


def _url(entorno):
    url = _requerida(entorno, VAR_URL)
    partes = urlsplit(url)
    if partes.scheme.lower() != ESQUEMA:
        raise ErrorConfiguracionSecretos(f'{VAR_URL} debe usar https://.')
    if partes.username or partes.password or partes.query or partes.fragment:
        raise ErrorConfiguracionSecretos(
            f'{VAR_URL} solo admite esquema, host, puerto y ruta.')
    host = partes.hostname
    if not host or es_ip_literal(host):
        raise ErrorConfiguracionSecretos(
            f'{VAR_URL} debe usar un nombre de host, no una dirección IP '
            '(el certificado se valida contra el nombre).')
    try:
        partes.port
    except ValueError:
        raise ErrorConfiguracionSecretos(
            f'{VAR_URL} tiene un puerto inválido.') from None
    return url.rstrip('/')


def _ca_cert_file(entorno):
    ruta = _leer(entorno, VAR_CA_CERT_FILE)
    if not ruta:
        return None
    if not os.path.isfile(ruta) or not os.access(ruta, os.R_OK):
        raise ErrorConfiguracionSecretos(
            f'{VAR_CA_CERT_FILE} no apunta a un archivo legible.')
    return ruta


def _formato(entorno, nombre, patron, mensaje):
    valor = _requerida(entorno, nombre)
    if not patron.fullmatch(valor):
        raise ErrorConfiguracionSecretos(f'{nombre} {mensaje}')
    return valor


def _tiempo_espera(entorno):
    por_defecto, minimo, maximo = TIEMPO_ESPERA_SEGUNDOS
    texto = _leer(entorno, VAR_TIEMPO_ESPERA)
    if not texto:
        return por_defecto
    try:
        valor = int(texto)
    except ValueError:
        valor = 0
    if not minimo <= valor <= maximo:
        raise ErrorConfiguracionSecretos(
            f'{VAR_TIEMPO_ESPERA} debe ser un entero entre {minimo} y {maximo}.')
    return valor


def cargar_configuracion(entorno=None):
    """Lee y valida `VAULTWARDEN_*`; lanza `ErrorConfiguracionSecretos`."""
    entorno = os.environ if entorno is None else entorno
    return ConfiguracionVaultwarden(
        url=_url(entorno),
        ca_cert_file=_ca_cert_file(entorno),
        client_id=_formato(entorno, VAR_CLIENT_ID, PATRON_CLIENT_ID,
                           'debe ser la llave de API personal (user.<uuid>).'),
        client_secret=_secreto(entorno, VAR_CLIENT_SECRET),
        correo=_formato(entorno, VAR_EMAIL, PATRON_CORREO,
                        'debe ser un correo.'),
        contrasena_maestra=_secreto(entorno, VAR_MASTER_PASSWORD),
        coleccion_id=_formato(entorno, VAR_COLECCION, PATRON_UUID,
                              'debe ser el id (uuid) de la colección.').lower(),
        tiempo_espera=_tiempo_espera(entorno),
    )


def validar_al_arrancar(entorno=None):
    """Fuera de dev y con alguna `VAULTWARDEN_*`, valida todo o detiene el
    arranque. En dev o sin ninguna, `None`."""
    entorno = os.environ if entorno is None else entorno
    if es_desarrollo(entorno) or not configurado(entorno):
        return None
    return cargar_configuracion(entorno)
