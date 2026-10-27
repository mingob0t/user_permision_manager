# DIS-043 — Diálogos destructivos con el botón de peligro

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-26 |

## Contexto
- `reject-dialog.tsx`, `revoke-access-dialog.tsx` y `admin-role-dialog.tsx` usan el botón primario para confirmar porque el `danger` fallaba AA (3,76:1)
- DIS-004 corrigió `danger` (`--color-error-solid`/`--color-on-error`, 4,83:1); los comentarios de esos archivos quedan desactualizados

## Objetivo
- Decidir con el dueño si esas confirmaciones pasan a `danger` (un patrón, una solución) y actualizar los comentarios

## Impacto cruzado
- Origen ← DIS-004

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-26 | Creada como Propuesta desde DIS-004 |
