# DIS-009 — Depurar components.css y global.css: clases sin uso y colores literales a tokens

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | estilos |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-009-012-limpieza-css` (junto con DIS-012) |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |
| **Aprobada** | 2026-10-27 (modo autónomo del orquestador, pendiente de validar en la prueba de concepto) |

## Contexto
154 de 170 clases sin uso; 260 colores literales fuera de `tokens.css`; modales duplicados.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-03, H-09
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-15, D-04

## Objetivo
- Dejar `components.css` y `global.css` solo con CSS que algo use y sin colores literales (todo por token), sin cambiar el aspecto: el dueño hace el diseño final.

## Alcance
- **Incluye:** borrar clases, reglas por id, `@keyframes` y variables `--nx-*` sin llamador en `frontend/src`; pasar los colores literales de esos CSS a tokens (existente o nuevo en los 7 temas); pruebas que lo impidan.
- **No incluye:** `tokens.css` (reglas sueltas `.dt-*`, `table.dataTable`, `.animate-shake` → DIS-047); TSX (DIS-012); cambiar el diseño visual; backend.

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados (H-03, H-09; H-15 y D-04 de accesibilidad)
- [x] Prueba de regresión que primero falla: contra el CSS original `colores-literales` falla 2 (components y global) y `css-sin-uso` falla 153
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas (ver Verificación)
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → —

## CSS sin uso detectado en DIS-007
- `.stacked-bar-label` (`components.css`): sin llamadores en `frontend/src`.
- `.nx-tour-counter` (`components.css`): sin llamadores.
- Reglas `table.dataTable …` y `.tab-panel-content table …` (cabeceras y filas tipo DataTables): sin llamadores.
- DIS-007 les subió el texto a `var(--text-xs)` solo para que la prueba `texto-minimo.test.ts` cubra todo `src/`; se pueden borrar aquí.

## Resultado
| Medida | Antes | Después |
|---|---|---|
| Líneas `components.css` | 1746 | 219 |
| Líneas `global.css` | 509 | 56 |
| Clases en los dos CSS | 167 (142 sin uso) | 19 (0 sin uso) |
| Reglas borradas | — | 236 de 2255 líneas, más comentarios huérfanos |
| `@keyframes` borrados | — | 6 (`float`, `shake` ×2, `nexus-pulse`, `nexus-modal-in`, `toastProgress`) |
| Variables borradas | — | `--dt-row-hover`, `--dt-zebra-bg`, `--color-brand-identity-bg/-text`, `--nx-primary` |
| Colores literales en los dos CSS (medidos con la regla de la prueba, sin comentarios) | 92: 18 hex, 61 `rgb()`/`rgba()` numéricos y 13 nombres (`white`) | 0 |
| CSS generado por `next build` | 80 449 bytes (59 237 + 21 212) | 45 208 bytes (−35 241, −44 %) |

### Cómo se comprobó que una clase no se usa (sin falsos negativos)
- `postcss` (de `node_modules`) recorre cada regla; una regla se borra solo si **todos** sus selectores contienen una clase sin uso. Una clase dentro de `:not()`, `:is()` o `:has()` no condena a la regla (solo `.dt-layout-row:has(.dt-paging)` y `table.dataTable:not(.border-separate)`, ya muertas por otra clase).
- Una clase cuenta como usada si aparece como palabra completa en cualquier `.ts`/`.tsx` de `src/` (literales, condicionales, mapas de tonos) **o** si su prefijo se completa al ejecutar: `` `nx-badge-${tono}` `` / `'prefijo-' + x`. Así se conservan `nx-badge-primary|success|error|warning|violet|sky|slate|cyan` (8 clases armadas).
- Se revisó que ninguna prueba, `tailwind.config.ts` ni archivo que no sea `.ts`/`.tsx` en `src/` las use, y que no haya `classList`/`querySelector` con ellas.
- Detalle: `border-error/30` (utilidad de Tailwind en `ui.tsx`) no cuenta como la clase `.border-error`, que tenía `#f43f5e` y no tenía llamador.
- Las reglas por id (`#mainContent`, `#sidebar`, `#sidebarOverlay`, `#toast-container`, `#templateEditor`, `#tab-panel-*`, `#userSearch`, `#platformSearchSub`, `input[id*="Search"]`) se borraron porque ningún `.ts`/`.tsx` tiene esos ids (`input[id*="Search"]` no coincide con ningún `id`).
- Se conserva `thead tr { height: 60px }` (selector de elemento que sí afecta a las tablas) y la parte de `global.css` que sí actúa (raíz, `scroll-bloqueado`, transiciones de vista, flecha de `select`, autocompletado).
- Notas de DIS-007 resueltas: `.stacked-bar-label`, `.nx-tour-counter`, `table.dataTable`, `.tab-panel-content`, `.kpi-conversion-bottom`, `.stacked-segment-secondary` borradas.

### Colores literales → tokens
| Literal | Dónde | Ahora |
|---|---|---|
| `white` (marca ✓ ×2 reglas) | `.nexus-checkbox:checked::after` | `rgb(var(--color-on-primary))` (token existente; igual en 6 temas, oscuro en obsidian) |
| `#ffffff`, `rgba(0,0,0,.15/.2)` | bloque `input[type=range]` | bloque sin llamador: borrado (los tokens `--color-slider-thumb` y `--color-shadow` creados antes se dieron de baja) |
| `#ffffff` | `--color-brand-identity-text` | variable sin uso: borrada |
| `#f43f5e`, `rgba(244,63,94,.15)` | `.border-error` | clase sin uso: borrada |
| `rgba(0,0,0,.45)`, `rgba(99,102,241,.3)`, `white`, `rgba(255,255,255,.05\|.1)` | `#sidebarOverlay`, `#templateEditor` | reglas por id sin elemento: borradas |

## Pruebas nuevas o endurecidas
- `colores-literales.test.ts`: ahora cubre `src/styles/*.css` (menos `tokens.css`), nombres de color en declaraciones CSS (`white`, `black`, `red`...) y descarta comentarios; incluye una prueba del propio detector.
- `css-sin-uso.test.ts` (nueva): cada clase, id, `@keyframes` y `--nx-*` de `components.css` y `global.css` debe tener llamador. Sin falsos positivos: las clases armadas con plantilla (`nx-badge-${tono}`) cuentan; si una debe quedarse hay `CLASES_SIN_LLAMADOR` con motivo (hoy vacío).
- `pares-contraste.ts`: par nuevo `checkbox-marca/relleno` (`--color-on-primary` sobre `--color-primary`, 3:1) en los 7 temas.

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- Borrar también las reglas por id y los `@keyframes`/variables huérfanos, no solo las clases (misma causa: nada del `src` los usa).
- Ajuste tras la auditoría: se borra el deslizador y sus dos tokens (no hay tokens nuevos netos); `.nexus-checkbox` se unifica en una regla con los mismos valores calculados (el `:hover` ya estaba tapado por el borde `!important` y se conserva tal cual); `input[type=text]` y `[type=tel]` salen de la lista de campos (ninguno en `src/`).
- `css-sin-uso.test.ts` ahora ignora comentarios, limita `nx-badge-` a los tonos de `Badge` y exige llamador a ids, elementos y atributos; `sin-estilos-inline.test.ts` detecta spread, objeto suelto y `setAttribute`.
- La ✓ usa `--color-on-primary` (no un token nuevo): es el texto sobre `--color-primary`; solo cambia en obsidian (mejora el contraste).
- No tocar los duplicados `.nexus-checkbox` ni `select { appearance: none }` en los dos CSS: consolidarlos es refactor fuera de alcance (no cambia el aspecto).
- `tokens.css` queda fuera (tiene reglas `.dt-*`, `table.dataTable` y `.animate-shake` sin uso): propuesta DIS-047.

## Verificación (en `frontend/`)
| Comando | Resultado |
|---|---|
| `npx tsc --noEmit` | código 0 |
| `npx next lint` | código 0, sin avisos |
| `npx vitest run` | 39 archivos y 1474 pruebas pasaron, código 0 (repetido 5 veces después; ver nota) |
| `npx next build` | código 0; CSS 80 449 → 45 208 bytes |
- Nota: una corrida de `vitest` dio código 1 una vez (no se guardó el detalle) y las 5 siguientes dieron 0; coincide con la intermitencia conocida de `areas-list.test.tsx` (DIS-040). No se atribuye a este cambio, pero no se pudo reproducir para comprobarlo.
- No verificado en navegador (no se levantó la app): tema claro/oscuro, móvil/escritorio ni la apariencia de la perilla del deslizador y la ✓. Se espera aspecto idéntico (mismos valores); validar en obsidian la ✓.
- Contraste, texto mínimo y área táctil siguen en 0 (sus pruebas pasan).
- No se pidieron `tester`, `revisor` ni auditores (orden del orquestador).

## Impacto en elementos compartidos
**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 9 elemento(s) usados en otras secciones: app/modules, frontend, frontend/src, frontend/tests, migrations/versions, scripts/lineamientos, tests, tests/access, tests/audit, tests/directory, tests/notifications, tests/provisioning. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `archivos` | función | `frontend/tests/accesibilidad/colores-literales.test.ts` | `app/modules/connectors/bd_sentencias.py`, `frontend/tests/accesibilidad/area-tactil.test.ts`, `frontend/tests/accesibilidad/texto-de-marca.test.ts`, `frontend/tests/accesibilidad/texto-minimo.test.ts`, `scripts/lineamientos/reglas.py`, `tests/provisioning/test_versionado.py` | app/modules, frontend/tests, scripts/lineamientos, tests/provisioning | ☐ |
| `body` | función/componente | `frontend/src/components/platform-card.tsx` | `app/modules/api/admin.py`, `app/modules/connectors/http_transporte.py`, `app/modules/notifications/models.py`, `app/modules/notifications/services.py`, `frontend/src/app/layout.tsx`, `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/approve-dialog.tsx`, `frontend/src/components/access/inventory-table.tsx` (+49) | app/modules, frontend, frontend/src, frontend/tests, migrations/versions, tests, tests/notifications | ☐ |
| `border-error` | clase CSS | `frontend/src/styles/global.css` | `frontend/src/components/ui.tsx` | frontend/src | ☐ |
| `literales` | función/componente | `frontend/tests/accesibilidad/colores-literales.test.ts` | `app/modules/connectors/bd_sentencias.py`, `app/modules/connectors/ssh.py`, `frontend/tailwind.config.ts`, `frontend/tests/accesibilidad/area-tactil.test.ts`, `tests/access/test_inventario.py`, `tests/directory/test_config.py`, `tests/provisioning/test_configuracion.py` | app/modules, frontend, frontend/tests, tests/access, tests/directory, tests/provisioning | ☐ |
| `nexus-btn-secondary` | clase CSS | `frontend/src/styles/components.css` | `frontend/src/components/access/inventory.tsx`, `frontend/src/components/audit/platform-audit-history.tsx`, `frontend/src/components/audit/user-audit-history.tsx`, `frontend/src/components/form.tsx`, `frontend/src/components/home/role-summary.tsx`, `frontend/src/components/platforms/platform-integration-fields.tsx`, `frontend/src/components/users/user-access-panel.tsx`, `frontend/tests/accesibilidad/area-tactil.test.ts` (+1) | frontend/src, frontend/tests | ☐ |
| `nexus-checkbox` | clase CSS | `frontend/src/styles/components.css` | `frontend/src/components/form.tsx`, `frontend/src/components/users/area-checklist.tsx` | frontend/src | ☐ |
| `nx-modal-glass` | clase CSS | `frontend/src/styles/components.css` | `frontend/src/components/form.tsx`, `frontend/tests/accesibilidad/velo.test.ts` | frontend/src, frontend/tests | ☐ |
| `remove` | función | `frontend/src/components/areas-list.tsx` | `app/modules/api/routes.py`, `frontend/src/components/connectors/connector-delete-dialog.tsx`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/src/lib/use-scroll-lock.ts`, `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/components/connectors/connectors-admin.test.tsx`, `frontend/tests/lib/access/peticiones.test.ts` (+4) | app/modules, frontend/src, frontend/tests, tests, tests/audit | ☐ |
| `sinComentarios` | función/componente | `frontend/tests/accesibilidad/colores-literales.test.ts` | `frontend/tests/accesibilidad/area-tactil.test.ts`, `frontend/tests/accesibilidad/texto-minimo.test.ts`, `frontend/tests/utils/tokens-css.ts` | frontend/tests | ☐ |

Lectura (decisión del orquestador, pendiente de validar en la prueba de concepto): `archivos`, `body`, `literales`, `remove` y `sinComentarios` son nombres genéricos que coinciden con otros archivos (falsos positivos). `nexus-btn-secondary` figura por vecindad en el diff: su regla no cambió. `border-error` es la clase propia de `global.css` (borrada, sin llamador); `ui.tsx` usa la utilidad de Tailwind `border-error/30`, que es otra clase y no se ve afectada. Los reales: `.nexus-checkbox` (la ✓ pasa de `white` a `--color-on-primary`: igual en 6 temas, oscura en obsidian) y `.nx-modal-glass` (sin cambio de reglas). Validar en navegador Usuarios, Áreas y todos los diálogos.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | DIS-007 anota CSS muerto: `.stacked-bar-label`, `.nx-tour-counter`, `table.dataTable` / `.tab-panel-content` |
| 2026-10-27 | En curso → En revisión: CSS depurado (−1892 líneas netas), 2 tokens nuevos, pruebas `css-sin-uso` y `colores-literales` para CSS; propuesta DIS-047 |
| 2026-10-27 | Ajustes tras auditoría: deslizador y sus tokens borrados, `.nexus-checkbox` unificado, pruebas más estrictas; propuesta DIS-048 |
