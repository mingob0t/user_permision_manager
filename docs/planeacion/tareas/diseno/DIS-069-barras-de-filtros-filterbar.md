# DIS-069 — Barras de filtros: todas sobre `FilterBar`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-069-barras-de-filtros-filterbar` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `FilterBar` solo en `access/catalog-filters.tsx`; a mano en `inventory-filters`, `scope-filters`, `audit-filters` y `jobs-filters` (plan §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Una sola barra de filtros con la misma rejilla, alturas y acción de limpiar.

## Alcance
- **Incluye:**
  - `FilterBar` con ranuras para campos, acción limpiar y error de rango (zona reservada)
  - Migrar las 4 barras a mano
  - Retirar sus excepciones
- **No incluye:**
  - Lógica de filtros, parámetros de URL o contratos

## Archivos previstos
- `frontend/src/components/filter-bar.tsx`
- `access/inventory-filters.tsx`, `access/scope-filters.tsx`, `audit/audit-filters.tsx`, `connectors/jobs-filters.tsx`

## Reutilización
`FilterBar`, `TextInput`, `Select`, `limpiarBusqueda`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `FilterBar` | componente | Catálogo, Inventario, Aprobaciones, Auditoría, Ejecuciones | No |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [ ] Filtros con el mismo comportamiento (pruebas de cada pantalla en verde)
- [ ] Campos y botones de la barra a `control-alto`
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §2.6, §4.4
- Depende de → DIS-059

## Riesgos y reversión
Bajo: cambio de marcado, no de lógica.

## Verificación
Pendiente (tarea en Propuesta).

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | | |
| revisor | | |
| auditor-accesibilidad | | |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
