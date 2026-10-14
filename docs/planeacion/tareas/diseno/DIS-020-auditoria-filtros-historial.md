# DIS-020 — Auditoría: filtros e historial por usuario y por plataforma

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | auditoria |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-020-auditoria-filtros-historial` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `audit-log.tsx` lista los últimos registros sin filtros, sin detalle de antes y después ni historial (F-AUD-03)
- Requerimientos: F-AUD-01, F-AUD-03, F-AUD-04

## Objetivo
- Filtros (fechas, evento, usuario, plataforma, área), paginación, detalle de cada registro con antes y después legible, y vistas de historial por usuario y por plataforma enlazadas desde Usuarios y Plataformas

## Alcance
- **Incluye:**
  - Filtros con `Select`/`TextInput` existentes (resuelve D-09 en esta pantalla)
  - Detalle en modal con la diferencia antes/después
  - Rutas `/audit/users/[id]` y `/audit/platforms/[id]`
- **No incluye:**
  - Exportar
  - Componente `DataTable` común (DIS-010)

## Archivos previstos
- `frontend/src/components/audit/audit-filters.tsx`
- `frontend/src/components/audit/audit-detail-modal.tsx`
- `frontend/src/components/audit/audit-history.tsx`
- `frontend/src/components/audit-log.tsx`
- `frontend/src/app/audit/users/[id]/page.tsx`
- `frontend/src/app/audit/platforms/[id]/page.tsx`

## Reutilización
- `TextInput`, `Select`, `Modal`, `Badge`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `audit-log.tsx` | Pantalla | `/audit` | Pendiente |

## Criterios de aceptación
- [ ] El JSON de antes/después se muestra como lista de campos, no como texto crudo
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-060
- Contrato → docs/contratos/auditoria.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
