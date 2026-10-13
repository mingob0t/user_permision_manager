# Diagnóstico de pruebas — 2026-10-13

Modo diagnóstico (sin escribir pruebas ni tocar código). Rama `fnc/FNC-001-incorporacion-metodo`. Ejecutado por el agente `tester`.

## 1. Resumen

- **No existe suite automatizada.** Confirmado: no hay `tests/`, `conftest.py`, `pytest.ini`, `*.test.*`, `*.spec.*`, ni CI (`.github/`, `.pre-commit-config.yaml` ausentes).
- Pruebas automatizadas: **0**. Scripts manuales: 3 (no son pruebas: requieren BD/servicios reales).
- Las comprobaciones del frontend (`typecheck`, `lint`) **no se pudieron ejecutar de forma válida**: no hay `node_modules`.
- Backend: no hay entorno virtual ni Flask instalado (`python3 -c "import flask"` falló), `pytest` no está disponible. `requirements.txt` no incluye `pytest`.
- Superficie a cubrir: 90 rutas `route(`; 46 en `/api/v1` y 44 heredadas.

## 2. Inventario por plataforma

| Plataforma | Framework / comando | Estado |
|---|---|---|
| Backend (Flask, `app/`) | Ninguno declarado. Propuesto: `pytest` (+ `pytest-flask` opcional) con SQLite en memoria | Sin suite; `pytest` no instalado |
| Web (Next.js 15, `frontend/`) | Scripts `npm run typecheck` (`tsc --noEmit`) y `npm run lint` (`next lint`). Sin runner de pruebas (ni jest/vitest/playwright) | Sin suite; dependencias no instaladas |

### Scripts manuales existentes (no cuentan como suite)

| Archivo | Qué hace | Por qué no es una prueba |
|---|---|---|
| `utils/test_ldap.py` | `create_app()` y `validate_ldap_connection()` contra la config LDAP de la BD | Usa BD y LDAP reales; solo imprime, sin aserciones |
| `utils/test_smtp.py` | Envía correo real con `send_test_email`; pide destino por `input()` | Servicio externo; interactivo; sin aserciones |
| `scratch/test_fail_query.py` | Ejecuta SQL crudo sobre `system_config` con la BD configurada | Depuración puntual; sin aserciones |

Si el runner de pytest los recoge (`test_*.py`), `utils/test_*.py` abriría conexiones reales: deben excluirse o renombrarse (tarea propuesta).

## 3. Comandos ejecutados y salida real

Directorio `frontend/`, sin `node_modules` (verificado con `ls`: "No existe el archivo o el directorio"). No se instalaron dependencias ni se tocó `.env`.

1. `npm run typecheck` (`tsc --noEmit`) — **falla, resultado no válido**. Salida (cola):
   ```
   src/lib/api.ts(20,6): error TS2580: Cannot find name 'process'. Do you need to install type definitions for node?
   src/lib/use-async.ts(3,50): error TS2307: Cannot find module 'react' or its corresponding type declarations.
   tailwind.config.ts(1,29): error TS2307: Cannot find module 'tailwindcss' or its corresponding type declarations.
   (además TS7026 "JSX.IntrinsicElements" y TS7006 en varios archivos, p. ej. src/components/users-list.tsx)
   ```
   Causa: dependencias ausentes. Estos errores NO prueban defectos del código; la línea base de tipos sigue **no verificada**.
2. `npm run lint` (`next lint`) — **no se pudo ejecutar**: `sh: 1: next: not found`.
3. Backend: `python3 -c "import flask"` -> falla (Flask no instalado); `pytest` no encontrado en el PATH. No se ejecutó nada del backend.

Entorno disponible: node v22.23.2, npm, python3 del sistema.

## 4. Mapa de protección de endpoints (leído del código, no ejecutado)

Control de acceso en `app/authz.py` (292 líneas): `is_admin`, `is_area_admin`, `scoped_areas/platforms/users`, `can_access_platform`, `can_manage_area/platform/user`, y decoradores `admin_required`, `any_admin_required`, `area_admin_required`, `platform_access_required`, `platform_manage_required`.

### `/api/v1` (46 rutas) — decorador por ruta

- `@login_required` + `@admin_required`: `admin.py` (settings PUT, smtp GET/PUT/test, templates GET/PUT, auth-config GET/PUT/test, backup GET/POST, directory/search); `crud.py` (POST/DELETE areas, users/inactive, users/purge).
- `@any_admin_required`: `GET /users`, `PUT /users/<id>/areas`, `POST /platforms`, `POST/PUT/DELETE /users...`, `PUT /users/<id>/platforms`.
- `@area_admin_required('area_id')`: `GET /areas/<id>`, `PUT /areas/<id>`, `PUT /areas/<id>/users`.
- `@platform_manage_required`: `PUT/DELETE /platforms/<id>`, `PUT /platforms/<id>/users`.
- Solo `@login_required` (el alcance depende del cuerpo de la función): `/me`, `/areas`, `/platforms`, `POST /platforms/<id>/visit`, `POST /platforms/<id>/favorite`, `/favorites`, `/stats`, `/audit`, `/notifications` (GET, read, DELETE), `PUT /me/preferences`, `GET /settings`.
- Sin `@login_required` (públicos por diseño): `GET /auth/context`, `POST /auth/sso`, `POST /auth/login`.
- Observación (no verificada con prueba): `GET /areas/<id>` está protegido con `area_admin_required`, pero un usuario normal con ese área no puede verla; confirmar que es la intención.

### Blueprints heredados (44 rutas: `/auth`, `/admin`, `/admin/areas`, `/audit`, `/notifications`, `/settings`, `/` )
Sin decoradores. Los revisados (`areas`, `auth`) devuelven 410 o redirigen al frontend. No se leyó cada función de `core`, `audit`, `notifications`, `settings` y `users`: **no verificado** que todas respondan 410 sin ejecutar lógica. Una prueba parametrizada debe confirmarlo (sin sesión y con admin).

Sin prueba hoy: **100%** de los endpoints (401/403/200/400).

## 5. Huecos de cobertura priorizados

### P0 — Crítico (autorización y autenticación)
1. **Protección por rol de cada endpoint `/api/v1`**: matriz sin sesión (401), usuario normal (403), admin de área, admin (200), entradas inválidas (400), formato estándar de respuesta. Prueba parametrizada que recorra `app.url_map` y falle si aparece una ruta nueva sin clasificar.
2. **Reglas de alcance por área (`scoped_*`, `can_*`)**: `scoped_users` (admin ve todos; admin de área solo miembros de sus áreas, **excluyendo superadmins**; sin áreas -> vacío; usuario normal solo a sí mismo; usuario inválido -> vacío), `scoped_areas`, `scoped_platforms`, `can_manage_user` (un admin de área no puede editar ni borrar a un superadmin ni a usuarios de otra área), `can_manage_area`, `can_manage_platform`, `can_access_platform`. Escalada de privilegios en `PUT /users/<id>` (cambio de rol), `set_user_areas`, `set_area_users`, `set_user_platforms` con ids fuera del alcance (`allowed = {...}`).
3. **Autenticación SSO (`/api/v1/auth/sso`, `/context`)**: `AUTHELIA_ENABLED` apagado -> 400; origen fuera de `TRUSTED_PROXIES` -> 403 con auditoría; sin cabecera -> 401; creación de usuario nuevo; mapeo de grupos a rol (`_role_from_groups`); **un admin de área local no pierde su rol** y un usuario degradado por grupos sí; cabeceras `Remote-*` falsificadas desde cliente.
4. **Autenticación LDAP/local (`POST /auth/login`, `authenticate_user_ldap`)**: con `ldap3` simulado (mock): credenciales válidas, inválidas, servidor caído, cuenta inactiva, usuario local, entradas vacías. Hoy solo existe `utils/test_ldap.py` manual contra servicio real.

### P1 — Alto
5. **Administración (`admin.py`)**: GET /settings de usuario normal, backup export/import (archivo inválido, estructura maliciosa, no devolver secretos), `directory/search` y `auth-config/test` con LDAP mock, cifrado de contraseñas en SMTP/LDAP (que el GET no devuelva el secreto).
6. **Notificaciones**: `add_in_app_notification` (por usuario y global), `list/read/delete` solo afectan a las propias, `send_notification_by_slug` con SMTP mock, plantilla inexistente, `resolve_smtp_settings`/`smtp_settings_from_env` (valor válido, inválido y faltante), `NOTIFY_USER_CREATED`, que un fallo SMTP no bloquee el acceso. Permisos de `PUT /smtp`, `/smtp/test`, `/templates`.
7. **Auditoría (`GET /audit`)**: alcance por rol (admin todo; admin de área solo su gente; usuario solo lo suyo), límite máximo de 500 y entrada no numérica.
8. **CRUD**: duplicados (nombre de área/plataforma, email), borrado en cascada, purga de inactivos (`days`), preferencias (`save_preferences`) con valores inválidos.

### P2 — Medio
9. **Rutas heredadas**: respuesta 410/redirect sin lógica ni sesión.
10. **CSRF**: los blueprints de API se excluyen con `csrf.exempt`; verificar el 400 JSON del `CSRFError` en rutas heredadas.
11. **Configuración**: arranque con variables válidas, inválidas y faltantes (`create_app`).
12. **Frontend**: sin runner. Línea base de `typecheck` y `lint` (requiere instalar dependencias), pruebas de componente de `users-list` y del cliente `src/lib/api.ts`; el tema claro/oscuro, estados de carga/vacío/error y la accesibilidad quedan para tareas de diseño/auditoría.
13. **Seguimiento de uso**: `register_visit`, `toggle_favorite` solo sobre plataformas dentro de `scoped_platforms` (otras -> 404).

## 6. No verificado y motivo

- Base de tipos y lint del frontend: falta `node_modules` (prohibido instalar sin permiso).
- Cualquier comportamiento del backend (arranque, endpoints, `authz`): sin Flask/pytest instalados; no se levantó la app. Los mapas de la sección 4 salen de leer el código.
- Rutas heredadas `core`, `audit`, `notifications`, `settings`, `users`: no se leyó cada cuerpo.
- Base de datos objetivo de las pruebas: el proyecto usa MySQL/PostgreSQL (PyMySQL, psycopg2); no se confirmó que los modelos corran en SQLite, lo que condiciona el diseño de *fixtures*.

## 7. Tareas propuestas (como `Propuesta`; no se crearon fichas ni se editó el tablero)

| # | Título | Plataforma | Prioridad |
|---|---|---|---|
| 1 | Crear la suite base de pruebas del backend (pytest, `requirements-dev.txt`, fixtures de app/BD de prueba, cliente con sesión por rol, excluir `utils/test_*.py`) | backend | Alta |
| 2 | Pruebas de protección por rol de todos los endpoints `/api/v1` (matriz 401/403/200/400 y guardia de rutas sin clasificar) | backend | Alta |
| 3 | Pruebas de alcance por área (`scoped_*`, `can_*`) y de escalada de privilegios en CRUD de usuarios, áreas y plataformas | backend | Alta |
| 4 | Pruebas de autenticación SSO (Authelia, proxies de confianza, mapeo de roles) y LDAP/local con mocks | backend | Alta |
| 5 | Pruebas de notificaciones y SMTP (servicios simulados, plantillas, permisos, configuración) | backend | Media |
| 6 | Pruebas de auditoría, backup/importación y configuración de arranque | backend | Media |
| 7 | Pruebas de rutas heredadas (410/redirect) y CSRF | backend | Baja |
| 8 | Establecer línea base web: instalar dependencias, ejecutar `typecheck` y `lint`, y registrar resultado | web | Alta |
| 9 | Añadir runner de pruebas al frontend (vitest + testing-library) con pruebas del cliente `api.ts` y de `users-list` | web | Media |
| 10 | Pipeline de CI que ejecute pytest, typecheck y lint | infra | Media |
