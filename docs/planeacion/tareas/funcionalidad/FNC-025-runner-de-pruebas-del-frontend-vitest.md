# FNC-025 — Runner de pruebas del frontend (Vitest) con prueba automática de contraste y tokens

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 2 |
| **Módulo / Área** | pruebas |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-13 |
| **Finalizada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-025-runner-pruebas-frontend` |
| **Commits / PR** | `dbd0e30` y la corrección de la ficha (locales, sin push) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (dependencias nuevas) — Aprobado |

## Contexto
El frontend no tiene runner de pruebas ni prueba de contraste.

Origen (diagnóstico inicial, FNC-001):
- [`docs/planeacion/diagnostico-pruebas-2026-10-13.md`](../../../planeacion/diagnostico-pruebas-2026-10-13.md): tarea 9
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): sección 4

## Objetivo
- Tener un runner de pruebas en el frontend (`npm test`).
- Medir el contraste de los tokens de forma automática y frenar colores literales nuevos.

## Alcance
- **Incluye:** Vitest + Testing Library + jsdom; pruebas de `api.ts`, de un componente, de contraste y de colores literales.
- **No incluye:** corregir contraste, tokens, componentes o estilos (lo hacen las tareas DIS); CI (FNC-026).

## Criterios de aceptación
- [x] `npm test` corre Vitest y termina en verde (código 0).
- [x] Pruebas de `src/lib/api.ts` con `fetch` simulado: éxito, error HTTP y 401.
- [x] Prueba de componente con datos simulados (`AuditLog`).
- [x] Contraste WCAG por tema leído de `tokens.css`; fallas actuales marcadas con `it.fails` y su tarea DIS.
- [x] Colores literales en `src/components` y `src/app` con tope por archivo.
- [x] Sin direcciones IP ni secretos. Lint, typecheck y build en verde.
- No aplica: prueba de regresión que primero falla (no corrige un defecto).

## Cambios
- `frontend/package.json`: scripts `test` y `test:watch`; devDependencies exactas `vitest` 4.1.11, `@testing-library/react` 16.3.3, `@testing-library/dom` 10.4.1, `jsdom` 29.1.1; `overrides.vite` 6.4.3.
- `frontend/package-lock.json`: 136 paquetes nuevos; `nanoid` 3.3.18→3.3.20 y `source-map-js` 1.2.1→1.2.2 (deduplicación de npm).
- `frontend/vitest.config.ts`: entorno jsdom, JSX automático, alias `@`.
- `frontend/tests/utils/wcag.ts`: luminancia y razón de contraste WCAG.
- `frontend/tests/utils/tokens-css.ts`: lee `tokens.css` y arma los 7 temas.
- `frontend/tests/accesibilidad/`: pares a medir, fallas conocidas, prueba de contraste y prueba de colores literales con su lista de topes.
- `frontend/tests/lib/api.test.ts` y `frontend/tests/components/audit-log.test.tsx`.

## Decisiones
- `overrides.vite` 6.4.3: con vite 8 npm 10.9.8 falla (`Cannot read properties of null (reading 'edgesOut')`) y vite 7 pide `@types/node` ≥ 22.12 (el proyecto tiene 22.10.5). Vite 6 funciona sin tocar otras dependencias.
- jsdom 29.1.1 en vez de 30.x: la 30 exige Node ≥ 22.22; la 29 admite Node 20.19 / 22.13.
- Componente probado: `AuditLog` en lugar de `users-list` (581 líneas, varias llamadas); es la pantalla con datos más simple.
- Prueba de literales por **tope de conteo** por archivo: falla si sube (deuda nueva) o si baja (hay que bajar el tope).
- Pruebas en `frontend/tests/`: `next lint` no revisa esa carpeta; se verificó con `npx eslint tests vitest.config.ts`.
- Los pares de contraste y sus mínimos salen de la sección 1 de la auditoría de accesibilidad.

## Pares de contraste que hoy fallan (marcados con `it.fails`)
Temas: claro, so-oscuro, html.dark, emerald, obsidian, rose, violet. 88 celdas en total.
- DIS-001: `header-text/header-bg` (emerald, rose); `panel-header-text/panel-header-bg` (html.dark, obsidian, violet); `tab-active-text/tab-active-bg` (emerald, rose, violet).
- DIS-001: `accent-peach/panel` (claro, emerald, rose); `accent/panel` (so-oscuro, html.dark, emerald, rose, violet); `accent-sky/panel` (claro, emerald, rose); `brand/panel` (so-oscuro, html.dark, obsidian, violet).
- DIS-001: insignias `badge-*` (8 tonos) en so-oscuro, obsidian y violet.
- DIS-002: `primary/body-bg` (so-oscuro, html.dark, emerald, rose); `primary/panel` (so-oscuro, html.dark, emerald, rose, violet); `success/panel` (claro, emerald, rose); `ntf-text-subject/ntf-card` y `status-active/panel` (emerald, rose).
- DIS-004: `button-text/button-bg` (emerald, rose, violet).
- DIS-005: `bi-text-muted/panel` (obsidian); `bi-text-muted/surface-container` (claro, emerald, obsidian, rose); `secondary/panel` (so-oscuro, html.dark, obsidian).
- DIS-006: `input-border/panel` y `panel-border/body-bg` (3:1) en los 7 temas.
- Cuando una tarea DIS corrija un par, su `it.fails` empezará a fallar: hay que quitarlo de `fallas-contraste-conocidas.ts`.

## Colores literales existentes (tope en `colores-literales.excepciones.ts`)
- `app/error.tsx`, `app/not-found.tsx`: 1 clase de paleta cada uno (DIS-004 / DIS-012).
- `areas-list.tsx` 2 hex + 3 paleta; `platform-admin.tsx` 4 hex + 5 paleta; `settings-panel.tsx` 2 hex + 8 paleta (DIS-002 / DIS-012).
- `dashboard.tsx` 1 hex (DIS-003 / DIS-012); `form.tsx` 1 paleta (DIS-012).
- `notifications-list.tsx` 9 paleta; `users-list.tsx` 3 paleta; `platform-card.tsx` 1 paleta (DIS-002).

## Verificación (Node 22.23.2, npm 10.9.8, en `frontend/`)
- `npm ci`: código 0.
- `npm test`: 4 archivos, 182 pasan y 88 fallas esperadas (`it.fails`), 270 en total; código 0.
- `npm run lint`: "No ESLint warnings or errors", código 0. `npx eslint tests vitest.config.ts`: código 0.
- `npm run typecheck`: código 0.
- `npm run build`: compila 14 páginas, código 0.
- Prueba de que detectan: al bajar el tope de `dashboard.tsx` a 0 y quitar `brand/panel` de las fallas conocidas, 5 pruebas fallaron (código 1); se restauró.
- `npm audit`: 12 vulnerabilidades antes y después; ninguna nueva por estas dependencias (ver FNC-016).
- No verificado: ejecución en CI (no existe aún, FNC-026); Node 20.

## Impacto en elementos compartidos
- `impacto.py` (contra `develop`): reporta 8 nombres (`Tipo`, `Variables`, `archivos`, `color`, `comprobar`, `error`, `respuesta`, `texto`). Son funciones o tipos locales de `frontend/tests/` que se llaman igual que código de `app/`, `frontend/src/` y `scripts/`: coincidencias de nombre, sin impacto real (revisado).
- `frontend/package.json`: npm reordenó alfabéticamente las devDependencies existentes; ninguna versión cambió.
- `package.json` y `package-lock.json` del frontend son compartidos por todo el frontend: solo se agregaron devDependencies y `overrides.vite`; el build no cambia.
- No se tocaron componentes, estilos, tokens ni `next.config.ts`.

## Impacto cruzado
- Depende de → Depende de FNC-024

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-13 | Aprobada por el dueño. Implementada en `fnc/FNC-025-runner-pruebas-frontend`; pruebas, lint, typecheck y build en verde; commit local sin push |
- auditor-seguridad (modo cambio, 2026-10-13): Aprobado; npm audit baja de 13 a 12, nada nuevo en producción.
- revisor (2026-10-13): Requiere cambios menores de la ficha; corregidos (seguridad, impacto, reordenamiento, commit).

## Observaciones de la segunda revisión (2026-10-13)
- Despliegue: `deploy/install.sh` hace `npm ci`, que ahora también instala vitest, jsdom y vite en el servidor (son necesarias para compilar otras devDependencies; sin efecto en el portal publicado).
- Node mínimo: las pruebas piden 20.19+ o 22.13+; `deploy/preflight.sh` acepta 18. Registrado como FNC-073 (Propuesta, infra).
- Límite: la prueba de contraste mide los tokens, no el CSS final (p. ej. `.nexus-btn-primary` fuerza blanco con `!important`; lo cubre DIS-004).
- Límite: la prueba de colores literales no detecta colores con nombre (`fill="white"`), `oklch()`/`lab()` ni valores arbitrarios de Tailwind; hoy hay 0 casos.
