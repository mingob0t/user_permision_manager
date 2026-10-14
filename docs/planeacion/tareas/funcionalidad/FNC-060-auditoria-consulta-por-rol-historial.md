# FNC-060 — Consulta de auditoría por rol e historial por usuario y por plataforma

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auditoria |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-060-auditoria-consulta-por-rol-historial` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de datos por rol) |

## Contexto
- `GET /audit` (`app/modules/api/routes.py:430-440`) filtra al admin por actor y no por área: ve lo que sus usuarios hicieron en otras áreas (SEG-16)
- No hay historial por usuario ni por plataforma (F-AUD-03)
- Requerimientos: F-AUD-03, F-AUD-04, RF-05

## Objetivo
- Mover la consulta a `app/modules/audit/api.py` con filtros (fecha, evento, usuario, plataforma, área), paginación y visibilidad superadmin todo, admin por área afectada, usuario sus registros; y agregar el historial por usuario y por plataforma

## Alcance
- **Incluye:**
  - `GET /audit` con filtros y paginación (contrato)
  - `GET /audit/users/<id>` y `GET /audit/platforms/<id>`
  - Alcance por `area_id` de FNC-047
- **No incluye:**
  - Exportar (sugerencia)
  - Retención (FNC-018)
  - Pantalla (DIS-020)

## Requisitos de FNC-047 (revisión 2026-10-14)
- Requisito previo de FNC-054 y FNC-056: no se registran eventos con antes/después de accesos sin esta consulta por alcance
- Admin: `area_id IN managed_area_ids()`; eventos sin área solo para el superadmin (SEG-16)
- `before`/`after` solo para el superadmin o dentro del alcance del admin
- `ip` = null para el usuario normal
- `time` en UTC (SEC-AUD-02): pendiente de decisión del dueño (hoy hora local)
- `page` (lista paginada) según el contrato `auditoria.md`

## Hallazgos de seguridad que absorbe
- **FNC-015** (resto): SEG-16. Con FNC-047 cierra FNC-015.

## Archivos previstos
- `app/modules/audit/api.py`
- `app/modules/audit/queries.py`
- `app/modules/api/routes.py` (retiro de `GET /audit`)
- `app/__init__.py` (registro)
- `tests/audit/test_api.py`

## Reutilización
- Modelo de FNC-047
- `managed_area_ids`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `GET /api/v1/audit` | Endpoint | Pantalla `/audit` (`audit-log.tsx`), `lib/api.ts` (`api.audit`) | Pendiente |

## Variables y configuración
- `AUDIT_PAGE_SIZE_MAX` (hoy 500 fijo en `routes.py`): constante registrada.

## Criterios de aceptación
- [ ] Admin del área X no ve eventos del área Y de un usuario compartido (prueba de regresión SEG-16)
- [ ] Usuario ve solo los suyos (prueba)
- [ ] El historial por plataforma de un área ajena responde 403 al admin (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-020
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-047, FNC-038
- Contrato → docs/contratos/auditoria.md

## Riesgos y reversión
- La pantalla actual usa `?limit=`: se mantiene compatible hasta DIS-020.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-14 | Requisitos agregados por la revisión de FNC-047 |
