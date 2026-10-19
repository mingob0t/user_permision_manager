"""Comando del worker: `flask provisioning worker` (FNC-049).

- Exige `REDIS_PASS` (SEG-29) y que Redis responda; si no, sale con código 1
  y un mensaje claro.
- La unidad systemd del despliegue es FNC-067.
"""
import logging

import click
from flask.cli import AppGroup

from app.modules.provisioning.configuracion import (
    ErrorConfiguracionAprovisionamiento, cargar_configuracion)
from app.modules.provisioning.queue import cola, conexion_redis
from app.modules.provisioning.worker import ejecutar

provisioning_cli = AppGroup('provisioning',
                            help='Ejecutor de aprovisionamiento (FNC-049).')

MENSAJE_SIN_REDIS = ('No se pudo conectar con Redis ({}). Revisa REDIS_HOST, '
                     'REDIS_PORT y REDIS_PASS.')


@provisioning_cli.command('worker')
def worker():
    """Procesa la cola de aprovisionamiento hasta SIGTERM o Ctrl+C."""
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    try:
        cfg = cargar_configuracion()
        conexion = conexion_redis()
    except ErrorConfiguracionAprovisionamiento as exc:
        raise click.ClickException(str(exc)) from None
    try:
        conexion.ping()
    except Exception as exc:  # solo el tipo: el mensaje puede traer el host
        raise click.ClickException(
            MENSAJE_SIN_REDIS.format(type(exc).__name__)) from None
    ejecutar(cola(conexion), cfg)
