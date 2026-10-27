# DIS-007 — Tamaño mínimo de texto 12 px

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-26 |
| **Finalizada** | |
| **Estatus Git** | commit local, sin push |
| **Rama** | `dis/DIS-007-032-texto-minimo` (junto con DIS-032) |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
Textos de 9 a 11 px en badges, botones, cabeceras y ejes.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-12

## Objetivo
_Se completa al aprobar la tarea._

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** _se precisa al aprobar._

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados (H-12; verificación visual solo en página de prueba)
- [x] Prueba de regresión que primero falla (`texto-minimo.test.ts`)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → —
- Relacionada con DIS-032 (misma rama)

## Cambios
- `frontend/src/styles/components.css`: `font-size` → `var(--text-xs)` en l. 185 (cabeceras de tabla, 11 px), 672 (`.stacked-bar-label`, 9 px), 1494 (`.nx-tour-counter`, 11 px), 1659 (`.nexus-checkbox:checked::after`, 10 px); y l. 254 y 1509 de DIS-032.
- `frontend/src/components/dashboard.tsx` l. 74 y 82: ejes `fontSize` 11 → 12.
- `frontend/src/components/platform-admin.tsx` l. 168: iniciales `text-[10px]` → `text-xs` (caja de 28 px).
- `frontend/src/styles/tokens.css` l. 223: baja de `--text-2xs` (10 px).
- Prueba nueva `frontend/tests/accesibilidad/texto-minimo.test.ts`: tokens `--text-*`, `font-size` de todo CSS de `src/` (px, rem, `var(--text-*)`), `text-[…]` y `fontSize` en TS/TSX.
- Docs: `VARIABLES.md` (`--text-xs`, baja de `--text-2xs`), `HISTORIAL.md` (2 filas), `docs/frontend/README.md` §6, `CHANGELOG.md`, bitácora del día.

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- Se usa el token existente `var(--text-xs)` (12 px) en CSS y `text-xs` en Tailwind; sin escala nueva.
- Se da de baja `--text-2xs` (10 px, sin usos) para que la escala no permita bajar de 12 px.
- Se conservan peso, mayúsculas y `letter-spacing` de botones e insignias, y `min-width: 140px`/`height: 3rem` de `.nexus-btn`: cambio mínimo; el dueño hará el diseño final.
- Ejes de Recharts con `fontSize: 12` numérico (atributo SVG, no admite `var()`).
- También se suben las clases heredadas sin llamadores (cabeceras `dataTable`, `.nx-tour-counter`, `.stacked-bar-label`) para que la prueba cubra todo `src/`.
- La prueba falla con valores no medibles (`em`, `%`, `calc`) en `font-size`: se debe usar la escala.

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npx vitest run tests/accesibilidad/texto-minimo.test.ts` antes del cambio | código 1: 3 de 4 fallan (token `--text-2xs`; 6 `font-size` en `components.css`; 3 en TSX) |
| `npm run typecheck` | código 0 |
| `npm run lint` | código 0, sin advertencias |
| `npx vitest run` | código 0: 35 archivos, 1218 pasan; `FALLAS_CONOCIDAS` de contraste sigue vacía (0) |
| `npx next build` | código 0 |
| Chromium headless (binario de Playwright) con el CSS compilado de `.next`, página de prueba con los 10 botones más largos y 5 insignias, `html.light` y `html.dark`, 360 y 1280 px | `font-size` 12 px; botones 48 px de alto, 140–256 px de ancho, sin desborde ni salto de línea (`nowrap`); insignias 28 px de alto, la más larga 298 px (cabe en 328 px útiles de móvil); iniciales 28×28 sin desborde; mismas medidas en los dos temas |

**No verificado:** la app real no se levantó (requiere backend); no se vieron las pantallas reales ni los estados de carga/vacío/error (no cambian). Una insignia larga dentro de una fila flex estrecha puede crecer ~9 % (era `nowrap` antes). Contraste: no cambia color; el texto más grande no empeora AA.

## Impacto en elementos compartidos
Salida de `python3 ~/.claude/agentes/herramientas/impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `--radius-panel` | token CSS | `frontend/src/styles/tokens.css` | `frontend/tailwind.config.ts` | frontend | ☐ |
| `nexus-btn` | clase CSS | `frontend/src/styles/components.css` | `access/inventory.tsx`, `audit/platform-audit-history.tsx`, `audit/user-audit-history.tsx`, `form.tsx`, `home/role-summary.tsx`, `platforms/platform-integration-fields.tsx`, `ui.tsx`, `users/user-access-panel.tsx` (+3) | frontend/src, frontend/tests | ☐ |
| `nexus-checkbox` | clase CSS | `frontend/src/styles/components.css` | `form.tsx`, `users/area-checklist.tsx`, `tests/accesibilidad/pares-contraste.ts` | frontend/src, frontend/tests | ☐ |
| `nx-badge` | clase CSS | `frontend/src/styles/components.css` | `ui.tsx` | frontend/src | ☐ |

- `--radius-panel`: falso positivo de `impacto.py` (línea vecina de la baja de `--text-2xs`); su valor no cambió.
- `--text-2xs`: baja, sin consumidores (`grep` en `frontend/src` y `tailwind.config.ts`).

**Pantallas a validar:**
- `.nexus-btn` → todo `Button` (`form.tsx`) y los enlaces con `nexus-btn`: login, Inicio (`/`), catálogo y favoritos, mis solicitudes, aprobaciones, inventario, áreas, usuarios, auditoría, notificaciones, Ajustes (incl. Directorio y conectores), Administrar plataformas, y todos los diálogos (`Modal`, `ConfirmDialog`).
- `.nx-badge` → todo `Badge` (`ui.tsx`): tarjetas del catálogo, estados de solicitud y de acceso, áreas, usuarios, auditoría (tabla y detalle), conectores y ejecuciones, Administrar plataformas, Ajustes → Directorio.
- `.nexus-checkbox` → `Checkbox` (`form.tsx`) y `area-checklist.tsx` (usuarios, admin de área).
- Locales: ejes de `Dashboard` (Inicio), iniciales de `platform-admin.tsx` (Administrar plataformas).
- Sin llamadores en `src` (CSS heredado): cabeceras `table.dataTable`/`.tab-panel-content`, `.nx-tour-counter`, `.stacked-bar-label`.

## Propuestas
- Ninguna nueva.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-26 | En curso → En revisión (modo autónomo), junto con DIS-032. Texto mínimo 12 px con `--text-xs`, baja de `--text-2xs`, prueba que primero falló. Verificación en la ficha; app real no levantada |
