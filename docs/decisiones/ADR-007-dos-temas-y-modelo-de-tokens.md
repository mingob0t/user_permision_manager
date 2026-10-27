# ADR-007 — Dos temas y modelo de tokens

- **Estatus:** Propuesta · **Fecha:** 2026-10-27 · **Plan:** [PLAN-FASE-7](../planeacion/PLAN-FASE-7-diseno-visual.md) · **Tareas:** DIS-054, DIS-055, FNC-132

## Contexto
- 7 contextos de tema en `tokens.css`; el dueño pide solo claro y oscuro.
- El oscuro del sistema (`@media`) y `html.dark` difieren hoy en 7 tokens.
- 99 tokens con nombres por pantalla y 23 sin uso; las cuentas guardan `pref_theme` (`sistema` por defecto).

## Decisión 1 — «Según el sistema»
| Alternativa | Pros | Contras |
|---|---|---|
| **A. Se queda (por defecto)** | Respeta la preferencia del SO; no migra las cuentas en `sistema`; sin costo de tercer tema | Exige que el oscuro del SO sea idéntico a `html.dark` |
| B. Se retira | Una opción menos | Hay que decidir por cada cuenta; ignora la preferencia del SO |

## Decisión 2 — Cómo evitar dos oscuros
| Alternativa | Pros | Contras |
|---|---|---|
| **A. Bloque `@media` + prueba de igualdad con `html.dark`** | Funciona sin JS; sin cambio de soporte de navegadores; las pruebas actuales lo leen | Valores escritos dos veces (la prueba impide que diverjan) |
| B. `light-dark()` con `color-scheme` | Un valor por token | Navegadores de 2024 en adelante; reescribir el lector de pruebas |
| C. El script de `<head>` traduce «sistema» a `light`/`dark` y escucha cambios del SO | Un solo bloque oscuro | Depende de JS; sin JS queda claro |

## Decisión 3 — Nombres
| Alternativa | Pros | Contras |
|---|---|---|
| **A. Semánticos nuevos + alias de los heredados hasta DIS-067** | Migración gradual, sin cambio visual por renombre | Convivencia temporal de nombres |
| B. Renombrar todo de una vez | Sin alias | Una tarea enorme (≈ 400 usos) y de alto riesgo |

## Recomendación
- 1A, 2A, 3A.

## Decisión del dueño
- Pendiente.
