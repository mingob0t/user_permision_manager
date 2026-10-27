# DIS-043 — Diálogos destructivos con el botón de peligro

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Aprobada** | 2026-10-26 (modo autónomo; dentro de DIS-031/DIS-038) |
| **Rama** | `dis/DIS-031-038-modal` (desde `develop`, d642e1f) |
| **Creada** | 2026-10-26 |

## Contexto
- `reject-dialog.tsx`, `revoke-access-dialog.tsx` y `admin-role-dialog.tsx` usan el botón primario para confirmar porque el `danger` fallaba AA (3,76:1)
- DIS-004 corrigió `danger` (`--color-error-solid`/`--color-on-error`, 4,83:1); los comentarios de esos archivos quedan desactualizados

## Objetivo
- Decidir con el dueño si esas confirmaciones pasan a `danger` (un patrón, una solución) y actualizar los comentarios

## Implementación
| Archivo | Cambio |
|---|---|
| `access/reject-dialog.tsx` | "Rechazar" → `variant="danger"`; comentario actualizado |
| `users/revoke-access-dialog.tsx` | "Revocar" → `danger`; comentario actualizado |
| `users/admin-role-dialog.tsx` | "Quitar admin" → `danger`; "Hacer admin"/"Guardar áreas" siguen primarios; comentarios actualizados |
| `connectors/connector-delete-dialog.tsx` | "Eliminar" → `danger`; comentario actualizado |
| `connectors/job-retry-dialog.tsx` | Sigue primario (reintentar no es destructivo); comentario actualizado |
| `tests/components/dialogos-descripcion.test.tsx` | Variante del botón de cada diálogo |

## Decisiones
Decisión del orquestador (pendiente de validar en la prueba de concepto):
| # | Decisión | Motivo |
|---|---|---|
| 1 | `danger` en rechazar, revocar, quitar admin y eliminar conector | Retiran algo o no se deshacen; un patrón, una solución con `ConfirmDialog` |
| 2 | Primario en aprobar, hacer admin, guardar áreas y reintentar | No destruyen nada |
| 3 | Se mantiene `aria-disabled:opacity-40` y el anillo de foco que ya tenían | Sin cambio de comportamiento; el botón `danger` usa `--color-error-solid`/`--color-on-error` (4,83:1, par `on-error/error-solid` ya medido) |

## Impacto en elementos compartidos
Ninguno modificado: `Button` no cambia, solo la variante elegida en 4 diálogos. Pantallas a validar: `/approvals` (rechazar), `/users` (revocar, quitar admin), `/admin/connectors` (eliminar conector).

## Verificación
- `dialogos-descripcion.test.tsx`: 7 pruebas, salida 0 en la corrida completa (1194 pasan). Contraste del botón `danger`: par `on-error/error-solid` en verde en los 7 temas.
- No verificado en navegador.

## Impacto cruzado
- Origen ← DIS-004

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-26 | Creada como Propuesta desde DIS-004 |
| 2026-10-26 | Aprobada en modo autónomo y resuelta dentro de DIS-031/DIS-038: 4 confirmaciones destructivas a `danger`, comentarios actualizados. En revisión |
| 2026-10-26 | H3 de auditor-accesibilidad: el botón `danger` de `ConfirmDialog` usa `aria-disabled` al enviar, como estos 4 diálogos |
