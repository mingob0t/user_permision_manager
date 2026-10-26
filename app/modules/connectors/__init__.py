"""Conectores de plataformas sin Authelia (FNC-050, ADR-005).

- `base.py`: interfaz `Conector`; `registry.py`: tipos registrados;
  `models.py`: configuración por plataforma (`platform_connectors`);
  `validacion.py`: reglas del contrato; `credenciales.py`: resolvedor de
  credenciales con caché; `provider.py`: proveedor `conector` del ejecutor
  (FNC-049); `noop.py`: tipo de prueba; `api_http.py`: tipo `api` (FNC-051)
  con `destino_seguro.py` (DNS e IP públicas) y `http_transporte.py` (HTTPS);
  `ssh.py`: tipo `ssh` (FNC-052) con `ssh_transporte.py` (paramiko).
- `registrar(app)` corre en `create_app()`: registra el proveedor, los tipos `api` y `ssh` y, solo en
  dev (`APP_ENV=development`) o pruebas (`TESTING`), el tipo `noop`.
"""
import os

from app.modules.connectors import api_http, noop, registry, ssh
from app.modules.connectors.credenciales import ENTORNO_DESARROLLO, VAR_ENTORNO
from app.modules.connectors.provider import ProveedorConector
from app.modules.provisioning.providers import registrar_proveedor
from app.modules.provisioning.tipos import PROVEEDOR_CONECTOR


def _dev_o_pruebas(app):
    entorno = (os.environ.get(VAR_ENTORNO) or '').strip().lower()
    return bool(app.config.get('TESTING')) or entorno == ENTORNO_DESARROLLO


def registrar(app):
    registrar_proveedor(PROVEEDOR_CONECTOR, ProveedorConector)
    registry.registrar_tipo(api_http.TIPO)
    registry.registrar_tipo(ssh.TIPO)
    if _dev_o_pruebas(app):
        registry.registrar_tipo(noop.TIPO)
    else:
        registry.quitar_tipo(noop.TIPO.nombre)
