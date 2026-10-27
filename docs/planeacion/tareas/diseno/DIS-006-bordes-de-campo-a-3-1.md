# DIS-006 — Bordes de campo a 3:1 y foco visible

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-26 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-004-005-006-contraste` (conjunta con DIS-004, DIS-005 y DIS-006) |
| **Commits / PR** | `6509484` (DIS-004), `a00e391` (DIS-005), `e638568` (DIS-006) y cierre de documentación |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
Ningún borde llega a 3:1; inputs con `outline-none` y sin `:focus-visible`.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-11

## Objetivo
Bordes de campo y de panel a 3:1 (WCAG 1.4.11) en los 7 temas, y foco visible en los campos.

## Alcance
- **Incluye:** pares `input-border/panel`, `panel-border/body-bg` y nuevo `panel-border/panel`; foco de `TextInput`/`Select`/`TextArea`, del buscador y filtro de `/platforms` y de `.nexus-checkbox`.
- **No incluye:** rediseño visual; el normalizador global `:where(input…)` de `components.css` (lo pisan las clases de `form.tsx`).

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Cada borde se mezcla con el tono 500 de su misma familia (Slate, Stone, Zinc; violeta hacia Violet-400; Rose-200 hacia Rose-700) hasta 3,05:1 contra panel y fondo de página | Mismo tono e intención; el mínimo que cumple. La mezcla HSL daba bordes más saturados |
| 2 | `--color-input-border` = `--color-panel-border` donde ya eran iguales; en rose conserva su tono rosa | Mantiene la intención de cada tema; `input-border` no tiene consumidores |
| 3 | Inputs de `form.tsx`: `focus:ring-primary/20` → `focus:ring-primary` | El halo al 20 % no llega a 3:1; el anillo `primary` ya se mide (`foco-primary/panel`, `tab-indicador/body-bg`) y es el patrón de los demás controles |
| 4 | Buscador y filtro de `/platforms`: `focus-visible:ring-2 focus-visible:ring-primary` | Tenían `outline-none` y solo cambio de borde |
| 5 | `.nexus-checkbox:focus-visible` con anillo `primary` de 2 px; se conserva el halo de `:focus` | Foco visible con teclado sin cambiar el clic con ratón |
| 6 | El nuevo valor de `panel-border` también corrige el borde de la casilla sin marcar (DIS-039) | Mismo token; queda medido por `panel-border/panel`. DIS-039 se propone cerrar como resuelta por DIS-006 |

## Cambios
| Archivo | Cambio |
|---|---|
| `frontend/src/styles/tokens.css` | `--color-panel-border` e `--color-input-border` en los 7 contextos |
| `frontend/src/components/form.tsx` | Anillo de foco `ring-primary` en `INPUT` |
| `frontend/src/components/platform-catalog.tsx` | Anillo `focus-visible` en buscador y filtro |
| `frontend/src/styles/components.css` | `.nexus-checkbox:focus-visible` |
| `frontend/tests/accesibilidad/pares-contraste.ts` | Par `panel-border/panel` |
| `frontend/tests/accesibilidad/fallas-contraste-conocidas.ts` | Salen las 14 celdas de DIS-006; la lista queda vacía |

## Contraste medido (antes → después)
| Par | claro | SO oscuro | `html.dark` | emerald | obsidian | rose | violet |
|---|---|---|---|---|---|---|---|
| `input-border/panel` | 1,48 → 3,20 | 1,72 → 3,06 | 1,72 → 3,06 | 1,49 → 3,19 | 1,70 → 3,07 | 1,41 → 3,06 | 2,02 → 3,06 |
| `panel-border/body-bg` | 1,42 → 3,06 | 1,94 → 3,45 | 1,72 → 3,06 | 1,43 → 3,06 | 1,91 → 3,44 | 1,30 → 3,08 | 2,09 → 3,17 |
| `panel-border/panel` (nuevo) | 1,48 → 3,20 | 1,72 → 3,06 | 1,72 → 3,06 | 1,49 → 3,19 | 1,70 → 3,07 | 1,42 → 3,39 | 2,02 → 3,06 |

## Elementos compartidos que cambian de color (para validar)
`--color-panel-border` es el borde general del portal: el cambio se ve en casi todas las pantallas.

| Elemento | Cambio visible | Pantallas |
|---|---|---|
| `Card`, tablas y separadores (`border-panel-border`, `ui.tsx`, `responsive-list.tsx`) | Bordes y divisores más marcados | Todas las pantallas con tarjetas o tablas: `/`, `/dashboard`, `/platforms`, `/favorites`, `/areas`, `/users`, `/notifications`, `/settings`, `/admin/platforms`, acceso (solicitudes, aprobaciones, inventario), conectores y auditoría |
| Shell y menú (`app-shell.tsx`, `mobile-menu.tsx`) | Bordes de barra lateral y menú móvil | Todas |
| Campos de `form.tsx` (`TextInput`, `Select`, `TextArea`) | Borde más marcado y anillo de foco sólido `primary` | Todo formulario y filtro (`inventory-filters`, `audit-filters`, `scope-filters`, login, ajustes, diálogos) |
| Buscador y filtro de `/platforms` | Borde más marcado y anillo de foco | `/platforms` |
| `.nexus-checkbox` | Borde más marcado; anillo de foco con teclado | Casillas de `Checkbox` y `area-checklist` (alta en directorio, elevación a admin) |
| `.nexus-btn-secondary` | Borde más marcado | Todos los botones secundarios |
| `global.css` (líneas 108, 380, 386, 499) y modales (`job-detail-modal`, `audit-detail-modal`, `request-form-modal`) | Bordes más marcados | Pantallas que los usan |
| `--color-input-border` | Ninguno visible (sin consumidores) | — |

## Verificación (2026-10-26, rama `dis/DIS-004-005-006-contraste`, en `frontend/`)
| Comando | Resultado real |
|---|---|
| `npm run typecheck` | código 0 |
| `npm run lint` y `npx eslint tests vitest.config.ts` | código 0, sin avisos |
| `npx vitest run` | código 0: 29 archivos, 1079 pasan, 0 `it.fails` (antes 1050 + 25 esperadas). Una corrida de cuatro dio 1 fallo intermitente que no se repitió en 3 corridas más (ver DIS-040) |
| `npm run build` | código 0 |
| `grep` del diff (`style=`, `<style`, `.style.`, `#hex`, `rgb(` numérico, IP) | sin resultados fuera de `tokens.css` |

- Fallas de contraste conocidas: **25 → 0** (DIS-004: 3; DIS-005: 8; DIS-006: 14). `fallas-contraste-conocidas.ts` queda vacío.
- **No verificado:** vista en navegador de temas claro y oscuro, móvil y escritorio (no se levantó la app); revisor, tester y auditor-accesibilidad no se lanzaron por indicación del orquestador.
- Límite: la prueba mide tokens, no el CSS final; las tarjetas con opacidad se midieron con un script de composición.

## Impacto en elementos compartidos (`impacto.py`, contra `develop`)
Falsos positivos: `body` (variable local de `platform-card.tsx`) y `--color-body-text` (sin cambio de valor; solo hay líneas nuevas junto a él).

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 8 elemento(s) usados en otras secciones: app/modules, frontend/src, frontend/tests, migrations/versions, tests, tests/notifications. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `--color-body-text` | token CSS | `frontend/src/styles/tokens.css` | `frontend/src/styles/global.css` | frontend/src | ☐ |
| `--color-on-primary` | token CSS | `frontend/src/styles/tokens.css` | `frontend/tests/accesibilidad/hover-botones.test.ts` | frontend/tests | ☐ |
| `--color-panel-border` | token CSS | `frontend/src/styles/tokens.css` | `frontend/src/styles/global.css` | frontend/src | ☐ |
| `Button` | función | `frontend/src/components/form.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/approve-dialog.tsx`, `frontend/src/components/access/inventory-filters.tsx`, `frontend/src/components/access/inventory.tsx`, `frontend/src/components/access/list-pager.tsx`, `frontend/src/components/access/my-access.tsx`, `frontend/src/components/access/my-requests.tsx`, `frontend/src/components/access/reject-dialog.tsx` (+29) | frontend/src | ☐ |
| `Field` | función | `frontend/src/components/form.tsx` | `frontend/src/components/access/inventory-filters.tsx`, `frontend/src/components/access/reject-dialog.tsx`, `frontend/src/components/access/request-form-modal.tsx`, `frontend/src/components/access/scope-filters.tsx`, `frontend/src/components/areas/area-admins-panel.tsx`, `frontend/src/components/areas/area-form.tsx`, `frontend/src/components/audit/audit-filters.tsx`, `frontend/src/components/connectors/connector-form.tsx` (+10) | frontend/src | ☐ |
| `PlatformCatalog` | función | `frontend/src/components/platform-catalog.tsx` | `frontend/src/app/platforms/page.tsx` | frontend/src | ☐ |
| `body` | función/componente | `frontend/src/components/platform-card.tsx` | `app/modules/api/admin.py`, `app/modules/connectors/http_transporte.py`, `app/modules/notifications/models.py`, `app/modules/notifications/services.py`, `frontend/src/app/layout.tsx`, `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/approve-dialog.tsx`, `frontend/src/components/access/inventory-table.tsx` (+40) | app/modules, frontend/src, frontend/tests, migrations/versions, tests, tests/notifications | ☐ |
| `nexus-checkbox` | clase CSS | `frontend/src/styles/components.css` | `frontend/src/components/users/area-checklist.tsx` | frontend/src | ☐ |

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
| 2026-10-26 | En curso: tokens de borde a 3:1 y foco visible (decisiones en la ficha). Junto con DIS-004 y DIS-005, la lista de fallas conocidas pasa de 25 a 0 |
| 2026-10-26 | En revisión: implementada junto con DIS-004/005/006 en modo autónomo; fallas conocidas 25 → 0; typecheck, lint, vitest y build en 0; sin verificación visual en navegador; pendientes revisor y auditor-accesibilidad |
