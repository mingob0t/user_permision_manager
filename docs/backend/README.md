# Backend (Flask, API JSON `/api/v1`)

> Línea base documentada en FNC-001 (2026-10-13) a partir del código heredado de NEXUS, rama `fnc/FNC-001-incorporacion-metodo`. Describe lo que el código **hace hoy**, no lo que debería hacer. Las discrepancias y la deuda se listan al final.

## 1. Arquitectura

- **Punto de entrada:** `run.py` llama a `create_app()` (`app/__init__.py`). En dev arranca el servidor de Flask en el puerto 5001 con `debug=True`; en producción lo sirve Gunicorn (`run:app`, 4 workers, ver `deploy/backend.service.tmpl`).
- **Solo API:** Flask se crea con `template_folder=None` y `static_folder=None`. No sirve interfaz ni estáticos; toda la UI vive en `frontend/` (Next.js). Los errores 404/500/CSRF se responden en JSON.
- **Sesión:** Flask-Login con cookie `nexus_session`, sesión permanente de 7 días (`PERMANENT_SESSION_LIFETIME`), `login_user(..., remember=True)`. La cookie la emite Flask y viaja al frontend porque ambos servicios van bajo el mismo dominio (nginx en prod, `rewrites` de Next.js en dev).
- **Sin sesión:** el `unauthorized_handler` devuelve `401` JSON si la petición es de API (`/api/` en la ruta, JSON aceptado o `X-Requested-With`); si no, redirige a `FRONTEND_URL + /login`.
- **CSRF:** Flask-WTF `CSRFProtect` se inicializa, pero **todos** los blueprints están exentos (los de la API v1 porque usan cookie y JSON; los heredados porque solo redirigen o devuelven 410). En la práctica no hay protección CSRF activa (ver deuda).
- **Extensiones:** Flask-SQLAlchemy (`pool_pre_ping`, `pool_recycle=3600`), Flask-Login, Flask-WTF, Flask-Compress.
- **Zona horaria:** al importar `app` se fija `TZ` del proceso con `TZ_APP` (o `TZ`), por defecto `America/Mexico_City`.
- **Redis:** `app/utils/redis_client.py` crea un cliente global (`registry`) y lo conecta al arrancar. Si falla solo imprime el error; **ningún módulo lo usa hoy**.
- **Creación de esquema:** `create_app()` ejecuta `db.create_all()` en cada arranque y, si no existe ningún usuario, crea un administrador inicial con credenciales por defecto conocidas (ver deuda).

### Estructura

```text
app/
├── __init__.py        # create_app(): config, extensiones, blueprints, create_all
├── authz.py           # Autorización centralizada: roles, alcance por área, decoradores
├── decorators.py      # Compatibilidad: reexporta decoradores de authz
├── utils/
│   ├── naming.py      # sanitize_display_name(): limpia nombres visibles (máx. 100)
│   └── redis_client.py# Cliente Redis global (sin uso funcional)
└── modules/
    ├── api/           # API v1 que consume el frontend
    │   ├── routes.py  # Lectura: me, áreas, plataformas, favoritos, usuarios, stats, auditoría
    │   ├── crud.py    # Escritura: áreas, plataformas, usuarios, preferencias, purga
    │   ├── admin.py   # Sistema (superadmin): portal, SMTP, plantillas, LDAP, respaldo, directorio; notificaciones in-app
    │   └── auth.py    # /api/v1/auth: contexto, SSO Authelia, login, logout
    ├── auth/          # Modelos User/AuthConfig y servicios LDAP; rutas heredadas (redirigen/410)
    ├── core/          # Modelos Area/Platform; rutas heredadas
    ├── audit/         # Modelo AuditLog y add_audit_log(); rutas heredadas
    ├── notifications/ # Modelos SMTP/plantillas/in-app y servicios de correo; rutas heredadas
    ├── settings/      # Modelo SystemConfig; rutas heredadas
    ├── users/         # Solo rutas heredadas
    └── areas/         # Solo rutas heredadas
```

## 2. Autorización (`app/authz.py`)

Tres roles (columna `users.role`, comparada en minúsculas):

| Rol | Alcance |
|---|---|
| `administrador` | Superadmin: todas las áreas, plataformas, usuarios y la configuración global. |
| `admin_area` | Administra solo las áreas asignadas en `area_admins`: sus plataformas, sus usuarios y sus permisos. Nunca administra a un superadmin. |
| `usuario` | Solo consulta las plataformas de las áreas asignadas en `user_areas`. |

- **Alcance por fila:** `scoped_areas()`, `scoped_platforms()`, `scoped_users()` devuelven queries ya filtradas según el usuario.
- **Permisos sobre objetos:** `can_access_platform`, `can_manage_area`, `can_manage_platform`, `can_manage_user`.
- **Decoradores:** `admin_required` (solo superadmin), `any_admin_required` (superadmin o admin de área; la vista debe acotar con `scoped_*`), `area_admin_required('area_id')`, `platform_access_required`, `platform_manage_required`. Al denegar responden `403` JSON si la petición es de API.

## 3. Modelo de datos

Las tablas las crea `db.create_all()` desde los modelos. `utils/nexus_structure.sql` es un volcado parcial (no incluye `areas`, `platforms` ni las tablas de relación).

| Tabla | Modelo | Campos clave |
|---|---|---|
| `users` | `auth.models.User` | `id`, `email` (único; también guarda identificadores sin `@`, p. ej. el admin inicial), `nombre`, `password_hash` (nulo en LDAP), `role`, `auth_source` (`local` / `ldap` / `sso`), `is_active`, `created_at`, `last_login_at`, preferencias `pref_notifications`, `pref_email_notifications`, `pref_refresh_interval` (15–3600 s), `pref_tour_enabled` |
| `areas` | `core.models.Area` | `id`, `name` (único), `description`, `icon`, `color` (hex), `status` (`Activo` / otro) |
| `platforms` | `core.models.Platform` | `id`, `name`, `description` (obligatoria), `area_id` (FK obligatoria), `direct_link`, `icon`, `logo_url`, `bg_color`, `text_color`, `status`, `visits`, `created_at` |
| `user_areas` | tabla de relación | `user_id`, `area_id`: pertenencia de un usuario a un área |
| `area_admins` | tabla de relación | `user_id`, `area_id`: áreas que administra un `admin_area` |
| `user_platforms` | tabla de relación | `user_id`, `platform_id`: acceso explícito a plataforma (se edita, pero `scoped_platforms` **no** lo usa para filtrar) |
| `user_favorites` | tabla de relación | `user_id`, `platform_id` |
| `audit_logs` | `audit.models.AuditLog` | `timestamp`, `user` (correo, texto), `action`, `module`, `target`, `detail`, `ip_address`, `status` (`success`/`error`/`warning`/`info`) |
| `auth_config` | `auth.models.AuthConfig` | `ldap_host`, `ldap_port`, `ldap_ssl`, `ldap_base_dn`, `ldap_user` (bind DN), `ldap_pass` (en claro), `ldap_user_attr` (por defecto `sAMAccountName`), `ldap_group_admin`, `ldap_group_user`, `ldap_role_mappings` (JSON `[{group, role}]`) |
| `smtp_config` | `notifications.models.SMTPConfig` | `server`, `port`, `encryption` (`starttls`/`ssl`/`none`), `auth_enabled`, `username`, `password` (en claro), `sender_name` |
| `notification_templates` | `NotificationTemplate` | `slug` (único), `name`, `subject`, `body`, `is_html` |
| `in_app_notifications` | `InAppNotification` | `user_id` (nulo = global), `type`, `title`, `message`, `is_read`, `created_at` |
| `system_config` | `settings.models.SystemConfig` | `portal_name`, `portal_identity_type` (`icon`/`image`), `portal_icon` (SVG o data URI de imagen, máx. 512 KB), `bg_color`, `text_color` |

## 4. Endpoints

Todos devuelven JSON. Errores con forma `{"status": "error", "message": "..."}`. "Sesión" = `@login_required`.

### 4.1 Autenticación — `app/modules/api/auth.py` (`/api/v1/auth`)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /context` | Pública | Indica si el SSO está activo, la identidad SSO (solo si la petición viene de `TRUSTED_PROXIES`), si ya hay sesión y si LDAP está disponible (siempre `true`). |
| `POST /sso` | Pública; exige `AUTHELIA_ENABLED=true` y origen en `TRUSTED_PROXIES` | Crea o actualiza el usuario a partir de las cabeceras de Authelia, deduce el rol por grupos (`AUTHELIA_GROUP_ADMIN`) salvo que sea `admin_area`, inicia sesión y audita. Si es nuevo, envía la plantilla `usuario_creado`. |
| `POST /login` | Pública | `method=directory` → LDAP (`authenticate_user_ldap`); `method=local` → contraseña local. Audita éxitos y fallos. Mismo mensaje si la cuenta no existe. |
| `POST /logout` | Sesión | Cierra la sesión y audita; con SSO devuelve la URL de cierre de Authelia (`AUTHELIA_SLO_URL?rd=BASE_URL/login`). |

### 4.2 Lectura — `app/modules/api/routes.py` (`/api/v1`)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /me` | Sesión | Identidad, áreas, áreas administradas, permisos (`is_admin`, `is_area_admin`, `can_manage_areas`, `can_manage_system`) y preferencias. |
| `GET /areas` | Sesión (filtrado por `scoped_areas`) | Áreas visibles con número de plataformas y usuarios. |
| `GET /areas/<id>` | `area_admin_required` | Detalle de un área administrable. |
| `GET /platforms?area_id=&q=` | Sesión (`scoped_platforms`) | Catálogo con marca de favorito. |
| `POST /platforms/<id>/visit` | Sesión (en alcance) | Suma una visita. |
| `POST /platforms/<id>/favorite` | Sesión (en alcance) | Alterna favorito. |
| `GET /favorites` | Sesión | Favoritos aún visibles. |
| `GET /users` | `any_admin_required` (`scoped_users`) | Usuarios administrables. |
| `PUT /users/<id>/areas` | `any_admin_required` + `can_manage_user` | Reasigna áreas dentro del alcance; conserva las que el solicitante no administra. |
| `GET /stats` | Sesión (alcance) | Contadores, top 5 de visitas, plataformas por área; `users` solo para administradores. |
| `GET /audit?limit=` | Sesión (alcance) | Superadmin: todo; admin de área: eventos de sus usuarios; usuario: los propios. Máximo 500. |

### 4.3 Escritura — `app/modules/api/crud.py` (`/api/v1`)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `POST /areas` | `admin_required` | Crea área. |
| `PUT /areas/<id>` | `area_admin_required` | Edita área. |
| `DELETE /areas/<id>` | `admin_required` | Borra área; `409` si tiene plataformas. |
| `PUT /areas/<id>/users` | `area_admin_required` | Define los miembros del área dentro del alcance. |
| `POST /platforms` | `any_admin_required` (área en alcance) | Crea plataforma. |
| `PUT /platforms/<id>` | `platform_manage_required` | Edita plataforma. |
| `DELETE /platforms/<id>` | `platform_manage_required` | Borra plataforma. |
| `PUT /platforms/<id>/users` | `platform_manage_required` | Define `user_platforms`. |
| `POST /users` | `any_admin_required` | Alta de usuario. Roles asignables: `usuario`, `admin_area`; `administrador` solo por superadmin. `admin` es identificador reservado. Si no llega contraseña, se asigna una por defecto (ver deuda). Un `admin_area` nuevo administra las mismas áreas a las que pertenece. |
| `PUT /users/<id>` | `any_admin_required` + `can_manage_user` | Edita usuario. |
| `DELETE /users/<id>` | `any_admin_required` + `can_manage_user` | Borra usuario; no permite borrarse a sí mismo ni la cuenta maestra `admin`. |
| `PUT /users/<id>/platforms` | `any_admin_required` + `can_manage_user` | Define `user_platforms` con plataformas en alcance. |
| `PUT /me/preferences` | Sesión | Guarda preferencias propias. |
| `GET /users/inactive?days=` | `admin_required` | Usuarios sin acceso en N días (mínimo `PURGE_MIN_DAYS` = 7), excluye superadmins. |
| `POST /users/purge` | `admin_required` | Elimina esos usuarios y audita. |

### 4.4 Sistema y notificaciones — `app/modules/api/admin.py` (`/api/v1`)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /settings` | Sesión | Identidad del portal (la lee cualquiera). |
| `PUT /settings` | `admin_required` | Guarda nombre, colores y logo (data URI validado: tipo, base64, 512 KB). |
| `GET /smtp` | `admin_required` | Configuración SMTP efectiva, su origen (`env`/`db`/`none`), si está forzada por entorno y si es editable. Nunca devuelve la contraseña. |
| `PUT /smtp` | `admin_required` | Guarda SMTP en BD; `409` si `SMTP_FORCE_ENV=true`. Contraseña vacía no borra la guardada. |
| `POST /smtp/test` | `admin_required` | Envía correo de prueba. |
| `GET /templates` | `admin_required` | Lista plantillas de correo. |
| `PUT /templates/<slug>` | `admin_required` | Crea o edita plantilla. |
| `GET /notifications` | Sesión | Últimas 50 notificaciones in-app propias y globales (vacío si el usuario las desactivó). |
| `POST /notifications/read` | Sesión | Marca como leídas (todas o `ids`). Afecta también a las globales para todos (ver deuda). |
| `DELETE /notifications` | Sesión | Borra las propias. |
| `GET /auth-config` | `admin_required` | Configuración LDAP sin contraseña. |
| `PUT /auth-config` | `admin_required` | Guarda configuración LDAP y mapeos de roles. |
| `POST /auth-config/test` | `admin_required` | Prueba de bind LDAP. |
| `GET /backup` | `admin_required` | Descarga ZIP `nexus_config.json` con portal, LDAP, SMTP (sin contraseñas), plantillas y usuarios locales con su hash. |
| `POST /backup` | `admin_required` | Restaura desde ese ZIP; solo agrega usuarios que no existan. |
| `GET /directory/search?q=` | `admin_required` | Busca en el directorio (mín. 2 caracteres, máx. 50 resultados, filtro escapado RFC 4515) y marca quién ya existe. |

### 4.5 Rutas heredadas

Los blueprints `auth` (`/auth`), `core` (`/`), `audit` (`/audit`), `settings` (`/settings`), `notifications`, `users_module` (`/admin`) y `areas_module` (`/admin/areas`) ya no procesan datos: las rutas de pantalla redirigen a `FRONTEND_URL + <ruta>` y las de datos responden `410` con el endpoint que las reemplaza.

## 5. Integraciones

### LDAP / OpenLDAP (solo lectura)
- Configuración en la tabla `auth_config`, editable desde Ajustes → Directorio. No hay variables de entorno para LDAP (salvo `DEBUG_LDAP`).
- `authenticate_user_ldap`: bind de servicio → búsqueda por `ldap_user_attr` → bind con el DN del usuario para validar la contraseña → crea/actualiza el usuario local (`auth_source=ldap`) y le asigna rol por `ldap_role_mappings` o, en su defecto, por `ldap_group_admin`.
- El código **solo lee** del directorio (bind y search); nunca escribe en él. Sin embargo, si el usuario no existe en el directorio, **borra la cuenta local** ("protocolo de purga").
- TLS con `CERT_NONE`: no valida el certificado del servidor.
- Los atributos consultados (`sAMAccountName`, `memberOf`, `displayName`) son de Active Directory; con OpenLDAP hay que ajustar `ldap_user_attr` (p. ej. `uid`) y verificar `memberOf` (overlay).

### Authelia (SSO por cabeceras)
- Nginx consulta Authelia (`auth_request`, comentado en la plantilla) y reinyecta `Remote-Email`, `Remote-Name`, `Remote-Groups`; antes borra esas cabeceras si vienen del cliente.
- El backend solo las acepta si `request.remote_addr` está en `TRUSTED_PROXIES` (por defecto loopback) y `AUTHELIA_ENABLED=true`.
- El rol se deduce de los grupos en `AUTHELIA_GROUP_ADMIN`; un `admin_area` local conserva su rol.

### SMTP y plantillas
- `resolve_smtp_settings()`: con `SMTP_FORCE_ENV=true` manda el entorno (y si falta `SMTP_SERVER` no envía); si no, manda la BD y el entorno es respaldo.
- `send_notification_by_slug(slug, correo, contexto)`: sustituye `{clave}` en asunto y cuerpo (no es Jinja2), envía HTML o texto según `is_html`. `ENABLE_NOTIFICATIONS=false` corta todo envío. Recarga `.env` en cada envío (`load_dotenv(override=True)`).
- Plantilla usada por el código: `usuario_creado` (alta por LDAP o SSO, si `NOTIFY_USER_CREATED` no es `false`). Variables: `nombre`, `usuario`, `base_url`, `url`.
- `add_in_app_notification()` existe en servicios.

### Auditoría
- `add_audit_log(action, status, detail, user_override, module, target)` escribe en `audit_logs` con el correo del usuario (o `SYSTEM`) y la IP de `request.remote_addr` (`INTERNAL` fuera de petición). Si falla, solo imprime y hace rollback.
- Se audita: accesos (local, directorio, SSO, fallidos, SSO rechazado), cierre de sesión, CRUD de áreas/plataformas/usuarios, configuración, SMTP, LDAP, respaldos, purgas y altas/bajas automáticas por LDAP.

## 6. Cómo arrancar en dev

```bash
cp .env.example .env          # rellenar credenciales (nunca commitear .env)
python3.11 -m venv venv       # o 3.12
venv/bin/pip install -r requirements.txt
venv/bin/python run.py        # API en el puerto 5001
```

- Con `DB_ENGINE=mysql` usa MySQL/MariaDB vía PyMySQL; con cualquier otro valor (o sin definir) usa **SQLite** en `nexus.db`.
- Redis es opcional: si no responde, la app arranca igual.
- El frontend se arranca aparte (ver `docs/frontend/README.md`); su `rewrite` reenvía `/api/*` y `/auth/*` a este backend.
- Utilidades de mantenimiento en `utils/` (usan `create_app()`): `check_db.py`, `db_check.py`, `db_inspector.py`, `db_migrate.py`, `reset_admin.py`, `emergency_reset.py`, `seed_users.py`, `test_ldap.py`, `test_smtp.py`, `nexus_health.py`, `toggle_authelia.py` (edita el `.env` y la config de nginx).
- **Pruebas** (FNC-019): suite pytest en `tests/`, sin `.env` ni servicios externos.
  ```bash
  venv/bin/pip install -r requirements.txt -r requirements-dev.txt
  venv/bin/pytest                    # solo recoge tests/ (pytest.ini)
  venv/bin/pytest --cov=app          # con cobertura
  ```
  - `tests/conftest.py`: no carga `.env`, usa valores ficticios, BD SQLite temporal por prueba, Redis sin conectar, SMTP y LDAP bloqueados.
  - Fixtures: `app`, `client`, `crear_area`, `crear_plataforma`, `crear_usuario`, `cliente_como(usuario)`, `cliente_de_rol(rol)`, `cliente_admin`, `cliente_admin_area`, `cliente_usuario`.
  - `tests/fabricas.py`: fábricas de áreas, plataformas y usuarios por rol.
  - `tests/matriz_proteccion.py` (FNC-020): código esperado por rol de cada ruta `/api/v1`. **Todo endpoint nuevo agrega aquí su caso**; si no, falla `tests/test_guardia_rutas.py`.
  - `tests/test_proteccion_por_rol.py`: matriz ruta × rol (401/403/2xx), entradas inválidas (400) y RF-04 (casos `xfail` hasta FNC-007).
  - `utils/test_*.py` y `scratch/test_*.py` son scripts manuales con conexiones reales: pytest no los recoge.
  - `create_app(config_overrides=None)`: el parámetro opcional solo lo usan las pruebas; sin él no cambia nada.

## 7. Migraciones

`create_all()` crea tablas nuevas pero no altera las existentes. Los cambios de esquema se aplican a mano, en orden, desde `utils/migrations/` (el instalador no las ejecuta):

| Archivo | Tipo | Qué hace |
|---|---|---|
| `001_user_prefs.sql` | SQL (MySQL) | Agrega las columnas `pref_*` a `users`. |
| `002_drop_drive.sql` | SQL (MySQL) | Elimina `storage_stats`, `drive_activity` y columnas de archivos de `platforms`. Irreversible sin respaldo. |
| `003_logo_to_db.py` | Python | Pasa el logo del portal de archivo a data URI en `system_config`. Idempotente. |
| `004_drop_access_requests.sql` | SQL (MySQL) | Elimina la tabla huérfana `access_requests`. |

No hay registro de qué migraciones se aplicaron (no hay Alembic ni tabla de versiones).

## 8. Deuda conocida

| # | Deuda | Dónde |
|---|---|---|
| 1 | Usuario administrador inicial creado en cada BD vacía con credenciales por defecto conocidas e impresas en consola. | `app/__init__.py` |
| 2 | `SECRET_KEY` tiene valor por defecto en código si falta la variable. | `app/__init__.py` |
| 3 | Contraseña por defecto fija cuando el alta de usuario no la incluye. | `api/crud.py` `create_user` |
| 4 | **Dirección IP literal** como valor por defecto de `BASE_URL` en el correo de bienvenida LDAP (incumple el lineamiento "sin IPs"). | `auth/services.py` |
| 5 | CSRF exento en todos los blueprints; la API depende solo de la cookie de sesión (SameSite por defecto del navegador). | `app/__init__.py` |
| 6 | Contraseñas de LDAP y SMTP guardadas en claro en BD. | `auth_config`, `smtp_config` |
| 7 | LDAP con TLS sin validar certificado (`CERT_NONE`). | `auth/services.py`, `api/admin.py` |
| 8 | Borrado automático de la cuenta local si no aparece en el directorio. | `auth/services.py` |
| 9 | `run.py` usa `debug=True` y escucha en todas las interfaces; `PORT_APP` no se lee. | `run.py` |
| 10 | `DB_ENGINE` distinto de `mysql` cae a SQLite (no hay rama PostgreSQL aunque `psycopg2-binary` está en dependencias). | `app/__init__.py` |
| 11 | Dependencias sin versión fijada (`cryptography`, `ldap3`, `Flask-Mail`, `pandas`, `redis`, `gunicorn`, etc.); algunas sin uso aparente (`Flask-Mail`, `pexpect`, `openpyxl`, `xlrd`, `pandas`, `psycopg2-binary`). | `requirements.txt` |
| 12 | Redis conectado pero sin uso. | `app/utils/redis_client.py` |
| 13 | `user_platforms` se edita pero no restringe la visibilidad. | `authz.scoped_platforms` |
| 14 | `POST /notifications/read` marca como leídas las notificaciones globales para todos los usuarios. | `api/admin.py` |
| 15 | Sin control de migraciones aplicadas. Pruebas: suite base (FNC-019) y protección por rol de `/api/v1` (FNC-020); alcance, autenticación y servicios siguen en FNC-021 a FNC-023. | — |
| 16 | `purge_inactive_users` de `auth/services.py` devuelve un mensaje de error de LDAP no relacionado; la API usa su propia implementación en `crud.py` (duplicado). | `auth/services.py`, `api/crud.py` |
| 17 | `utils/seed_users.py` usa roles `admin`/`user` que el código ya no reconoce. | `utils/seed_users.py` |
| 18 | Mensajes de error que devuelven el texto de la excepción al cliente (LDAP, SMTP, respaldo). | `api/admin.py` |
