# DIS-012 — Eliminar estilos inline y colores literales en TSX

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | estilos |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | Merge a develop y push a github |
| **Rama** | `dis/DIS-009-012-limpieza-css` (junto con DIS-009) |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |
| **Aprobada** | 2026-10-27 (modo autónomo del orquestador, pendiente de validar en la prueba de concepto) |

## Contexto
`areas-list.tsx:156`, `platform-card.tsx:52,83`, `platform-admin.tsx:236`, `#6366f1` en 6 sitios.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-09

## Objetivo
- Ningún `style` visual en línea ni color literal en TSX; los valores que vienen de los datos viajan como variables CSS `--*` y los pinta una clase.

## Alcance
- **Incluye:** `platform-card.tsx`, `platform-admin.tsx`, `areas-list.tsx`, `error.tsx`, `not-found.tsx`; revisar cada excepción de `colores-literales.excepciones.ts`; prueba de estilos inline.
- **No incluye:** validar el contraste de los colores que elige el usuario (FNC-033); backend; cambiar el aspecto.

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados (H-09)
- [x] Prueba que impide la regresión: `sin-estilos-inline.test.ts` (127 pruebas; el detector se prueba con casos prohibidos y permitidos)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas (ver Verificación)
- [x] Cumple `docs/estandarizacion/` y no duplica código existente (`variablesCss` es la única vía)
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → Depende de FNC-033

## Resultado
| Sitio | Antes | Ahora |
|---|---|---|
| `platform-card.tsx` (icono, 55) | `style={{ background, color }}` | `nx-chip-solid` + `style={variablesCss({ '--chip-bg', '--chip-fg' })}` |
| `platform-card.tsx` (área, 87) | `style` con `${area_color}22` | `nx-chip-tint` + `--chip-color` (13 % = `22` hex) |
| `platform-admin.tsx` (180) | `style={{ background, color }}` | `nx-chip-solid` |
| `areas-list.tsx` (97) | `style` con `${color}22` | `nx-chip-tint` |
| `app/error.tsx`, `app/not-found.tsx` | `text-white` sobre `bg-primary` | `text-on-primary` (excepciones retiradas) |
| `#6366f1` en 6 sitios | ya retirado en DIS-003 y por la deuda original (grep: 0) | — |
- `lib/variables-css.ts` (`variablesCss`): único punto con el `as CSSProperties` de variables `--*`; las clases `.nx-chip-solid` y `.nx-chip-tint` están en `components.css`.
- Excepciones de `colores-literales.excepciones.ts`: de 3 archivos a 1. Se retiran `error.tsx` y `not-found.tsx`. Queda `settings-panel.tsx` (2 hex, `#0f172a` y `#ffffff`): son los valores por defecto de `<input type="color">` (exige `#rrggbb`; el backend usa el mismo `#0f172a` en `settings/models.py`), es un dato y no un estilo; no se puede pasar a token porque el usuario los guarda en la base.
- Recharts (`dashboard.tsx`: `contentStyle`, `itemStyle`, `labelStyle`) se acepta porque ya estaba justificado en DIS-003 (valores de `useTokenColors`, sin literales); la prueba nueva lo limita a ese archivo y esas tres props.

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- La dependencia "Depende de FNC-033" no bloquea: aquí solo se cambia cómo se pinta el color, no se valida su contraste (los colores de datos siguen sin validarse, como antes).
- `text-white` → `text-on-primary`: en obsidian el texto pasa a `9 9 11` sobre Zinc-400 (mejora el contraste); en los otros 6 temas es idéntico.
- Una variable CSS `--*` desde el dato es la forma aceptada de "valor solo conocido al ejecutar" (lineamiento y hook `reglas.py`).

## Verificación (en `frontend/`)
Misma corrida que DIS-009: `tsc` 0, `next lint` 0, `vitest` 0 (1460 pruebas), `next build` 0.
- No verificado en navegador: iconos de plataforma y área (colores del dato, tinte al 13 %) y los botones de las páginas de error en claro/oscuro, móvil/escritorio.
- `color-mix(in srgb, …)` ya se usaba en el proyecto; no se midió soporte en navegadores antiguos.

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
| 2026-10-27 | En curso → En revisión: 4 estilos inline a variables `--*`, 2 `text-white` a token, `variablesCss`, prueba `sin-estilos-inline`, excepciones 3 → 1 |

- 2026-10-27: auditoría de accesibilidad (`auditor-accesibilidad`): sin regresiones, estilos computados idénticos en 6 temas; hallazgos B, C y D corregidos en `f36ef0d`, A registrado como DIS-048. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
