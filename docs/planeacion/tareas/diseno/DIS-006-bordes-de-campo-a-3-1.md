# DIS-006 — Bordes de campo a 3:1 y foco visible

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | En curso |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-26 |
| **Finalizada** | |
| **Estatus Git** | Rama local |
| **Rama** | `dis/DIS-004-005-006-contraste` (conjunta con DIS-004, DIS-005 y DIS-006) |
| **Commits / PR** | |
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
