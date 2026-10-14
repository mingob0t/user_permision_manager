# FNC-038 — Contratos v1 backend↔web del gestor de accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | contratos |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-038-contratos-gestor-accesos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- No existe `docs/contratos/`
- La fase 3 agrega unos 25 endpoints que consumirá el frontend Next.js y, por el método, el acuerdo de interfaz se integra a `develop` antes de implementar para que backend y web trabajen sobre lo mismo
- Hoy los tipos viven solo del lado web (`frontend/src/lib/types.ts`)
- Requerimientos: todas las F-* de la fase 3

## Objetivo
- Redactar e integrar los contratos versionados, con permisos por rol, validaciones, errores, estados y datos simulados, a partir de la plantilla `~/.claude/plantillas/coordinacion/CONTRATO.md`

## Alcance
- **Incluye:**
  - `docs/contratos/areas-y-roles.md`: alta de área por el admin, asignación de admins (superadmin), creación y elevación de admins
  - `docs/contratos/plataformas-integracion.md`: campos `integration_type` (`ldap`/`conector`) y grupos por nivel
  - `docs/contratos/solicitudes.md`: catálogo solicitable, crear, mis solicitudes, bandeja, aprobar, rechazar con motivo; estados `pendiente`, `aprobada`, `rechazada`
  - `docs/contratos/accesos.md`: accesos por usuario, mis accesos, revocar, inventario; estados del acceso (`en_proceso`, `activo`, `fallido`, `revocando`, `revocado`, `fallo_revocacion`) y origen (`solicitud`, `admin_de_area`, `heredado` si se aprueba FNC-065)
  - `docs/contratos/auditoria.md`: consulta con filtros y paginación, historial por usuario y por plataforma, visibilidad por rol
  - `docs/contratos/conectores-y-ejecuciones.md`: configuración de conectores, bitácora de ejecuciones y reintento
  - `docs/contratos/usuarios-directorio.md`: alta de cuentas en OpenLDAP
  - `docs/contratos/inicio.md`: resumen por rol
  - `docs/contratos/README.md` con el índice y la convención de versiones
  - Mecanismo de actualización de cada pantalla según ADR-006
- **No incluye:**
  - Implementación de endpoints o pantallas
  - Endpoints existentes que la fase 3 no cambia

## Archivos previstos
- `docs/contratos/*.md` (nuevos)

## Reutilización
- Forma de error existente `{"status": "error", "message": ...}` (`app/modules/api/crud.py` `_error`)
- Tipos y nombres actuales de `frontend/src/lib/types.ts` para no renombrar lo existente

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Forma de respuesta de `/api/v1` | Convención de API | Todo el frontend (`lib/api.ts`, `lib/types.ts`) | Pendiente |

## Criterios de aceptación
- [ ] Un contrato por sección, con versión 1 y fecha
- [ ] Cada endpoint declara método, ruta, permiso por rol, entrada con límites, salida con ejemplo y errores
- [ ] Revisado por el dueño (decisiones de las preguntas de FNC-037 reflejadas)
- [ ] Integrado a `develop` antes de iniciar FNC-044 y FNC-069
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → FNC-069 (consumidor web)
- Origen ← FNC-037
- Depende de → FNC-036 (lineamientos de seguridad), Respuestas del dueño a las preguntas P1 a P14 de FNC-037, ADR-006

## Riesgos y reversión
- Un contrato cerrado demasiado pronto obliga a nuevas versiones; se mitiga esperando las respuestas del dueño.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
