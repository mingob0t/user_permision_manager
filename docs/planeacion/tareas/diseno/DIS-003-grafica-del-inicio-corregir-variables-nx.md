# DIS-003 — Gráfica del inicio: corregir variables --nx-* inexistentes y colores de ejes

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | dashboard |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-003-grafica-del-inicio-corregir-variables-nx` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
`components/dashboard.tsx:54-74` usa variables no definidas.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-03

## Objetivo
Corregir la gráfica "Plataformas por área" para que use solo tokens de tema válidos, con contraste AA y alternativa textual.

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** rediseño visual (lo hace el dueño), cambios al backend ni a `/stats`.

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
| 2026-10-26 | Nota de auditor-accesibilidad (DIS-031/038): `dashboard.tsx:69` y `:87` usan `rgb(var(--nx-border))` (variable de `.nx-*`, no token de tema); queda en esta tarea, fuera del alcance de DIS-031 |

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- Se retira todo `--nx-*` y `rgb(var(...))`: ejes, rejilla, tooltip y barras usan tokens de tema (`--color-label-text`, `--color-panel-border`, `--color-panel-fill`, `--color-body-text`, `--color-primary`)
- Recharts escribe atributos SVG, donde `var()` no es fiable: `useTokenColors` lee el token con `getComputedStyle` y se actualiza al cambiar el tema (clase o `data-theme` de `<html>`) o la preferencia del sistema
- Serie: todas las barras en `--color-primary` (3:1 sobre panel en los 7 temas). El color por área que envía el backend (`color`) y el literal de respaldo `#6366f1` se dejan de usar: un color libre no garantiza 3:1; el nombre del área queda en el eje y en la tabla
- Ticks de 12 px (DIS-007): eje X de 72 px de alto, eje Y de 40 px de ancho y margen de 8 px
- Alternativa textual: tabla `sr-only` con caption "Plataformas por área" y los mismos datos; la gráfica pasa a `aria-hidden`
- Pares nuevos en `pares-contraste.ts`: `grafica-serie/panel` y `grafica-rejilla/panel` (3:1); el texto reutiliza `label-text/panel` y `body-text/panel`
- Tras auditor-accesibilidad (H1): `--color-body-text` está en hex; `useTokenColors` devuelve hex y funciones de color tal cual y envuelve en `rgb()` solo "r g b" y "r g b / a"; pruebas del hook (hex, tripleta, con alfa y cambio de clase en `<html>`)
- Se quita la excepción de `dashboard.tsx` en `colores-literales.excepciones.ts` (0 literales)

## Impacto en elementos compartidos (`impacto.py`, contra `develop`)
| Elemento | Usado en | Nota |
|---|---|---|
| `Dashboard` (`dashboard.tsx`) | `app/page.tsx` | Es la ruta `/`; validar en navegador |
| `useTokenColors` (nuevo, `lib/use-token-colors.ts`) | solo `dashboard.tsx` | Sin otros usos |
| `PARES` (`pares-contraste.ts`) | `contraste.test.ts` | 2 pares nuevos, solo pruebas |
| `contadores` (falso positivo) | — | Ayuda local de `dashboard.test.tsx`; el nombre coincide con otro de `role-summary` y del backend, sin relación |
| `TopeLiterales` | `colores-literales.test.ts` | Se quita la excepción de `dashboard.tsx` (hex 1 → 0) |

## Verificación (2026-10-27, en `frontend/`)
- typecheck 0, lint 0, vitest 0 (1302 pruebas), next build 0; contraste conocido 0, texto mínimo 0, área táctil 0
- No verificado en navegador (tema claro y oscuro, móvil): la gráfica se lee con `getComputedStyle`, solo medida con pares de tokens

| 2026-10-27 | En curso → En revisión: gráfica con tokens, `useTokenColors`, tabla alternativa, 2 pares de contraste; commit `[DIS-003]` |
| 2026-10-27 | Correcciones del auditor: H1 (valor hex en `useTokenColors`, con pruebas), D2 (sin salto y respaldo si falla el resumen), D1 anotada en DIS-037 |
