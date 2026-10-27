# DIS-004 — Botones: texto sobre primary por token, peligro y advertencia, hover del secundario

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
`.nexus-btn-primary` fuerza blanco (`components.css:1526-1530`): 2.56-4.23 según tema.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-05, H-09

## Objetivo
Texto de los botones con contraste AA (4.5:1) en los 7 temas, solo por tokens.

## Alcance
- **Incluye:** par `button-text/button-bg`; botón `danger` de `form.tsx`; medir el hover de `.nexus-btn-secondary` (H-09).
- **No incluye:** botón primario (DIS-015); rediseño visual (lo hace el dueño); cambiar a `danger` los diálogos que hoy usan primario por la falla anterior (propuesta DIS-043).

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | `--color-button-bg`/`-text` = `var(--color-primary-solid)`/`var(--color-on-primary)` en los 5 bloques que los declaran | Mismo arreglo que la pestaña activa (DIS-001); sin consumidores en clases ni componentes |
| 2 | Tokens nuevos `--color-error-solid` (Red-600 `220 38 38`) y `--color-on-error` (blanco) en los 7 temas; obsidian `var(--color-error)` + `9 9 11` | Un paso más oscuro del mismo rojo, como `primary-solid` (DIS-001); obsidian conserva su texto oscuro sobre relleno claro (5,29:1) |
| 3 | `danger` = `nexus-btn-primary !bg-error-solid !text-on-error shadow-error/20` | Mismo patrón de override que ya tenía; la sombra conserva `error` |
| 4 | Botón de advertencia: no se crea | No existe ninguna variante ni botón de advertencia en `src/`; crear tokens sin consumidor queda fuera del alcance |
| 5 | Hover del secundario: sin cambio de valores | Ya usa `--color-primary-text` (DIS-001): 4,95–7,69:1; se agregan pares para fijarlo |

## Cambios
| Archivo | Cambio |
|---|---|
| `frontend/src/styles/tokens.css` | `--color-button-bg/-text` por referencia; `--color-error-solid` y `--color-on-error` en los 7 bloques |
| `frontend/tailwind.config.ts` | Utilidades `error-solid` y `on-error` |
| `frontend/src/components/form.tsx` | Variante `danger` de `Button` con los tokens nuevos |
| `frontend/tests/accesibilidad/pares-contraste.ts` | Pares `on-error/error-solid`, `btn-secondary-hover/panel` y `/body-bg` |
| `frontend/tests/accesibilidad/fallas-contraste-conocidas.ts` | Sale `button-text/button-bg` (3 celdas) |

## Contraste medido (antes → después)
| Par | claro | SO oscuro | `html.dark` | emerald | obsidian | rose | violet |
|---|---|---|---|---|---|---|---|
| `button-text/button-bg` | 5,17 → 5,17 | 5,17 → 5,17 | 5,17 → 5,17 | 3,77 → 5,48 | 7,76 → 7,76 | 3,67 → 4,70 | 4,23 → 5,70 |
| texto de `danger` | 3,76 → 4,83 | 3,76 → 4,83 | 3,76 → 4,83 | 3,76 → 4,83 | 5,29 → 5,29 | 3,76 → 4,83 | 3,76 → 4,83 |
| hover secundario sobre panel | 6,26 | 6,74 | 6,74 | 5,17 | 6,42 | 5,89 | 6,61 |

## Elementos compartidos que cambian de color (para validar)
| Elemento | Cambio visible | Pantallas |
|---|---|---|
| `Button variant="danger"` (`form.tsx`) | Relleno rojo un tono más oscuro (Red-500 → Red-600), salvo obsidian | `/notifications` (Vaciar), `/users` (Purgar cuentas) y todo `ConfirmDialog`: `/admin/platforms`, `/areas` (áreas y administradores de área), `/users`, `/notifications`, bandeja de aprobaciones (`approve-dialog`) |
| `--color-button-bg/-text`, utilidades `bg-button-bg`/`text-button-text` | Ninguno visible (sin consumidores) | — |

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

## Tareas propuestas
- Propuesta DIS-043: los diálogos que usan primario en vez de `danger` por la falla anterior (`reject-dialog`, `revoke-access-dialog`, `admin-role-dialog`) y sus comentarios desactualizados.

## Criterios de aceptación
- [ ] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [ ] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [ ] Cumple `docs/estandarizacion/` y no duplica código existente
- [ ] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → Depende de DIS-001

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | DIS-002 (revisión): botón `danger` (`form.tsx:84`, `!bg-error`) texto blanco sobre `#ef4444` = 3.76:1 (falla previa, sin cambio en DIS-002). Proponer `--color-error-solid` + `--color-on-error`, como DIS-001 hizo con `primary-solid`/`on-primary` |
| 2026-10-20 | Parte del botón primario resuelta en DIS-015 (auditor-accesibilidad): `.nexus-btn-primary` (`components.css`) usa `--color-primary-solid` y `--color-on-primary` (antes `--color-primary` con blanco: obsidian 2,56, rose 3,67, emerald 3,77, violet 4,23); par `nexus-btn-primary` en la prueba de contraste, pasa en los 7 temas. Sigue pendiente: el par `button-text/button-bg` (tokens `--color-button-*`, sin uso en clases ni componentes; falla conocida en emerald, rose y violet), el botón `danger` (3,76:1) y advertencia/hover del secundario |
| 2026-10-26 | En revisión: implementada junto con DIS-004/005/006 en modo autónomo; fallas conocidas 25 → 0; typecheck, lint, vitest y build en 0; sin verificación visual en navegador; pendientes revisor y auditor-accesibilidad |
