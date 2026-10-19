"""Plantillas tal como las inserta la migración `0003` (FNC-048).

Las pruebas del servicio las cargan en la BD de pruebas para comprobar el
correo real, no una plantilla de prueba.
"""

import importlib.util
import pathlib

from app import db
from app.modules.notifications.models import NotificationTemplate

RUTA = (pathlib.Path(__file__).resolve().parents[2] / 'migrations' / 'versions'
        / '0003_plantillas_gestor_accesos.py')


def _modulo():
    spec = importlib.util.spec_from_file_location('migracion_0003', RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


PLANTILLAS = _modulo().PLANTILLAS


def cargar_plantillas():
    for datos in PLANTILLAS:
        db.session.add(NotificationTemplate(is_html=True, **datos))
    db.session.commit()
