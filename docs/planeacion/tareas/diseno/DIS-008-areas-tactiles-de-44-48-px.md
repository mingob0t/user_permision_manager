# DIS-008 — Áreas táctiles de 44-48 px en acciones de fila, chips y favorito

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-008-035-areas-tactiles` (junto con DIS-035) |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
Acciones de fila de ~24 px, chips de ~26 px.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-13

## Objetivo
- Todo control interactivo de `frontend/src` con área táctil ≥ 44 px (objetivo 48: `min-h-12`, `min-w-12` si es solo ícono), foco visible y una prueba que impida volver atrás

## Alcance
- **Incluye:** inventario de controles < 44 px, corrección a 48 px, prueba estática `area-tactil.test.ts`
- **No incluye:** rediseño visual (lo hace el dueño), nombres accesibles y cabeceras (DIS-045, DIS-046), colores literales de las páginas de error (DIS-004 / DIS-012)
- **Aprobada:** 2026-10-27 (modo autónomo del orquestador)

## Criterios de aceptación
- [x] Hallazgos de origen corregidos (verificados por clases y pruebas; no en navegador)
- [x] Prueba de regresión que primero falla: `area-tactil.test.ts` contra `develop` (6ee18fa) da 18 hallazgos; con el cambio, 0
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente (`ACCION_FILA` reemplaza tres copias y `ACCION_ROL`)
- [x] Sin direcciones IP ni secretos

## Inventario de controles (2026-10-27)
| Control | Archivo | Antes | Después |
|---|---|---|---|
| Editar, Accesos, Eliminar (tarjeta de usuario) | `components/users-list.tsx` | `px-2 py-1 text-xs` ≈ 24–28 px | `ACCION_FILA` / `ACCION_FILA_PELIGRO` (48 px) |
| Hacer admin, Áreas admin, Quitar admin | `components/users-list.tsx` | `ACCION_ROL` (`min-h-12`, sin `min-w`) | `ACCION_FILA` |
| Chips de áreas y plataformas (`TagPicker`) | `components/users-list.tsx` | `px-2.5 py-1` ≈ 26 px, sin foco visible | `min-h-12 min-w-12 px-3` + anillo de foco |
| Editar, Administradores, Eliminar (tarjeta de área) | `components/areas-list.tsx` | ≈ 24 px | `ACCION_FILA` / `ACCION_FILA_PELIGRO`, `flex-wrap` |
| Editar, Eliminar (fila de plataforma) | `components/platform-admin.tsx` | ≈ 24 px | `ACCION_FILA` / `ACCION_FILA_PELIGRO` + "Historial" (DIS-035) |
| Estrella de favorito | `components/platform-card.tsx` | `p-1 text-lg` ≈ 28×28 px, sin foco visible | 48×48 px + anillo de foco |
| Entradas de la barra lateral | `components/app-shell.tsx` | `py-2` ≈ 36 px (48 solo en el menú móvil), sin foco visible | 48 px y anillo en ambas |
| "Salir" | `components/app-shell.tsx` | `py-1.5` ≈ 32 px | `min-h-12` + anillo |
| Etiqueta de `Checkbox` (todas las casillas) | `components/form.tsx` | ≈ 20 px | `min-h-12` |
| Buscador y filtro de área del catálogo | `components/platform-catalog.tsx` | `py-2` ≈ 38 px | `min-h-12` |
| Entradas de archivo (logo, restaurar) | `components/settings-panel.tsx` | nativas ≈ 30 px | `min-h-12` |
| Entradas de color (portal, área, plataforma) | `settings-panel.tsx`, `areas/area-form.tsx`, `platforms/platform-form.tsx` | `h-10` (40 px) | `h-12` de `INPUT` |
| Reintentar / Ir al inicio (500), Volver (404) | `app/error.tsx`, `app/not-found.tsx` | `py-2` ≈ 36 px | `min-h-12` + anillo |
| "Volver a iniciar sesión" | `components/logout-view.tsx` | enlace de texto ≈ 20 px | `min-h-12 min-w-12` + anillo |

Ya cumplían (sin cambios): `Button` / `.nexus-btn` (48 px, `min-width` 140 px), ✕ de `Modal` (DIS-031), pestañas de Ajustes y Mis solicitudes (DIS-034), botón y panel del menú móvil (DIS-025), "Historial" de Inventario y del panel de accesos (`.nexus-btn`), filas de `AreaChecklist` (DIS-019), opciones de nivel de la solicitud (`label` con `p-3` y dos líneas), contadores del inicio y tarjetas del catálogo (tarjetas completas).

## Pantallas afectadas
- Todas las autenticadas (`AppShell`): barra lateral y "Salir"
- `/users` (acciones, chips del formulario), `/areas` (acciones, color), `/admin/platforms` (acciones e Historial, color), `/platforms` y `/favorites` (estrella; catálogo: buscador y filtro)
- Formularios con casillas: inicio de sesión, plataforma, área, conector, Ajustes, usuario y admins de área
- `/settings` (archivo y color), páginas 500 y 404, `/logout`

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
1. Acciones de fila y de tarjeta con la constante compartida `ACCION_FILA` (texto, 48 px) y no con `.nexus-btn`: este tiene `min-width: 140px` y mayúsculas, y tres por fila rompen la densidad
2. La barra lateral también mide 48 px en escritorio: desde `md` la usan tabletas táctiles. Se retira la prop `touch` de `Nav`; dos pruebas de `menu-movil.test.tsx` que exigían "la barra lateral no cambia" se invierten
3. La etiqueta de `Checkbox` mide 48 px (la caja sigue de 20 px): más separación vertical en los formularios
4. Chips de 48 px de alto; si el dueño los quiere más bajos, 44 px (`min-h-11`) también pasa la prueba
5. Prueba con umbral 44 px (WCAG 2.5.5 / guías de plataforma) y código con 48 px
6. Los colores `text-white` de las páginas de error no se tocan (DIS-004 / DIS-012)

## Prueba automática (`frontend/tests/accesibilidad/area-tactil.test.ts`)
- Revisa `<button>`, `<a>`, `<Link>`, `<summary>` y etiquetas con `role` button/tab/link/menuitem/option/switch de `src/**/*.tsx`
- Lee las clases de `className` (cadenas, plantillas, constantes locales e importadas) y mide alto (`min-h`/`h`/`size`, `nexus-btn`, o relleno vertical × 2 + 16 px) y ancho (`min-w`/`w`/`size` ≥ 44 o relleno horizontal ≥ 12 px)
- Excepciones exactas por archivo con motivo en `area-tactil.excepciones.ts` (hoy: el contador-enlace del inicio)
- Límites: no mide el texto (un `px-3` con una letra pasa); une las ramas de un ternario (por eso no detectaba la barra lateral de escritorio); no sigue `props.className`; no ve CSS de `styles/` salvo `nexus-btn`; no revisa `<input>`/`<select>` (cubiertos por `INPUT` y `Checkbox`)

## Verificación (2026-10-27, en `frontend/`)
| Comando | Resultado |
|---|---|
| `npm run typecheck` | código 0 |
| `npm run lint` | código 0, sin avisos |
| `npx vitest run` | código 0: 36 archivos, 1277 pruebas |
| `npm run build` | código 0 |
| `area-tactil.test.ts` contra `src/` de `develop` (6ee18fa) | falla con 18 hallazgos (los del inventario, salvo la barra lateral: límite del ternario) |
| Fallas de contraste conocidas (`FALLAS_CONOCIDAS`) | 0 (`contraste.test.ts` en verde) |
| Texto mínimo (`texto-minimo.test.ts`) | 0 hallazgos |
| `grep` de las líneas agregadas en `src` | sin `style=`, `<style`, `.style.`, colores literales ni IPs |

- Pruebas nuevas: `area-tactil.test.ts` (23), `platform-admin.test.tsx` (Historial y 48 px), `users-list.test.tsx` (acciones y chips de 48 px)
- **No verificado en navegador:** temas claro y oscuro, móvil y escritorio, ni la altura real de las filas. Solo tokens existentes (`primary-text`, `error-text`, `primary/10`, `error/10`, `ring-primary`), ya medidos en ambos temas
- Sin `tester`, `revisor` ni auditores (instrucción del orquestador)

## Impacto en elementos compartidos
Salida de `impacto.py` (contra `develop`; `abrir`, `body`, `remove`, `save` y `dialogo` son coincidencias por nombre, no usos reales):

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 9 elemento(s) usados en otras secciones: app/modules, frontend, frontend/src, frontend/tests, migrations/versions, tests, tests/audit, tests/connectors, tests/notifications. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Checkbox` | función | `frontend/src/components/form.tsx` | `frontend/src/components/areas/area-admins-panel.tsx`, `frontend/src/components/connectors/connector-form.tsx`, `frontend/src/components/login-form.tsx`, `frontend/src/components/users/area-checklist.tsx` | frontend/src | ☐ |
| `LogoutView` | función | `frontend/src/components/logout-view.tsx` | `frontend/src/app/logout/page.tsx` | frontend/src | ☐ |
| `PlatformCatalog` | función | `frontend/src/components/platform-catalog.tsx` | `frontend/src/app/platforms/page.tsx` | frontend/src | ☐ |
| `Select` | función | `frontend/src/components/form.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/inventory-filters.tsx`, `frontend/src/components/access/my-access.tsx`, `frontend/src/components/access/my-requests.tsx`, `frontend/src/components/access/request-catalog.tsx`, `frontend/src/components/access/scope-filters.tsx`, `frontend/src/components/audit/audit-filters.tsx`, `frontend/src/components/connectors/connector-form.tsx` (+4) | frontend/src, frontend/tests | ☐ |
| `abrir` | función | `frontend/tests/components/menu-movil.test.tsx` | `app/modules/api/routes.py`, `app/modules/connectors/bd_motores.py`, `app/modules/connectors/http_transporte.py`, `app/modules/directory/errors.py`, `app/modules/notifications/services.py`, `app/modules/secretos/vaultwarden.py`, `frontend/src/app/platforms/page.tsx`, `frontend/src/components/access/approvals-inbox.tsx` (+10) | app/modules, frontend/src, frontend/tests, tests, tests/connectors | ☐ |
| `body` | función/componente | `frontend/src/components/platform-card.tsx` | `app/modules/api/admin.py`, `app/modules/connectors/http_transporte.py`, `app/modules/notifications/models.py`, `app/modules/notifications/services.py`, `frontend/src/app/layout.tsx`, `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/approve-dialog.tsx`, `frontend/src/components/access/inventory-table.tsx` (+47) | app/modules, frontend, frontend/src, frontend/tests, migrations/versions, tests, tests/notifications | ☐ |
| `dialogo` | función | `frontend/tests/components/users-list.test.tsx` | `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/components/access/request-catalog.test.tsx`, `frontend/tests/components/areas-list.test.tsx`, `frontend/tests/components/audit-log.test.tsx`, `frontend/tests/components/connectors/connectors-admin.test.tsx`, `frontend/tests/components/connectors/jobs-log.test.tsx`, `frontend/tests/components/modal.test.tsx`, `frontend/tests/components/users/user-access-panel.test.tsx` | frontend/tests | ☐ |
| `remove` | función | `frontend/src/components/areas-list.tsx`, `frontend/src/components/users-list.tsx` | `app/modules/api/routes.py`, `frontend/src/components/connectors/connector-delete-dialog.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/src/lib/use-scroll-lock.ts`, `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/components/connectors/connectors-admin.test.tsx`, `frontend/tests/lib/access/peticiones.test.ts`, `frontend/tests/utils/dom-simulado.ts` (+3) | app/modules, frontend/src, frontend/tests, tests, tests/audit | ☐ |
| `save` | función | `frontend/src/components/areas/area-form.tsx`, `frontend/src/components/platforms/platform-form.tsx`, `frontend/src/components/settings-panel.tsx` | `frontend/src/components/connectors/connector-form.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/src/styles/global.css`, `frontend/tests/components/connectors/connectors-admin.test.tsx`, `frontend/tests/lib/access/errores.test.ts`, `frontend/tests/lib/access/peticiones.test.ts`, `tests/test_rutas_retiradas.py` | frontend/src, frontend/tests, tests | ☐ |

Revisión manual:
- `AppShell` / `Nav` (`app-shell.tsx`): todas las pantallas autenticadas (barra lateral y "Salir")
- `Checkbox` (`form.tsx`): login, plataforma, área, conector, Ajustes (3 pestañas), usuario, admins de área, `AreaChecklist`
- `ACCION_FILA` / `ACCION_FILA_PELIGRO` (nuevo, `acciones-fila.ts`): Usuarios, Áreas, Administrar plataformas
- `PlatformCard`: Catálogo y Favoritos
- Sin cambios en tokens ni en CSS compartido; sin variables nuevas

## Tareas creadas
- DIS-045 (chips de `TagPicker` dentro del `<label>` de `Field`: el primer chip toma el nombre de la etiqueta)
- DIS-046 (Editar/Eliminar de Usuarios sin nombre con contexto; `<th>` vacío de acciones en Plataformas)

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | DIS-017 (auditor-accesibilidad): botones Editar/Eliminar de la tabla de `platform-admin.tsx` miden 24 px de alto; heredado, no corregido en DIS-017 |

- 2026-10-20 (auditoría DIS-018): en `users-list.tsx` los botones de fila "Editar", "Eliminar" y el nuevo "Accesos" (`px-2 py-1 text-xs`) miden ~28 px; llevarlos juntos a 48 px (`min-h-12` o `Button variant="secondary"`).
- 2026-10-27: aprobada en modo autónomo y En curso; implementada junto con DIS-035 en `dis/DIS-008-035-areas-tactiles`; En revisión (sin revisor ni auditores; no verificada en navegador).

## Correcciones tras auditor-accesibilidad (2026-10-27)
El auditor aprobó sin fallas de contraste ni controles < 44 px. Corregido en la misma rama:
- DIS-045 (resuelta en DIS-008): `TagPicker` de `UserForm` va en `fieldset`/`legend` (`GrupoChips`, pista con `aria-describedby`) y no dentro del `<label>` de `Field`; el primer chip conserva su nombre y la leyenda no lo activa
- DIS-046 (resuelta en DIS-008): `aria-label` "Editar {nombre}" y "Eliminar {nombre}" en Usuarios; "Áreas admin" pasa a "Áreas admin de {nombre}" (2.5.3: el nombre empieza con el texto visible)
- `platform-admin.tsx`: `<th>` de acciones con `<span className="sr-only">Acciones</span>`; la tabla desplazable va en `div role="region" aria-label="Plataformas" tabIndex={0}` con `focus-visible:ring-primary`. Es la única región con `overflow-x-auto` en `src` (revisado con grep)
- Pruebas: `users-list.test.tsx` (DIS-045, DIS-046), `platform-admin.test.tsx` (región); se actualizaron dos nombres en `admin-role-dialog.test.tsx`
- Nota de contraste: el tema `emerald-light` tiene márgenes justos en los pares medidos (4,86:1 y 4,57:1 frente a 4,5:1); un cambio de tokens ahí puede romper AA
- Verificación: typecheck 0, lint 0, vitest 0 (36 archivos, 1280), build 0; contraste conocido y texto mínimo en 0. No verificado en navegador
