# DIS-021 — Inventario de permisos

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | inventario |
| **Prioridad** | Alta |
| **Estatus** | En curso |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local `dis/DIS-021-inventario-permisos` |
| **Rama** | `dis/DIS-021-inventario-permisos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- F-AUD-02 pide ver quién tiene qué plataforma, nivel, desde cuándo y quién aprobó
- Requerimientos: F-AUD-02, F-AUD-04

## Objetivo
- Pantalla `/inventory` con filtros (área, plataforma, usuario, nivel, estado, origen) y paginación, con alcance por rol

## Alcance
- **Incluye:**
  - Tabla responsive con las columnas del contrato
  - Enlaces al historial (DIS-020)
- **No incluye:**
  - Exportar (sugerencia)

## Archivos previstos
- `frontend/src/components/access/inventory-table.tsx`
- `frontend/src/components/access/inventory-filters.tsx`
- `frontend/src/app/inventory/page.tsx`

## Reutilización
- `access-status-badge.tsx`, `Select`, `TextInput`, estados de `ui.tsx`

## Criterios de aceptación
- [ ] En móvil cada fila se presenta como tarjeta legible
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-059
- Contrato → docs/contratos/accesos.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada por el orquestador (modo autónomo) y En curso en el worktree `pokemon-wt-d023` |
