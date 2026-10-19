# DIS-001 — Completar tokens por tema: panel-header-text, badge, on-primary, brand y accent en oscuro

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
| **Rama** | `dis/DIS-001-tokens-por-tema` (worktree `pokemon-wt-d001`) |
| **Commits / PR** | `a46ee94` (local, sin push ni PR) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
Título de modales 1.44-1.61 en oscuro; insignias 1.61-3.39 en SO oscuro, obsidian y violet.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-01, H-02, H-05, H-06

## Objetivo
Todos los pares texto/fondo de DIS-001 a >= 4.5:1 en los 7 contextos de `tokens.css`, sin cambiar la identidad de color (el dueño rediseña al final).

## Alcance
- **Incluye:** `--color-panel-header-text` y `--badge-*` donde faltaban; `--color-on-primary` y `--color-primary-solid`; variantes de texto `--color-{primary,brand,accent,accent-sky,accent-peach}-text` por tema; `text-primary` → `text-primary-text` (9 usos); header de emerald y rose un tono más oscuro.
- **No incluye:** `success`/`danger`/`warning` y clases Tailwind literales (DIS-002); `.nexus-btn-primary` y `button-*` (DIS-004, puede usar `primary-solid`/`on-primary`); `color: rgb(var(--color-primary))` heredado en `components.css`/`global.css` (DIS-009); selector de tema.

## Decisiones (del orquestador, pendientes de validar en la prueba de concepto)
- Color de marca como texto: variante `*-text` por tema; el token base queda como relleno. Los pares de prueba `primary/…`, `brand/…`, `accent*/…` pasan a medir la variante (`*-text/…`).
- Relleno con texto encima: `--color-primary-solid` (= primary salvo emerald 700, rose 600, violet 600) y `--color-on-primary` (blanco; obsidian `9 9 11`). Se conserva el texto blanco y se oscurece un tono el relleno.
- Header emerald `#059669` → `#047857` y rose `#f43f5e` → `#e11d48` (mismo tono, un paso más oscuro).
- Insignias de SO oscuro, obsidian y violet: mismos valores que `html.dark`.
- `primary-text/primary-15` y `/primary-10` nuevos (entrada activa del menú, chips, hover de Editar).

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados (H-01, H-02, H-05 header/pestaña, H-06 marca como texto)
- [x] Prueba de regresión que primero falla (`texto-de-marca.test.ts`: 9 usos de `text-primary` antes del cambio; 56 `it.fails` que empezaron a pasar)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Verificación
| Comando (`frontend/`) | Resultado real |
|---|---|
| `npm ci` | código 0 |
| `npm test` | código 0; 14 archivos; 399 passed, 32 expected fail (antes: 88 expected fail) |
| `npm run lint` | código 0; sin avisos |
| `npm run typecheck` | código 0 |
| `npm run build` | código 0 |

- Contraste: 56 celdas pasaron de falla a cumple (47 de DIS-001 + 9 de `primary` de DIS-002); 21 celdas nuevas (`primary-text/primary-15`, `/primary-10`, `on-primary/primary-solid`) cumplen. Mínimo medido 4.52 (`badge-warning` claro, sin cambio).
- Medido (WCAG, `tests/accesibilidad/medir.ts`):

| par | claro | so-osc | html.dark | emerald | obsidian | rose | violet |
|---|---|---|---|---|---|---|---|
| header-text/header-bg | 5.17 | 8.40 | 8.40 | 5.48 | 13.96 | 4.70 | 11.72 |
| panel-header-text/panel-header-bg | 8.40 | 6.12 | 6.12 | 9.13 | 10.08 | 8.63 | 6.12 |
| tab-active-text / on-primary sobre primary-solid | 5.17 | 5.17 | 5.17 | 5.48 | 7.76 | 4.70 | 5.70 |
| primary-text/panel | 6.70 | 7.02 | 7.02 | 5.48 | 6.91 | 6.29 | 6.92 |
| primary-text/primary-15 | 5.43 | 6.12 | 6.12 | 4.57 | 5.39 | 5.16 | 5.90 |
| brand-text/panel | 7.90 | 5.98 | 5.98 | 5.48 | 6.91 | 6.29 | 6.92 |
| accent-text/panel | 5.70 | 6.56 | 6.56 | 5.47 | 11.57 | 6.29 | 6.92 |
| accent-sky-text/panel | 5.36 | 7.35 | 7.35 | 5.47 | 6.91 | 6.29 | 6.92 |
| accent-peach-text/panel | 5.02 | 8.31 | 8.31 | 5.02 | 11.57 | 5.18 | 8.32 |
| badge-* (mín.–máx.) | 4.52–8.91 | 5.58–9.40 | 5.58–9.40 | 4.52–8.91 | 5.55–9.30 | 4.52–8.91 | 5.90–10.15 |

- Visual: `next dev` con API simulada local; capturas de `/platforms` (claro/oscuro, 1280 y 390 px) y `/areas` (claro/oscuro, 1280) en el scratchpad. Se ven menú activo, Editar/Administradores e insignias legibles en ambos temas.
- No verificado visualmente: título de modal (requiere abrirlo; medido) y los temas emerald/obsidian/rose/violet/`html.dark` (inalcanzables sin selector; medidos).
- Grep del diff: sin `style=`, `<style`, `.style.`, IPs; colores literales nuevos solo en `tokens.css`.

## Revisiones
- Accesibilidad (auditor-accesibilidad, 2026-10-19, medición propia en 7 contextos): **Con observaciones**. Los pares declarados pasan y no se rompió ninguno de los 7 contextos; observaciones: `components.css` conserva `color: rgb(var(--color-primary))` en estados hover (líneas 91, 803, 1546...; 3.45–3.77:1 en SO oscuro, emerald, rose), y un tema claro (emerald/rose) con SO oscuro y sin `.light` recibiría insignias claras (1.3–2.3:1) por el bloque `:root:not(.light)`.
- Revisor (2026-10-19): **Requiere cambios** (documentación: DIS-002 sin anotar, origen de `--color-header-bg`).
- Correcciones (commit posterior a `9f662bb`):
  - `color:` de texto con `--color-primary` → `rgb(var(--color-primary-text))` en `components.css` (9) y `global.css` (1); dos eran `var(--color-primary)` sin `rgb()` (inválido). Bordes, fondos y tintes quedan con el relleno; el resto del CSS heredado lo depura DIS-009.
  - `texto-de-marca.test.ts` revisa también `color:` en `src/styles/*.css` (falló antes con 10 usos).
  - Bloque oscuro: `:root:not(.light):not([class*="theme-"])`. Emerald/rose con SO oscuro ya no reciben insignias ni `panel-header-text` oscuros; aplican sus contextos medidos (insignias 4.52-8.91, título 9.13/8.63). Obsidian y violet redefinen todo lo del bloque.
  - DIS-002 anotada (absorbe `primary`); `--color-header-bg` con origen; DIS-025 anotada (corte a 390 px).
- Observación sin tarea: los 8 pares `--badge-*` se repiten igual en 4 bloques oscuros.

## Impacto en elementos compartidos
`tokens.css` y `tailwind.config.ts` son compartidos por toda la UI. Salida real de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Usado en (fuera de la tarea) | Nota |
|---|---|---|---|
| `--badge-*-bg` (8) | token CSS | `components.css` (`.nx-badge-*` → `Badge`) | Insignias en SO oscuro, obsidian y violet: tarjetas de plataforma, usuarios, auditoría, áreas |
| `--color-panel-header-text` | token CSS | `components.css` (cabeceras de tabla), `form.tsx` (título de modales) | Solo cambia en `html.dark`, obsidian y violet |
| `--color-accent` | token CSS | `components.css` | Homónimo: coincide por prefijo con `--color-accent-*-text`; su valor no cambió |
| `LogoutView`, `SettingsPanel` | función | `app/logout/page.tsx`, `app/settings/page.tsx` | Solo `text-primary` → `text-primary-text` |
| `color`, `texto`, `remove` | función | backend y otros | Homónimos: helpers locales de prueba / funciones no modificadas que caen en el hunk |

Además `components.css`/`global.css` (`color:` → `primary-text`) y el selector del bloque oscuro (todas las pantallas con SO oscuro).

Vistas a validar: menú lateral (entrada activa), Áreas, Usuarios (chips y Editar), Administrar plataformas (Editar), Ajustes (pestaña activa), Notificaciones (tono info), Cerrar sesión (enlace), insignias en SO oscuro.

## Impacto cruzado
- Depende de → —
- Desbloquea → DIS-004 (`primary-solid`/`on-primary`), FNC-033

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | FNC-070 (auditor-accesibilidad): entrada activa del menú `text-primary` sobre `bg-primary/15` da 4.19 claro y 3.01 oscuro (< 4.5); se reutiliza en las rutas nuevas |
| 2026-10-19 | DIS-017 (auditor-accesibilidad): `nx-badge-warning` del aviso de guardado y "Sin enlace" en temas oscuros; `text-primary` del botón Editar en oscuro; heredado, no corregido en DIS-017 |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador; adelantada de fase 4). Implementada: tokens por tema, `text-primary-text`, pares de prueba y lista de fallas. test/lint/typecheck/build código 0; 56 celdas de contraste pasan. En revisión, sin revisores (por instrucción) |
| 2026-10-19 | Revisiones: accesibilidad Con observaciones, revisor Requiere cambios → corregidos (CSS `color:`, selector del bloque oscuro, documentación). test/lint/typecheck/build código 0. Sigue En revisión |
