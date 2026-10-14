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
│   ├── api.ts      # Cliente de la API v1
│   ├── types.ts    # Contrato de tipos con la API
│   └── use-async.ts# Hook de carga con estado loading/error y reload()
└── styles/         # tokens.css, global.css, components.css (portados del portal original)
```

## 2. Pantallas (`frontend/src/app`)

| Ruta | Componente | Qué hace | Visible en el menú para |
|---|---|---|---|
| `/` | `Dashboard` | Panel: contadores (áreas, plataformas, visitas y, para administradores, usuarios), top de visitas y plataformas por área (gráfica recharts). | Todos |
| `/platforms` | `PlatformCatalog` | Catálogo de plataformas visibles: filtro por área (servidor) y búsqueda (cliente); abre el enlace, registra visita y marca favorito. | Todos |
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

Definido en `components/app-shell.tsx` (`NAV`). Cada entrada puede exigir `any_admin` (superadmin o admin de área) o `admin` (solo superadmin; hoy ninguna entrada lo usa). Los permisos salen de `GET /api/v1/me` (`permissions.is_admin`, `permissions.is_area_admin`).

| Entrada | `usuario` | `admin_area` | `administrador` |
|---|---|---|---|
| Panel, Plataformas, Favoritos, Notificaciones, Auditoría, Ajustes | Sí | Sí | Sí |
| Administrar plataformas, Áreas, Usuarios | No | Sí | Sí |

Dentro de Ajustes, las pestañas de sistema solo se muestran a `administrador`. Ocultar en la interfaz no protege: el backend vuelve a validar cada endpoint.

## 4. Componentes principales

| Componente | Archivo | Rol |
|---|---|---|
| `AppShell` | `app-shell.tsx` | Marco: barra lateral (oculta en móvil), cabecera con nombre, rol y "Salir"; estados de carga y error de sesión. |
| `SessionProvider` / `useSession` | `session-provider.tsx` | Pide `/me` una vez; sin sesión redirige a `/login`. |
| `Card`, `PanelHeader`, `StatTile`, `Spinner`, `ErrorNote`, `EmptyNote`, `Badge` | `ui.tsx` | Piezas base con clases del portal original (estados de carga, vacío y error). |
| `Field`, `TextInput`, `TextArea`, `Select`, `Checkbox`, `Button`, `Modal`, `ConfirmDialog` | `form.tsx` | Controles de formulario y modales (`.nexus-btn`, `.nexus-checkbox`, `.nx-modal-glass`). |
| `PlatformCard` | `platform-card.tsx` | Tarjeta de plataforma con favorito y apertura del enlace. |
| Pantallas | `dashboard.tsx`, `platform-catalog.tsx`, `favorites-list.tsx`, `notifications-list.tsx`, `platform-admin.tsx`, `areas-list.tsx`, `users-list.tsx`, `audit-log.tsx`, `settings-panel.tsx`, `login-form.tsx`, `logout-view.tsx` | Una por ruta. `settings-panel.tsx` (745 líneas) y `users-list.tsx` (581) concentran varias responsabilidades. |

## 5. Cliente de la API (`src/lib/api.ts`)

- `request<T>(path, init)` antepone `/api/v1`, envía `credentials: 'include'`, `redirect: 'manual'` y `Accept: application/json`; añade `Content-Type: application/json` si hay cuerpo.
- En el servidor (SSR) usa `BACKEND_URL`; en el navegador, ruta relativa.
- Errores como `ApiError(status, message)` con `isForbidden` (403) e `isUnauthenticated` (401/302/redirección opaca).
- El objeto `api` expone una función por endpoint (sesión, áreas, plataformas, usuarios, preferencias, settings, SMTP, plantillas, notificaciones, auth, respaldo como Blob/FormData, LDAP y búsqueda en directorio). Los tipos están en `src/lib/types.ts`.
- `useAsync(load, deps)` (`src/lib/use-async.ts`) da `data`, `loading`, `error` y `reload()`.

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

**Estado al documentar:** en esta copia no hay `node_modules`, así que `typecheck`, `lint` y `build` **no se ejecutaron** en FNC-001. Además, `eslint` y `eslint-config-next` no están en `devDependencies` ni hay configuración de ESLint, por lo que `npm run lint` pedirá configurarlo la primera vez.

## 8. Deuda conocida

| # | Deuda | Dónde |
|---|---|---|
| 1 | Estilos inline con colores dinámicos (color de plataforma o área) en 4 lugares. | `platform-card.tsx`, `platform-admin.tsx`, `areas-list.tsx` |
| 2 | Colores hex literales como valores por defecto en formularios y gráfica. | `platform-admin.tsx`, `areas-list.tsx`, `dashboard.tsx`, `settings-panel.tsx` |
| 3 | Colores literales en `tailwind.config.ts` (`warning`, `error`, `info`) en lugar de tokens. | `tailwind.config.ts` |
| 4 | `text-white` fijo en el botón de `error.tsx`. | `app/error.tsx` |
| 5 | Sin selector de tema; temas adicionales definidos pero inalcanzables. | `styles/tokens.css` |
| 6 | ESLint no instalado ni configurado; sin pruebas de frontend. | `package.json` |
| 7 | Componentes grandes con varias responsabilidades (`settings-panel.tsx`, `users-list.tsx`). | `components/` |
| 8 | Navegación lateral oculta en móvil (`hidden md:block`) sin menú alternativo. | `app-shell.tsx` |
| 9 | Valor por defecto del backend escrito como dirección de loopback numérica en el código (incumple "sin IPs"; debería ser `localhost` o configuración). | `next.config.ts`, `lib/api.ts` |
| 10 | Título "Nexus" fijo en `layout.tsx` y en la barra lateral, aunque el nombre del portal es configurable en `system_config`. | `app/layout.tsx`, `app-shell.tsx` |
