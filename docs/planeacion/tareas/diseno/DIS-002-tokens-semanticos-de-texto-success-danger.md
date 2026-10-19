# DIS-002 — Tokens semánticos de texto (success, danger, warning) y sustituir clases Tailwind literales

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
| **Rama** | `dis/DIS-002-tokens-semanticos-de-texto-success-danger` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
`text-emerald-600` 3.77 en claro; `text-red-600` 3.70 en oscuro; estrella `amber-400` 1.67.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-04, H-06, H-15

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
| 2026-10-19 | FNC-070 (auditor-accesibilidad): `ErrorNote` `text-error` en claro da 3.30 (< 4.5); lo usa también el estado "sin permiso" de `RequireRole` |
| 2026-10-19 | DIS-017 (auditor-accesibilidad): `text-error` de los errores por campo y de `ErrorNote`; tarjeta `amber` de "sin enlace" y botón Eliminar `text-red-*` en `platform-admin.tsx`; heredado, no corregido en DIS-017 |
| 2026-10-19 | DIS-001 absorbió `primary` como texto (`--color-primary-text`, pares `primary-text/*`); el alcance queda en success, danger y warning y las clases literales |
