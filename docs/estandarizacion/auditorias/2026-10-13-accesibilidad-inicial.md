# Auditoría de accesibilidad visual inicial (FNC-001)

- Fecha: 2026-10-13. Rama: `fnc/FNC-001-incorporacion-metodo`. Modo: diagnóstico, sin modificar código.
- Alcance: `frontend/` (Next.js 15 + Tailwind). Tokens en `frontend/src/styles/tokens.css`, config en `frontend/tailwind.config.ts`, componentes en `frontend/src/components`, estilos en `frontend/src/styles/{components,global}.css`.
- Método: fórmula WCAG de luminancia relativa; los colores con alpha se componen sobre el fondo real (panel sobre body; tinte sobre panel). Script de cálculo en el scratchpad de la sesión (no está en el repo). Umbrales: 4.5 texto normal, 3 texto grande (>=24 px, o >=18.66 px en negrita), íconos y bordes de control.
- Leyenda: `*` = entre 3 y 4.5 (falla como texto normal), `!` = menor que 3.

## 0. Hallazgo estructural: el tema no se puede cambiar y `dark:` nunca se activa

- `tokens.css` define 7 contextos: `:root/html.light`, `@media (prefers-color-scheme: dark)` (`:root:not(.light)`, línea 207), `html.dark` (271) y 4 temas (`theme-emerald-light` 331, `theme-obsidian-dark` 400, `theme-rose-light` 468, `theme-violet-dark` 537).
- Búsqueda `classList|documentElement|theme-emerald` en `frontend/src`: solo aparece en `tokens.css`. Ningún componente aplica `dark`, `light` ni `theme-*` a `<html>` (`app/layout.tsx:20`). Consecuencias:
  1. Con `darkMode: 'class'` (`tailwind.config.ts:16`) las variantes `dark:` de Tailwind nunca se activan. El usuario con SO oscuro ve texto de tema claro (`text-red-600`, `text-emerald-600`, `text-amber-600`) sobre fondo oscuro.
  2. Con SO oscuro solo aplica el bloque `@media` (35 tokens). No define las 8 parejas `--badge-*`, así que las insignias usan los valores del tema claro sobre fondo oscuro.
  3. Los 4 temas con nombre, `html.dark` y `.light` son código inalcanzable hoy. Se miden igual porque el portal original los activaba y el clon los hereda.
- Falta decidir si se implementa el selector de tema (tarea FNC) o se elimina el código muerto.

## 1. Tokens medidos

Texto sobre superficie, fondo real compuesto. Columnas: claro (`:root`), SO-oscuro (`@media`), `html.dark`, emerald (claro), obsidian (oscuro), rose (claro), violet (oscuro).

| par | claro | SO-osc | html.dark | emerald | obsidian | rose | violet |
|---|---|---|---|---|---|---|---|
| body-text / body-bg | 17.06 | 16.33 | 16.30 | 16.74 | 15.68 | 15.92 | 15.00 |
| header-text / header-bg | 5.17 | 8.40 | 8.40 | 3.77* | 13.96 | 3.67* | 11.72 |
| panel-header-text / panel-header-bg | 8.40 | 6.12 | **1.50!** | 9.13 | **1.44!** | 8.63 | **1.61!** |
| button-text / button-bg (primary) | 5.17 | 5.17 | 5.17 | 3.77* | 7.76 | 3.67* | 4.23* |
| tab-active-text / bg | 5.17 | 5.17 | 5.17 | 3.77* | 7.76 | 3.67* | 4.23* |
| tab-inactive-text / inactive-bg | 5.87 | 5.71 | 5.71 | 10.18 | 5.81 | 6.58 | 6.12 |
| label-text / panel | 10.35 | 6.96 | 6.96 | 7.63 | 6.91 | 7.63 | 6.92 |
| label-text / input-bg | 10.35 | 5.71 | 5.71 | 7.63 | 5.81 | 7.63 | 6.12 |
| input-text / input-bg | 17.85 | 11.87 | 11.87 | 17.49 | 11.74 | 17.49 | 12.82 |
| bi-text-main / panel | 17.85 | 14.48 | 14.48 | 17.49 | 13.96 | 17.49 | 14.48 |
| bi-text-muted / panel | 4.76 | 6.96 | 6.96 | 4.80 | 3.67* | 4.80 | 7.34 |
| bi-text-muted / surface-container | 4.34* | 5.71 | 5.71 | 4.40* | 3.08* | 4.37* | 6.50 |
| secondary / panel | 4.76 | 3.75* | 3.75* | 4.80 | 3.67* | 4.80 | 7.34 |
| primary como texto / body | 4.94 | 3.90* | 3.45* | 3.61* | 7.76 | 3.34* | 4.61 |
| primary como texto / panel | 5.17 | 3.45* | 3.45* | 3.77* | 6.91 | 3.67* | 4.44* |
| success / panel | 3.77* | 4.74 | 4.74 | 3.77* | 10.17 | **2.28!** | 9.79 |
| accent-peach (KPI) / panel | **2.15!** | 8.31 | 8.31 | **2.15!** | 11.57 | **2.26!** | 8.32 |
| accent / panel | 5.70 | 3.13* | 3.13* | 3.74* | 11.57 | 3.67* | 4.44* |
| accent-sky / panel | **2.43!** | 7.35 | 7.35 | **2.49!** | 6.91 | **2.69!** | 6.92 |
| brand / panel | 7.90 | **2.26!** | **2.26!** | 5.48 | 3.67* | 4.70 | 3.30* |
| ntf-text-subject / ntf-card | 5.17 | 9.65 | 6.96 | 3.77* | 6.91 | 3.67* | 6.92 |
| status-active / panel | 5.17 | 9.29 | 9.29 | 3.77* | 10.17 | 3.67* | 9.79 |
| button-disabled-text / bg (exento) | 1.73! | 1.73! | 1.73! | 1.69! | 1.93! | 1.69! | 1.79! |

Elementos no textuales (umbral 3:1): `input-border` / panel 1.48 (claro), 1.72 (oscuro), 1.41 (rose); `panel-border` / body 1.42 a 2.09. Ningún borde de campo llega a 3:1 en ningún tema.

Notas sobre la tabla:
- `panel-header-text` solo se redefine en el bloque `@media` (línea 217-ish, `96 165 250`). Los bloques `html.dark`, `obsidian` y `violet` no lo definen y heredan `30 58 138` (azul 900) del claro sobre un fondo oscuro. Se usa en el título de todos los modales (`form.tsx:138`).
- Insignias `.nx-badge-*` (texto 10 px negrita, sobre su tinte compuesto sobre panel):

| tema | primary | success | error | warning | violet | sky | slate | cyan |
|---|---|---|---|---|---|---|---|---|
| claro / emerald / rose | 5.83 | 4.86 | 5.37 | 4.52 | 6.13 | 5.37 | 8.91 | 6.46 |
| `html.dark` | 6.12 | 7.34 | 5.76 | 8.33 | 5.58 | 8.13 | 9.40 | 9.09 |
| SO-oscuro (sin tokens badge) | **2.44!** | **2.92!** | **2.69!** | 3.18* | **2.34!** | **2.61!** | **1.62!** | **2.19!** |
| obsidian (sin tokens badge) | **2.44!** | **2.91!** | **2.65!** | 3.12* | **2.33!** | **2.61!** | **1.61!** | **2.19!** |
| violet-dark (sin tokens badge) | **2.59!** | 3.15* | **2.82!** | 3.39* | **2.46!** | **2.81!** | **1.72!** | **2.35!** |

## 2. Hallazgos (por causa, de más grave a más marginal)

### Confirmados

**H-01. Tokens de texto de modales y panel en oscuro sin definir (ilegible).** `--color-panel-header-text` heredado del claro: 1.50 en `html.dark`, 1.44 en obsidian, 1.61 en violet.
Ubicaciones: tokens `tokens.css:271-329` (sin la variable), `:400-466`, `:537-597`; consumo en `components/form.tsx:138` (título de todos los modales: usuarios, áreas, plataformas, confirmaciones). Corrección en el token.

**H-02. Insignias `.nx-badge-*` ilegibles con SO oscuro.** 1.62 a 3.18 (slate 1.62, violet 2.34, primary 2.44). El bloque `@media dark` (`tokens.css:207-250`) y los temas obsidian/violet no definen `--badge-*`. Consumo: `components/ui.tsx:101-104` (`Badge`), usado en `platform-card.tsx` (estado y "Sin enlace"), listas de usuarios, auditoría y plataformas. Corrección en tokens.

**H-03. Gráfica del dashboard con variables inexistentes.** `components/dashboard.tsx:54,59,67,71-74` usa `--nx-muted`, `--nx-panel`, `--nx-content`, que no están definidas en ningún archivo (`grep` sobre `frontend/src`: 0 definiciones). `--nx-border` existe (`components.css:1146`) pero ya trae `rgb(...)`, así que `rgb(var(--nx-border))` es inválido. Resultado: etiquetas de ejes con el fill por defecto de SVG (negro) sin tema (sobre panel oscuro `15 23 42` ~1.1:1), tooltip y cuadrícula sin estilo. Pantalla: Dashboard (`/`). Además, texto de eje de 11 px.

**H-04. Colores Tailwind literales con `dark:` inoperante (texto de tema claro en SO oscuro).** Con SO oscuro `dark:` no se activa (sección 0):
- `text-red-600` (botón "Eliminar") sobre panel oscuro: 3.70 (SO-oscuro), 3.67 (obsidian), 3.90 (violet). En claro 4.83 pasa. `areas-list.tsx:200`, `users-list.tsx:526`, `platform-admin.tsx:277`.
- `text-emerald-600` ("Guardado", confirmaciones) sobre panel claro: **3.77** (falla incluso en claro); sobre tinte 15 %: 3.14. `settings-panel.tsx:17,189,377,617`; `notifications-list.tsx:16`.
- `text-amber-600` sobre tinte 15 %: 2.71 en claro. `notifications-list.tsx:18`.
- `text-red-600` sobre `bg-red-500/15`: 3.82 (claro), 3.37 (oscuro). `notifications-list.tsx:17`.
- Estrella de favorito `text-amber-400` (ícono, requiere 3:1) sobre panel claro: **1.67**. `platform-card.tsx:66`. Pantallas: Plataformas, Favoritos, Notificaciones, Ajustes, Áreas, Usuarios.
- Corrección propuesta: tokens semánticos por tema (sección 3), no clases literales.

**H-05. Texto sobre color primario en temas de marca.** Botón primario (`.nexus-btn-primary`, `color: white !important`, `components.css:1526-1530`, 11 px negrita, texto normal) y pestañas activas: emerald 3.77, rose 3.67, violet 4.23, obsidian **2.56** (blanco sobre zinc-400; el token `--button-text` oscuro `9 9 11` da 7.76 pero el CSS lo ignora). Mismo valor para `header-text/header-bg` en emerald (3.77) y rose (3.67). Botones `text-white` con `bg-primary`: `app/not-found.tsx:15`, `app/error.tsx:32`. Botón peligro `!bg-error` (`#ef4444`) con texto blanco: 3.76 en todos los temas (`form.tsx:84`).

**H-06. Colores de marca usados como texto o ícono sin variante por tema.**
- `primary` como texto (enlace "Editar", nav activo `app-shell.tsx:55-56`, chips `users-list.tsx:48-50`): claro 5.17, pero 3.45 (SO-oscuro/dark), 3.77 (emerald), 3.67 (rose), 4.44 (violet). Nav activo (primary sobre `primary/15`): 4.19 claro, 3.01 oscuro, 3.14 emerald, 3.01 rose.
- `brand` / `accent` sobre panel: brand 2.26 en oscuro (el valor de `:root` índigo 700 no se reasigna en `@media`/`html.dark`).
- `accent-peach` / KPI `text-warning` (`#f59e0b` fijo en `tailwind.config.ts:80`): 2.15 en claro. `accent-sky`: 2.43 en claro.
- `text-error` (`#ef4444`, `tailwind.config.ts:81`): 3.76 sobre panel claro, y 3.30 sobre `bg-error/10` (la caja de `ErrorNote`, `ui.tsx:60`, texto 14 px negrita: no califica como grande). Falla en claro.
- `warning`, `error`, `info` están como hex literal en la config de Tailwind, fuera de `tokens.css`.

**H-07. Texto atenuado por opacidad.** `text-label/60` en pistas y vacíos: 3.35 (claro), 3.31 (oscuro), 2.88 (emerald/rose). `ui.tsx:91` (`EmptyNote`), `form.tsx:29` (hint de campos, 12 px). Placeholder `placeholder:text-label/30`: 1.61 a 1.75 (`form.tsx:38`). Tarjetas leídas `opacity-70` (`notifications-list.tsx:84`) y plataformas sin enlace `opacity-70` (`platform-card.tsx:103`): `label` baja a ~4.05 oscuro / 4.35 claro y a 3.59 en emerald/rose.

**H-08. Tokens de texto atenuado por debajo de 4.5.** `bi-text-muted` sobre surface-container: 4.34 claro, 4.40 emerald, 3.08 obsidian; sobre panel obsidian 3.67. `secondary` (`#64748b`) sobre panel con SO oscuro: 3.75. Uso: `StatTile` hint (`ui.tsx:44`, 12 px).

**H-09. Hover del botón secundario.** `.nexus-btn-secondary:hover` pone `primary` sobre `primary/5`: 2.71 (oscuro), 3.26 (emerald), 3.14 (rose), 4.42 (claro). `components.css:1544-1548`.

**H-10. Texto de color arbitrario del usuario.** `area.color` sobre su tinte `${color}22` (`areas-list.tsx:156`, `platform-card.tsx:83-85`): con el valor por defecto `#6366f1` da 3.78 (claro) y 3.48 (oscuro). `platform.bg_color`/`text_color` (`platform-card.tsx:52`, `platform-admin.tsx:236`) no se validan contra 4.5. Falta validación de contraste en el formulario (campos de color en `platform-admin.tsx:137-145`, `areas-list.tsx:86`). Gráfica: barras `#6366f1` literal (`dashboard.tsx:79`).

**H-11. Bordes de campos y paneles bajo 3:1.** `input-border`/`panel-border`: 1.4 a 2.1 en todos los temas (WCAG 1.4.11). Los inputs se distinguen del fondo solo por ese borde. Además `outline: none` en inputs (`form.tsx:39`, `components.css:761`) y foco solo con `ring-primary/20` (casi invisible) y cambio de borde primario; no hay `:focus-visible` en ningún CSS (0 resultados). Los enlaces/botones usan el foco nativo salvo `outline-none` en campos.

### Tamaños y áreas táctiles

**H-12. Texto menor al mínimo web (12 px).** Evidencia de CSS:
- `components.css:672` 9 px (`.stacked-bar-label`), `:254` 10 px (`.nx-badge`), `:1654` 10 px (`.nexus-checkbox:checked::after`), `:185`, `:1489`, `:1504` 11 px (cabeceras de tabla, contador del tour, `.nexus-btn` en todo botón de la app).
- `platform-admin.tsx:235` `text-[10px]` (iniciales); `dashboard.tsx:59,67` 11 px.
- Valor mágico fuera de la escala: la escala `--text-2xs: 10px` (`tokens.css:160`) es la que permite 10 px; el mínimo del proyecto debería ser 12 px.

**H-13. Áreas táctiles.** Los botones de acción de fila ("Editar", "Eliminar") son `px-2 py-1 text-xs` (~24 px de alto, ancho ~50 px): `areas-list.tsx:189-203`, `users-list.tsx:516-528`, `platform-admin.tsx:267-279`. Cumplen el mínimo WCAG 2.2 (24x24) por muy poco y no los 44-48 px. Chips de selección `px-2.5 py-1 text-xs` (`users-list.tsx:41-55`, ~26 px de alto). Estrella de favorito `p-1 text-lg` (~32 px, `platform-card.tsx:58-64`). Botón de cerrar del modal 36x36 (`form.tsx:142-148`). Los botones `.nexus-btn` miden 48 px (correcto).

**H-14. Semántica y nombres accesibles.**
- Botones "Editar"/"Eliminar" repetidos sin nombre contextual (`aria-label` con el nombre de la fila): los lectores de pantalla oyen "Editar" N veces (3 pantallas).
- `title=` se usa como nombre del modal (`Modal title`), no como tooltip; ningún botón de solo ícono sin `aria-label` (favorito y cerrar sí lo tienen: correcto).
- Los `<th>` no llevan `scope` (`audit-log.tsx:67-71`, `platform-admin.tsx:222-226`); el `<th>` vacío de acciones (`platform-admin.tsx:226`) no tiene texto oculto.
- Los íconos de estado en notificaciones son `aria-hidden` con carácter de tipo (correcto) pero el tipo (éxito/error) solo se distingue por color y un glifo `ICONS` (`notifications-list.tsx:88`), sin texto accesible.
- Positivo: `nav aria-label`, `aria-current`, `role="alert"`, `role="status"`, `aria-pressed`, `aria-modal`, `lang="es"`, `aria-label` en búsquedas y filtros.

**H-15. Colores literales fuera de tokens.** 74 coincidencias en CSS (`grep -cE "#[0-9a-fA-F]{3,8}\b|rgba?\([0-9]"`: `global.css` 26, `components.css` 48), p. ej. `global.css:199-200` (`#f43f5e` de validación), `:218,237,324,336` (fondos rgba de diálogos); `tailwind.config.ts:79-81` (`warning`, `error`, `info`); `#6366f1` en `platform-admin.tsx:17,137`, `areas-list.tsx:30,86`, `dashboard.tsx:79`; `bg-black/60` en el fondo del modal (`form.tsx:125`, aceptable como scrim).

### Dudosos (requieren verificación visual o decisión)
- D-01. Contraste real de `.nx-modal-glass` y fondos rgba de `global.css:218-336`: el fondo depende de lo que haya detrás (transparencia).
- D-02. `panel-header-bg` con alpha (oscuro) compuesto sobre `panel-fill`; se asumió ese fondo.
- D-03. `html.dark` y los temas no son alcanzables hoy (sección 0). Si se decide eliminarlos, H-01 y parte de H-05 pasan a ser código muerto.
- D-04. Clases `.badge-nexus`, `.badge-pending`... (`components.css:982-1062`) y `.nx-tour-*`, `.dt-*`, `table.dataTable`: no se encontraron llamadores en `frontend/src` (`grep`), son CSS heredado del portal. Reportar aparte; no medidos.

## 3. Tokens semánticos propuestos (con razón calculada)

Valores sobre panel claro `255 255 255` y panel oscuro `15 23 42`:

| token propuesto | claro | razón | oscuro | razón |
|---|---|---|---|---|
| `--color-text-success` | `4 120 87` (emerald-700) | 5.48 | `52 211 153` | 9.29 |
| `--color-text-danger` | `190 18 60` (rose-700) | 6.32 aprox. | `251 113 133` | 6.9 aprox. |
| `--color-text-warning` | `180 83 9` (amber-700) | 5.0 aprox. | `251 191 36` | 10.69 |
| `--color-text-primary` (enlaces) | `29 78 216` (blue-700) | 6.7 aprox. | `96 165 250` | 6.9 aprox. |
| `--color-panel-header-text` en `html.dark`, obsidian, violet | n/a | n/a | `96 165 250` / `212 212 216` / `167 139 250` | 7.0 / 11 / 6.9 aprox. |
| `--color-on-primary` por tema | `255 255 255` en claro y SO-oscuro (5.17); emerald con `4 120 87` como primary (5.48); obsidian `9 9 11` (7.76); rose con primary `190 18 60` (6.32 aprox.) | | | |
| `--badge-*` en `@media`, obsidian, violet | copiar el bloque de `html.dark` | 5.58 a 9.40 | | |

Las razones marcadas "aprox." están estimadas con la escala Tailwind y deben recalcularse con el script al implementar. Las cifras sin "aprox." salen de la medición de esta auditoría (emerald-700 sobre blanco 5.48, `52 211 153` y `251 191 36` sobre panel oscuro).
Otras propuestas: función/utilidad `onColor(fondo)` para elegir texto blanco u oscuro según luminancia; validar `bg_color/text_color/area.color` con esa función en los formularios; `--text-min: 12px` y subir `.nx-badge`, `.nexus-btn`, cabeceras y ejes a 12 px.

## 4. Pruebas automáticas

- Estado: no existen. `package.json` solo tiene `dev`, `build`, `start`, `lint`, `typecheck`; no hay carpeta de pruebas ni archivos `*.test.*` en `frontend/`.
- Esbozo propuesto (`frontend/tests/contraste.test.ts`, Vitest): leer `tokens.css`, resolver `var()`, componer alpha, calcular la razón y comprobar, por cada contexto (7), los pares de la tabla de la sección 1 con umbral 4.5 (texto) o 3 (bordes de control, íconos); lista de excepciones: `button-disabled-*`. Segunda prueba (`tokens.test.ts`): recorrer `src/**/*.tsx` y fallar con `#hex`, `rgb(`, clases Tailwind de paleta (`text-red-600`, etc.) y `text-[Npx]` con N menor que 12, y comprobar que cada token definido en `:root` existe en los otros contextos (detecta H-01 y H-02).

## 5. Conteos y comandos

- Contextos de tema medidos: 7. Pares de tokens de texto: 25 por 7 contextos (175 celdas), más 2 de borde y los pares de uso real de la sección 1 y H-04 a H-10.
- Fallas confirmadas de texto bajo 3:1 (`!`) en tokens: 12 celdas de texto (7 son de deshabilitado, exentas, o sea 5 reales); entre 3 y 4.5: 42 celdas; ninguno de los 14 bordes llega a 3:1. Insignias: 21 de 24 celdas fuera de rango en los 3 contextos oscuros sin tokens badge.
- Comandos: `grep -rnE "text-(white|amber)|style=\{\{|<button" frontend/src`; `grep -rn "classList|documentElement" frontend/src` (0 en componentes); `grep -cE "#[0-9a-fA-F]{3,8}\b|rgba?\([0-9]" frontend/src/styles/*.css`; `grep -rn "nx-muted|nx-panel|nx-content" frontend/src`.
