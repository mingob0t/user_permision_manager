# DIS-069 — Barras de filtros: todas sobre `FilterBar`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | 2026-10-27 |
| **Estatus Git** | Fusionada |
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
| `FilterBar` | componente | Catálogo, Inventario, Aprobaciones, Auditoría, Ejecuciones | Sí |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [x] Filtros con el mismo comportamiento (pruebas de cada pantalla en verde)
- [x] Campos y botones de la barra a `control-alto`
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [x] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §2.6, §4.4
- Depende de → DIS-059

## Riesgos y reversión
Bajo: cambio de marcado, no de lógica.

## Verificación
Implementada `FilterBar` unificada con soporte de rejilla (`FilterBarGrid`), búsqueda accesible (`FilterBarSearch`), botón limpiar (`FilterBarClear`) y zona reservada para errores de rango (`FilterBarError`) que previene layout shifts. Migradas `inventory-filters.tsx`, `audit-filters.tsx`, `jobs-filters.tsx`. Retirada excepción de `escala-simetria.excepciones.ts`. Pruebas en `barras-de-filtros.test.tsx` (5 pruebas) y suite completa de 65 archivos (2143 pruebas) pasando al 100%.

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | Aprobado | 2026-10-27 |
| revisor | Aprobado | 2026-10-27 |
| auditor-accesibilidad | Aprobado | 2026-10-27 |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
| 2026-10-27 | Implementación unificada de FilterBar y migración completada (disenador-web) |
