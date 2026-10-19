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
│   └── use-async.ts# Hook de carga con estado loading/error y reload()
└── styles/         # tokens.css, global.css, components.css (portados del portal original)
```

## 2. Pantallas (`frontend/src/app`)

| Ruta | Componente | Qué hace | Visible en el menú para |
|---|---|---|---|
| `/` | `Dashboard` | Panel: contadores (áreas, plataformas, visitas y, para administradores, usuarios), top de visitas y plataformas por área (gráfica recharts). | Todos |
| `/platforms` | `PlatformCatalog` | Catálogo de plataformas visibles: filtro por área (servidor) y búsqueda (cliente); abre el enlace, registra visita y marca favorito. | Todos |
| `/requests` | — (reservada, DIS-014) | Mis solicitudes; guarda `requester`. | `usuario`, `admin_area` |
| `/approvals` | — (reservada, DIS-015) | Aprobaciones; guarda `any_admin`. | `administrador`, `admin_area` |
| `/inventory` | — (reservada, DIS-021) | Inventario; alcance por rol en el backend. | Todos |
| `/admin/connectors` | — (reservada, DIS-022) | Conectores; guarda `admin`. | `administrador` |
| `/favorites` | `FavoritesList` | Plataformas marcadas como favoritas. | Todos |
| `/notifications` | `NotificationsList` | Notificaciones in-app: marcar leídas y borrar. | Todos |
| `/admin/platforms` | `PlatformAdmin` | Crear, editar y eliminar plataformas; asignar usuarios. | `administrador`, `admin_area` |
| `/areas` | `AreasList` | Áreas visibles; el superadmin crea/edita/borra y gestiona miembros. | `administrador`, `admin_area` |
| `/users` | `UsersList` | Alta, edición y baja de usuarios; asignación de áreas y plataformas; búsqueda en el directorio; usuarios inactivos y purga (superadmin). | `administrador`, `admin_area` |
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
| Panel, Catálogo, Favoritos, Notificaciones, Inventario, Auditoría, Ajustes | Sí | Sí | Sí |
| Mis solicitudes | Sí | Sí | No |
| Aprobaciones, Administrar plataformas, Áreas, Usuarios | No | Sí | Sí |
| Conectores | No | No | Sí |

- Guarda de ruta: `<RequireRole requires="…">` muestra "sin permiso" (`ErrorNote`) y no monta la pantalla, así que no llama a la API
- Hoy la usan `/requests`, `/approvals` y `/admin/connectors`; las rutas previas no la usan
- Dentro de Ajustes, las pestañas de sistema solo se muestran a `administrador`. Ocultar en la interfaz no protege: el backend vuelve a validar cada endpoint.

## 4. Componentes principales

| Componente | Archivo | Rol |
|---|---|---|
| `AppShell` | `app-shell.tsx` | Marco: barra lateral (oculta en móvil), cabecera con nombre, rol y "Salir"; estados de carga y error de sesión. |
| `SessionProvider` / `useSession` | `session-provider.tsx` | Pide `/me` una vez; sin sesión redirige a `/login`. |
| `RequireRole` / `meetsRequirement` | `require-role.tsx` | Guarda de ruta y regla de visibilidad por rol (FNC-070). |
| `Card`, `PanelHeader`, `StatTile`, `Spinner`, `ErrorNote`, `EmptyNote`, `Badge` | `ui.tsx` | Piezas base con clases del portal original (estados de carga, vacío y error). |
| `Field`, `TextInput`, `TextArea`, `Select`, `Checkbox`, `Button`, `Modal`, `ConfirmDialog` | `form.tsx` | Controles de formulario y modales (`.nexus-btn`, `.nexus-checkbox`, `.nx-modal-glass`). |
| `PlatformCard` | `platform-card.tsx` | Tarjeta de plataforma con favorito y apertura del enlace. |
| Pantallas | `dashboard.tsx`, `platform-catalog.tsx`, `favorites-list.tsx`, `notifications-list.tsx`, `platform-admin.tsx`, `areas-list.tsx`, `users-list.tsx`, `audit-log.tsx`, `settings-panel.tsx`, `login-form.tsx`, `logout-view.tsx` | Una por ruta. `settings-panel.tsx` (745 líneas) y `users-list.tsx` (581) concentran varias responsabilidades. |

## 5. Cliente de la API (`src/lib/api.ts`)

- `request<T>(path, init)` antepone `/api/v1`, envía `credentials: 'include'`, `redirect: 'manual'` y `Accept: application/json`; añade `Content-Type: application/json` si hay cuerpo.
- En el servidor (SSR) usa `BACKEND_URL`; en el navegador, ruta relativa.
- Errores como `ApiError(status, message, {code, fields, correlationId})` con `isForbidden` (403) e `isUnauthenticated` (401/302/redirección opaca); `fields` anidados se aplanan (`params.base_path`).
- `request` se exporta como `apiRequest`; `BACKEND_URL` por defecto `http://localhost:5001`.
- El objeto `api` expone una función por endpoint (sesión, áreas, plataformas, usuarios, preferencias, settings, SMTP, plantillas, notificaciones, auth, respaldo como Blob/FormData, LDAP y búsqueda en directorio). Los tipos están en `src/lib/types.ts`.
- `useAsync(load, deps)` (`src/lib/use-async.ts`) da `data`, `loading`, `error` y `reload()`.

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
- Pruebas: `tests/lib/access/` (forma por endpoint, errores 401/403/409/422/500, bandera) y `tests/components/users-list.test.tsx`

## 6. Estilos, tokens y tema

- Orden de carga en `app/layout.tsx`: `styles/tokens.css` → `styles/global.css` → `styles/components.css` → `app/globals.css` (Tailwind).
- **Tokens:** variables CSS en `styles/tokens.css` (`--color-primary`, `--color-body-bg`, `--color-panel-fill`, `--color-input-*`, `--color-tab-*`, `--color-success`, `--radius-base`, `--radius-panel`, etc.), muchas como canales `R G B` para admitir opacidad.
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
- `tests/components/audit-log.test.tsx`: `AuditLog` con la API simulada (datos, filtro, vacío, error).
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
