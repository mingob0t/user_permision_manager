# DIS-004 — Botones: texto sobre primary por token, peligro y advertencia, hover del secundario

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-004-botones-texto-sobre-primary-por-token` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
`.nexus-btn-primary` fuerza blanco (`components.css:1526-1530`): 2.56-4.23 según tema.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-05, H-09

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
- Depende de → Depende de DIS-001

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | DIS-002 (revisión): botón `danger` (`form.tsx:84`, `!bg-error`) texto blanco sobre `#ef4444` = 3.76:1 (falla previa, sin cambio en DIS-002). Proponer `--color-error-solid` + `--color-on-error`, como DIS-001 hizo con `primary-solid`/`on-primary` |
| 2026-10-20 | Parte del botón primario resuelta en DIS-015 (auditor-accesibilidad): `.nexus-btn-primary` (`components.css`) usa `--color-primary-solid` y `--color-on-primary` (antes `--color-primary` con blanco: obsidian 2,56, rose 3,67, emerald 3,77, violet 4,23); par `nexus-btn-primary` en la prueba de contraste, pasa en los 7 temas. Sigue pendiente: el par `button-text/button-bg` (tokens `--color-button-*`, sin uso en clases ni componentes; falla conocida en emerald, rose y violet), el botón `danger` (3,76:1) y advertencia/hover del secundario |
