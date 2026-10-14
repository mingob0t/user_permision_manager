"""Catálogo cerrado de eventos de auditoría del gestor de accesos (FNC-047).

- Fuente: `docs/contratos/auditoria.md`, sección "Catálogo de `action`".
- Agregar un valor es aditivo (misma versión del contrato); renombrar o quitar
  uno rompe el filtro `action` de `GET /audit` y requiere una versión nueva.
- Las llamadas heredadas a `add_audit_log` siguen usando texto libre; las tareas
  de la fase 3 registran con un `Evento`.
"""

from enum import Enum

# Valor de `AuditLog.user` cuando actúa el sistema (sin actor humano).
ACTOR_SISTEMA = 'sistema'


class Evento(str, Enum):
    """Valores de `action` del gestor de accesos."""

    AREA_CREADA = 'area_creada'
    AREA_EDITADA = 'area_editada'
    AREA_ELIMINADA = 'area_eliminada'
    ADMIN_ASIGNADO = 'admin_asignado'
    ADMIN_RETIRADO = 'admin_retirado'
    ROL_CAMBIADO = 'rol_cambiado'
    PLATAFORMA_CREADA = 'plataforma_creada'
    PLATAFORMA_EDITADA = 'plataforma_editada'
    SOLICITUD_CREADA = 'solicitud_creada'
    SOLICITUD_APROBADA = 'solicitud_aprobada'
    SOLICITUD_RECHAZADA = 'solicitud_rechazada'
    ACCESO_OTORGADO = 'acceso_otorgado'
    ACCESO_ACTIVO = 'acceso_activo'
    ACCESO_FALLIDO = 'acceso_fallido'
    ACCESO_REVOCADO = 'acceso_revocado'
    REVOCACION_FALLIDA = 'revocacion_fallida'
    CUENTA_DIRECTORIO_CREADA = 'cuenta_directorio_creada'
    CONECTOR_CONFIGURADO = 'conector_configurado'
    CONECTOR_ELIMINADO = 'conector_eliminado'
    CONECTOR_PROBADO = 'conector_probado'
    EJECUCION_REINTENTADA = 'ejecucion_reintentada'
