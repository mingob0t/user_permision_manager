# DIS-009 — Depurar components.css y global.css: clases sin uso y colores literales a tokens

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | estilos |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-009-depurar-components-css-y-global-css` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
154 de 170 clases sin uso; 260 colores literales fuera de `tokens.css`; modales duplicados.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-03, H-09
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-15, D-04

## Objetivo
_Se completa al aprobar la tarea._

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** _se precisa al aprobar._

## Criterios de aceptación
- [ ] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [ ] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [ ] Cumple `docs/estandarizacion/` y no duplica código existente
- [ ] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → —

## CSS sin uso detectado en DIS-007
- `.stacked-bar-label` (`components.css`): sin llamadores en `frontend/src`.
- `.nx-tour-counter` (`components.css`): sin llamadores.
- Reglas `table.dataTable …` y `.tab-panel-content table …` (cabeceras y filas tipo DataTables): sin llamadores.
- DIS-007 les subió el texto a `var(--text-xs)` solo para que la prueba `texto-minimo.test.ts` cubra todo `src/`; se pueden borrar aquí.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | DIS-007 anota CSS muerto: `.stacked-bar-label`, `.nx-tour-counter`, `table.dataTable` / `.tab-panel-content` |
