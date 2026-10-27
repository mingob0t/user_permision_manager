# Frontend web (Next.js)

> Línea base documentada en FNC-001 (2026-10-13) a partir del código heredado de NEXUS. Describe el estado actual; la deuda se lista al final.

## 1. Arquitectura

- **Next.js 15.5.7 (App Router) + React 19.2.0 + TypeScript 5.7.3 (strict) + Tailwind CSS 3.4.17.** Gráficas con `recharts` 2.15.4.
- **Sin acceso a BD:** toda la información sale de la API Flask `/api/v1`. La sesión es la cookie que emite Flask (`credentials: 'include'`); no se guardan tokens en `localStorage`.
- **Mismo origen:** `next.config.ts` (vía `rewrites-dev.ts`) define el rewrite de `/api/*` hacia `BACKEND_URL` (por defecto `http://localhost:5001`, nunca una IP) **solo con `NODE_ENV=development`**; no hay rewrite de `/auth` (FNC-005, FNC-118). `next build` y `next start` no generan ninguno: en producción enruta nginx (`/` a Next, `/api/` a Flask). El cliente usa siempre la ruta relativa `/api/v1` en el navegador.
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
│   ├── use-polling.ts# useAsync con refresco periódico (ADR-006, FNC-071)
│   ├── use-focus-trap.ts# Trampa de foco de Modal y menú móvil (DIS-031)
│   ├── use-scroll-lock.ts# Bloqueo del fondo e inert en la raíz (DIS-038, DIS-044)
│   └── raiz-app.ts # Id de la raíz desplazable de layout.tsx (DIS-044)
└── styles/         # tokens.css, global.css, components.css (portados del portal original)
```

## 2. Pantallas (`frontend/src/app`)

| Ruta | Componente | Qué hace | Visible en el menú para |
|---|---|---|---|
| `/` | `Dashboard` | Panel. Arriba, resumen por rol (`RoleSummary`, `GET /home/summary`, `usePolling`): usuario, mis solicitudes y mis accesos; admin de área, pendientes, sus áreas y lo propio; superadmin, pendientes y global. Cada contador enlaza a `/requests`, `/approvals`, `/inventory`, `/areas` o `/admin/platforms`; botón "Ver auditoría" (DIS-024). Debajo, "Actividad del portal" de `/stats`: visitas, usuarios, top de visitas y plataformas por área (gráfica recharts con tokens leídos por `useTokenColors` y tabla `sr-only` alternativa, DIS-003); "Áreas" y "Plataformas" solo para quien no administra, porque el resumen ya los muestra (DIS-037). | Todos |
| `/platforms` | `PlatformsView` → `RequestCatalog` | `h1` "Plataformas" y un solo `h2` "Catálogo" (DIS-030): `GET /access-requests/catalog` cruzado en cliente con `GET /platforms`. Un filtro por área y una búsqueda (`FilterBar`). Cada tarjeta muestra el estado; si ya se puede abrir suma "Abrir" (solo con acceso `activo` y `https://`, cuenta la visita) y favorito; las abribles que el catálogo no trae se agregan sin solicitar. Solicitar con nivel y justificación no cambió (DIS-013); superadmin solo consulta. Si falla `/platforms` el catálogo se ve sin enlaces, con "Reintentar enlaces". | Todos |
| `/requests` | `MyRequestsView` | Lee `?tab=accesos` y `?status=` al montar (DIS-036). Pestañas "Mis solicitudes" (`mine`: estado, nivel, fechas, motivo de rechazo, estado del acceso) y "Mis accesos" (`/me/access`, `vigente` por defecto, estado explicado); filtro por estado, paginación y `usePolling`. Superadmin: estado vacío explicado, sin llamadas (DIS-014). | `usuario`, `admin_area` |
| `/approvals` | `ApprovalsInbox` | Lee `?status=` al montar (DIS-036). Bandeja (`inbox`): solicitante, plataforma, nivel, estado, fechas y justificación; filtros por estado (`pendiente` por defecto) y área, paginación y `usePolling`; aprobar con confirmación (`ApproveDialog`) y rechazar con motivo de 10–500 (`RejectDialog`); la fila se actualiza con la respuesta y el aviso (`status`) recibe el foco; la solicitud propia no tiene acciones. Guarda `any_admin` (DIS-015). | `administrador`, `admin_area` |
| `/inventory` | `Inventory` | Lee `?status=` al montar (DIS-036). Inventario de permisos (`GET /access/inventory`, `vigente` por defecto): usuario, plataforma, área, nivel, origen, desde, quién aprobó ("Sistema" si es automático) y estado; filtros por área (admin: las suyas; superadmin: `GET /areas`), plataforma (del alcance, acotada al área), nivel, origen, estado y búsqueda por nombre o correo (al enviar, sin caracteres de control, ≤ 100); paginación y botón "Recargar" (sin refresco periódico, contrato; `aria-disabled` mientras carga para conservar el foco y "Recargando…" en la región viva). Filtros con etiqueta visible (`Field`); vacío con filtros en `role="status"`. Guarda `any_admin` (DIS-021). | `administrador`, `admin_area` |
| `/admin/connectors` | `ConnectorsAdmin` | Plataformas con integración `conector` (`GET /platforms`, `has_connector`, accesos vigentes); "Configurar" abre una sección con la configuración (`GET .../connector`; `404` = sin configurar), formulario de tipo, host, puerto, parámetros del tipo, referencia de la credencial (nunca la contraseña) y activo (`PUT`), "Probar conexión" con texto propio (`POST .../test`) y eliminar con confirmación (`DELETE`, `409` con accesos). Debajo, bitácora de ejecuciones (`GET /provisioning/jobs`): filtros de estado, operación, proveedor, área y plataforma; detalle con intentos en `Modal`; reintentar fallidas con confirmación (solo superadmin); `usePolling` solo con ejecuciones transitorias y "Recargar". Guarda `admin` (DIS-022). | `administrador` |
| `/admin/jobs` | `JobsLog` | Bitácora de ejecuciones del admin de área (DIS-041): la misma `JobsLog` de Conectores, sin la configuración; el backend limita a sus áreas y se oculta "Reintentar" (solo superadmin). Guarda `any_admin`. | `admin_area`, `administrador` |
| `/favorites` | `FavoritesList` | Plataformas marcadas como favoritas. | Todos |
| `/notifications` | `NotificationsList` | Notificaciones in-app: marcar leídas y borrar. | Todos |
| `/admin/platforms` | `PlatformAdmin` | Crear, editar y eliminar plataformas con tipo de integración; grupos de acceso por nivel solo para el superadmin; avisos tras guardar (DIS-017). Por fila, "Historial" (enlace a `/audit/platforms/[id]`, `aria-label` "Historial de X en Auditoría") y, si gestiona, Editar y Eliminar, en una línea y de 48 px (DIS-035). Guarda `any_admin`. | `administrador`, `admin_area` |
| `/areas` | `AreasList` | Áreas visibles; superadmin y admin de área crean; cada uno edita y borra las que gestiona; el superadmin asigna administradores (`areas/area-admins-panel.tsx`). Guarda `any_admin`. | `administrador`, `admin_area` |
| `/users` | `UsersList` | Alta, edición y baja de usuarios; asignación de áreas y plataformas; búsqueda en el directorio; usuarios inactivos y purga (superadmin). Botón "Accesos" por usuario: panel `UserAccessPanel` (`GET /users/<id>/access`, `vigente` por defecto, filtro, paginación y `usePolling`) con revocación confirmada y motivo opcional ≤ 500 (`RevokeAccessDialog`); sin botón donde el contrato no lo permite, con el motivo (DIS-018). "Nuevo usuario" abre el alta en el directorio (`DirectoryAccountForm`, `POST /users/directory`: identificador, correo, nombre, apellidos y áreas; sin contraseña; admin de área solo sus áreas y al menos una). Editar ya no ofrece rol ni áreas administradas; contraseña solo para la cuenta de emergencia. Solo el superadmin ve "Hacer admin", "Áreas admin" y "Quitar admin" (`AdminAreasDialog`, `RemoveAdminDialog`) con el efecto explicado; el resultado se anuncia en una región `status` con foco (DIS-019). | `administrador`, `admin_area` |
| `/audit` | `AuditLog` | Registros de auditoría dentro del alcance (`GET /audit` paginado): fecha, quién ("Sistema" si `actor` es null), evento (catálogo en español; texto libre tal cual), sobre qué con plataforma y área, y resultado. Filtros con etiqueta visible: búsqueda en actor y destino (al enviar, sin control, ≤ 100), Desde/Hasta (`from ≤ to`, ≤ 366 días; si no, se explica y no se envía), evento, resultado y, para quien administra, área y plataforma (`ScopeSelects`). Paginación, "Recargar" (`aria-disabled`), vacío en `role="status"`, error sin texto del servidor. "Ver detalle" (48 px) abre un `Modal` con antes/después como lista de campos en texto plano; el foco vuelve al botón (DIS-020). | Todos |
| `/audit/users/[id]` | `UserAuditHistory` | Historial de un usuario (`GET /audit/users/<id>`): mismos filtros y detalle; nombre tomado de los registros. El usuario solo ve el suyo ("Mi historial"); otro id, "sin permiso". 404 → "No existe o está fuera de tu alcance." Enlace desde el panel de accesos de Usuarios (DIS-020). | Todos (usuario: solo el propio) |
| `/audit/platforms/[id]` | `PlatformAuditHistory` | Historial de una plataforma (`GET /audit/platforms/<id>`), sin filtros de área ni plataforma. Guarda `any_admin`. Enlace desde Inventario con una plataforma elegida (DIS-020) y desde cada fila de Administrar plataformas (DIS-035). | `administrador`, `admin_area` |
| `/settings` | `SettingsPanel` | Pestañas: Portal, Correo (SMTP), Plantillas, Directorio, Respaldo — solo superadmin —, y Mis preferencias para todos. Pestañas con ←/→/Inicio/Fin, *roving tabindex*, `tabpanel` y 48 px (DIS-034). Directorio (`DirectoryTab`, DIS-023): solo lectura de `GET /auth-config` (estado, cada valor con su variable `LDAP_*` y si viene del entorno o es por defecto; contraseña de bind nunca mostrada ni pedida, con su fuente explicada) y "Probar conexión" sin cuerpo (`POST /auth-config/test`) con texto propio. | Todos |
| `/login` | `LoginForm` | Consulta `/auth/context`; si hay SSO ofrece entrar con Authelia; si no, formulario con casilla "directorio" (LDAP) o cuenta local. | Sin sesión |
| `/logout` | `LogoutView` | Llama a `/auth/logout` y, con SSO, redirige al cierre de Authelia. | — (botón "Salir") |
| `error.tsx` | — | Página de error 500 con "Reintentar". | — |
| `not-found.tsx` | — | Página 404. | — |

## 3. Menú por rol

Definido en `components/app-shell.tsx` (`NAV`, FNC-070). La misma lista (`Nav`) se muestra en la barra lateral desde `md` y en el menú móvil bajo `md` (DIS-025). Cada entrada puede exigir un `RoleRequirement` de `components/require-role.tsx`; los permisos salen de `GET /api/v1/me` (`permissions.is_admin`, `permissions.is_area_admin`).

- `any_admin`: superadmin o admin de área; `admin`: solo superadmin; `requester`: usuario y admin de área (el superadmin no solicita)

| Entrada | `usuario` | `admin_area` | `administrador` |
|---|---|---|---|
| Panel, Catálogo, Favoritos, Notificaciones, Auditoría, Ajustes | Sí | Sí | Sí |
| Mis solicitudes | Sí | Sí | No |
| Aprobaciones, Administrar plataformas, Áreas, Usuarios, Inventario (DIS-021) | No | Sí | Sí |
| Conectores | No | No | Sí |
| Ejecuciones (DIS-041) | No | Sí | Sí |

- `/requests` no usa la guarda: el superadmin ve un estado vacío explicado (DIS-014)
- Guarda de ruta: `<RequireRole requires="…">` muestra "sin permiso" (`ErrorNote`) y no monta la pantalla, así que no llama a la API
- Hoy la usan `/approvals`, `/admin/connectors` (DIS-022), `/areas` (dentro de `AreasList`, DIS-016) y `PlatformAdmin` (`any_admin`, DIS-017); las demás rutas previas no la usan
- Dentro de Ajustes, las pestañas de sistema solo se muestran a `administrador`. Ocultar en la interfaz no protege: el backend vuelve a validar cada endpoint.

## 4. Componentes principales

| Componente | Archivo | Rol |
|---|---|---|
| `AppShell` | `app-shell.tsx` | Marco: barra lateral (`md` y mayores), cabecera con menú móvil, nombre, rol y "Salir"; estados de carga y error de sesión. |
| `MobileMenu` | `mobile-menu.tsx` | Bajo `md`: botón "Menú" (`aria-expanded`, `aria-controls`) y panel `role="dialog"` con la misma `Nav` por rol; cierra con Escape, al elegir opción y con clic fuera; foco al primer enlace, de vuelta al botón y atrapado con Tab (`useFocusTrap`, DIS-031); panel en portal, velo `bg-overlay` y bloqueo del fondo (DIS-038); áreas de 48 px (DIS-025). |
| `SessionProvider` / `useSession` | `session-provider.tsx` | Pide `/me` una vez; sin sesión redirige a `/login`. |
| `RequireRole` / `meetsRequirement` | `require-role.tsx` | Guarda de ruta y regla de visibilidad por rol (FNC-070). |
| `RoleSummary`, `gruposDelResumen`, `RUTAS_INICIO` | `home/role-summary.tsx` | Resumen de inicio por rol: grupos de contadores según los campos del contrato `inicio.md`; cada contador es `StatTile` dentro de `Link` con nombre accesible "Etiqueta: n. Ir a Pantalla"; carga, vacío (usuario: enlace al catálogo) y error con Reintentar (DIS-024). Cada enlace lleva el filtro del contador en la URL (DIS-036). |
| `Card`, `PanelHeader`, `StatTile`, `Spinner`, `ErrorNote`, `EmptyNote`, `Badge` | `ui.tsx` | Piezas base con clases del portal original (estados de carga, vacío y error). |
| `Field`, `TextInput`, `TextArea`, `Select`, `Checkbox`, `Button`, `Modal`, `ConfirmDialog` | `form.tsx` | Controles de formulario y modales (`.nexus-btn`, `.nexus-checkbox`, `.nx-modal-glass`). `Modal`: foco inicial en el primer campo (o el panel), atrapado con Tab y devuelto al cerrar, `describedBy` para el texto que explica la acción, nombre con `aria-labelledby`, ✕ de 48 px, Escape que respeta `defaultPrevented`; se pinta en un portal en `body` (DIS-031); velo `bg-overlay` (`--color-overlay`) y bloqueo del fondo con `scroll-bloqueado` e `inert` en la raíz (DIS-038, DIS-044). `ConfirmDialog` usa `aria-disabled` mientras envía. Confirmaciones destructivas con `variant="danger"` (rechazar, revocar, quitar admin, eliminar, `ConfirmDialog`); las demás, primario (DIS-043). |
| `useFocusTrap`, `useScrollLock` | `lib/use-focus-trap.ts`, `lib/use-scroll-lock.ts` | Trampa de foco y bloqueo de desplazamiento comunes de `Modal` y `MobileMenu` (DIS-031, DIS-038). |
| `PlatformCard` | `platform-card.tsx` | Tarjeta de plataforma con favorito y apertura del enlace (solo `https://`, `enlaceSeguro`); enlace en el nombre con pseudo-elemento que cubre la tarjeta y estrella hermana (DIS-051). |
| `PlatformForm`, `PlatformIntegrationFields`, `PlatformSaveNotice`, `field-notes`, `platform-payload`, `platform-save-errors` | `platforms/` | Formulario, sección Integración, aviso con `warnings` (región `status`), errores por campo con `aria-describedby` y foco, validación y cuerpo por rol (DIS-017). |
| `PlatformsView` (`components/`), `unirCatalogo` (`catalog-union.ts`), `RequestCatalog` (orquesta; DIS-052: `use-catalogo-solicitable.ts`, `catalog-filters.tsx`, `catalog-grid.tsx`, `catalog-notice.tsx`), `RequestCatalogCard`, `RequestFormModal`, `AccessStatusBadge`, `describeRequestError` | `access/` | Catálogo solicitable, tarjeta con estado y motivo sin acción, modal con nivel y justificación (≤ 500, `aria-describedby`, foco), insignia de estado de acceso reutilizable y mensajes de `POST /access-requests` (DIS-013). |
| `MyRequestsView`, `MyRequests`, `MyAccess`, `ResponsiveList`/`ResponsiveRow`, `ListPager`, `RequestStatusBadge`, `formatearFecha`, `describeListError`/`listLoadError` | `access/` | Mis solicitudes y mis accesos; lista que es tabla en `md` y lista en móvil (`dl` por fila); paginación de `Paginated`; insignia de estado de solicitud; fechas `es-MX`; error de carga sin texto del servidor que conserva el 401 para `usePolling` (DIS-014). |
| `ApprovalsInbox`, `ApproveDialog`, `RejectDialog`, `describeDecisionError`, `MOTIVO_MIN`/`MOTIVO_MAX` | `access/` | Bandeja de aprobaciones; confirmación de aprobar (`Modal`, botón primario); rechazo con motivo obligatorio, contador y envío deshabilitado con la pista ligada; mensajes de approve/reject del contrato (DIS-015). |
| `UserAccessPanel`, `RevokeAccessDialog`, `motivoSinRevocar`, `describeRevokeError`, `REVOCACION_MOTIVO_MAX` | `users/` | Accesos de un usuario (sección, no `Modal`, para no anidar diálogos): plataforma, nivel, origen, quién aprobó, estado explicado y última ejecución; revocar con confirmación y motivo opcional (patrón de `RejectDialog`); fila actualizada y aviso con foco; mensajes de `POST /access/<id>/revoke` sin texto del servidor (DIS-018). |
| `Inventory`, `InventoryFilters`, `InventoryTable`, `limpiarBusqueda`, `ORIGENES_INVENTARIO` | `access/` | Inventario de permisos: contenedor (datos, filtros a la página 1, recarga), filtros (selectores y buscador con envío) y filas en `ResponsiveList` con ocho datos en cinco columnas (DIS-021). |
| `useOpcionesAlcance`, `ScopeSelects`, `PlataformaFiltro` | `access/scope-filters.tsx` | Áreas (admin: las suyas; superadmin: `GET /areas`) y plataformas del alcance, y los dos selectores encadenados; extraído del inventario en DIS-020 para reutilizarlo en Auditoría. |
| `AuditHistory`, `AuditFilters`, `AuditTable`, `AuditDetailModal`, `compararCampos`, `etiquetaAccion`, `UserAuditHistory`, `PlatformAuditHistory`, `rutaHistorialUsuario`/`rutaHistorialPlataforma` | `audit/` | Auditoría: contenedor común de `/audit` y de los historiales (filtros a la página 1, recarga, estados, paginación, detalle con foco de vuelta), filtros, filas en `ResponsiveList`, detalle con antes/después en texto plano, catálogo de eventos y rutas (DIS-020). |
| `DirectoryAccountForm`, `AdminAreasDialog`, `RemoveAdminDialog`, `AreaChecklist`, `validarAlta`, `describeDirectoryAccountError`, `describeRoleError`, `efectoAdmin` | `users/` | Alta en el directorio sin contraseña con validación espejo del contrato y errores por campo (409 en su campo, 422 con mensajes propios); hacer admin (`PUT /users/<id>` `admin_area` y luego `managed-areas`, al menos un área), cambiar áreas o quitar admin, con el efecto en las áreas concretas; casillas de áreas en `fieldset` con estados (DIS-019). |
| `DirectoryTab`, `directory-catalog`, `directory-errors` | `settings/` | Pestaña Directorio de Ajustes: configuración efectiva solo lectura con variable y origen, estados (carga, sin configurar, inválida, error, sin permiso) y prueba de conexión con avisos `status`/`alert` propios y `aria-disabled` (DIS-023). Cada pestaña de Ajustes vive en su archivo de `settings/` (`portal-tab`, `smtp-tab`, `templates-tab`, `backup-tab`, `preferences-tab`; DIS-011). |
| `ConnectorsAdmin`, `ConnectorList`, `ConnectorPanel`, `ConnectorForm`, `ConnectorDeleteDialog`, `JobsLog`, `JobsFilters`, `JobsTable`, `JobDetailModal`, `JobRetryDialog`, `connector-params`, `ConnectorParamFields`, `connector-catalog`, `connector-errors`, `job-catalog`, `job-errors` | `connectors/` | Conectores y bitácora de ejecuciones: lista, sección de configuración sin contraseñas (reglas espejo del servidor, parámetros por tipo `api`, `ssh` y `bd` (DIS-042) con error por campo `params.<ruta>`, conservados sin editor), prueba y borrado confirmados; bitácora con filtros, detalle de intentos, reintento confirmado y refresco solo con estados transitorios (DIS-022). |
| `AreaForm`, `AreaAdminsPanel`, `mensajeDeError` | `areas/` | Alta/edición de área con errores por campo; administradores del área (superadmin); mensajes del contrato `areas-y-roles.md` (DIS-016). |
| `variablesCss`, `.nx-chip-solid`, `.nx-chip-tint` | `lib/variables-css.ts`, `styles/components.css` | Color de los datos (plataforma, área) como variables `--chip-*`, sin `style` visual en línea (DIS-012). | `PlatformCard`, `PlatformAdmin`, `AreasList`. DIS-048: texto del chip de área con `--color-body-text`; texto del ícono de plataforma elegido por luminancia (`lib/color-legible.ts` + `data-texto`, tokens `--color-texto-sobre-fondo-*`, >= 4,5:1). |
| `useTokenColors` | `lib/use-token-colors.ts` | Lee tokens `--color-*` con `getComputedStyle` para librerías SVG sin `var()`; se actualiza al cambiar el tema (DIS-003). |
| `ThemeSelector`, `lib/tema.ts` | `components/theme-selector.tsx`, `lib/tema.ts` | Selector de tema en la cabecera de `AppShell` (FNC-032): pone la clase (`light`, `dark`, `theme-*`; sin clase = sistema) en `<html>` y la guarda en `localStorage` (`nexus-tema`). `SCRIPT_RESTAURAR_TEMA`, en `<head>` de `layout.tsx`, la restaura antes de pintar. Además se guarda en la cuenta (`PUT /me/preferences`, FNC-123): al iniciar sesión manda el tema de la cuenta (`aplicarTemaDeCuenta`; inválido → sistema); si falla el guardado, toast sin revertir. |
| Pantallas | `dashboard.tsx`, `platforms-view.tsx`, `favorites-list.tsx`, `notifications-list.tsx`, `platform-admin.tsx`, `areas-list.tsx`, `users-list.tsx`, `audit-log.tsx`, `settings-panel.tsx`, `login-form.tsx`, `logout-view.tsx` | Una por ruta. `settings-panel.tsx` (634 líneas desde DIS-023; su división es DIS-011) y `users-list.tsx` (695) concentran varias responsabilidades. |

## 5. Cliente de la API (`src/lib/api.ts`)

- `request<T>(path, init)` antepone `/api/v1`, envía `credentials: 'include'`, `redirect: 'manual'` y `Accept: application/json`; añade `Content-Type: application/json` si hay cuerpo.
- En el servidor (SSR) usa `BACKEND_URL`; en el navegador, ruta relativa.
- Errores como `ApiError(status, message, {code, fields, correlationId})` con `isForbidden` (403) e `isUnauthenticated` (401/302/redirección opaca); `fields` anidados se aplanan (`params.base_path`).
- `request` se exporta como `apiRequest`; `BACKEND_URL` por defecto `http://localhost:5001`.
- El objeto `api` expone una función por endpoint (sesión, áreas, plataformas, usuarios, preferencias, settings, SMTP, plantillas, notificaciones, auth, respaldo como Blob/FormData y búsqueda en directorio). La configuración del directorio va por `directoryApi` (`lib/access/directory.ts`); DIS-023 retiró `authConfig`/`saveAuthConfig`/`testAuthConfig` y el tipo `AuthConfig` heredados de NEXUS. Los tipos están en `src/lib/types.ts`.
- `useAsync(load, deps)` (`src/lib/use-async.ts`) da `data`, `loading`, `error` y `reload()`.
- `usePolling(load, { intervalSeconds, deps })` (`src/lib/use-polling.ts`, FNC-071): `useAsync` con polling según ADR-006.
  - `intervalSeconds` = `session.preferences.refresh_interval` (acotado a 15–3600 s; sin valor, 60 s)
  - Pestaña oculta: sin consultas; al volver, una inmediata. Una consulta a la vez
  - Error: espera ×2 por fallo hasta 3600 s con *jitter*; éxito restablece; `401` detiene
  - `refresh()` tras una escritura propia; `loading` es `true` en cada consulta: mostrar carga solo sin `data`
  - `data` es el último dato válido: se conserva tras un error, junto con `error`
  - `activo: false` (por defecto `true`, DIS-022): sin consultas periódicas ni al volver a la pestaña; la carga inicial, el cambio de `deps` y `refresh()` siguen

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
- **Texto mínimo 12 px (DIS-007, DIS-032):** el menor tamaño es `--text-xs` / `text-xs` (12 px); se retiró `--text-2xs` (10 px). `.nx-badge`, `.nexus-btn` y la marca de `.nexus-checkbox` usan `var(--text-xs)`; ejes de `Dashboard` `fontSize: 12`. `tests/accesibilidad/texto-minimo.test.ts` falla con un `font-size`, `text-[Npx]` o `fontSize` menor a 12 px en `src/`.
- **Área táctil 48 px (DIS-008):** todo botón, enlace o control con `role` interactivo mide al menos 44 px (objetivo 48: `min-h-12`, y `min-w-12` si es solo ícono), con foco `focus-visible:ring-2 focus-visible:ring-primary`. Acciones de fila y de tarjeta: `ACCION_FILA` / `ACCION_FILA_PELIGRO` de `components/acciones-fila.ts` (Usuarios, Áreas, Administrar plataformas); acciones principales: `Button` / `.nexus-btn` (48 px). Entradas de la barra lateral y del menú móvil, "Salir", chips de `TagPicker`, estrella de favorito, etiqueta de `Checkbox`, buscador y filtro del catálogo y entradas de archivo y de color también a 48 px. `tests/accesibilidad/area-tactil.test.ts` lo revisa por clases (límites en su encabezado; excepciones con motivo en `area-tactil.excepciones.ts`).
- **Tema claro/oscuro:** claro en `:root, html.light`; oscuro automático por `@media (prefers-color-scheme: dark)` (salvo `html.light`) y forzable con `html.dark`. Existen temas adicionales (`theme-emerald-light`, `theme-obsidian-dark`, `theme-rose-light`, `theme-violet-dark`). **No hay selector de tema en la interfaz**: solo aplica la preferencia del sistema.
- Clases de componentes portadas del portal original en `components.css` (`.nexus-btn`, `.nx-badge-*`, `.nx-modal-glass`, `.nexus-checkbox` en una sola regla, `.nx-chip-*`).
- **CSS depurado (DIS-009):** `components.css` pasó de 1746 a 219 líneas y `global.css` de 509 a 56; se retiraron 142 clases sin uso (DataTables, KPI, monitoreo, tour, toast, select propio, `nexus-modal`, `modal-*`...), reglas por id sin elemento, 6 `@keyframes` y variables `--nx-*` sin referencia. `tests/accesibilidad/css-sin-uso.test.ts` impide que vuelvan (clases, ids, elementos, atributos, animaciones y `--nx-*`; sin contar comentarios; las clases armadas solo valen para `nx-badge-<tono>`). `tokens.css` quedó solo con variables (DIS-047): se borraron `.dt-*`, `table.dataTable`, `.animate-shake` y `@keyframes shake` (sin llamador) y `html, body { color; margin; padding }` pasó a `global.css`; la misma prueba exige que `tokens.css` solo declare `--*` y selectores `:root`/`html`.
- **Sin estilos inline ni colores literales (DIS-009, DIS-012):** ni los CSS (salvo `tokens.css`) ni los TSX llevan colores literales. Un color que solo se conoce al ejecutar (plataforma, área) se pasa con `style={variablesCss({ '--chip-bg': … })}` y lo consume `.nx-chip-solid` / `.nx-chip-tint`. Única excepción: los valores por defecto de `<input type="color">` de `settings-panel.tsx` (dato, no estilo). Las props de Recharts de `dashboard.tsx` usan tokens de `useTokenColors` (DIS-003).

## 7. Cómo arrancar y verificar

Requiere Node 22 LTS (mínimo 18.18) y el backend corriendo.

```bash
cd frontend
npm ci                 # instala según package-lock.json
npm run dev            # http://localhost:3000, reenvía /api al backend (solo en dev)
npm run typecheck      # tsc --noEmit
npm run lint           # next lint
npm run build          # build standalone
```

Para apuntar a otro backend en dev: `BACKEND_URL=<url con nombre de host> npm run dev` (una IP se rechaza). Con el backend en `localhost:5001` no hace falta ninguna variable. Prueba: `tests/lib/next-config.test.ts`.

**Pruebas (FNC-025):**
- `npm test`: corre todas las pruebas una vez (Vitest + Testing Library + jsdom). `npm run test:watch`: modo vigilancia.
- Requiere Node 20.19+ o 22.13+ (por Vitest y jsdom).
- Las pruebas viven en `frontend/tests/`; configuración en `vitest.config.ts`.
- `tests/lib/api.test.ts`: cliente de la API con `fetch` simulado (éxito, error HTTP, 401).
- `tests/lib/use-polling.test.ts`: `usePolling` con temporizadores simulados (intervalo, pausa, *backoff*, sin solape, 401, desmontaje).
- `tests/components/audit-log.test.tsx`: Auditoría (FNC-025, reescrita en DIS-020): filas, "Sistema", HTML escapado, filtros al contrato y a la página 1 (C1 incluido), fechas válidas e inválidas, alcance por rol, carga, vacío con y sin filtros, error sin texto del servidor, recarga con foco, detalle antes/después y foco de vuelta.
- `tests/components/audit/audit-historiales.test.tsx`: historiales por usuario (propio, ajeno sin permiso, 404) y por plataforma (sin filtros de alcance), rutas, `compararCampos` y `valorLegible` (DIS-020).
- `tests/components/platform-admin.test.tsx` y `platform-card.test.tsx`: formulario de plataforma por rol, errores `403`/`404`/`409`/`422`, `warnings`, estados y SEG-24 (DIS-017); enlace "Historial" y acciones de fila de 48 px (DIS-035).
- `tests/accesibilidad/area-tactil.test.ts`: ningún botón, enlace ni `role` interactivo de `src/` bajo 44 px según sus clases (DIS-008).
- `tests/components/access/request-catalog.test.tsx`: catálogo solicitable (estados, filtro, envío, 409/403/422, foco) (DIS-013).
- `tests/components/home/filtro-url.test.tsx`: filtros por URL en `/requests`, `/inventory` y `/approvals` (DIS-036).
- `tests/components/access/my-requests-view.test.tsx`: Mis solicitudes y Mis accesos (pestañas, superadmin, motivo de rechazo, filtro, paginación, carga, vacío, error, 403, 401) (DIS-014).
- `tests/components/access/approvals-inbox.test.tsx`: bandeja (filtros, superadmin, propia, justificación escapada, paginación, carga, vacío, error), aprobar y rechazar (confirmación, motivo 10–500, fila actualizada, aviso con foco, 403/404/409/422) (DIS-015).
- `tests/components/users/user-access-panel.test.tsx`: accesos de un usuario (reglas de revocación del contrato, lista, filtro, paginación, carga, vacío, error, superadmin, foco), revocar (motivo opcional ≤ 500, recorte, `aria-disabled`, fila actualizada, aviso con foco, 403/404/409/422) y el botón "Accesos" de `UsersList` (DIS-018).
- `tests/components/users/directory-account-form.test.tsx` y `admin-role-dialog.test.tsx`: alta en el directorio (campos, sin contraseña, validación, 409/422/404/503, `aria-disabled`, áreas por rol, aviso con foco) y acciones de rol (solo superadmin, orden rol → áreas, fallo del segundo paso, quitar admin, errores, foco de vuelta) (DIS-019).
- `tests/components/access/inventory.test.tsx`: inventario (columnas del contrato, "Sistema", retirado, filtros al contrato y a la página 1, áreas y plataformas por rol, búsqueda limpia, carga, vacío con y sin filtros, 403/500 sin texto del servidor, recarga) (DIS-021).
- `tests/components/connectors/jobs-page.test.tsx`: pantalla `/admin/jobs` por rol (usuario sin permiso y sin llamar a la API, admin de área sin "Reintentar", superadmin con él) y estados de carga, vacío y error (DIS-041).
- `tests/components/connectors/connectors-admin.test.tsx` y `jobs-log.test.tsx`: conectores (solo plataformas `conector`, 404 sin configurar, obligatorios, sin contraseñas, cuerpo del contrato, 422/409 propios, prueba, borrado confirmado, foco) y bitácora (filas, `cancelado`, filtros a la página 1, carga, vacío, error, detalle escapado, reintento confirmado, 409/403, refresco solo transitorio) (DIS-022).
- `tests/components/connectors/connector-params.test.tsx`: parámetros por tipo `api`, `ssh` y `bd` (campos visibles, validación, cuerpo anidado, cambio de tipo, 422 `params.<ruta>` en su campo y con foco) (DIS-042).
- `tests/components/settings/directory-tab.test.tsx`: pestaña Directorio (valores con variable y origen, sin controles editables ni contraseña, sin configurar, inválida, error y 403 sin texto del servidor, reintento, prueba con texto propio en `status`/`alert`, foco, 409 recarga, `aria-disabled`) y pestañas de Ajustes (teclado, `tabpanel`, Directorio solo superadmin) (DIS-023, DIS-034).
- `tests/components/navegacion-por-rol.test.tsx`: entradas del menú por rol y `RequireRole` (sin permiso no monta ni llama a la API).
- `tests/accesibilidad/contraste.test.ts`: contraste WCAG de los tokens en los 7 temas (4.5:1 texto, 3:1 bordes).
- Los pares que fallan van en `fallas-contraste-conocidas.ts` con su tarea DIS y se marcan `it.fails`. Si una tarea los corrige, la prueba avisa: quita el par de la lista. Desde DIS-004, DIS-005 y DIS-006 (2026-10-26) la lista está vacía: todo par nuevo debe cumplir.
- Botón de peligro: `Button variant="danger"` usa `--color-error-solid` y `--color-on-error` (DIS-004). Foco de campos: anillo `ring-primary` sólido (DIS-006).
- `tests/accesibilidad/colores-literales.test.ts`: falla si aparece un color literal (`#hex`, `rgb()`, nombres como `white`, clases como `text-red-600`) en `src/components`, `src/app` o los CSS de `src/styles` (todos menos `tokens.css`; sin contar comentarios) (DIS-009).
- Los literales justificados tienen tope por archivo en `colores-literales.excepciones.ts` (hoy ninguno). Si corriges uno, baja el tope.
- `tests/accesibilidad/css-sin-uso.test.ts`: cada clase, id, `@keyframes` y variable `--nx-*` de `components.css` y `global.css` debe tener llamador en `src/` (las armadas como `nx-badge-${tono}` cuentan) (DIS-009).
- `tests/accesibilidad/sin-estilos-inline.test.ts`: ningún `style` en línea en `src/` (tampoco spread, objeto suelto ni `setAttribute`) salvo variables `--*` con `variablesCss()` y las props de Recharts de `dashboard.tsx` (DIS-012).
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
| 2 | Colores hex literales como valores por defecto en formularios y gráfica. | `platform-admin.tsx`, `areas-list.tsx`, `settings-panel.tsx` (`dashboard.tsx` corregido en DIS-003) |
| 3 | Colores literales en `tailwind.config.ts` (`warning`, `error`, `info`) en lugar de tokens. | `tailwind.config.ts` |
| 4 | `text-white` fijo en el botón de `error.tsx`. | `app/error.tsx` |
| 5 | Sin selector de tema; temas adicionales definidos pero inalcanzables. | `styles/tokens.css` |
| 6 | Pocas pruebas de frontend: runner y pruebas base listas (FNC-025); faltan pruebas de más pantallas. | `frontend/tests/` |
| 7 | Componentes grandes con varias responsabilidades (`settings-panel.tsx`, `users-list.tsx`). **Resuelto en DIS-011** (98, 239 y 188 líneas). | `components/` |
| 8 | ~~Navegación lateral oculta en móvil sin menú alternativo~~ — resuelta por DIS-025 (`MobileMenu`). | `app-shell.tsx` |
| 9 | Valor por defecto del backend escrito como dirección de loopback numérica en el código (incumple "sin IPs"; debería ser `localhost` o configuración). | `next.config.ts`, `lib/api.ts` |
| 10 | Título "Nexus" fijo en `layout.tsx` y en la barra lateral, aunque el nombre del portal es configurable en `system_config`. | `app/layout.tsx`, `app-shell.tsx`, `mobile-menu.tsx` |

> Límites de las pruebas automáticas: la de contraste mide los tokens de `tokens.css`, no el CSS final (reglas con `!important` pueden ignorarlos); la de colores literales no detecta colores con nombre, `oklch()`/`lab()` ni valores arbitrarios de Tailwind.

## Desplazamiento (DIS-044)
- `html` y `body` no se desplazan (`global.css`, heredado). Se desplaza la raíz `#raiz-app` de `layout.tsx` (`h-dvh overflow-y-auto`, páginas sin `AppShell`) o, con `AppShell`, su `<main>` (`min-h-0 flex-1 overflow-y-auto`, `tabIndex={-1}`); cabecera fija y barra lateral con desplazamiento propio.
- Los contenedores desplazables llevan `data-desplazable`; `useScrollLock` los bloquea con `scroll-bloqueado` en la raíz y la marca `inert` mientras hay un diálogo o el menú móvil abiertos (ambos en portal en `body`).
