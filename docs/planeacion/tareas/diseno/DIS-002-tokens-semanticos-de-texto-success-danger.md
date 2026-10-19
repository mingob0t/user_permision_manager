# DIS-002 — Tokens semánticos de texto (success, danger, warning) y sustituir clases Tailwind literales

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | tokens |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-19 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-002-tokens-semanticos-texto` (worktree `pokemon-wt-d002`) |
| **Commits / PR** | `6df30b6` (local, sin push ni PR) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
`text-emerald-600` 3.77 en claro; `text-red-600` 3.70 en oscuro; estrella `amber-400` 1.67.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-04, H-06, H-15

## Objetivo
Texto de estado (success, error, warning, info) a >= 4.5:1 en los 7 contextos de `tokens.css` con tokens por tema, sin clases de paleta fija ni literales en `tailwind.config.ts`, sin cambiar la identidad de color (el dueño rediseña al final).

## Alcance
- **Incluye:** `--color-{success,error,warning,info}-text` por tema; rellenos `--color-error` y `--color-info` (valor = literal anterior); `warning`/`error`/`info` de Tailwind a tokens; utilidades `*-text`; reemplazo en 9 componentes; `ntf-text-subject` y `status-active` de emerald/rose; regresión.
- **No incluye:** botones (`!bg-error` de `danger`, `text-white` de `error.tsx`/`not-found.tsx`: DIS-004); `bg-black/60` del overlay y `.border-error` de `global.css` (DIS-012/DIS-009); texto atenuado (DIS-005); `--color-danger` heredado sin uso.

## Decisiones (del orquestador, pendientes de validar en la prueba de concepto)
- Nombre `error` (no `danger`): coincide con la utilidad `error` y `--badge-error-*` que ya usa el marcado. `--color-danger` queda sin uso; unificar con DIS-004.
- Relleno de estado = mismo valor que antes (`#ef4444`, `#f59e0b`, `#3b82f6`): botón Peligro y tintes no cambian. `success` usa su token (`5 150 105`) en vez de `emerald-500` en el tinte de notificaciones.
- Texto claro: tono 700 (`warning` 800, porque 700 da < 4.5 sobre su tinte); oscuro: tono 300, lo que ya usaba `dark:text-*-300`. Ahora también aplica con SO oscuro (antes `dark:` solo con `html.dark`).
- Estrella de favorito: `text-warning-text` (de `amber-400` 1.67:1 a `amber-800` 7.09:1 en claro). Cambio visible necesario para AA.
- `ntf-text-subject`/`status-active` (sin consumidor en React) a Emerald-700 / Rose-700 en emerald/rose.

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados (H-04, H-06 de estado, H-15)
- [x] Prueba de regresión que primero falla (`texto-de-marca.test.ts` + pares nuevos: 69 failed antes del cambio)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Verificación
| Comando (`frontend/`) | Resultado real |
|---|---|
| `npm ci` | código 0 |
| `npm test` antes del cambio (pruebas nuevas) | 2 archivos fallan; 69 failed, 403 passed, 25 expected fail |
| `npm test` | código 0; 14 archivos; 472 passed, 25 expected fail (antes 401 / 32) |
| `npm run lint` | código 0; sin avisos |
| `npm run typecheck` | código 0 |
| `npm run build` | código 0; CSS generado con `text-*-text` y `bg-*/NN` sobre tokens |

- Fallas conocidas: 32 → 25 (las 7 de DIS-002 cumplen; quedan DIS-004 3, DIS-005 8, DIS-006 14).
- Topes de paleta fija: `areas-list`, `notifications-list`, `platform-admin`, `platform-card`, `users-list` salen de excepciones; `settings-panel` 8 → 0.
- Medido (WCAG, `tests/accesibilidad/medir.ts`):

| par | claro | so-osc | html.dark | emerald | obsidian | rose | violet |
|---|---|---|---|---|---|---|---|
| success-text/panel | 5.48 | 11.71 | 11.71 | 5.48 | 11.62 | 5.48 | 12.35 |
| error-text/panel | 6.47 | 9.41 | 9.41 | 6.47 | 9.33 | 6.47 | 9.92 |
| warning-text/panel | 7.09 | 12.38 | 12.38 | 7.09 | 12.29 | 7.09 | 13.05 |
| info-text/panel | 6.70 | 9.90 | 9.90 | 6.70 | 9.82 | 6.70 | 10.44 |
| success-text/success-15 | 4.57 | 9.85 | 9.85 | 4.57 | 8.53 | 4.82 | 9.61 |
| error-text/error-15 | 5.32 | 8.19 | 8.19 | 5.32 | 8.00 | 5.32 | 8.61 |
| warning-text/warning-15 | 6.32 | 9.65 | 9.65 | 6.32 | 9.39 | 6.32 | 10.39 |
| info-text/info-15 | 5.64 | 8.21 | 8.21 | 5.64 | 8.20 | 5.64 | 8.79 |
| error-text/error-10 | 5.68 | 8.65 | 8.65 | 5.68 | 8.49 | 5.68 | 9.11 |
| body-text/warning-10 | 16.54 | 12.43 | 13.99 | 16.21 | 11.82 | 16.21 | 12.65 |
| ntf-text-subject/ntf-card | 5.17 | 10.10 | 7.45 | 5.48 | 7.39 | 6.29 | 7.05 |
| status-active/panel | 5.17 | 9.29 | 9.29 | 5.48 | 10.17 | 6.29 | 9.79 |

- Visual: `next dev` + API simulada local, Chromium sin cabeza; claro/oscuro (SO) en 1280 y 390 px: `/admin/platforms` (tarjeta sin enlace, Eliminar), modal con errores por campo, `/platforms` (estrella), `/notifications` (4 tonos), `/users` con 500 (`ErrorNote`), `/areas`. `getComputedStyle` confirma los valores del token por tema. Capturas en el scratchpad de la sesión.
- No verificado visualmente: "Guardado"/pruebas de Ajustes (requieren acción; medido), temas emerald/obsidian/rose/violet y `html.dark` (sin selector; medidos).
- Grep del diff: sin `style=`, `<style`, `.style.`, IPs; hex solo en comentarios de `tokens.css`.

## Impacto en elementos compartidos
`tokens.css` y `tailwind.config.ts` son compartidos por toda la UI. Salida real de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Usado en (fuera de la tarea) | Nota |
|---|---|---|---|
| `ErrorNote` | función | `app-shell`, `area-admins-panel`, `audit-log`, `dashboard`, `favorites-list`, `login-form`, `platform-catalog`, `platform-form` (+1) | Real: `text-error` → `text-error-text` (todos los errores de carga y "sin permiso" de `RequireRole`) |
| `FieldErrorNote` | función | `platform-form`, `platform-integration-fields` | Real: error por campo de plataformas |
| `TopeLiterales` | tipo | `colores-literales.test.ts` | Solo bajan los topes |
| `archivos`, `body`, `remove`, `save`, `texto` | función | backend y otros | Homónimos: helpers locales de prueba o funciones no modificadas que caen en el hunk |

No los lista `impacto.py`: utilidades `error`/`warning`/`info` de Tailwind (mismo valor; las usan el botón `danger` de `form.tsx` y `ErrorNote`) y los tokens nuevos (sin uso previo).

Vistas a validar: Notificaciones (iconos por tono), Administrar plataformas (tarjeta sin enlace, Eliminar, errores del formulario), Áreas y Usuarios (Eliminar, errores por campo), Catálogo/Favoritos (estrella), Ajustes (mensajes de éxito), cualquier `ErrorNote`.

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | FNC-070 (auditor-accesibilidad): `ErrorNote` `text-error` en claro da 3.30 (< 4.5); lo usa también el estado "sin permiso" de `RequireRole` |
| 2026-10-19 | DIS-017 (auditor-accesibilidad): `text-error` de los errores por campo y de `ErrorNote`; tarjeta `amber` de "sin enlace" y botón Eliminar `text-red-*` en `platform-admin.tsx`; heredado, no corregido en DIS-017 |
| 2026-10-19 | DIS-001 absorbió `primary` como texto (`--color-primary-text`, pares `primary-text/*`); el alcance queda en success, danger y warning y las clases literales |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador; adelantada de fase 4). Implementada: tokens de estado por tema, utilidades sin literales, 9 componentes, regresión (69 failed antes). test/lint/typecheck/build código 0; fallas conocidas 32 → 25. En revisión, sin revisores (por instrucción) |
