"""Consultas de la bitácora de ejecuciones (FNC-062, contrato
`conectores-y-ejecuciones.md`).

- Alcance: el superadmin ve todo; el admin de área, los trabajos cuyo
  `area_id` (el área de la plataforma al encolar) es de las que administra;
  un trabajo con el área borrada (`NULL`) solo lo ve el superadmin.
  Decisión del orquestador (pendiente de validar en la prueba de concepto).
- Orden fijo: `created_at` descendente (y `id` para desempatar).
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.authz import is_admin, managed_area_ids
from app.modules.provisioning.models import ProvisioningJob


@dataclass(frozen=True)
class FiltrosTrabajos:
    status: Optional[str] = None
    operation: Optional[str] = None
    provider: Optional[str] = None
    area_id: Optional[int] = None
    platform_id: Optional[int] = None
    user_id: Optional[int] = None
    access_id: Optional[int] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None  # exclusivo


def a_utc(instante):
    """Instante de `leer_filtros` (hora local sin zona) → UTC sin zona, como
    se guardan los trabajos (`reloj.ahora`)."""
    if instante is None:
        return None
    return instante.astimezone(timezone.utc).replace(tzinfo=None)


def visibles(actor):
    """Trabajos que `actor` (superadmin o admin de área) puede ver."""
    if is_admin(actor):
        return ProvisioningJob.query
    return ProvisioningJob.query.filter(
        ProvisioningJob.area_id.in_(managed_area_ids(actor)))


def filtrar(consulta, filtros):
    columnas = (('status', ProvisioningJob.status),
                ('operation', ProvisioningJob.operation),
                ('provider', ProvisioningJob.provider),
                ('area_id', ProvisioningJob.area_id),
                ('platform_id', ProvisioningJob.platform_id),
                ('user_id', ProvisioningJob.user_id),
                ('access_id', ProvisioningJob.access_id))
    for campo, columna in columnas:
        valor = getattr(filtros, campo)
        if valor is not None:
            consulta = consulta.filter(columna == valor)
    if filtros.desde is not None:
        consulta = consulta.filter(ProvisioningJob.created_at >= filtros.desde)
    if filtros.hasta is not None:
        consulta = consulta.filter(ProvisioningJob.created_at < filtros.hasta)
    return consulta


def ordenados(consulta):
    return consulta.order_by(ProvisioningJob.created_at.desc(),
                             ProvisioningJob.id.desc())
