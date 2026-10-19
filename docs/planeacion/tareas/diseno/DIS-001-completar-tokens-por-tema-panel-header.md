# DIS-001 — Completar tokens por tema: panel-header-text, badge, on-primary, brand y accent en oscuro

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | tokens |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-001-completar-tokens-por-tema-panel-header` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
Título de modales 1.44-1.61 en oscuro; insignias 1.61-3.39 en SO oscuro, obsidian y violet.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-01, H-02, H-05, H-06

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

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | FNC-070 (auditor-accesibilidad): entrada activa del menú `text-primary` sobre `bg-primary/15` da 4.19 claro y 3.01 oscuro (< 4.5); se reutiliza en las rutas nuevas |
| 2026-10-19 | DIS-017 (auditor-accesibilidad): `nx-badge-warning` del aviso de guardado y "Sin enlace" en temas oscuros; `text-primary` del botón Editar en oscuro; heredado, no corregido en DIS-017 |
