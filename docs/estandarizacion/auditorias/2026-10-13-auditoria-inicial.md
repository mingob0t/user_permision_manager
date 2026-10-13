# Auditoría de estándares inicial — 2026-10-13

Alcance: proyecto completo (rama `fnc/FNC-001-incorporacion-metodo`), solo lectura. Primera auditoría: no hay anterior contra la cual comparar; todo es **nuevo**. No existía ninguna tarea del tablero relacionada (no se editó el tablero, ver "Tareas propuestas").

## Resumen por categoría

| Categoría | Hallazgos | Cifras clave |
|---|---|---|
| 1 Código duplicado | 7 (H-04, H-05, H-06, H-07, H-08, H-12, H-13) | 4 `_moved`, 8 lecturas de `FRONTEND_URL`, 2 purgas, 3 conexiones LDAP |
| 2 Clases y estilos | 5 (H-03, H-09, H-10, H-11, H-14) | 154 de 170 clases CSS sin uso, 4 estilos inline, 260 colores literales en CSS fuera de tokens |
| 3 Patrones de interfaz | 3 (H-10, H-11, H-15) | Tablas, botón de borrar e inputs resueltos de 2-3 formas |
| 4 Comportamiento | 3 (H-16, H-17, H-18) | 44 rutas heredadas sin protección, sin toasts, `dark:` inoperante |
| 5 Modularidad | 6 (H-05, H-19) | `admin.py` 645 líneas, `create_app` 183 líneas, `settings-panel.tsx` 745 |
| 6 Variables | 4 (H-02, H-20, H-21, H-22) | 20 variables leídas sin registrar; 5 registradas sin uso |
| 7 Móviles | 0 | Sin Flutter ni Unity |
| 8 Otros | 5 (H-01, H-23, H-24, H-25, H-26) | 1 IP, 3 contraseñas de ejemplo en código, 15 scripts `scratch/` |

## Hallazgos por impacto

### H-01 — Código muerto: 7 blueprints heredados que solo redirigen o devuelven 410 (cat. 8/5, FNC, backend)
- 44 rutas, 382 líneas: `app/modules/auth/routes.py` (11 rutas, 86 líneas), `users/routes.py` (9), `areas/routes.py` (7), `notifications/routes.py` (8), `settings/routes.py` (4), `audit/routes.py` (2), `core/routes.py` (3).
- Registrados en `app/__init__.py:127-133` y exentos de CSRF en `app/__init__.py:140-143`. `app/decorators.py:1-10` solo reexporta `app.authz`. `app/modules/core/services.py` y los `__init__.py` están vacíos. Son los únicos usos de `FRONTEND_URL`.
- `authz.py:222` redirige a `core.index`: depender de una ruta heredada.
- Propuesta: retirar los blueprints y `decorators.py`, conservando solo `GET /` JSON de salud si se necesita. Los modelos de cada módulo (`models.py`, `services.py`) permanecen.

### H-02 — Variables sin registro y registro que no corresponde al código (cat. 6, FNC, backend)
`docs/configuracion/VARIABLES.md:9-20` es una plantilla genérica de la incorporación.
- Leídas por el código y **no registradas**: `TZ_APP`/`TZ` (`app/__init__.py:13`), `DB_PASS` (`:37`), `REDIS_HOST/PORT/PASS` (`:93-95`), `FRONTEND_URL` (`core/routes.py:16`), `SMTP_SERVER/PORT/ENCRYPTION/AUTH/USER/PASSWORD/SENDER_NAME/SENDER_EMAIL/FORCE_ENV` (`notifications/services.py:35-84`), `ENABLE_NOTIFICATIONS` (`:203`), `DEBUG_SMTP` (`:116,179`), `DEBUG_LDAP` (`auth/services.py:10`), `NOTIFY_USER_CREATED` (`auth/services.py:151`, `api/auth.py:111`), `TRUSTED_PROXIES` (`api/auth.py:32`), `AUTHELIA_ENABLED/HEADER_USER/HEADER_NAME/HEADER_GROUPS/GROUP_ADMIN/SLO_URL` (`api/auth.py:38-183`), `BACKEND_URL` (`frontend/next.config.ts:10`, `src/lib/api.ts:20`), `NGINX_CONF_PATH` (`utils/toggle_authelia.py:13`).
- Registradas y **sin uso en el código**: `APP_ENV`, `LOG_DIR`, `LOG_LEVEL`, `DB_PASSWORD` (el código usa `DB_PASS`), `NEXT_PUBLIC_API_URL` (el código usa `BACKEND_URL`).
- Discrepancias de valor por defecto: `DB_ENGINE` registrado `postgresql`, código `sqlite` (`app/__init__.py:35`) y `.env.example` `mysql`; `DB_PORT` registrado 5432, `.env.example` 3306; `BASE_URL` registrado `http://localhost:5000`, código `http://<IP privada>` (`auth/services.py:152`).
- `.env.example` incluye variables que el código no lee: `FLASK_APP`, `FLASK_ENV`, `PORT_APP`, `AUTHELIA_SSO_URL`, `DEBUG_AUTH`. Faltan en él: `DEBUG_LDAP`, `NOTIFY_USER_CREATED`, `REDIS_PASS`, `BACKEND_URL`.
- Sin validación al arrancar: `SECRET_KEY` cae a `'nexus-premium-secret-key'` (`app/__init__.py:34`); `DB_*` se usan sin comprobar (`:37`).
- `HISTORIAL.md` tiene solo el alta inicial. En git, ``.env.example` y `deploy/` tuvieron 9 commits de cambios de infraestructura sin entrada; el historial previo a la incorporación no puede reconstruirse con motivo (se debe preguntar al responsable).
- Propuesta: reescribir VARIABLES.md desde el código, crear `app/config.py` único con validación al arrancar.

### H-03 — CSS: 154 de 170 clases definidas sin uso (cat. 2, DIS, web)
- `frontend/src/styles/components.css` (1741 líneas) y `global.css` (499) son el CSS del portal original con DataTables (`dt-*`, `dataTable`, `components.css:17-244`), tours (`nx-tour-*`), KPIs (`kpi-*`, `components.css`), monitores, `stacked-*`, `toast*`, `nx-select-*`, `nx-btn-*`, etc. Ninguna se referencia desde `src/**/*.tsx`. Solo se usan clases `nx-badge`/`nx-badge-<tono>` (dinámicas, `ui.tsx:105`) y algunas utilitarias.
- Referencias a PSX5K: `components.css:981` (Operational Badges), `:1130` (PSX5K TERMINAL), `:1143` (PSX5K UTILS & MODALS).
- Definidas en dos archivos: `nexus-modal`, `modal-backdrop/panel/header/body/footer` (`components.css:1551-1621` y `global.css:204-335`), `custom-scrollbar` (`components.css:1108-1126`, `global.css:75-83`), `tab-panel-content`, `is-collapsed`, `ghost-row`, `dt-*` también en `tokens.css:9-33` (CSS en archivo de tokens).
- Propuesta: depurar los CSS a lo que se usa; mantener `tokens.css` solo con variables.

### H-04 — Lógica de usuario creado/avisos y purga duplicada (cat. 1, FNC, backend)
- Aviso "usuario_creado": `api/auth.py:111-121` y `auth/services.py:151-158` (la segunda con IP por defecto y URL `/auth/login` heredada).
- Purga de inactivos: `auth/services.py:172-200` (criterio sin nulos; sin uso actual desde la API) y `api/crud.py:415-480` (criterio vigente).
- Propuesta: una función en `notifications/services.py` y `users/services.py`.

### H-05 — Monolitos de backend (cat. 5, FNC, backend)
- `app/modules/api/admin.py` — 645 líneas, mezcla ≥7 responsabilidades: identidad (`:79`), SMTP (`:130-250`), plantillas (`:254`), notificaciones (`:294`), config LDAP (`:338`), respaldo/importación (`:417-577`), búsqueda de directorio (`:579-645`), con consultas y reglas dentro de la ruta. Partir en `settings`, `smtp`, `templates`, `notifications`, `auth_config`, `backup`, `directory`.
- `app/modules/api/crud.py` — 480 líneas, áreas, plataformas y usuarios juntos (`:36`, `:140`, `:300+`). Partir por entidad (`areas_api.py`, `platforms_api.py`, `users_api.py`) más `users/services.py`.
- `app/__init__.py:26` `create_app` — 183 líneas: configuración, BD, CSRF, blueprints, creación de tablas y usuario semilla.
- `auth/services.py:21` `authenticate_user_ldap` — 150 líneas; `admin.py:477` `import_backup` — 96 líneas; `notifications/services.py:191`, `api/auth.py:71` ≈50.
- Capas mezcladas: rutas con `Model.query` y reglas de negocio (`crud.py`, `routes.py`); `routes.py:216` `stats` agrega datos en la ruta.
- Sin carpeta de pruebas: no existe ningún test automatizado (los `test_*.py` de `utils/` son scripts manuales).

### H-06 — Monolitos de frontend (cat. 5, DIS, web)
- `settings-panel.tsx` — 745 líneas, 8 pestañas en un archivo (`PortalTab :21`, `BackupTab :145`, `SmtpTab :225` 162 líneas, `TemplatesTab :387`, `LdapTab :482` 142 líneas, `PreferencesTab :624`). Partir en `components/settings/`.
- `users-list.tsx` — 581 líneas: `TagPicker :22`, `UserForm :62` (166), `DirectoryPicker :228`, `PurgePanel :308`, `UsersList :411` (172). Partir en `components/users/`.
- `platform-admin.tsx` (327; `PlatformAdmin` 168 líneas), `areas-list.tsx` (241), `login-form.tsx:17` (140 líneas).
- Los componentes hacen `useAsync`, validan y renderizan a la vez; no hay capa de presentación separada.
- `PlatformCard` (`platform-card.tsx`) y `platform-admin.tsx` mezclan catálogo y administración (carpetas `/platforms` y `/admin/platforms`).

### H-07 — Utilidades heredadas del producto original (cat. 8, FNC, backend)
- `utils/` (16 archivos de scripts manuales): `nexus_health.py:14-75` importa `psx5k_cmd` y `psx5k_worker.pid`; `db_migrate.py:60-68` altera `psx5k_details`; `db_inspector.py`, `db_check.py`, `check_db.py` (tres revisores de esquema solapados); `toggle_authelia.py`, `test_ldap.py`, `test_smtp.py`.
- Contraseñas de ejemplo en código: `utils/seed_users.py:31` (`Nexus2024!`), `utils/emergency_reset.py:33,39` y `app/__init__.py:164-167` (`admin123`, además impresa en consola), `utils/nexus_structure.sql:174`. `app/__init__.py:160-169` crea siempre un superadmin con clave conocida en un despliegue vacío (riesgo de seguridad, escalar a `auditor-seguridad`).
- Migraciones SQL sueltas: `utils/migrations/001..004` (3 `.sql`, 1 `.py`) y `nexus_structure.sql` (191 líneas, 7 tablas, sin `areas/platforms`); no hay herramienta de migraciones (Alembic) ni registro de cuáles se aplicaron. `db.create_all()` corre al arrancar (`app/__init__.py:156`).
- Propuesta: decidir con el usuario qué conservar; adoptar Alembic y consolidar.

### H-08 — `scratch/`: 15 scripts desechables (cat. 8, FNC, backend)
`scratch/` completo (41+32+28+27+25+23+23+22+22+20+20+19+19+18+17 líneas). Contiene credenciales de ejemplo (`list_dbs.py:5`, `cross_db_search_v2.py:8`, `multi_fix_db.py:8` con `username:password@localhost`), una IP de ejemplo (`seed_notifications.py:20`: <IP privada de ejemplo>), `fix_db.py`/`fix_db_schema.py`/`multi_fix_db.py` con el mismo propósito, y `seed_*`/`list_*`/`inspect_db.py` solapados con `utils/`. Propuesta: borrar o mover a `.gitignore`.

### H-09 — Estilos inline y valores de color en TSX (cat. 2, DIS, web)
- `style={{…}}` con datos de color de la BD: `areas-list.tsx:156`, `platform-card.tsx:52,83`, `platform-admin.tsx:236`. Son colores dinámicos del usuario; proponer variable CSS `--*` (`style={{'--c': …}}`) y clase con token.
- `document.body.style.overflow`: `form.tsx:114-119` (alternativa: clase en `<body>`).
- Colores literales en TSX: `#6366f1` (`areas-list.tsx:30,86`, `platform-admin.tsx:17,137`, `dashboard.tsx:79`), `#ffffff`/`#0f172a` (`platform-admin.tsx:18,145`, `settings-panel.tsx:34-35`). `dashboard.tsx:71-74` usa estilos de objeto en el tooltip del gráfico.
- Colores Tailwind crudos fuera de tokens (`emerald-*`, `red-*`, `amber-*`): ver D-11.
- CSS: 260 usos de `#hex`/`rgba()` en `components.css` y `global.css` (p. ej. `global.css:46,199-200,218,237-242,307,324-336`) fuera de `tokens.css`; `!important` en `global.css:199-200,289`.

### H-10 — Tablas, formularios y acciones sin patrón común (cat. 3, DIS, web)
- Tablas: `audit-log.tsx:64` y `platform-admin.tsx:219` usan `<table>` a mano con los mismos encabezados; users y areas usan filas de tarjetas (`users-list.tsx`, `areas-list.tsx:140+`). Sin paginación (auditoría pide 200 filas, `audit-log.tsx:19`), sin ordenamiento ni toolbar común.
- Botón "Eliminar" en línea tres veces (D-08) mientras `Button` existe (`form.tsx:73`).
- Filtros (`platform-catalog.tsx:50,58`, `audit-log.tsx:47`) con clases largas propias en lugar de `TextInput`/`Select`.
- Modales: `Modal` (`form.tsx:96`) con footer propio por pantalla; el `ConfirmDialog` fija el texto "Eliminando…" (`form.tsx:187`) aun cuando la acción es "Vaciar" o "Purgar".
- Sin breadcrumbs, toasts ni asistentes. Confirmaciones de éxito mediante texto verde en línea (`settings-panel.tsx:17,189`) vs. otros sin retroalimentación.

### H-11 — Modo oscuro y temas inoperantes (cat. 2/4, DIS, web)
- `tailwind.config.ts` usa `darkMode: 'class'`, pero ningún código añade `dark`/`light` al `<html>` (`layout.tsx:19`; `grep classList` sin resultados). Las 10 variantes `dark:` (p. ej. `notifications-list.tsx:16-18`, `settings-panel.tsx:17`) no actúan; el oscuro solo llega por `@media (prefers-color-scheme: dark)` (`tokens.css:207`).
- `html.dark` (`tokens.css:271`) y los temas `theme-emerald-light`, `theme-obsidian-dark`, `theme-rose-light`, `theme-violet-dark` (`tokens.css:331-537`) no tienen selector de tema en la UI (la pestaña Preferencias no los aplica).
- Posible tema sin valor completo: no verificado (AA y contraste se delegan a `auditor-accesibilidad`).

### H-12 — Duplicados de helpers y estructura en backend (cat. 1, FNC, backend)
Ver D-02, D-03, D-06 del catálogo: `_frontend()` en 3 archivos y `FRONTEND_URL` leído en 8 sitios; `_payload/_error` en `crud.py:23-28` y `admin.py:25-30`; `_env_flag` importado como privado desde otro módulo (`admin.py:35`, acoplamiento a un interno); LDAP `Server/Connection` con `connect_timeout=5` en `auth/services.py:47,219` y `admin.py:614`; `_escape_ldap_filter` en `admin.py:579`.
- Formatos de error: `{'status':'error','message'}` en la API v1, pero `jsonify({'status':'deprecated','use'})` y `{'status':'moved','to'}` en `core/routes.py:39,45` y `purge` usa 400/409 de forma mixta.

### H-13 — Respuestas y auditoría con formas distintas (cat. 4, FNC, backend)
- `add_audit_log` se invoca con firmas diferentes: con `module/target` (`crud.py:55`), sin ellos (`api/auth.py:106`, `auth/services.py:195` con minúsculas "usuario purgado"); acciones en mayúsculas con prefijo vs. minúsculas. `audit/services.py:21-24` usa `except:` desnudo; falla de auditoría silenciosa.
- `print()` en lugar de logger: `app/__init__.py:167-169`, `auth/services.py:178+`.
- Las 15 rutas de `crud.py` y todas las de `admin.py` llevan `@login_required` y permiso explícito (**sin hallazgo de seguridad** salvo `/notifications` en `admin.py:294-324` que solo exige sesión por diseño). Rutas públicas legítimas: `api/auth.py:51,70,126`.

### H-14 — Dependencias y archivos sin uso (cat. 8, FNC, backend/web)
- `requirements.txt` incluye `redis` y `ldap3`; `redis_client.py` se usa solo al arrancar (`app/__init__.py:93-95`) y `redis_registry` no tiene consumidores (por verificar con el responsable). Sin pruebas ni linter declarados.
- `app/modules/core/services.py` vacío; 8 `__init__.py` vacíos (normal).
- `frontend/src/app/globals.css` (12 líneas) además de `styles/global.css` (nombres casi iguales, riesgo de confusión).
- `logs/` en la raíz del repo (revisar `.gitignore`).

### H-15 — Pantallas fuera del patrón (cat. 3, DIS, web)
- Estados de carga/error/vacío: están en `ui.tsx`, pero `dashboard.tsx:17` retorna `Spinner` y sale (sin conservar la estructura) mientras otras muestran el spinner sobre la lista (`audit-log.tsx:50`).
- Confirmaciones: solo `ConfirmDialog`, correcto; `users-list.tsx:313,397` controla la purga con estado propio, no con la API del componente.
- Páginas `/platforms` y `/admin/platforms` con dos modelos de tarjetas/tablas distintos.

### H-16 — Valores mágicos (cat. 6, FNC, backend)
- `timedelta(days=7)`, `'nexus_session'`, `pool_recycle 3600` (`app/__init__.py:47,48,57-58`); `connect_timeout=5` (`auth/services.py:47,219`, `admin.py:614`); `timeout=10` SMTP (`notifications/services.py:110,112,172,174`); `days=30` (`auth/services.py:172`); `.limit(50)` (`admin.py:305`), `.limit(5)` (`routes.py:225`); `[:200]` (`admin.py:238,409`, `auth.py:148`); `[:20]` (`crud.py:479`); `MAX_LOGO_BYTES=512*1024` (`admin.py:46`); `MAX_LENGTH=100` (`naming.py:15`); puerto 5001 en `deploy/backend.service.tmpl:16`, `nginx.conf.tmpl:12`, `frontend/next.config.ts:10`, `src/lib/api.ts:20`; 3000 en `nginx.conf.tmpl:17`.
- `TRUSTED_PROXIES` por defecto `127.0.0.1,::1` (`api/auth.py:33`) y `'administrador'` como grupo por defecto (`:44`). Propuesta: `app/config.py` y registrar en `VARIABLES.md` (sección constantes).

### H-17 — Sin mecanismo de feedback en la interfaz (cat. 4, DIS, web)
- Sin toasts: las acciones muestran texto en línea o nada (ver H-10). Errores de acción mediante `ErrorNote` según pantalla; `error.tsx` global existe. Revisar acciones que no reflejan estado ocupado (`platform-card.tsx:64` favorito).
- Regla de habilitación por selección: no aplica (las listas no tienen selección múltiple).

### H-18 — Documentación obsoleta (cat. 8, FNC, docs)
- `docs/business_rules.md` (77 líneas): describe el portal original (módulos, mensajes de error de áreas "No se pueden eliminar las siguientes áreas…" que difiere del backend actual `crud.py:96-99`). Mezclar lo vigente en `docs/REQUERIMIENTOS.md` o `docs/backend/` y archivar.
- `docs/ARCHITECTURE.md` (46 líneas): vigente en el patrón Flask+Next.js, pero duplica `docs/decisiones/ADR-001-stack.md` y `docs/backend/README.md`; el README de `docs/` no los enlaza.
- `docs/planeacion/diagnostico-pruebas-2026-10-13.md` y `docs/REQUERIMIENTOS.md` por contrastar con el código en la planeación.
- `deploy/README.md` (236 líneas) documenta variables SMTP y `TRUSTED_PROXIES` fuera de `VARIABLES.md` (fuente duplicada).

### H-19 — Direcciones IP (cat. 8, FNC, backend)
- `app/modules/auth/services.py:152`: `os.getenv('BASE_URL', 'http://<IP privada>')` (IP privada real en código).
- `scratch/seed_notifications.py:20` (<IP privada de ejemplo>, dato de ejemplo).
- Las `127.0.0.1` de `deploy/*.tmpl`, `next.config.ts:10`, `api.ts:20` y `api/auth.py:33` son bucle local; usar `localhost` desde configuración por política. `deploy/install.sh:7` cita `un rango de red privado` en ayuda.

## Hallazgos de variables adicionales
- H-20: `.env.example` con host de producción real (`auth.vivaro.com`, `AUTHELIA_SSO_URL`, `AUTHELIA_GROUP_ADMIN=InfraestructuraVOIP,Soporte de Red`) y `DB_NAME=admin_test`: confirmar que son valores de ejemplo.
- H-21: `deploy/preflight.sh:228,236` repite defaults (`3306`, `6379`) que ya viven en `.env.example`/código.
- H-22: sin entrada en `HISTORIAL.md` para cambios previos de `.env.example`/`deploy` (9 commits previos sobre `.env.example` y `deploy/`).
- H-23 a H-26: otros menores ya incluidos arriba (H-14, H-18); no generan tarea aparte.

## Comparación con auditoría anterior
Primera auditoría: no hay resueltos ni vigentes previos; los 26 identificadores son nuevos.

## Tareas propuestas (para el tablero; no se escribieron en él)

| # | Título | Carril / plataforma | Prioridad | Hallazgos |
|---|---|---|---|---|
| 1 | Retirar blueprints heredados (redirects/410) y `decorators.py` | FNC / backend | Alta | H-01, D-01, D-02 |
| 2 | Reescribir `VARIABLES.md` desde el código, alinear `.env.example` y `app/config.py` con validación al arrancar | FNC / backend | Alta | H-02, H-16, H-20, H-21, H-22 |
| 3 | Quitar IP y credenciales por defecto (`BASE_URL`, `admin/admin123`, `SECRET_KEY` por defecto) | FNC / backend | Alta (seguridad) | H-07, H-19, H-02 |
| 4 | Limpiar `scratch/` y `utils/` (PSX5K, scripts solapados) y adoptar Alembic con las migraciones 001-004 | FNC / backend | Media | H-07, H-08 |
| 5 | Dividir `admin.py`, `crud.py` y `create_app` en módulos por responsabilidad | FNC / backend | Media | H-05, H-04, H-12, H-13 |
| 6 | Unificar helpers duplicados (usuario creado, purga, LDAP, `_payload/_error`, auditoría) | FNC / backend | Media | H-04, H-12, H-13 |
| 7 | Depurar `components.css`/`global.css` (154 clases sin uso, PSX5K) y mover colores a tokens | DIS / web | Alta | H-03, H-09 |
| 8 | Reparar modo oscuro/temas (clase `dark` en `<html>`, selector de tema o retirar temas) | DIS / web | Alta | H-11 |
| 9 | Componentes comunes: `DataTable`, `Button` variante peligro, filtros, tonos de estado, toast | DIS / web | Media | H-10, H-15, H-17, D-08 a D-11 |
| 10 | Dividir `settings-panel.tsx`, `users-list.tsx`, `platform-admin.tsx` | DIS / web | Media | H-06 |
| 11 | Eliminar estilos inline y colores literales en TSX | DIS / web | Media | H-09, D-12 |
| 12 | Depurar documentación obsoleta (`business_rules.md`, `ARCHITECTURE.md`) y consolidar | FNC / backend (docs) | Baja | H-18 |
| 13 | Crear base de pruebas automatizadas (backend y frontend) | FNC / backend | Media | H-05 |
