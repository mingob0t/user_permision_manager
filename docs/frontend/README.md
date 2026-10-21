# Frontend web (Next.js)

> Línea base documentada en FNC-001 (2026-10-13) a partir del código heredado de NEXUS. Describe el estado actual; la deuda se lista al final.

## 1. Arquitectura

- **Next.js 15.5.7 (App Router) + React 19.2.0 + TypeScript 5.7.3 (strict) + Tailwind CSS 3.4.17.** Gráficas con `recharts` 2.15.4.
- **Sin acceso a BD:** toda la información sale de la API Flask `/api/v1`. La sesión es la cookie que emite Flask (`credentials: 'include'`); no se guardan tokens en `localStorage`.
- **Mismo origen:** en dev, `next.config.ts` define `rewrites` de `/api/*` y `/auth/*` hacia `BACKEND_URL` (por defecto el backend local en el puerto 5001). En producción enruta nginx y los rewrites quedan inertes.
- **Build `output: 'standalone'`:** se arranca `.next/standalone/server.js` (no `next start`); hay que copiar `.next/static` (y `public/` si existe) dentro de `standalone` (ver `deploy/README.md`).
- Todas las pantallas autenticadas son componentes cliente (`'use client'`) envueltos en `AppShell`.
- Alias de importación `@/*` → `src/*`.

```text
frontend/src/
├── app/            # Rutas (App Router)
├── components/     # Pantallas y piezas de interfaz
├── lib/
│   ├── api.ts      # Cliente de la API v1 (exporta apiRequest y ApiError)
│   ├── types.ts    # Contrato de tipos con la API
│   ├── access/     # Cliente y tipos del gestor de accesos por sección (FNC-069)
│   ├── use-async.ts# Hook de carga con estado loading/error y reload()
│   └── use-polling.ts# useAsync con refresco periódico (ADR-006, FNC-071)
└── styles/         # tokens.css, global.css, components.css (portados del portal original)
```

## 2. Pantallas (`frontend/src/app`)

| Ruta | Componente | Qué hace | Visible en el menú para |
|---|---|---|---|
| `/` | `Dashboard` | Panel: contadores (áreas, plataformas, visitas y, para administradores, usuarios), top de visitas y plataformas por área (gráfica recharts). | Todos |
| `/platforms` | `RequestCatalog` + `PlatformCatalog` | `h1` "Plataformas" y dos `h2`. Catálogo solicitable (DIS-013): estado por plataforma, filtro por área y búsqueda en cliente, modal de solicitud de nivel con justificación opcional; superadmin solo consulta. Debajo, "Mis plataformas": abre el enlace, registra visita y marca favorito. | Todos |
| `/requests` | `MyRequestsView` | Pestañas "Mis solicitudes" (`mine`: estado, nivel, fechas, motivo de rechazo, estado del acceso) y "Mis accesos" (`/me/access`, `vigente` por defecto, estado explicado); filtro por estado, paginación y `usePolling`. Superadmin: estado vacío explicado, sin llamadas (DIS-014). | `usuario`, `admin_area` |
| `/approvals` | `ApprovalsInbox` | Bandeja (`inbox`): solicitante, plataforma, nivel, estado, fechas y justificación; filtros por estado (`pendiente` por defecto) y área, paginación y `usePolling`; aprobar con confirmación (`ApproveDialog`) y rechazar con motivo de 10–500 (`RejectDialog`); la fila se actualiza con la respuesta y el aviso (`status`) recibe el foco; la solicitud propia no tiene acciones. Guarda `any_admin` (DIS-015). | `administrador`, `admin_area` |
| `/inventory` | `Inventory` | Inventario de permisos (`GET /access/inventory`, `vigente` por defecto): usuario, plataforma, área, nivel, origen, desde, quién aprobó ("Sistema" si es automático) y estado; filtros por área (admin: las suyas; superadmin: `GET /areas`), plataforma (del alcance, acotada al área), nivel, origen, estado y búsqueda por nombre o correo (al enviar, sin caracteres de control, ≤ 100); paginación y botón "Recargar" (sin refresco periódico, contrato; `aria-disabled` mientras carga para conservar el foco y "Recargando…" en la región viva). Filtros con etiqueta visible (`Field`); vacío con filtros en `role="status"`. Guarda `any_admin` (DIS-021). | `administrador`, `admin_area` |
| `/admin/connectors` | — (reservada, DIS-022) | Conectores; guarda `admin`. | `administrador` |
| `/favorites` | `FavoritesList` | Plataformas marcadas como favoritas. | Todos |
| `/notifications` | `NotificationsList` | Notificaciones in-app: marcar leídas y borrar. | Todos |
| `/admin/platforms` | `PlatformAdmin` | Crear, editar y eliminar plataformas con tipo de integración; grupos de acceso por nivel solo para el superadmin; avisos tras guardar (DIS-017). Guarda `any_admin`. | `administrador`, `admin_area` |
| `/areas` | `AreasList` | Áreas visibles; superadmin y admin de área crean; cada uno edita y borra las que gestiona; el superadmin asigna administradores (`areas/area-admins-panel.tsx`). Guarda `any_admin`. | `administrador`, `admin_area` |
| `/users` | `UsersList` | Alta, edición y baja de usuarios; asignación de áreas y plataformas; búsqueda en el directorio; usuarios inactivos y purga (superadmin). Botón "Accesos" por usuario: panel `UserAccessPanel` (`GET /users/<id>/access`, `vigente` por defecto, filtro, paginación y `usePolling`) con revocación confirmada y motivo opcional ≤ 500 (`RevokeAccessDialog`); sin botón donde el contrato no lo permite, con el motivo (DIS-018). | `administrador`, `admin_area` |
| `/audit` | `AuditLog` | Registros de auditoría dentro del alcance del usuario. | Todos |
| `/settings` | `SettingsPanel` | Pestañas: Portal, Correo (SMTP), Plantillas, Directorio (LDAP), Respaldo — solo superadmin —, y Mis preferencias para todos. | Todos |
| `/login` | `LoginForm` | Consulta `/auth/context`; si hay SSO ofrece entrar con Authelia; si no, formulario con casilla "directorio" (LDAP) o cuenta local. | Sin sesión |
| `/logout` | `LogoutView` | Llama a `/auth/logout` y, con SSO, redirige al cierre de Authelia. | — (botón "Salir") |
| `error.tsx` | — | Página de error 500 con "Reintentar". | — |
| `not-found.tsx` | — | Página 404. | — |

## 3. Menú por rol

Definido en `components/app-shell.tsx` (`NAV`, FNC-070). Cada entrada puede exigir un `RoleRequirement` de `components/require-role.tsx`; los permisos salen de `GET /api/v1/me` (`permissions.is_admin`, `permissions.is_area_admin`).

- `any_admin`: superadmin o admin de área; `admin`: solo superadmin; `requester`: usuario y admin de área (el superadmin no solicita)

| Entrada | `usuario` | `admin_area` | `administrador` |
|---|---|---|---|
| Panel, Catálogo, Favoritos, Notificaciones, Auditoría, Ajustes | Sí | Sí | Sí |
| Mis solicitudes | Sí | Sí | No |
| Aprobaciones, Administrar plataformas, Áreas, Usuarios, Inventario (DIS-021) | No | Sí | Sí |
| Conectores | No | No | Sí |

- `/requests` no usa la guarda: el superadmin ve un estado vacío explicado (DIS-014)
- Guarda de ruta: `<RequireRole requires="…">` muestra "sin permiso" (`ErrorNote`) y no monta la pantalla, así que no llama a la API
- Hoy la usan `/approvals`, `/admin/connectors`, `/areas` (dentro de `AreasList`, DIS-016) y `PlatformAdmin` (`any_admin`, DIS-017); las demás rutas previas no la usan
- Dentro de Ajustes, las pestañas de sistema solo se muestran a `administrador`. Ocultar en la interfaz no protege: el backend vuelve a validar cada endpoint.

## 4. Componentes principales

| Componente | Archivo | Rol |
|---|---|---|
| `AppShell` | `app-shell.tsx` | Marco: barra lateral (oculta en móvil), cabecera con nombre, rol y "Salir"; estados de carga y error de sesión. |
| `SessionProvider` / `useSession` | `session-provider.tsx` | Pide `/me` una vez; sin sesión redirige a `/login`. |
| `RequireRole` / `meetsRequirement` | `require-role.tsx` | Guarda de ruta y regla de visibilidad por rol (FNC-070). |
| `Card`, `PanelHeader`, `StatTile`, `Spinner`, `ErrorNote`, `EmptyNote`, `Badge` | `ui.tsx` | Piezas base con clases del portal original (estados de carga, vacío y error). |
| `Field`, `TextInput`, `TextArea`, `Select`, `Checkbox`, `Button`, `Modal`, `ConfirmDialog` | `form.tsx` | Controles de formulario y modales (`.nexus-btn`, `.nexus-checkbox`, `.nx-modal-glass`). |
| `PlatformCard` | `platform-card.tsx` | Tarjeta de plataforma con favorito y apertura del enlace (solo `https://`, `enlaceSeguro`). |
| `PlatformForm`, `PlatformIntegrationFields`, `PlatformSaveNotice`, `field-notes`, `platform-payload`, `platform-save-errors` | `platforms/` | Formulario, sección Integración, aviso con `warnings` (región `status`), errores por campo con `aria-describedby` y foco, validación y cuerpo por rol (DIS-017). |
| `RequestCatalog`, `RequestCatalogCard`, `RequestFormModal`, `AccessStatusBadge`, `describeRequestError` | `access/` | Catálogo solicitable, tarjeta con estado y motivo sin acción, modal con nivel y justificación (≤ 500, `aria-describedby`, foco), insignia de estado de acceso reutilizable y mensajes de `POST /access-requests` (DIS-013). |
| `MyRequestsView`, `MyRequests`, `MyAccess`, `ResponsiveList`/`ResponsiveRow`, `ListPager`, `RequestStatusBadge`, `formatearFecha`, `describeListError`/`listLoadError` | `access/` | Mis solicitudes y mis accesos; lista que es tabla en `md` y lista en móvil (`dl` por fila); paginación de `Paginated`; insignia de estado de solicitud; fechas `es-MX`; error de carga sin texto del servidor que conserva el 401 para `usePolling` (DIS-014). |
| `ApprovalsInbox`, `ApproveDialog`, `RejectDialog`, `describeDecisionError`, `MOTIVO_MIN`/`MOTIVO_MAX` | `access/` | Bandeja de aprobaciones; confirmación de aprobar (`Modal`, botón primario); rechazo con motivo obligatorio, contador y envío deshabilitado con la pista ligada; mensajes de approve/reject del contrato (DIS-015). |
| `UserAccessPanel`, `RevokeAccessDialog`, `motivoSinRevocar`, `describeRevokeError`, `REVOCACION_MOTIVO_MAX` | `users/` | Accesos de un usuario (sección, no `Modal`, para no anidar diálogos): plataforma, nivel, origen, quién aprobó, estado explicado y última ejecución; revocar con confirmación y motivo opcional (patrón de `RejectDialog`); fila actualizada y aviso con foco; mensajes de `POST /access/<id>/revoke` sin texto del servidor (DIS-018). |
| `Inventory`, `InventoryFilters`, `InventoryTable`, `limpiarBusqueda`, `ORIGENES_INVENTARIO` | `access/` | Inventario de permisos: contenedor (datos, filtros a la página 1, recarga), filtros (selectores y buscador con envío) y filas en `ResponsiveList` con ocho datos en cinco columnas (DIS-021). |
| `AreaForm`, `AreaAdminsPanel`, `mensajeDeError` | `areas/` | Alta/edición de área con errores por campo; administradores del área (superadmin); mensajes del contrato `areas-y-roles.md` (DIS-016). |
| Pantallas | `dashboard.tsx`, `platform-catalog.tsx`, `favorites-list.tsx`, `notifications-list.tsx`, `platform-admin.tsx`, `areas-list.tsx`, `users-list.tsx`, `audit-log.tsx`, `settings-panel.tsx`, `login-form.tsx`, `logout-view.tsx` | Una por ruta. `settings-panel.tsx` (745 líneas) y `users-list.tsx` (581) concentran varias responsabilidades. |

## 5. Cliente de la API (`src/lib/api.ts`)

- `request<T>(path, init)` antepone `/api/v1`, envía `credentials: 'include'`, `redirect: 'manual'` y `Accept: application/json`; añade `Content-Type: application/json` si hay cuerpo.
- En el servidor (SSR) usa `BACKEND_URL`; en el navegador, ruta relativa.
- Errores como `ApiError(status, message, {code, fields, correlationId})` con `isForbidden` (403) e `isUnauthenticated` (401/302/redirección opaca); `fields` anidados se aplanan (`params.base_path`).
- `request` se exporta como `apiRequest`; `BACKEND_URL` por defecto `http://localhost:5001`.
- El objeto `api` expone una función por endpoint (sesión, áreas, plataformas, usuarios, preferencias, settings, SMTP, plantillas, notificaciones, auth, respaldo como Blob/FormData, LDAP y búsqueda en directorio). Los tipos están en `src/lib/types.ts`.
- `useAsync(load, deps)` (`src/lib/use-async.ts`) da `data`, `loading`, `error` y `reload()`.
- `usePolling(load, { intervalSeconds, deps })` (`src/lib/use-polling.ts`, FNC-071): `useAsync` con polling según ADR-006.
  - `intervalSeconds` = `session.preferences.refresh_interval` (acotado a 15–3600 s; sin valor, 60 s)
  - Pestaña oculta: sin consultas; al volver, una inmediata. Una consulta a la vez
  - Error: espera ×2 por fallo hasta 3600 s con *jitter*; éxito restablece; `401` detiene
  - `refresh()` tras una escritura propia; `loading` es `true` en cada consulta: mostrar carga solo sin `data`
  - `data` es el último dato válido: se conserva tras un error, junto con `error`

### Formulario de plataformas (DIS-017)
- Alta: `integration_type` obligatorio; el superadmin puede escribir los DN (vacío = convención del directorio)
- Edición: tipo solo superadmin ("Sin cambiar" no lo envía); admin de área nunca envía tipo ni DN
- `GET /platforms` aún no trae tipo, DN ni `active_grants` (FNC-063): la edición muestra "Sin dato" y no bloquea por accesos hasta entonces

### Gestor de accesos (`src/lib/access/`, FNC-069)
| Archivo | Contrato | Objeto |
|---|---|---|
| `requests.ts` | solicitudes.md | `requestsApi` (catalog, create, mine, inbox, approve, reject) |
| `grants.ts` | accesos.md | `grantsApi` (mine, ofUser, revoke) |
| `inventory.ts` | accesos.md | `inventoryApi.list` |
| `audit.ts` | auditoria.md | `auditApi` (list, ofUser, ofPlatform; siempre paginado) |
| `connectors.ts` | conectores-y-ejecuciones.md | `connectorsApi` (get, save, remove, test) |
| `provisioning.ts` | conectores-y-ejecuciones.md | `provisioningApi` (jobs, job, retry) |
| `users.ts` | areas-y-roles.md, usuarios-directorio.md | `usersApi` (setManagedAreas, createDirectoryAccount) |
| `directory.ts` | usuarios-directorio.md (FNC-043) | `directoryApi` (config, reload, test) |
| `home.ts` | inicio.md | `homeApi.summary` |
| `types.ts`, `client.ts`, `query.ts`, `mocks.ts` | README.md | Tipos, `accessRequest`, `withQuery`/`jsonBody`, datos simulados |

- Plataformas y áreas v1: `api.createPlatform`/`updatePlatform`/`createArea`… de `api.ts` (sin duplicar)
- Simulados: `NEXT_PUBLIC_ACCESS_MOCKS=1 npm run dev`; ignorados en producción; pendientes de integración
- Pruebas: `tests/lib/access/` (forma por endpoint, errores 401/403/409/422/500, bandera), `tests/components/users-list.test.tsx` y `tests/components/areas-list.test.tsx` (DIS-016)

## 6. Estilos, tokens y tema

- Orden de carga en `app/layout.tsx`: `styles/tokens.css` → `styles/global.css` → `styles/components.css` → `app/globals.css` (Tailwind).
- **Tokens:** variables CSS en `styles/tokens.css` (`--color-primary`, `--color-body-bg`, `--color-panel-fill`, `--color-input-*`, `--color-tab-*`, `--color-success`, `--radius-base`, `--radius-panel`, etc.), muchas como canales `R G B` para admitir opacidad.
- **Marca como texto (DIS-001):** `primary`, `brand`, `accent`, `accent-sky`, `peach` son rellenos. Como texto se usa `text-primary-text`, `text-brand-text`, `text-accent-text`, `text-accent-sky-text`, `text-accent-peach-text` (>= 4.5:1 por tema). Relleno con texto encima: `bg-primary-solid` + `text-on-primary`. `texto-de-marca.test.ts` falla si vuelve `text-primary`.
- **Estado como texto (DIS-002):** `success`, `error`, `warning`, `info` son rellenos y tintes (`bg-error/10`, `border-warning/40`). Como texto: `text-success-text`, `text-error-text`, `text-warning-text`, `text-info-text` (>= 4.5:1 por tema, también sobre su tinte). Sin clases de paleta fija como texto (`text-red-600`, `dark:text-*`): lo impide `texto-de-marca.test.ts`.
- **Tailwind** (`tailwind.config.ts`) mapea esas variables a utilidades (`bg-panel-fill`, `text-label`, `bg-primary/15`…). Fuente `Inter`.
- **Tema claro/oscuro:** claro en `:root, html.light`; oscuro automático por `@media (prefers-color-scheme: dark)` (salvo `html.light`) y forzable con `html.dark`. Existen temas adicionales (`theme-emerald-light`, `theme-obsidian-dark`, `theme-rose-light`, `theme-violet-dark`). **No hay selector de tema en la interfaz**: solo aplica la preferencia del sistema.
- Clases de componentes portadas del portal original en `components.css` (`.nexus-btn`, `.nx-badge-*`, `.nx-modal-glass`, estilos tipo DataTables `.dt-*`).

## 7. Cómo arrancar y verificar

Requiere Node 22 LTS (mínimo 18.18) y el backend corriendo.

```bash
cd frontend
npm ci                 # instala según package-lock.json
npm run dev            # http://localhost:3000, reenvía /api y /auth al backend
npm run typecheck      # tsc --noEmit
npm run lint           # next lint
npm run build          # build standalone
```

Para apuntar a otro backend en dev: `BACKEND_URL=<url del backend> npm run dev`.

**Pruebas (FNC-025):**
- `npm test`: corre todas las pruebas una vez (Vitest + Testing Library + jsdom). `npm run test:watch`: modo vigilancia.
- Requiere Node 20.19+ o 22.13+ (por Vitest y jsdom).
- Las pruebas viven en `frontend/tests/`; configuración en `vitest.config.ts`.
- `tests/lib/api.test.ts`: cliente de la API con `fetch` simulado (éxito, error HTTP, 401).
- `tests/lib/use-polling.test.ts`: `usePolling` con temporizadores simulados (intervalo, pausa, *backoff*, sin solape, 401, desmontaje).
- `tests/components/audit-log.test.tsx`: `AuditLog` con la API simulada (datos, filtro, vacío, error).
- `tests/components/platform-admin.test.tsx` y `platform-card.test.tsx`: formulario de plataforma por rol, errores `403`/`404`/`409`/`422`, `warnings`, estados y SEG-24 (DIS-017).
- `tests/components/access/request-catalog.test.tsx`: catálogo solicitable (estados, filtro, envío, 409/403/422, foco) (DIS-013).
- `tests/components/access/my-requests-view.test.tsx`: Mis solicitudes y Mis accesos (pestañas, superadmin, motivo de rechazo, filtro, paginación, carga, vacío, error, 403, 401) (DIS-014).
- `tests/components/access/approvals-inbox.test.tsx`: bandeja (filtros, superadmin, propia, justificación escapada, paginación, carga, vacío, error), aprobar y rechazar (confirmación, motivo 10–500, fila actualizada, aviso con foco, 403/404/409/422) (DIS-015).
- `tests/components/users/user-access-panel.test.tsx`: accesos de un usuario (reglas de revocación del contrato, lista, filtro, paginación, carga, vacío, error, superadmin, foco), revocar (motivo opcional ≤ 500, recorte, `aria-disabled`, fila actualizada, aviso con foco, 403/404/409/422) y el botón "Accesos" de `UsersList` (DIS-018).
- `tests/components/access/inventory.test.tsx`: inventario (columnas del contrato, "Sistema", retirado, filtros al contrato y a la página 1, áreas y plataformas por rol, búsqueda limpia, carga, vacío con y sin filtros, 403/500 sin texto del servidor, recarga) (DIS-021).
- `tests/components/navegacion-por-rol.test.tsx`: entradas del menú por rol y `RequireRole` (sin permiso no monta ni llama a la API).
- `tests/accesibilidad/contraste.test.ts`: contraste WCAG de los tokens en los 7 temas (4.5:1 texto, 3:1 bordes).
- Los pares que hoy fallan están en `fallas-contraste-conocidas.ts` con su tarea DIS y se marcan `it.fails`. Si una tarea los corrige, la prueba avisa: quita el par de la lista.
- `tests/accesibilidad/colores-literales.test.ts`: falla si aparece un color literal nuevo (`#hex`, `rgb()`, clases como `text-red-600`) en `src/components` o `src/app`.
- Los literales que ya existían tienen tope por archivo en `colores-literales.excepciones.ts`. Si corriges uno, baja el tope.
- `next lint` no revisa `tests/`; para lint de pruebas: `npx eslint tests vitest.config.ts`.

**Línea base (FNC-024, 2026-10-13):**
- ESLint configurado en `eslint.config.mjs` (`next/core-web-vitals` + `next/typescript`); `npm run lint` ya no pregunta nada.
- `typecheck`: sin errores. `lint`: 1 error y 3 avisos (detalle en la ficha de FNC-024).
- `build`: falla en el paso de lint por el error de `app/error.tsx`; sin lint (`next build --no-lint`) compila. Decisión pendiente en FNC-024.
- `next lint` está obsoleto en Next.js 15.5; migrar a la CLI de ESLint al pasar a Next.js 16.

## 8. Deuda conocida

| # | Deuda | Dónde |
|---|---|---|
| 1 | Estilos inline con colores dinámicos (color de plataforma o área) en 4 lugares. | `platform-card.tsx`, `platform-admin.tsx`, `areas-list.tsx` |
| 2 | Colores hex literales como valores por defecto en formularios y gráfica. | `platform-admin.tsx`, `areas-list.tsx`, `dashboard.tsx`, `settings-panel.tsx` |
| 3 | Colores literales en `tailwind.config.ts` (`warning`, `error`, `info`) en lugar de tokens. | `tailwind.config.ts` |
| 4 | `text-white` fijo en el botón de `error.tsx`. | `app/error.tsx` |
| 5 | Sin selector de tema; temas adicionales definidos pero inalcanzables. | `styles/tokens.css` |
| 6 | Pocas pruebas de frontend: runner y pruebas base listas (FNC-025); faltan pruebas de más pantallas. | `frontend/tests/` |
| 7 | Componentes grandes con varias responsabilidades (`settings-panel.tsx`, `users-list.tsx`). | `components/` |
| 8 | Navegación lateral oculta en móvil (`hidden md:block`) sin menú alternativo. | `app-shell.tsx` |
| 9 | Valor por defecto del backend escrito como dirección de loopback numérica en el código (incumple "sin IPs"; debería ser `localhost` o configuración). | `next.config.ts`, `lib/api.ts` |
| 10 | Título "Nexus" fijo en `layout.tsx` y en la barra lateral, aunque el nombre del portal es configurable en `system_config`. | `app/layout.tsx`, `app-shell.tsx` |

> Límites de las pruebas automáticas: la de contraste mide los tokens de `tokens.css`, no el CSS final (reglas con `!important` pueden ignorarlos); la de colores literales no detecta colores con nombre, `oklch()`/`lab()` ni valores arbitrarios de Tailwind.
