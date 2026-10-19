# DIS-005 — Texto atenuado con tokens muted de 4.5:1

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | tokens |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-005-texto-atenuado-con-tokens-muted-de` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
`text-label/60` 2.88-3.35, placeholder 1.61-1.75, tarjetas `opacity-70`.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-07, H-08

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
| 2026-10-19 | FNC-070 (auditor-accesibilidad): `EmptyNote` `text-label/60` (3.35 claro, 3.31 oscuro) ya cubierto aquí; lo usan también las rutas reservadas de FNC-070 |
| 2026-10-19 | DIS-017 (auditor-accesibilidad): pista `text-label/60` de `Field` (`form.tsx:29`, 3.35 claro, 3.31 oscuro); DIS-017 usa su propia pista `text-label` fuera de `Field`; `form.tsx` sin tocar |
