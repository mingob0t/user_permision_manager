"""Configuración de los conectores (FNC-050).

- `CONNECTOR_ALLOWED_HOSTS`: lista blanca de nombres de host destino
  (SEC-CON-07), separada por comas. Vacía = ningún destino permitido (lo más
  seguro). Una IP o algo que no sea un nombre de host detiene el arranque.
- `CONNECTOR_TIMEOUT_SECONDS`: tiempo de espera de cada llamada de un
  conector; menor que `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS` para que el
  conector corte antes que RQ.
- `CONNECTOR_CREDENTIAL_CACHE_SECONDS`: vida de la caché en memoria de las
  credenciales (ADR-005); 0 = sin caché.
- `CONNECTOR_SSH_TIMEOUT_SECONDS`, `CONNECTOR_SSH_MAX_OUTPUT_BYTES` y
  `CONNECTOR_SSH_KNOWN_HOSTS_FILE`: plazo único de una operación SSH (red,
  autenticación y comando), límite de
  la salida remota que se lee y `known_hosts` del despliegue del conector
  `ssh` (FNC-052); el tiempo también es menor que el del intento.
- `validar_al_arrancar()` corre en `create_app()`.
"""
import os
import re
from dataclasses import dataclass

from app.modules.directory.configuracion import es_ip_literal
from app.modules.provisioning.configuracion import \
    cargar_configuracion as cargar_aprovisionamiento

VAR_HOSTS = 'CONNECTOR_ALLOWED_HOSTS'
VAR_TIEMPO = 'CONNECTOR_TIMEOUT_SECONDS'
VAR_CACHE = 'CONNECTOR_CREDENTIAL_CACHE_SECONDS'
VAR_SSH_TIEMPO = 'CONNECTOR_SSH_TIMEOUT_SECONDS'
VAR_SSH_SALIDA = 'CONNECTOR_SSH_MAX_OUTPUT_BYTES'
VAR_SSH_KNOWN_HOSTS = 'CONNECTOR_SSH_KNOWN_HOSTS_FILE'
SEPARADOR_HOSTS = ','

# (por defecto, mínimo, máximo) de cada entero.
TIEMPO_ESPERA_SEGUNDOS = (10, 1, 120)
CACHE_SEGUNDOS = (60, 0, 300)
SSH_TIEMPO_SEGUNDOS = (30, 1, 300)
SSH_SALIDA_BYTES = (4096, 1, 65536)

# Nombre de host RFC 1123: etiquetas de 1 a 63 de letras, dígitos y "-".
_ETIQUETA = r'(?!-)[a-z0-9-]{1,63}(?<!-)'
PATRON_HOST = re.compile(rf'{_ETIQUETA}(\.{_ETIQUETA})*')
LARGO_MAXIMO_HOST = 253


class ErrorConfiguracionConectores(RuntimeError):
    """Variable `CONNECTOR_*` inválida."""


@dataclass(frozen=True)
class ConfiguracionConectores:
    hosts_permitidos: frozenset
    tiempo_espera: int
    segundos_cache: int
    ssh_tiempo: int = SSH_TIEMPO_SEGUNDOS[0]
    ssh_maximo_salida: int = SSH_SALIDA_BYTES[0]
    ssh_known_hosts: str = ''


def normalizar_host(host):
    """Host en minúsculas y sin espacios, o `None` si no es un nombre válido
    (incluidas las IP en cualquier forma)."""
    if not isinstance(host, str):
        return None
    limpio = host.strip().lower()
    if (not limpio or len(limpio) > LARGO_MAXIMO_HOST or es_ip_literal(limpio)
            or not PATRON_HOST.fullmatch(limpio)):
        return None
    return limpio


def _leer(entorno, nombre):
    return (entorno.get(nombre) or '').strip()


def _entero(entorno, nombre, limites):
    por_defecto, minimo, maximo = limites
    texto = _leer(entorno, nombre)
    if not texto:
        return por_defecto
    try:
        valor = int(texto)
    except ValueError:
        raise ErrorConfiguracionConectores(
            f'{nombre} debe ser un entero.') from None
    if not minimo <= valor <= maximo:
        raise ErrorConfiguracionConectores(
            f'{nombre} debe estar entre {minimo} y {maximo}.')
    return valor


def _hosts(entorno):
    hosts = set()
    for parte in _leer(entorno, VAR_HOSTS).split(SEPARADOR_HOSTS):
        if not parte.strip():
            continue
        host = normalizar_host(parte)
        if host is None:
            raise ErrorConfiguracionConectores(
                f'{VAR_HOSTS} solo admite nombres de host (nunca IP ni URL).')
        hosts.add(host)
    return frozenset(hosts)


def cargar_configuracion(entorno=None):
    """Lee y valida `CONNECTOR_*`; lanza `ErrorConfiguracionConectores`."""
    entorno = os.environ if entorno is None else entorno
    tiempo = _entero(entorno, VAR_TIEMPO, TIEMPO_ESPERA_SEGUNDOS)
    intento = cargar_aprovisionamiento(entorno).tiempo_intento
    if tiempo >= intento:
        raise ErrorConfiguracionConectores(
            f'{VAR_TIEMPO} debe ser menor que '
            f'PROVISIONING_ATTEMPT_TIMEOUT_SECONDS ({intento}).')
    ssh_tiempo = _entero(entorno, VAR_SSH_TIEMPO, SSH_TIEMPO_SEGUNDOS)
    if ssh_tiempo >= intento:
        raise ErrorConfiguracionConectores(
            f'{VAR_SSH_TIEMPO} debe ser menor que '
            f'PROVISIONING_ATTEMPT_TIMEOUT_SECONDS ({intento}).')
    return ConfiguracionConectores(
        hosts_permitidos=_hosts(entorno), tiempo_espera=tiempo,
        segundos_cache=_entero(entorno, VAR_CACHE, CACHE_SEGUNDOS),
        ssh_tiempo=ssh_tiempo,
        ssh_maximo_salida=_entero(entorno, VAR_SSH_SALIDA, SSH_SALIDA_BYTES),
        ssh_known_hosts=_leer(entorno, VAR_SSH_KNOWN_HOSTS))


def validar_al_arrancar(entorno=None):
    return cargar_configuracion(entorno)


def host_permitido(host, cfg=None):
    """`True` si `host` es un nombre de la lista blanca (SEC-CON-07)."""
    cfg = cfg or cargar_configuracion()
    limpio = normalizar_host(host)
    return limpio is not None and limpio in cfg.hosts_permitidos
