"""Hora del ejecutor: UTC sin zona, para comparar fechas en MySQL y SQLite."""
from datetime import datetime, timezone


def ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)
