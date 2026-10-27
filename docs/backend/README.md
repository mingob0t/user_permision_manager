# Backend (Flask, API JSON `/api/v1`)

> Línea base documentada en FNC-001 (2026-10-13) a partir del código heredado de NEXUS, rama `fnc/FNC-001-incorporacion-metodo`. Describe lo que el código **hace hoy**, no lo que debería hacer. Las discrepancias y la deuda se listan al final.

## 1. Arquitectura

- **Punto de entrada:** `run.py` llama a `create_app()` (`app/__init__.py`). En dev arranca el servidor de Flask en el puerto 5001 con `debug=True`; en producción lo sirve Gunicorn (`run:app`, 4 workers, ver `deploy/backend.service.tmpl`).
- **Solo API:** Flask se crea con `template_folder=None` y `static_folder=None`. No sirve interfaz ni estáticos; toda la UI vive en `frontend/` (Next.js). Los errores 404/500/CSRF se responden en JSON.
- **Sesión:** Flask-Login con cookie `nexus_session`, sesión permanente de 7 días (`PERMANENT_SESSION_LIFETIME`), `login_user(..., remember=True)`. La cookie la emite Flask y viaja al frontend porque ambos servicios van bajo el mismo dominio (nginx en prod, `rewrites` de Next.js en dev).
- **Sin sesión:** el `unauthorized_handler` devuelve siempre `401` JSON (el backend ya no redirige; `FRONTEND_URL` se retiró en FNC-027).
- **CSRF:** Flask-WTF `CSRFProtect` se inicializa, pero **todos** los blueprints están exentos (los de la API v1 porque usan cookie y JSON). Los blueprints heredados se retiraron en FNC-027. En la práctica no hay protección CSRF activa (ver deuda).
- **Extensiones:** Flask-SQLAlchemy (`pool_pre_ping`, `pool_recycle=3600`), Flask-Login, Flask-WTF, Flask-Compress.
- **Zona horaria:** al importar `app` se fija `TZ` del proceso con `TZ_APP` (o `TZ`), por defecto `America/Mexico_City`.
- **Redis:** `app/utils/redis_client.py` crea un cliente global (`registry`) y lo conecta al arrancar. Si falla solo imprime el error; **ningún módulo lo usa hoy**.
- **Creación de esquema:** el esquema se versiona con Alembic (§7). `create_app()` sigue ejecutando `db.create_all()` en cada arranque y, si no existe ningún usuario, crea un administrador inicial con credenciales por defecto conocidas (ver deuda).
- **URI de la BD:** `construir_uri_bd()` (`app/utils/uri_bd.py`) la arma desde `DB_*`; la usan `create_app()` y `migrations/env.py`.

### Estructura

```text
app/
├── __init__.py        # create_app(): orquesta funciones pequeñas (_configurar, _validar_configuracion, _iniciar_extensiones, _registrar_blueprints, _registrar_cli_y_manejadores, _crear_tablas, _registrar_manejadores_de_error; FNC-029)
├── authz.py           # Autorización centralizada: roles, alcance por área, decoradores
├── utils/
│   ├── naming.py      # sanitize_display_name(): limpia nombres visibles (máx. 100)
│   ├── uri_bd.py      # construir_uri_bd(): URI de la BD desde DB_* (app y Alembic)
│   └── redis_client.py# Cliente Redis global (sin uso funcional)
└── modules/
    ├── api/           # API v1 que consume el frontend
    │   ├── routes.py  # Lectura: me, áreas, plataformas, favoritos, usuarios, stats
    │   ├── auth.py    # /api/v1/auth: contexto, SSO Authelia, login, logout
    │   └── helpers.py # (`crud.py` y `admin.py` se dividieron en los módulos de dominio, FNC-029) error_response(), validation_error(), json_object(), json_payload(), leer_cuerpo() (`permitidos=None`: solo exige objeto), campos_no_permitidos()/campos_prohibidos(), is_id_list() y errores del contrato (FNC-044, FNC-030, FNC-082)
    ├── auth/          # Modelos User/AuthConfig (obsoleto) y servicios de login
    ├── directory/     # OpenLDAP: configuración LDAP_*, cliente, escritura, api.py (/auth-config, /directory/search; FNC-043); único que importa ldap3
    ├── core/          # Modelos Area/Platform
    ├── access_requests/ # Solicitudes: models, tipos, catalogo (P1 y estado del actor), services (crear), serializacion, api.py (catalog, POST, mine) (FNC-056); approvals (bandeja, aprobar, rechazar) y rutas inbox/approve/reject (FNC-057); consultas (`mias`, FNC-066)
    ├── access/        # Accesos otorgados: models, tipos, rules, services (otorgar/revocar), manejadores (resultado del ejecutor), consultas (FNC-054); api.py y serializacion.py (FNC-058); inventario e inventario_api (FNC-059)
    ├── provisioning/  # Ejecutor de aprovisionamiento: models, queue (encolar), ejecucion, worker, providers, ldap_provider, cli (FNC-049); api, consultas, serializacion y reintento (FNC-062)
    ├── secretos/      # Vaultwarden (FNC-068): configuracion (VAULTWARDEN_*), cifrado (Bitwarden del lado del cliente), vaultwarden (cliente de solo lectura)
    ├── connectors/    # Conectores (FNC-050): base (interfaz), registry (tipos), models (platform_connectors), validacion, credenciales (fuente y caché), provider (proveedor `conector`), consultas, noop (solo dev/pruebas), configuracion (CONNECTOR_*); api y prueba (FNC-061)
    ├── platforms/     # api.py (escritura de plataformas), validacion.py, grupos.py (DN), tipos.py, estado.py (puntos de extensión; `tiene_conector` desde FNC-050) (FNC-046)
    ├── audit/         # Modelo AuditLog y add_audit_log(); api.py (consulta e historiales), queries.py (alcance y filtros), parametros.py (FNC-060)
    ├── notifications/ # Modelos SMTP/plantillas/in-app, servicios de correo y avisos del gestor (access_notifications.py); api.py (SMTP, plantillas, notificaciones in-app; FNC-029)
    ├── settings/      # Modelo SystemConfig; api.py (`/settings`), logo.py (validación del logo), respaldo_api.py (`/backup`) (FNC-029)
    ├── users/         # api.py (alta, edición y baja de cuentas, `/users/<id>/platforms` retirado, managed-areas, alta en directorio), preferencias_api.py (`/me/preferences`), higiene_api.py (`/users/inactive`, `/users/purge`) (FNC-029), directory_accounts.py (FNC-064), roles.py, areas_administradas.py, serializacion.py (FNC-044), correos.py (FNC-043); routes.py heredadas
    ├── areas/         # api.py (alta, edición y baja; `PUT /areas/<id>/users`, FNC-029), validacion.py, baja.py (FNC-045)
    └── home/          # Inicio: services.py (resumen por rol) y api.py (`/home/summary`) (FNC-066)
alembic.ini            # Configuración de Alembic (sin URL ni secretos)
migrations/
├── env.py             # URL de construir_uri_bd(); importa app/modules/*/models.py
├── script.py.mako     # Plantilla de nuevas migraciones
└── versions/          # 0001_linea_base_esquema_actual.py y las siguientes
```

## 2. Autorización (`app/authz.py`)

Tres roles (columna `users.role`, comparada en minúsculas):

| Rol | Alcance |
|---|---|
| `administrador` | Superadmin: todas las áreas, plataformas, usuarios y la configuración global. |
| `admin_area` | Administra solo las áreas asignadas en `area_admins`: sus plataformas y las cuentas `usuario` de sus áreas. Nunca gestiona a otro admin ni al superadmin (FNC-044). |
| `usuario` | Solo consulta las plataformas de las áreas asignadas en `user_areas`. |

- **Alcance por fila:** `scoped_areas()`, `scoped_platforms()`, `scoped_users()` devuelven queries ya filtradas según el usuario.
- **Mis plataformas (`scoped_platforms`, FNC-063, P4):** superadmin todas; admin de área las de sus áreas administradas más las de sus accesos `activo`; usuario solo las de sus accesos `activo`. Un acceso cuenta solo si la plataforma es de un área a la que la cuenta pertenece (`user_areas`). `can_access_platform` usa la misma query. No incluye el catálogo para solicitar (`access_requests/catalogo.py`). Ni `user_areas` sola ni `user_platforms` (obsoleta) dan visibilidad: quien veía una plataforma solo por `user_platforms` ya no la ve desde FNC-063 y debe solicitar acceso. Para un admin de área, `scoped_users()` solo devuelve cuentas `usuario` de sus áreas (FNC-044). La auditoría usa `audit.queries.visibles()`: admin por `area_id IN managed_area_ids()` (FNC-060).
- **Permisos sobre objetos:** `can_access_platform`, `can_manage_area`, `can_manage_platform`, `can_manage_user` (admin de área: solo rol `usuario` de sus áreas).
- **Roles asignables** (`users/roles.py`, FNC-044): superadmin `usuario` o `admin_area`; admin de área solo `usuario`; `administrador` nunca por la API.
- **Decoradores:** `admin_required` (solo superadmin), `any_admin_required` (superadmin o admin de área; la vista debe acotar con `scoped_*`), `area_admin_required('area_id')`, `platform_access_required`, `platform_manage_required`. Al denegar responden `403` JSON si la petición es de API.

## 3. Modelo de datos

Las tablas las crean las migraciones de Alembic (§7); `db.create_all()` sigue activo al arrancar. El volcado parcial `utils/nexus_structure.sql` se retiró en FNC-028.

| Tabla | Modelo | Campos clave |
|---|---|---|
| `users` | `auth.models.User` | `id`, `email` (único; también guarda identificadores sin `@`, p. ej. el admin inicial), `nombre`, `password_hash` (nulo en LDAP), `role`, `auth_source` (`local` / `ldap` / `sso`), `is_active`, `created_at`, `last_login_at`, preferencias `pref_notifications`, `pref_email_notifications`, `pref_refresh_interval` (15–3600 s), `pref_tour_enabled` |
| `areas` | `core.models.Area` | `id`, `name` (único), `description`, `icon`, `color` (hex), `status` (`Activo` / otro) |
| `platforms` | `core.models.Platform` | `id`, `name`, `description` (obligatoria), `area_id` (FK obligatoria), `direct_link`, `icon`, `logo_url`, `bg_color`, `text_color`, `status`, `visits`, `created_at`; FNC-046 (0005): `integration_type` (`ldap`/`conector`), `ldap_group_user_dn`, `ldap_group_admin_dn` (512), `groups_status` (`ok`/`no_existe`/`sin_verificar`) |
| `user_areas` | tabla de relación | `user_id`, `area_id`: pertenencia de un usuario a un área |
| `area_admins` | tabla de relación | `user_id`, `area_id`: áreas que administra un `admin_area` |
| `user_platforms` | tabla de relación | **Obsoleta** (FNC-065, P4): `user_id`, `platform_id`; nada la lee ni la escribe y sus filas se descartan (no se migran a accesos). No se borra aquí: su borrado va en FNC-107 |
| `platform_access_grants` | `access.models.PlatformAccessGrant` | FNC-054 (0007): `user_id`, `platform_id` (FK sin `ON DELETE`), `level` (`usuario`/`admin`), `origin` (`solicitud`/`admin_de_area`), `request_id` (sin FK; la tabla de solicitudes existe desde FNC-056, FK propuesta en FNC-088), `granted_by`/`revoked_by` (FK `SET NULL`; nulo = sistema), `granted_at`, `status`, `revoked_at`, `revoke_reason` (500), `last_job_id`, `updated_at`; únicos `slot_vigente` (usuario, plataforma, nivel) y `slot_ocupante` (usuario, plataforma: P5). Nunca se borra |
| `platform_access_requests` | `access_requests.models.PlatformAccessRequest` | FNC-056 (0008): `user_id`, `platform_id` (FK sin `ON DELETE`), `level`, `justification` (opcional, 500), `status` (`pendiente`/`aprobada`/`rechazada`), `current_level` (nivel ocupado al solicitar), `created_at`, `decided_by` (FK `SET NULL`), `decided_at`, `rejection_reason` (500); único `slot_pendiente` (usuario, plataforma): una pendiente por plataforma también ante carreras |
| `platform_connectors` | `connectors.models.PlatformConnector` | FNC-050 (0009): `platform_id` (FK única, `ON DELETE CASCADE`), `type` (20), `host` (253, nombre de la lista blanca), `port`, `params` (JSON sin secretos), `credential_ref` (200, referencia del gestor; nunca el valor), `credential_status` (`ok`/`no_encontrada`/`sin_verificar`; cambiar `host` o `credential_ref` la deja `sin_verificar`), `active`, `created_at`, `updated_at` |
| `user_favorites` | tabla de relación | `user_id`, `platform_id` |
| `audit_logs` | `audit.models.AuditLog` | `timestamp`, `user` (correo o `sistema`, 255), `action` (150), `module`, `target` (255), `detail`, `ip_address`, `status` (`success`/`error`/`warning`/`info`); FNC-047: `actor_id`, `target_user_id`, `area_id`, `platform_id` (FK `SET NULL`), `before_state`/`after_state` (JSON), `request_id`, `grant_id`; índices por fecha, actor, usuario afectado, área y plataforma. Inmutable desde el ORM |
| `auth_config` | `auth.models.AuthConfig` | **Obsoleta** (FNC-043): nada la lee; solo viaja en el respaldo. `ldap_pass` vacía (migración 0004) y el modelo rechaza escribirla. Resto: `ldap_host`, `ldap_port`, `ldap_ssl`, `ldap_base_dn`, `ldap_user`, `ldap_user_attr`, `ldap_group_admin`, `ldap_group_user`, `ldap_role_mappings` |
| `smtp_config` | `notifications.models.SMTPConfig` | `server`, `port`, `encryption` (`starttls`/`ssl`/`none`), `auth_enabled`, `username`, `password` (en claro), `sender_name` |
| `notification_templates` | `NotificationTemplate` | `slug` (único), `name`, `subject`, `body`, `is_html` |
| `in_app_notifications` | `InAppNotification` | `user_id` (nulo = global), `type`, `title`, `message`, `is_read` (solo propias), `created_at` |
| `notification_reads` | `NotificationRead` | FNC-031 (0010): `notification_id` y `user_id` (`ON DELETE CASCADE`, par único), `read_at`; lectura por usuario de las globales |
| `system_config` | `settings.models.SystemConfig` | `portal_name`, `portal_identity_type` (`icon`/`image`), `portal_icon` (SVG o data URI de imagen, máx. 512 KB), `bg_color`, `text_color` |

## 4. Endpoints

Todos devuelven JSON. Errores con forma `{"status": "error", "message": "..."}`. "Sesión" = `@login_required`.

### 4.1 Autenticación — `app/modules/api/auth.py` (`/api/v1/auth`)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /context` | Pública | Indica si el SSO está activo, la identidad SSO (solo si la petición viene de `TRUSTED_PROXIES`), si ya hay sesión y si LDAP está disponible (siempre `true`). |
| `POST /sso` | Pública; exige `AUTHELIA_ENABLED=true` y origen en `TRUSTED_PROXIES` | Crea o actualiza el usuario a partir de las cabeceras de Authelia (nuevo: rol `usuario`; existente: conserva su rol; `Remote-Groups` no se usa, FNC-042), inicia sesión y audita. Si es nuevo, envía la plantilla `usuario_creado`. |
| `POST /login` | Pública | `method=directory` → LDAP (`authenticate_user_ldap`); `method=local` → contraseña local, solo para la cuenta de emergencia (superadmin con `auth_source=local`); otra cuenta → 401 (FNC-077, `auth/acceso_local.py`). En desarrollo, `APP_ENV=development` + `LOGIN_LOCAL_TODAS_LAS_CUENTAS=true` admite cualquier cuenta local. Audita éxitos y fallos (el motivo solo en la auditoría). Todo fallo, incluida la cuenta desactivada, responde 401 `Credenciales incorrectas.` (FNC-042). |
| `POST /logout` | Sesión | Cierra la sesión y audita; con SSO devuelve la URL de cierre de Authelia (`AUTHELIA_SLO_URL?rd=BASE_URL/login`). |

### 4.2 Lectura — `app/modules/api/routes.py` (`/api/v1`)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /me` | Sesión | Identidad, áreas, áreas administradas, permisos (`is_admin`, `is_area_admin`, `can_manage_areas`, `can_manage_system`) y preferencias. |
| `GET /areas` | Sesión (filtrado por `scoped_areas`) | Áreas visibles con número de plataformas y usuarios. |
| `GET /areas/<id>` | `area_admin_required` | Detalle de un área administrable. |
| `GET /platforms?area_id=&q=` | Sesión (`scoped_platforms`) | Mis plataformas (accesos `activo`, FNC-063) con marca de favorito. |
| `POST /platforms/<id>/visit` | Sesión (en alcance) | Suma una visita. |
| `POST /platforms/<id>/favorite` | Sesión (en alcance) | Alterna favorito. |
| `GET /favorites` | Sesión | Favoritos aún visibles. |
| `GET /users` | `any_admin_required` (`scoped_users`) | Usuarios administrables. |
| `PUT /users/<id>/areas` | `any_admin_required` + `can_manage_user` (fuera de alcance → `404`) | Reasigna áreas dentro del alcance; conserva las que el solicitante no administra. Cuerpo no objeto o `area_ids` no lista de enteros → `400 cuerpo_invalido`. |
| `GET /stats` | Sesión (alcance) | Contadores, top 5 de visitas, plataformas por área; `users` solo para administradores. |

### 4.2.1 Auditoría — `app/modules/audit/api.py` (`/api/v1`, FNC-060)

| Endpoint | Protección | Comportamiento |
|---|---|---|
| `GET /audit` | Sesión (alcance) | Superadmin: todo; admin de área: eventos con `area_id` de sus áreas (sin área: solo superadmin; SEG-16); usuario: los propios (actor o afectado, solo por id; los anteriores a FNC-047 solo el superadmin, SEG-060-01). Sin `page`: arreglo (`limit` 100, máx. 500); con `page`: `{items, page, per_page, total}`. |
| `GET /audit/users/<id>` | Sesión; superadmin cualquiera, admin él mismo o `can_manage_user`, usuario solo él; si no → `404` | Paginado; eventos de la cuenta dentro del alcance. |
| `GET /audit/platforms/<id>` | `any_admin_required` (usuario → `403`) + `can_manage_platform` (ajena → `404`) | Paginado; eventos de la plataforma dentro del alcance. |

- Filtros: `action` (catálogo), `result`, `area_id`, `platform_id`, `user_id`, `from`/`to` (ISO 8601, ≤ 366 días; `to` de solo fecha incluye el día), `q` (≤ 100, en `user` y `target`), `page`, `per_page` (1–100); inválido → `400 parametro_invalido` con `fields`.
- `ip`, `before`, `after`: `null` para el usuario normal. Orden `time` y `id` descendente.
- `time` sigue en hora local `AAAA-MM-DD HH:MM:SS` (UTC pendiente del dueño, SEC-AUD-02); `from`/`to` con zona se convierten a la hora local.

### 4.2.2 Accesos — `app/modules/access/api.py` (`/api/v1`, FNC-058)

| Endpoint | Protección | Comportamiento |
|---|---|---|
| `GET /me/access` | Sesión | Accesos propios; superadmin: vacío. Sin `last_job_id` para el rol usuario. |
| `GET /users/<id>/access` | `any_admin_required` (usuario → `403`); admin: él mismo o `can_manage_user`, si no → `404` | Superadmin: todos; admin: solo plataformas de sus áreas. |
| `POST /access/<id>/revoke` | `any_admin_required`; JSON (`415`) y no `cross-site` (`403 csrf_invalido`); `rules.validar_revocacion` (área ajena, otro admin o `admin_de_area` → `404`; propio → `403 operacion_propia`) | Cuerpo solo `reason` (≤ 500, opcional; otro campo → `400 campo_no_permitido`). `activo` → `revocando` + trabajo + `acceso_revocado` en una transacción (`services.revocar`); otro estado o choque simultáneo → `409 estado_invalido`. Responde `{"status": "success", "access": Access}`. |

- Listas: `status` (estado o `vigente`, por defecto), `page`, `per_page` (`audit.parametros.leer_paginacion`); inválido → `400 parametro_invalido`. Orden `granted_at` e `id` descendente.
- Forma `Access`: `access/serializacion.py` (fechas UTC con `Z`; `granted_by`/`revoked_by` en una consulta por página).
- CSRF provisional (H1): `POST /access/<id>/revoke` usa `api.csrf_provisional.escritura_del_portal` (no JSON → `415 tipo_no_soportado`; `Sec-Fetch-Site: cross-site` → `403 csrf_invalido`). El CSRF real sigue en FNC-008 (`xfail` en `tests/access/test_api.py`).
- Concurrencia (H2): `services.revocar` toma el acceso con `UPDATE ... WHERE status = 'activo'`; la segunda revocación simultánea da `409 estado_invalido` sin sobrescribir `revoked_by` ni `revoke_reason`.

### 4.3 Escritura — `users/api.py`, `users/preferencias_api.py`, `users/higiene_api.py` y `areas/api.py` (`/api/v1`; antes `api/crud.py`, FNC-029)

Todos leen el cuerpo con `leer_cuerpo` (FNC-119): un cuerpo que no es objeto → `400 cuerpo_invalido` (antes 500). Los campos que no lee el endpoint se siguen ignorando; `PUT /areas/<id>/users` además exige `user_ids` como lista de enteros.

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `PUT /areas/<id>/users` | `area_admin_required` | Define los miembros del área dentro del alcance. |
| `POST /users` | `any_admin_required` | Alta de cuenta local (`auth_source` lo fija el servidor). Rol fuera de lo asignable → `403 rol_reservado`; `managed_area_ids`, `auth_source`, `password_hash` → `400 campo_no_permitido`. `admin` es identificador reservado. Fuera de desarrollo nace `auth_source=ldap` sin clave y se vincula al entrar por directorio/SSO (con la bandera: `local`); sin contraseña local: `password` → `400 campo_no_permitido` salvo en desarrollo con `LOGIN_LOCAL_TODAS_LAS_CUENTAS` (FNC-077, SEG-02). Un `admin_area` nace sin áreas administradas. |
| `PUT /users/<id>` | `any_admin_required` + `can_manage_user` (fuera de alcance → `404`) | Edita usuario. Mismas reglas de rol y campos; el rol actual reenviado se ignora; el propio → `403 operacion_propia`. Degradar borra las áreas administradas y audita `rol_cambiado`. Contraseña: solo la de la cuenta de emergencia (superadmin local); otra cuenta → `400 campo_no_permitido`, salvo en desarrollo con `LOGIN_LOCAL_TODAS_LAS_CUENTAS` (cuentas `local` del alcance) (FNC-077). |
| `DELETE /users/<id>` | `any_admin_required` + `can_manage_user` (fuera de alcance → `404`) | Borra usuario; no permite borrarse a sí mismo ni la cuenta maestra `admin`. |
| `PUT /users/<id>/platforms` | `any_admin_required` | **Retirado** (FNC-065): `410 endpoint_retirado`, `use: POST /access-requests`; no escribe. Usuario → `403`, sin sesión → `401`. |
| `PUT /me/preferences` | Sesión | Guarda preferencias propias. |
| `GET /users/inactive?days=` | `admin_required` | Usuarios sin acceso en N días (mínimo `PURGE_MIN_DAYS` = 7), excluye superadmins. |
| `POST /users/purge` | `admin_required` | Elimina esos usuarios y audita. |

### 4.3.0 Plataformas — `app/modules/platforms/api.py` (`/api/v1`, FNC-046)

Contrato `docs/contratos/plataformas-integracion.md`. Respuesta de `POST`/`PUT`: `{"status", "platform", "warnings": []}`.

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `POST /platforms` | `any_admin_required`; área inexistente o ajena → `404` | Alta con lista blanca (`400 campo_no_permitido`); `name`, `description`, `area_id`, `integration_type` obligatorios (`422 validacion`). URL solo `https://`. `ldap`: DN bajo `LDAP_GROUPS_BASE_DN` o derivados de `LDAP_PLATFORM_GROUP_TEMPLATE`; sin directorio o sin DN → `422`; iguales → `409 grupos_iguales`; DN de otra plataforma → `409 grupo_en_uso`. Audita `plataforma_creada` ("admin X dio de alta la plataforma Y") en la misma transacción. |
| `PUT /platforms/<id>` | `any_admin_required` + `can_manage_platform` (ajena → `404`) | Mismas reglas, campos parciales. DN solo superadmin (`403 dn_solo_superadmin`). Cambiar tipo, grupos o área con `accesos_vigentes > 0` → `409 plataforma_con_accesos`. Cambiar `integration_type` solo superadmin. Pasar a `conector` borra los DN. Audita `plataforma_editada` con antes/después solo si algo cambió. |
| `DELETE /platforms/<id>` | `platform_manage_required` | Borra plataforma (movida de `crud.py` sin cambios). |
| `PUT /platforms/<id>/users` | `any_admin_required` | **Retirado** (FNC-065): `410 endpoint_retirado`, igual que `PUT /users/<id>/platforms` (`api/helpers.py: endpoint_retirado`). |

- Grupos: existencia con `ClienteDirectorio.existe_dn`; no existe → aviso `grupo_no_existe` y `groups_status: no_existe`; directorio sin respuesta → `directorio_no_disponible` y `sin_verificar`. Nunca es error.
- `Platform.to_dict` agrega `integration_type`, los DN, `groups_status`, `has_connector` y `active_grants`; ya no expone `user_ids`. `GET /platforms` solo cambia en que las URL guardadas que no cumplen `validar_url` salen `null` (`url_segura`); el resto queda para FNC-063.
- `validar_url`: solo `https://` con nombre de host; sin credenciales, IP literal, espacios, control ni DEL.
- Puntos de extensión en `platforms/estado.py`: `accesos_vigentes` (FNC-054) y `tiene_conector` (FNC-050), hoy `0`/`False`.

### 4.3.1 Cuentas — `app/modules/users/api.py` (`/api/v1`, FNC-044)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `PUT /users/<id>/managed-areas` | `admin_required` | Reemplaza `area_admins` de un `admin_area` con `{"area_ids": [...]}` (0–50, existentes, sin repetidos; si no → `422 validacion`). Destino sin rol `admin_area` → `409 rol_no_admin`. Audita `admin_asignado`/`admin_retirado` por área en la misma transacción. Responde `{"status": "success", "user": ManagedUser}`. |
| `POST /users/directory` | `any_admin_required`; admin solo sus áreas | FNC-064, contrato `usuarios-directorio.md`. Lista blanca `uid`, `email`, `given_name`, `surname`, `area_ids` (otro, incluido `password` o `role` → `400 campo_no_permitido`). Admin: `area_ids` 1–50 de sus áreas (ajena o inexistente → `404`); superadmin: cualquiera o vacío. `422 validacion` por campo (correo ≤ 120, la columna). Correo solo ASCII. Duplicados (auditados `warning`): uid en el directorio, reservado o cuenta heredada → `409 uid_duplicado`; correo en el portal o en el directorio (`ClienteDirectorio.buscar_por_correo`; ambiguo también) → `409 correo_duplicado`. Reserva el correo con la fila de `users` sin confirmar (UNIQUE: dos altas simultáneas, una gana), busca el `mail` justo antes de escribir, crea la entrada sin contraseña (`EscritorDirectorio.create_user`) y confirma la cuenta `usuario` `auth_source=ldap` sin `password_hash`; fallo del directorio (o sin configurar) → `503 directorio_no_disponible` sin tocar la BD; fallo parcial (`commit`) → `500 error_interno`, rollback, auditoría `warning` con el DN (entrada para revisión) y la persona se registra en su primer acceso. Audita `cuenta_directorio_creada` (éxito en la misma transacción; fallos `error`/`warning`). Responde `201 {"status": "success", "user": ManagedUser}`. |

### 4.3.2 Áreas — `app/modules/areas/api.py` (`/api/v1`, FNC-045)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `POST /areas` | `any_admin_required` | Crea área; un `admin_area` queda en `area_admins` en la misma transacción. Audita `area_creada`. |
| `PUT /areas/<id>` | `any_admin_required` + `can_manage_area` (ajena o inexistente → `404`) | Edita área; el valor reenviado sin cambio se ignora. Audita `area_editada` con antes/después. |
| `DELETE /areas/<id>` | `any_admin_required` + `can_manage_area` (ajena o inexistente → `404`) | Baja (P11). `409 area_con_otros_admins` (admin de área con otros admins en el área), `409 area_con_plataformas` o `409 area_con_accesos` (miembros en `user_areas`). En SQLite pone `area_id` en NULL en la auditoría del área antes de borrarla; en MySQL lo hace la FK (`ON DELETE SET NULL`). Audita `area_eliminada` (sin `area_id`; nombre en `target`, estado en `before`). |

- Entrada (`areas/validacion.py`): lista blanca `name`, `description`, `icon`, `color`, `status`; otro campo → `400 campo_no_permitido`; cuerpo no objeto → `400 cuerpo_invalido`.
- Reglas: `name` 2–100 (obligatorio en alta), `description` ≤ 500, `icon` ≤ 50 (`[A-Za-z0-9_-]`), `color` `#rrggbb`, `status` `Activo`/`Inactivo`; si no → `422 validacion` con `fields`.
- Nombre único sin distinguir mayúsculas ni acentos en mayúscula (`casefold`) → `409 area_duplicada` (también si la restricción única falla por carrera: `IntegrityError` → rollback).
- Condiciones de baja: `areas/baja.py` (`conflicto_de_baja`).

### 4.3.3 Solicitudes — `app/modules/access_requests/api.py` (`/api/v1`, FNC-056)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /access-requests/catalog` | Sesión | Plataformas `Activo` de áreas `Activo` del actor (P1: `user_areas`; un admin además las que administra, solo ver; superadmin todas, solo ver) con `my_level`, `my_access_status`, `pending_request_id`, `can_request`, `requestable_levels`. Filtros `area_id`, `q` (≤ 100, sin comodines). |
| `POST /access-requests` | Sesión; JSON (`415`); `Sec-Fetch-Site: cross-site` → `403 csrf_invalido` | Crea la solicitud `pendiente` y audita `solicitud_creada` en la misma transacción; tras el commit avisa `solicitud_nueva` a los admins del área. |
| `GET /access-requests/mine` | Sesión | Solicitudes propias paginadas (`created_at` desc); filtros `status`, `platform_id`; `access` del acceso generado. |

- Lista blanca: `platform_id`, `level`, `justification` (opcional, ≤ 500; decisión del dueño 2026-10-20); otro → `400 campo_no_permitido`.
- Errores en orden: superadmin `403 sin_permiso`; `422 validacion`; fuera de sus áreas `404`; área que administra `409 ya_administra_area` (RF-03); inactiva o nivel sin grupo/conector `409 plataforma_no_disponible`; pendiente `409 solicitud_duplicada` (también por la restricción única ante carreras); mismo nivel o superior `409 nivel_vigente`; subir con el acceso aún no `activo` `409 estado_invalido` (reglas P5 de `access.rules.acceso_a_reemplazar`).

### 4.3.4 Inventario de permisos — `app/modules/access/inventario_api.py` (`/api/v1`, FNC-059)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /access/inventory` | `any_admin_required` (usuario `403`) | F-AUD-02: accesos con usuario, plataforma, área, nivel, origen, `granted_at`, `granted_by` (null = sistema) y estado. Superadmin todo; admin solo plataformas de sus áreas. Filtros `area_id`, `platform_id`, `user_id`, `level`, `origin`, `status` (estado o `vigente`, por defecto), `q` (nombre o correo, ≤ 100, sin comodines); paginada (`per_page` ≤ `ACCESS_INVENTORY_PAGE_SIZE_MAX`). Orden área, plataforma, usuario. |

- Un filtro fuera de alcance da lista vacía (los filtros se suman al alcance, como en la auditoría). Valor inválido → `400 parametro_invalido`.
- Consulta en `access/inventario.py` (`visibles`, `filtrar`, `ordenados`); forma `Access` con `access.serializacion.accesos_publicos` (FNC-058).

### 4.3.5 Ejecuciones — `app/modules/provisioning/api.py` (`/api/v1/provisioning`, FNC-062)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /provisioning/jobs` | `any_admin_required` (usuario `403`) | Bitácora paginada (`created_at` desc), sin `attempts`. Superadmin todo; admin solo trabajos con `area_id` de sus áreas. Filtros `status`, `operation`, `provider`, `area_id`, `platform_id`, `user_id`, `access_id`, `from`, `to`. |
| `GET /provisioning/jobs/<id>` | `any_admin_required` | Detalle con `attempts` (error saneado otra vez al salir, SEC-CON-10); ajeno o inexistente → `404`. |
| `POST /provisioning/jobs/<id>/retry` | `admin_required` (P10) + `escritura_del_portal` | Cuerpo `{}` (otro campo → `400`). Solo desde `fallido`: `reintento.reintentar` (reabre trabajo y acceso con `UPDATE` condicional, auditoría `ejecucion_reintentada`, aviso al worker tras el commit). No fallido, simultáneo, con revocación posterior, sin acceso o un otorgar que ya no pasa `rules.validar_otorgamiento` (cuenta borrada, inactiva, superadmin o fuera del área) → `409 estado_invalido`. |

- `from`/`to` sin zona: hora local del proceso (como la auditoría), comparadas en UTC; un extremo que desborda al convertir → `400 parametro_invalido` (SEG-062-03).
- No se envían `idempotency_key`, `locked_by` ni `locked_at`. Área de un trabajo = la de la plataforma al encolar (decisión del orquestador, pendiente de validar en la prueba de concepto).

### 4.3.7 Conectores — `app/modules/connectors/api.py` (`/api/v1`, FNC-061)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /platforms/<id>/connector` | `admin_required` (SEC-CON-11; admin de área y usuario `403`) | Forma `Connector` (solo `credential_ref`, nunca el valor). Plataforma o configuración inexistente → `404`. |
| `PUT /platforms/<id>/connector` | `admin_required` + `escritura_del_portal` | Crea o reemplaza. Orden: `404` → `400 cuerpo_invalido`/`campo_no_permitido` (lista blanca `type`, `host`, `port`, `params`, `credential_ref`, `active`) → `409 plataforma_sin_conector` → `422 validacion` (`validar_configuracion` con `referencias_de_otras`; host de `CONNECTOR_ALLOWED_HOSTS`) → cambiar `type` con `accesos_vigentes > 0` → `409 plataforma_con_accesos`; creación simultánea (restricción única) → `409 conector_concurrente`. Audita `conector_configurado` (antes/después de lo que cambió; nada si no cambia) y llama a `limpiar_cache()` tras el commit. |
| `DELETE /platforms/<id>/connector` | `admin_required` + `escritura_del_portal` | Cuerpo `{}`. `404`; con `accesos_vigentes > 0` → `409 plataforma_con_accesos`. Audita `conector_eliminado` (antes) y `limpiar_cache()`. |
| `POST /platforms/<id>/connector/test` | `admin_required` + `escritura_del_portal` | Cuerpo `{}`. `prueba.probar_conexion`: `consultar` del proveedor `conector` con la cuenta del superadmin (no otorga ni revoca), tras vaciar la caché. `200` con `result` `ok`/`error` y mensaje genérico; motivo solo al log. `credential_status` → `ok` o `no_encontrada`. Audita `conector_probado`. |

- Decisiones del orquestador (pendientes de validar en la prueba de concepto): ficha FNC-061.

### 4.3.6 Inicio — `app/modules/home/api.py` (`/api/v1`, FNC-066)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /home/summary` | Sesión (alcance) | Contrato `inicio.md`: `scope` `propio` (usuario: `my_access`, `my_requests`), `areas` (admin: lo propio más `pending_approvals`, `failed_access`, `oldest_pending_at` y `totals` de sus áreas) o `global` (superadmin: lo mismo sin lo propio). Solo conteos y una fecha. |

- Decisión: endpoint propio, `GET /stats` no cambia (contrato `inicio.md`: "`GET /stats` no cambia"; su forma la consume el panel actual).
- Sin consultas propias: `access.consultas.de_usuario`, `access_requests.consultas.mias`, `approvals.bandeja` (mismo total que `/access-requests/inbox`), `access.inventario.visibles` (mismo alcance que `/access/inventory`) y `authz.scoped_areas`.

### 4.4 Sistema y notificaciones — `settings/api.py`, `notifications/api.py` y `settings/respaldo_api.py` (`/api/v1`; antes `api/admin.py`, FNC-029)

También con `leer_cuerpo` (FNC-119): cuerpo no objeto → `400 cuerpo_invalido`.

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
| `POST /notifications/read` | Sesión | Marca como leídas para quien consulta (todas o `ids`); las globales se registran en `notification_reads` y no afectan a otros. `GET` calcula `is_read` por usuario (FNC-031). |
| `DELETE /notifications` | Sesión | Borra las propias. |
| `GET /backup` | `admin_required` | Descarga ZIP `nexus_config.json` con portal, LDAP, SMTP (sin contraseñas), plantillas y usuarios locales con su hash. |
| `POST /backup` | `admin_required` | Restaura desde ese ZIP; solo agrega usuarios que no existan. |

### 4.4.1 Directorio — `app/modules/directory/api.py` (`/api/v1`, FNC-043)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /auth-config` | `admin_required` | Configuración efectiva de `LDAP_*`: `active`, `editable: false`, `config` (sin contraseña ni ruta de CA), `origins` (`env`/`default`) y `variables`; `error: configuracion_invalida` si no carga. No conecta. |
| `PUT /auth-config` | `admin_required` | Sin campos editables (ADR-004): cualquier campo → `400 campo_no_permitido`; `{}` → 200 con la configuración. |
| `POST /auth-config/test` | `admin_required` | Bind de la cuenta de servicio con la configuración efectiva; cuerpo con campos → `400`; inactivo → `409 directorio_no_configurado`; fallo → `503 directorio_no_disponible` genérico. Audita `PRUEBA LDAP`. |
| `GET /directory/search?q=` | `admin_required` | `buscar_personas` (atributo `LDAP_USER_ATTR`, `mail`, `cn`, `displayName`; filtro escapado); `q` de 2–64 caracteres (`400 parametro_invalido`); máx. 50; marca `exists`. `409`/`503` como la prueba. |

### 4.5 Rutas heredadas (retiradas, FNC-027)

Los siete blueprints heredados de NEXUS (`auth`, `core`, `audit`, `settings`, `notifications`, `users_module`, `areas_module`; 44 rutas) y `app/decorators.py` se eliminaron. Esas rutas responden `404`, sin `410` para clientes viejos (el frontend solo usa `/api/v1`). Fuera de `/api/v1` el backend no tiene rutas; la guardia `tests/test_guardia_rutas.py` lo exige. Las denegaciones de los decoradores de `app/authz.py` son siempre `403` JSON.

## 5. Integraciones

### Cliente OpenLDAP centralizado (`app/modules/directory/`, FNC-040)
- Activo solo con `LDAP_URL`; la configuración (`LDAP_*`, ver `VARIABLES.md`) se valida en `create_app()` y, si falla, la app no arranca.
- TLS obligatorio: `ldaps://` o `ldap://` + StartTLS antes del bind; `CERT_REQUIRED`, nombre del host verificado, CA de `LDAP_CA_CERT_FILE` o del sistema.
- `ClienteDirectorio`: `conexion_servicio(solo_lectura=True)` (escritura solo desde `writer.py`), `buscar_usuario()`, `grupos_de_usuario()` (búsqueda bajo `LDAP_GROUPS_BASE_DN`, sin overlay `memberOf`), `existe_dn()`, `verificar_contrasena()` (bind de la persona; vacía = `False` sin conectar; FNC-042), `buscar_personas(texto, limite)` (FNC-043), `buscar_por_correo(correo)` (filtro exacto; `PersonaAmbigua` si hay varias; FNC-049).
- Escape: `escapar_filtro` (RFC 4515) y `escapar_valor_dn` (RFC 4514).
- `valor_de_membresia(cfg, usuario)`: DN o identificador según `LDAP_GROUP_MEMBER_ATTR` (lo usan lectura y escritura).
- Errores: `registrar_error` (público) devuelve `ErrorDirectorio` con mensaje genérico y `causa` (excepción de `ldap3`, solo para clasificar); detalle al log sin la contraseña de bind.
- Llamadores: login (FNC-042). Búsqueda y prueba de conexión (FNC-043) siguen en el código heredado de abajo; escritura en `writer.py` (FNC-041).

### Escritura en OpenLDAP (`app/modules/directory/writer.py`, FNC-041)
- `EscritorDirectorio(cliente)`: `add_member(group_dn, user)`, `remove_member(group_dn, user)`, `create_user(DatosCuenta)`; sin borrado de cuentas.
- Devuelve `ResultadoEscritura` (`errors.py`): `hecho`, `ya_estaba`, `no_existe`, `error_transitorio` (reintentable), `error_permanente`; nunca lanza por fallos del directorio.
- Solo bajo `LDAP_GROUPS_BASE_DN` / `LDAP_USERS_BASE_DN` (RDN normalizados); fuera → `error_permanente` `fuera_de_base` sin conectar.
- Membresía: lee el grupo y aplica un solo `MODIFY_ADD`/`MODIFY_DELETE`; DN comparados normalizados; `memberUid` usa el identificador.
- Último miembro de `groupOfNames`/`groupOfUniqueNames`: con `LDAP_GROUP_PLACEHOLDER_MEMBER` agrega el relleno y quita al usuario en la misma operación; sin él, `error_permanente` `ultimo_miembro`. Al agregar un miembro real se quita el relleno.
- DN comparados con `dn.py`: RDN multivaluados como conjunto; espacios escapados significativos.
- Alta: uid `[a-z0-9._-]+` y correo válido, si no `datos_invalidos`; DN `LDAP_USER_ATTR=<uid escapado>,LDAP_USERS_BASE_DN`; clases `LDAP_USER_OBJECT_CLASSES`; `cn`, `sn`, `givenName`, `mail` (provisionales hasta cerrar ADR-004); sin `userPassword` (P8: Authelia).
- Una sola cuenta de servicio (`LDAP_BIND_DN`) para lectura y escritura (dueño, 2026-10-15); ACL en `docs/operacion/ENTORNOS.md` (SEC-LDAP-03).
- Log de fallos de escritura: solo tipo y código de resultado (`registrar_error(..., con_detalle=False)`), sin DN de la persona.
- Llamadores: `provisioning/ldap_provider.py` (FNC-049, membresía; valida que el grupo sea el de la plataforma) y FNC-064 (alta de cuentas, pendiente).

### Ejecutor de aprovisionamiento (`app/modules/provisioning/`, FNC-049)
- Cola: Redis + RQ (ADR-003, dueño). La BD es la cola persistente (*outbox*); Redis solo despierta al worker.
- `queue.encolar(operacion, usuario_id, plataforma, nivel, clave_idempotencia, access_id=None)`: agrega el trabajo **sin commit** (va en la transacción del llamador); tras el commit despierta al worker. Sin Redis, espera al barrido. Clave repetida → mismo trabajo.
- `provider` = `integration_type` de la plataforma al encolar; `max_attempts` = `PROVISIONING_MAX_ATTEMPTS` al encolar.
- Estados: `pendiente` → `en_ejecucion` → `exitoso` \| `reintentando` \| `fallido`. Intentos en `provisioning_job_attempts` (`exitoso`, `sin_cambios`, `error_transitorio`, `error_permanente`).
- Orden por terna (usuario, plataforma, nivel): un trabajo no se reserva si hay uno anterior de la terna sin terminar. `encolar` de una revocación cancela los otorgar en espera de su terna (`cancelado`, auditoría `ejecucion_cancelada`).
- Reserva atómica (`UPDATE … WHERE`): un solo worker por trabajo; el cierre vuelve a comprobar `locked_by` (si otro la retomó, no pisa nada); vence a `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS` + 30 s y otro worker lo retoma (intento abierto → `interrumpido`).
- Transitorio: *backoff* `min(max, base·2^(n-1))` con *equal jitter*; permanente: sin reintentos. Excepción del proveedor o tiempo de espera de RQ → transitorio, sin guardar su texto.
- Error de la bitácora: mensaje del catálogo (`saneo.py`) + detalle saneado (sin secretos del despliegue, `clave=valor` sensibles, `Bearer` ni credenciales en URL), ≤ 500 (SEC-CON-10).
- Resultado final, en la misma transacción: auditoría con actor `sistema` (`acceso_activo`, `acceso_fallido`, `acceso_revocado`, `revocacion_fallida`; `grant_id` = `access_id`) y `manejadores` (`registrar_manejador(on_success, on_failure)`, para FNC-054; sin commit).
- `fallido`: después del commit y en `try`, `notificar_aprovisionamiento_fallido` (FNC-048).
- Proveedores (`providers.py`): `Provisioner` con `otorgar`/`revocar`/`consultar(Operacion)` → `ResultadoProveedor` (SEC-CON-01); `registrar_proveedor(tipo, fabrica)`. `ldap` registrado en el módulo; `conector` lo registra `connectors.registrar(app)` en `create_app()` (FNC-050).
- `ProveedorLdap`: grupo del nivel de la plataforma, bajo `LDAP_GROUPS_BASE_DN` (SEC-LDAP-04); persona con `ClienteDirectorio.buscar_por_correo` (filtro exacto `(mail=…)`, cualquier valor; varias → `persona_ambigua`); usa `EscritorDirectorio`.
- Mensajes RQ en JSON (`SERIALIZADOR_RQ`); el worker descarta sin ejecutar todo mensaje que no sea `ejecutar_trabajo(<int>)`. Despertar desde la web: tiempo de espera de 0,5 s.
- Reintento manual (FNC-062): `ejecucion.reabrir(trabajo, cfg)` sube `max_attempts` con `UPDATE … WHERE status = 'fallido'` (un segundo reintento simultáneo → `EstadoInvalido`); `queue.despertar_tras_commit(id)` avisa al worker tras el commit.
- Worker: `flask provisioning worker` (§6). `SimpleWorker` de RQ sin *fork*; cada vuelta barre la BD (vencidos y reservas vencidas) y trabaja hasta quedar ocioso `PROVISIONING_POLL_INTERVAL_SECONDS`. `SIGTERM`/`SIGINT`: termina el intento y sale.
- Exige `REDIS_PASS` y `REDIS_HOST` como nombre de host; variables `PROVISIONING_*` validadas en `create_app()`.
- API de ejecuciones y reintento manual: §4.3.5 (FNC-062). Unidad systemd: FNC-067.

### Conectores (`app/modules/connectors/`, FNC-050, ADR-005)
- Un conector es el proveedor `conector` del ejecutor (FNC-049): `ProveedorConector` (`provider.py`) carga `platform_connectors`, revalida el host y resuelve la credencial en cada operación.
- Interfaz (`base.py`): `Conector(destino, credencial)` con `otorgar`/`revocar(SolicitudConector)` → `ResultadoProveedor`; `consultar` opcional (sin ella, permanente `consulta_no_disponible`). `SolicitudConector`: ids, operación, nivel y `cuenta` (correo del portal en minúsculas; SEC-CON-03). `Destino`: host, puerto, `params` (solo lectura), `tiempo_espera` (`CONNECTOR_TIMEOUT_SECONDS`).
- Registro (`registry.py`): `registrar_tipo(TipoConector(nombre, fabrica, validar_params))`. `noop` solo con `APP_ENV=development` o `TESTING`; `api` (FNC-051) y `ssh` (FNC-052) siempre; `bd`: FNC-053.
- Registro (`registry.py`): `registrar_tipo(TipoConector(nombre, fabrica, validar_params))`. `noop` solo con `APP_ENV=development` o `TESTING`; `api` (FNC-051) y `bd` (FNC-053) siempre; `ssh`: FNC-052.
- Validación (`validacion.validar_configuracion(datos)` → `(limpio, errores)`): reglas del `PUT /platforms/<id>/connector` del contrato (endpoint en FNC-061); host en `CONNECTOR_ALLOWED_HOSTS` (vacía = ninguno; nunca IP); `params` sin claves sensibles (también en listas) y con a lo más `PROFUNDIDAD_MAXIMA_PARAMS` niveles, y según el tipo; `credential_ref` ≤ 200, sin `__` en su variable de dev y sin equivalente en otra plataforma (`referencias_en_uso`).
- Credenciales (`credenciales.py`): `ProveedorDeSecretos`; `development` → entorno (`CONNECTOR_CREDENTIAL_<REFERENCIA>`); otro entorno → Vaultwarden (`app/modules/secretos/`, FNC-068). Caché en memoria por fuente y referencia (`CONNECTOR_CREDENTIAL_CACHE_SECONDS`, ≤ `MAXIMO_EN_CACHE`), sin guardar fallos; `resolver_en_gestor()` siempre Vaultwarden (bind LDAP); `repr` oculta el valor; `limpiar_cache()` al cambiar la configuración (FNC-061) o rotar (FNC-068). Referencia ambigua (`referencia_valida`, `referencias_en_conflicto`) → permanente `credencial_no_encontrada`. El `Destino` lleva el host normalizado.
- Errores sin detalles (`saneo.py`): `credencial_no_encontrada`, `gestor_no_configurado`, `host_no_autorizado`, `conector_no_disponible` → permanentes; `gestor_no_disponible` y excepción del tipo → transitorios. El valor de la credencial se borra del detalle antes de la bitácora (SEC-CON-10).
- `platforms.estado.tiene_conector` = `consultas.conector_disponible` (configuración activa de un tipo registrado): lo usan `has_connector` y el catálogo de solicitudes.

### Conector API HTTP (`connectors/api_http.py`, FNC-051, SEC-CON-06)
- Tipo `api` registrado siempre. Esquema de `params` y estados HTTP: contrato `conectores-y-ejecuciones.md` 1.2. Solo biblioteca estándar (`http.client` + `ssl`): sin dependencias nuevas.
- `destino_seguro.py`: resuelve el host y rechaza si **alguna** dirección no es pública (privada, loopback, *link-local*, multicast, sin especificar, reservada, *site-local* `fec0::/10`, CGNAT; IPv4 e IPv6, también IPv4 incrustada en mapeada, NAT64 y 6to4) → permanente `destino_no_permitido`. DNS caído → transitorio `red_no_disponible`.
- `http_transporte.py`: conecta a la **IP ya validada** (no vuelve a resolver) y valida el certificado contra el nombre del host (`CERT_REQUIRED`, TLS ≥ 1.2, CA del sistema o `CONNECTOR_HTTP_CA_FILE`); no sigue redirecciones (3xx → permanente); no lee el cuerpo de la respuesta.
- Plantillas: solo `{correo}`, `{nivel}`, `{plataforma}`, reemplazadas en una pasada (sin `eval` ni `format`); ruta y consulta con valor codificado por porcentaje; cuerpo JSON serializado con `json.dumps`. Los `params` se revalidan en cada operación.
- Valores de plantilla: vacíos, `.`, `..` o con segmento así, o un correo sin `@` → permanente `valor_no_valido` (sin llamar). Otra IP validada solo se prueba si falla la conexión TCP; tras enviar no se reintenta.
- Credencial: `bearer`, `basic` (usuario y secreto de la credencial) o cabecera propia; un secreto o usuario con caracteres de control no se envía (`credencial_no_encontrada`). Al revocar, 404 y 410 son `sin_cambios`; al otorgar, 409 es permanente salvo `sin_cambios: [409]`.
- Guía de configuración (plataforma piloto, P9 pendiente): 1) agregar el host a `CONNECTOR_ALLOWED_HOSTS`; 2) guardar la credencial en el gestor (en dev, `CONNECTOR_CREDENTIAL_<REFERENCIA>`); 3) `PUT /platforms/<id>/connector` con `type: "api"`, el host, puerto 443 y los `params` del contrato; 4) `POST .../test` (necesita `consultar`); 5) si la plataforma usa CA propia, `CONNECTOR_HTTP_CA_FILE`. El host debe resolver a una IP pública: una plataforma interna con IP privada no se alcanza (propuesta FNC-106).
### Conector base de datos (`connectors/base_de_datos.py`, FNC-053, SEC-CON-05)
- Tipo `bd` registrado siempre. Esquema de `params` y resultados: contrato `conectores-y-ejecuciones.md` 1.3. Sin SQL libre: sentencias fijas con `%s` en la configuración (validadas en `bd_sentencias.py`: una sola sentencia, sin comentarios ni comillas, `WHERE` en `UPDATE`/`DELETE`) y valores solo como parámetros del driver.
- Motores (`bd_motores.py`): `mysql` (MySQL y MariaDB; PyMySQL) y `postgresql` (psycopg2, versión fijada). Cada uno abre la conexión a la **IP validada** (`destino_seguro.resolver_seguro`) y verifica el certificado contra el **nombre del host**: MySQL entrega al driver un socket a la IP con contexto `CERT_REQUIRED` + `check_hostname` (TLS ≥ 1.2, `crear_contexto`); PostgreSQL usa `hostaddr` + `sslmode=verify-full` y `gssencmode=disable`. TLS no se puede desactivar (ni en dev); si un servidor MySQL no ofrece TLS se aborta (`tls_no_valido`), porque PyMySQL no falla solo. CA: sistema o `CONNECTOR_DB_CA_FILE`.
- Transacción explícita (sin *autocommit*): se confirma solo si la sentencia terminó bien y afectó ≤ `max_filas` (1 por defecto); si no, `rollback`. Una consulta nunca confirma. Filas 0 → `sin_cambios` (use `ON DUPLICATE KEY UPDATE` o `ON CONFLICT DO NOTHING` para que otorgar sea idempotente). Un fallo al confirmar es transitorio: el reintento es seguro por la idempotencia.
- Errores del driver → permanente o transitorio por código (MySQL 1213, 1205, 2003, 2013…; SQLSTATE clases 08, 40, 53, 57, 58 y `55P03`): transitorios; credencial (`1045`, `28xxx`), certificado y sentencia rechazada: permanentes. Nunca se guarda el mensaje del driver, solo `MySQL <n>` o `SQLSTATE <xxxxx>`. Una excepción que no es del driver la trata el proveedor (transitoria `inesperado`).
- Tiempos: `CONNECTOR_DB_TIMEOUT_SECONDS` para conectar y para leer, escribir y `statement_timeout`; el doble debe ser menor que el del intento. Una consulta que se pasa del tiempo se corta en el cliente; el servidor puede seguir ejecutándola (acótelo con el usuario de BD).
- Guía de configuración (plataforma piloto, P9 pendiente):
  1. Crear en la BD de la plataforma un **usuario exclusivo del portal con permisos mínimos**: solo `INSERT`/`UPDATE`/`DELETE`/`SELECT` sobre la tabla de cuentas que usan las sentencias (sin `GRANT`, `DDL`, `FILE`, `SUPER` ni otras tablas), obligado a TLS (`REQUIRE SSL` en MySQL; `hostssl` en `pg_hba.conf`) y con límite de conexiones.
  2. Agregar el host de la BD a `CONNECTOR_ALLOWED_HOSTS` (nombre, nunca IP; debe resolver a una IP pública mientras no exista FNC-106).
  3. Guardar usuario y contraseña en el gestor (en dev, `CONNECTOR_CREDENTIAL_<REFERENCIA>` y `…__USUARIO`).
  4. `PUT /platforms/<id>/connector` con `type: "bd"`, el host, el puerto del motor y los `params` del contrato; `POST .../test` (necesita `consultar`).
  5. Si el certificado lo firma una CA propia, `CONNECTOR_DB_CA_FILE`; el certificado del servidor debe incluir el nombre del host en el SAN.
- No incluye: MongoDB, SQL Server ni Oracle; sincronizar cuentas existentes; pantalla (DIS-042).
### Gestor de secretos (`app/modules/secretos/`, FNC-068, ADR-005)
- `configuracion.py`: `VAULTWARDEN_*`; fuera de dev y con alguna definida se valida todo en `create_app()` (sin conectar).
- `cifrado.py`: descifrado Bitwarden del lado del cliente (PBKDF2/Argon2id con `LIMITES_KDF`, HKDF, tipo 2 AES-CBC+HMAC, tipos 3/4 RSA-OAEP); rechaza el tipo 0 y los 5/6.
- `vaultwarden.py`: `ClienteVaultwarden.leer(referencia)` → `ItemSecreto`; sesión por llave de API, `sync` y búsqueda por nombre en `VAULTWARDEN_COLLECTION_ID`. Errores `SecretoNoEncontrado`/`SecretoAmbiguo`/`GestorCaido`/`GestorMalConfigurado`, sin valores. `transporte` inyectable (pruebas: `tests/secretos/vaultwarden_falso.py`).
- Bind LDAP: con `LDAP_BIND_PASSWORD_REF` (solo fuera de dev; reservada para conectores: `credenciales.referencia_reservada`, en `validacion.py` y `provider.py`), `ClienteDirectorio._contrasena_bind()` la pide al conectar; gestor caído → `ErrorDirectorio` transitorio (`LDAPCommunicationError`).
- Operación: `docs/operacion/SECRETOS.md`.

### Conector SSH (`connectors/ssh.py`, `ssh_transporte.py`, FNC-052, SEC-CON-04)
- Tipo `ssh` registrado siempre. Esquema de `params` y códigos de salida: contrato `conectores-y-ejecuciones.md` 1.3. Dependencia nueva: `paramiko==5.1.0` (`requirements.txt`).
- Técnica contra la inyección (decisión del orquestador, pendiente de validar en la prueba de concepto): **comando fijo por operación** (lista de argumentos de la configuración con lista blanca de caracteres, armado con `shlex.quote`; sin datos de la solicitud) y **datos por la entrada estándar** como una línea JSON. Nunca un shell con una cadena interpolada. Recomendado en el servidor: comando forzado (`command=` + `restrict` en `authorized_keys`) que lea esa línea.
- `ssh_transporte.py`: `paramiko.Transport` sobre un socket a la **IP ya validada** (`destino_seguro`); no usa `SSHClient` (sin `AutoAddPolicy`, `ssh_config`, `ProxyCommand`, agente ni reenvíos); verifica la llave del host **antes** de enviar la credencial (huellas `SHA256:` de `params` o `CONNECTOR_SSH_KNOWN_HOSTS_FILE`; sin ninguna, nunca conecta); sin `ssh-rsa`/`ssh-dss`, cifrados CBC ni MAC `hmac-md5`/`hmac-sha1` (también `-96`); sin *pty*; la salida remota se cuenta (`CONNECTOR_SSH_MAX_OUTPUT_BYTES`) y se descarta; **plazo único** `CONNECTOR_SSH_TIMEOUT_SECONDS` para toda la operación (reloj de plazo restante; cada etapa usa el menor entre `CONNECTOR_TIMEOUT_SECONDS` y lo que queda). Un `known_hosts` ilegible, no UTF-8 o con `@cert-authority`/`@revoked` cuenta como huella no válida; una llave corrupta, como `ssh_autenticacion_rechazada` (sin el texto del error).
- Autenticación: llave privada (RSA, ECDSA o Ed25519, sin frase de paso) de la credencial, con el usuario de la credencial; contraseña solo si `params.auth.metodo` es `contrasena`. Un usuario o secreto vacío → `credencial_no_encontrada`.
- Clasificación: huella distinta, credencial rechazada y salida excesiva → permanentes; fallo de red o de saludo (otra IP validada, máximo 3, solo antes de autenticar), tiempo agotado y cierre sin código → transitorios; código de salida según `params`.
- Pruebas (`tests/connectors/test_ssh.py`, `test_ssh_transporte.py`): doble del transporte y un servidor `paramiko` real en loopback (`servidor_ssh_falso.py`); sin red externa.
- Guía de configuración (plataforma piloto, P9 pendiente): 1) agregar el host a `CONNECTOR_ALLOWED_HOSTS`; 2) obtener la huella del host por un canal de confianza (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` en el servidor) y ponerla en `params.huellas`; 3) en el servidor, crear la cuenta de servicio y su llave con comando forzado y `restrict`; 4) guardar usuario y llave privada en el gestor (en dev, `CONNECTOR_CREDENTIAL_<REFERENCIA>` y `…__USUARIO`); 5) `PUT /platforms/<id>/connector` con `type: "ssh"`, el host, puerto, `params` y `credential_ref`; 6) `POST …/test` y revisar la bitácora. Si el host resuelve a una red interna, ver FNC-106.

### Accesos otorgados (`app/modules/access/`, FNC-054)
- `services.otorgar(usuario, plataforma, nivel, origen, actor=None, request_id=None)` y `services.revocar(acceso, actor=None, motivo=None)`: cambian el acceso, encolan (`acceso-<id>-otorgar|revocar`) y auditan (`acceso_otorgado`, `acceso_revocado`) **sin commit**; `actor=None` = sistema (FNC-055).
- Estados (contrato `accesos.md`): `en_proceso` → `activo`/`fallido`; `activo` → `revocando` → `revocado`/`fallo_revocacion`; reintento `fallido` → `en_proceso` y `fallo_revocacion` → `revocando` (`services.reabrir_acceso`, FNC-062, con `UPDATE` condicional sobre el estado fallido). Revocar solo desde `activo`.
- P5: subir a `admin` pasa el `usuario` (debe estar `activo`) a `revocando` con `reemplazado_por_nivel_superior`; mismo nivel o inferior → `nivel_vigente`.
- Reglas (`rules.py`): por solicitud, quien otorga administra la plataforma y la cuenta (`can_manage_user`) y la cuenta es del área (P1); `admin_de_area` solo el sistema, nivel `usuario`, a un admin del área; superadmin → `acceso_por_defecto`; propio → `operacion_propia`; un admin no revoca accesos `admin_de_area` ni de otros admins (404).
- Errores: `ErrorDeAcceso` con `respuesta` = (mensaje, HTTP, `code`, `fields`) para `error_response`.
- `manejadores.registrar()` (en `create_app`): el resultado del trabajo lleva el acceso a su estado en la misma transacción; transición inválida → solo log (SEC-CON-09).
- `consultas.de_usuario(usuario_id, estados, area_ids=None)`: accesos de una cuenta para la API (FNC-058).
- `consultas.plataformas_con_acceso_activo(usuario_id)`: subconsulta de `platform_id` con acceso `activo`; la usa `authz.scoped_platforms` (FNC-063).
- `consultas.py`: `platforms.estado.accesos_vigentes` (→ `active_grants`, `409 plataforma_con_accesos`) y `areas.baja.tiene_accesos_vigentes` (`409 area_con_accesos`; ya no cuenta `user_areas`).

### Acceso automático de los admins (`access/area_admin_sync.py`, FNC-055)
- P6: cada admin de área activo recibe en cada plataforma de sus áreas un acceso `admin_de_area`, nivel `usuario`, otorgado por el sistema (`services.otorgar`, auditoría "sistema dio permisos de acceso a admin X"). El superadmin no.
- Puntos de entrada, en la transacción del llamador (sin `commit`):
  - `sincronizar_plataforma(plataforma)`: `POST /platforms` (tras `plataforma_creada`) y `PUT /platforms/<id>` al cambiar área, tipo o grupos;
  - `sincronizar_cuenta(cuenta, areas_nuevas)`: `users.areas_administradas.asignar_areas_administradas` y `users.roles.cambiar_rol` (al dejar `admin_area`, tras `rol_cambiado`).
- Revoca (`services.revocar`, motivo `ya_no_administra_el_area`) solo accesos `activo`; uno `en_proceso` lo revoca `manejadores.al_exito` al confirmarse el otorgar.
- Solo otorga ante un evento: una revocación manual del superadmin no se deshace sola. No otorga si ya hay un vigente (cualquier nivel u origen) ni en `ldap` sin grupo de nivel `usuario`.
- Cambiar `area_id` con solo accesos automáticos ya no da 409 (`platforms.estado.accesos_que_impiden_mover`, `consultas.contar_vigentes_no_automaticos`); tipo y grupos siguen dando 409 (FNC-085).
- Pendiente: desactivar una cuenta no revoca (FNC-084); plataformas existentes al desplegar (FNC-086); `DELETE /platforms/<id>` con accesos falla por FK (FNC-083).

### Login de directorio (`authenticate_user_ldap`, FNC-042)
- Usa el cliente centralizado y `LDAP_*`; sin `LDAP_URL` el login de directorio falla siempre.
- Flujo: `buscar_usuario` (filtro escapado por `LDAP_USER_ATTR`, por defecto `uid`) → `verificar_contrasena` → cuenta local por el `mail` del directorio.
- Sin `mail` no hay acceso: la cuenta nunca se busca por lo escrito.
- Cuenta nueva: rol `usuario`, `auth_source=ldap`, sin contraseña; existente: conserva el rol y el origen.
- Cuenta `local`, con contraseña local o desactivada: 401 único y aviso `ACCESO BLOQUEADO`; no se modifica (también en SSO).
- Correo normalizado (`strip().lower()`) y búsqueda sin distinguir mayúsculas, en directorio y SSO.
- Una cuenta `sso` entra por directorio y una `ldap` por SSO: Authelia usa el mismo OpenLDAP (requisitos de `mail` en `docs/operacion/ENTORNOS.md`).
- Nunca borra cuentas; todo fallo devuelve `MENSAJE_CREDENCIALES` y el motivo va a la auditoría.

### LDAP heredado (`auth_config`)
- Obsoleta desde FNC-043: la API ya no la edita y nada la lee; `ldap_pass` vacía (migración 0004).
- `validate_ldap_connection` retirada (FNC-043); `DEBUG_LDAP` pasó a `directory/depuracion.py`.
- `utils/test_ldap.py` y `utils/nexus_health.py`, que la importaban, se retiraron en FNC-028.

### Authelia (SSO por cabeceras)
- Nginx consulta Authelia (`auth_request`, comentado en la plantilla) y reinyecta `Remote-Email`, `Remote-Name`, `Remote-Groups`; antes borra esas cabeceras si vienen del cliente.
- El backend solo las acepta si `request.remote_addr` está en `TRUSTED_PROXIES` (por defecto loopback) y `AUTHELIA_ENABLED=true`.
- El rol no sale de los grupos (FNC-042, RF-04): cuenta nueva `usuario`; existente, conserva su rol. `AUTHELIA_GROUP_ADMIN` y `AUTHELIA_HEADER_GROUPS` obsoletas.

### SMTP y plantillas
- `resolve_smtp_settings()`: con `SMTP_FORCE_ENV=true` manda el entorno (y si falta `SMTP_SERVER` no envía); si no, manda la BD y el entorno es respaldo.
- `send_notification_by_slug(slug, correo, contexto)`: sustituye `{clave}` en asunto y cuerpo en una pasada (no es Jinja2), envía HTML o texto según `is_html`. `ENABLE_NOTIFICATIONS=false` corta todo envío. Recarga `.env` en cada envío (`load_dotenv(override=True)`).
- Escape (FNC-048, SEG-23): en plantillas HTML los valores pasan por `html.escape`; el asunto sale sin CR/LF; un valor no se vuelve a sustituir (`render_template_text`, `render_subject`).
- Avisos del gestor (`notifications/access_notifications.py`, FNC-048): una función por evento, llamada **después del commit** y dentro de `try`; nunca lanza (datos incompletos → log y `error`); si falla queda en el log y en auditoría `notificacion_fallida` (actor `sistema`). Interruptor `NOTIFY_ACCESS_EVENTS`. Envío síncrono hasta FNC-049 (ADR-003).

| Función | Plantilla | Destinatarios (activos, en un solo envío) |
|---|---|---|
| `notificar_solicitud_nueva(solicitante, plataforma, nivel, justificacion)` | `solicitud_nueva` | Admins (`admin_area`) del área de la plataforma con `pref_email_notifications` |
| `notificar_solicitud_aprobada(solicitante, plataforma, nivel)` | `solicitud_aprobada` | Solicitante, si tiene `pref_email_notifications` |
| `notificar_solicitud_rechazada(solicitante, plataforma, nivel, motivo)` | `solicitud_rechazada` | Solicitante, si tiene `pref_email_notifications` |
| `notificar_aprovisionamiento_fallido(usuario, plataforma, nivel, operacion)` | `aprovisionamiento_fallido` | Admins del área y superadmins con `pref_email_notifications` (P10, 2026-10-15) |

- Plantillas: migración `0003` (HTML, español, editables en Ajustes → Plantillas); variables en `CLAVES_POR_PLANTILLA`; enlace `{url}` = `BASE_URL`.
- Plantilla usada por el código: `usuario_creado` (alta por LDAP o SSO, si `NOTIFY_USER_CREATED` no es `false`), enviada por `avisar_usuario_creado` de `notifications/services.py` (FNC-030). Variables: `nombre`, `usuario`, `base_url`, `url`.
- `add_in_app_notification()` existe en servicios.

### Auditoría
- `add_audit_log(action, status, detail, user_override, module, target, *, target_user_id, area_id, platform_id, before, after, request_id, grant_id, as_system)`: lo posterior a `target` es opcional y por nombre (FNC-047). Si falla, solo imprime y hace rollback.
- `commit=False` (FNC-044): solo agrega el registro; quien llama confirma cambio y auditoría juntos (SEC-AUD-06) y un error se propaga.
- Actor: correo e id de la sesión; `sistema` (sin id) con `as_system=True`, sin sesión o fuera de una petición.
- `action`: un `Evento` de `audit/events.py` (catálogo del contrato `auditoria.md`) o el texto heredado.
- Textos recortados al largo de su columna (SEG-25); los eventos de sesión llevan el correo en `target`.
- IP (`audit/ip_cliente.py`): último salto de `X-Forwarded-For` solo si el origen está en `TRUSTED_PROXIES`; si no, `remote_addr`; `INTERNAL` fuera de petición. Sin `ProxyFix` global: cambiaría el `remote_addr` que valida el SSO.
- `before`/`after` sin contraseñas, hashes, tokens, cookies, cabeceras ni secretos (`audit/sanitizar.py`, SEC-AUD-05).
- Inmutable (`audit/inmutabilidad.py`): el ORM rechaza `UPDATE`/`DELETE` (por objeto y masivos) con `RegistroInmutable`; sin rutas de edición ni borrado; borrar usuario, área o plataforma deja la referencia en NULL.
- Migración `0002_auditoria_ampliada`.
- Se audita: accesos (local, directorio, SSO, fallidos, SSO rechazado), cierre de sesión, CRUD de áreas/plataformas/usuarios, configuración, SMTP, LDAP, respaldos, purgas, altas/bajas automáticas por LDAP y correos del gestor no enviados (`notificacion_fallida`, FNC-048).

## 6. Cómo arrancar en dev

```bash
cp .env.example .env          # rellenar credenciales (nunca commitear .env)
python3.11 -m venv venv       # o 3.12
venv/bin/pip install -r requirements.txt
venv/bin/alembic upgrade head # crea o actualiza el esquema (§7), antes de arrancar
venv/bin/python run.py        # API en el puerto 5001
```

- Con `DB_ENGINE=mysql` usa MySQL/MariaDB vía PyMySQL; con cualquier otro valor (o sin definir) usa **SQLite** en `nexus.db`.
- Redis es opcional para la API: si no responde, la app arranca igual y los trabajos de aprovisionamiento esperan al worker.
- **Worker de aprovisionamiento** (FNC-049), en otra terminal, con Redis local con contraseña:
  ```bash
  redis-server --requirepass "$REDIS_PASS"   # o el Redis del sistema con requirepass
  # REDIS_HOST, REDIS_PORT y REDIS_PASS en el .env (REDIS_HOST: nombre de host, no IP)
  FLASK_APP=run.py venv/bin/flask provisioning worker   # Ctrl+C: termina el intento y sale
  ```
  Sin `REDIS_PASS` o sin Redis, el comando sale con código 1 y el motivo.
- Sin Authelia: entra la cuenta de emergencia (`admin`) con el login local; otras cuentas locales solo con `APP_ENV=development` y `LOGIN_LOCAL_TODAS_LAS_CUENTAS=true` (ver `docs/operacion/ENTORNOS.md`, FNC-077).
- El frontend se arranca aparte (ver `docs/frontend/README.md`); su `rewrite` reenvía `/api/*` y `/auth/*` a este backend.
- Sin scripts sueltos: `scratch/` y `utils/` se retiraron en FNC-028 (31 archivos heredados de PSX5K). El esquema se gestiona con Alembic (§7). El primer superadmin y el reinicio de la cuenta de emergencia quedan para un comando Flask CLI de FNC-003 (fase 5); la prueba de SMTP es `POST /api/v1/smtp/test`; el SSO se activa con `AUTHELIA_ENABLED`.
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
  - `tests/test_proteccion_por_rol.py`: matriz ruta × rol (401/403/2xx), entradas inválidas (400) y RF-04 (sin `xfail` desde FNC-044).
  - `tests/test_alcance_por_area.py` (FNC-021): alcance por área con áreas A y B y 5 actores, y escalada con ids ajenos (SEG-05 y SEG-09 sin `xfail` desde FNC-044; queda el de FNC-015).
  - Roles y áreas administradas (FNC-044): `tests/users/test_roles_y_areas_administradas.py`.
  - Alta de cuentas en OpenLDAP (FNC-064): `tests/users/test_alta_directorio.py` (directorio simulado de `tests/directorio_falso.py`).
  - Contraseñas locales y cuenta de emergencia (FNC-077): `tests/users/test_contrasenas_locales.py`; `peticiones_auth.activar_login_local_de_todas(monkeypatch, entorno)`.
  - Alta, edición y baja de áreas por el admin (FNC-045): `tests/areas/test_alta_y_baja_por_admin.py`.
  - Ejecutor de aprovisionamiento (FNC-049): `tests/provisioning/` (encolado, reintentos, permanentes, reserva, idempotencia, saneo, proveedor LDAP sobre `MOCK_SYNC`, worker y comando). `conftest.py`: `cola_falsa` (cola RQ en el mismo proceso, como `is_async=False`, sin Redis), `proveedor_simulado`, `avisos`.
  - API de conectores (FNC-061): `tests/connectors/test_api.py` (solo superadmin, 404, 422 por campo, lista blanca, `409` sin conector o con accesos, auditoría, caché, prueba de conexión sin secretos) y 4 casos en la matriz.
  - Conectores (FNC-050): `tests/connectors/` (esquema sin secretos, credenciales y caché, configuración, validación, `noop` otorgar → revocar con el ejecutor, referencia inexistente, credencial fuera de bitácora, auditoría y logs, `tiene_conector`). `conftest.py`: `entorno_conector`, `conector_noop`, `crear_conector`.
  - Accesos otorgados (FNC-054): `tests/access/` (servicio, estados, P5, alcance, unicidad en BD, puntos de extensión y punta a punta con `DirectorioMock` y `cola_falsa`).
  - Plataformas (FNC-046): `tests/platforms/` (tipo, DN, derivación, avisos, 409, auditoría; regresión SEG-24).
  - Autenticación (FNC-022): `test_login_local.py`, `test_login_directorio.py`, `test_sso.py`, `test_sesion_y_logout.py`; 3 `xfail` con su tarea (FNC-006, 014; el de SEG-02 pasó a prueba normal en FNC-077); los 9 de FNC-002 y FNC-013 pasaron a pruebas normales en FNC-042.
  - `tests/directorio_falso.py`: `instalar_directorio(monkeypatch, variables=None, **config)` activa `LDAP_*` ficticias y conecta el cliente centralizado a `MOCK_SYNC` (personas, grupos, filtros recibidos); `config` crea `auth_config` (FNC-042).
  - Endpoints retirados (FNC-065): `tests/access/test_endpoints_retirados.py`.
  - Directorio (FNC-043): `tests/directory/test_api.py` (configuración, prueba, búsqueda y escape, modelo sin clave), `tests/directory/test_aislamiento.py` (SEC-LDAP-01/02), `tests/test_migracion_0004.py`. El `MOCK_SYNC` no compara valores escapados ni devuelve entradas con `sizeLimitExceeded`: esas pruebas revisan el filtro y el límite pedidos.
  - `tests/directory/conftest.py`: `directorio` / `crear_directorio(**LDAP_*)` usan `ldap3` `MOCK_SYNC` con el cliente centralizado; `tests/directory/test_tls.py` abre TLS real solo hacia `localhost`.
  - `tests/peticiones_auth.py`: `iniciar_sesion_api`, `usuario_en_sesion`, `hay_auditoria` (con `target=` para el correo).
  - Auditoría (FNC-047): `tests/audit/` (registro ampliado, inmutabilidad y regresión de SEG-25).
  - Servicios (FNC-023): `test_notificaciones.py`, `test_auditoria_crud.py`, `test_respaldo.py`, `test_secretos_en_respuestas.py`, `test_rutas_retiradas.py` (FNC-027), `test_csrf.py`, `test_arranque.py`, `test_cuerpo_validado.py` (FNC-119); 13 `xfail` con su tarea (lista en la ficha).
  - `tests/smtp_falso.py`: `instalar_smtp(monkeypatch)` simula `smtplib` (mensajes enviados, conexiones, logins, fallo con `.error`).
  - `test_arranque.py` llama `create_app()` sin overrides; `instance/` va a un directorio temporal.
  - SSO en pruebas: el cliente llega desde loopback (de confianza por defecto); otro origen se simula con `TRUSTED_PROXIES` y `REMOTE_ADDR` ficticios.
  - Línea base (FNC-028): `tests/test_linea_base_cubre_sql_heredadas.py` comprueba que `0001` ya incluye las columnas `pref_*` y no trae lo que quitaron 002 y 004.
  - `create_app(config_overrides=None)`: el parámetro opcional solo lo usan las pruebas; sin él no cambia nada.

## 7. Migraciones

Alembic 1.20.0 directo (ADR-002, FNC-039). Sin Flask-Migrate: `migrations/env.py` no llama a `create_app()`, así no corren `create_all()` ni el admin semilla.

- **URL:** la de la app (`construir_uri_bd()`, variables `DB_*` del entorno o del `.env`); nada en `alembic.ini`.
- **Otra cuenta para migrar** (SEC-CFG-09): exportar `DB_USER` y `DB_PASS` solo para el comando; el entorno manda sobre el `.env`. No dejar la contraseña en el historial de la shell: leerla con `read -s DB_PASS` o usar un archivo de entorno con permisos 600.
- **Modelos:** `env.py` importa todo `app/modules/*/models.py`; un módulo nuevo con `models.py` entra solo.
- **SQLite:** la ruta relativa `nexus.db` se resuelve en `instance/`, igual que Flask-SQLAlchemy.
- **`render_as_batch`:** activo, para que las migraciones también corran en SQLite (pruebas).

### Comandos (desde la raíz, con el venv)

| Para | Comando |
|---|---|
| Crear las tablas en una BD nueva y vacía | `venv/bin/alembic upgrade head` (**antes** del primer arranque de la app) |
| Aplicar las migraciones pendientes | `venv/bin/alembic upgrade head` |
| Ver la versión aplicada | `venv/bin/alembic current` |
| Ver si los modelos tienen cambios sin migración | `venv/bin/alembic check` |
| Crear una migración nueva | cambiar el modelo y `venv/bin/alembic revision --autogenerate -m "descripcion"`; revisar el archivo generado |
| Revertir la última | `venv/bin/alembic downgrade -1` |
| Ver el SQL sin aplicarlo (MySQL) | `venv/bin/alembic upgrade head --sql` |
| Marcar una BD existente como en la línea base | `venv/bin/alembic stamp 0001` |

### BD existente de NEXUS (creada con `create_all()` + SQL sueltos 001-004, retirados)
- Respaldo previo (`docs/operacion/RESPALDOS.md`).
- Confirmar que 001, 002 y 004 están aplicadas (columnas `pref_*` en `users`; sin `storage_stats`, `drive_activity` ni `access_requests`).
- `venv/bin/alembic stamp 0001`: registra la línea base sin tocar tablas.
- `venv/bin/alembic check`: si reporta diferencias, se abre una tarea con una migración que las corrija (no se edita `0001`).

### Convivencia con `create_all()`
- `create_all()` sigue en `create_app()` hasta FNC-003 (ADR-002); crea tablas que falten, nunca altera.
- Orden obligatorio: **migrar primero, arrancar después**. Si la app arrancó antes en una BD nueva, `upgrade` falla con "table already exists": usar `alembic stamp head` (las tablas ya coinciden con los modelos).
- Una migración que cree una tabla nueva falla si la app arrancó con ese modelo antes de migrar: en despliegues, `upgrade head` va antes de reiniciar el servicio (`docs/operacion/RELEASES.md`).

### Reglas para nuevas migraciones
- Una migración por tarea, en su rama; `alembic check` vacío antes del commit.
- Tablas nuevas de la fase 3 con prefijo `platform_access_*`; nunca `access_requests` (la borra 004). Excepción: `provisioning_jobs` y `provisioning_job_attempts` (0006, nombres de la ficha FNC-049).
- Cada migración con `downgrade()` real; si es irreversible, se dice en su docstring.
- Dos ramas con migraciones en paralelo: el integrador fusiona cabezas (`alembic merge heads`); la prueba `test_hay_una_sola_cabeza` lo exige.
- Pruebas: `tests/test_migraciones.py` (upgrade sobre SQLite vacío = modelos, autogenerate vacío, downgrade a `base`, una sola cabeza).

### Histórico: `utils/migrations/001-004` (retirados en FNC-028)
La línea base `0001` ya contiene su efecto (verificado con `tests/test_linea_base_cubre_sql_heredadas.py`); no hizo falta una migración `0010`. Siguen en el historial de git.

| Archivo | Qué hizo | Cobertura |
|---|---|---|
| `001_user_prefs.sql` | Columnas `pref_*` en `users` | `0001` las crea |
| `002_drop_drive.sql` | Quitó `storage_stats`, `drive_activity` y columnas de archivos de `platforms` | `0001` no las crea |
| `003_logo_to_db.py` | Datos, no esquema: pasaba el logo de archivo a data URI en `system_config` | Una sola vez, ya aplicada; hoy la API guarda el logo como data URI. Un logo heredado en ruta se vuelve a subir desde Ajustes |
| `004_drop_access_requests.sql` | Quitó la tabla huérfana `access_requests` | `0001` no la crea |

## 8. Deuda conocida

| # | Deuda | Dónde |
|---|---|---|
| 1 | Usuario administrador inicial creado en cada BD vacía con credenciales por defecto conocidas e impresas en consola. | `app/__init__.py` |
| 2 | `SECRET_KEY` tiene valor por defecto en código si falta la variable. | `app/__init__.py` |
| 3 | ~~Contraseña por defecto fija cuando el alta de usuario no la incluye.~~ Resuelta en FNC-077 (nace sin clave local). | `users/api.py` `create_user` |
| 4 | ~~IP literal como valor por defecto de `BASE_URL` en el correo de bienvenida LDAP~~ Resuelta en FNC-042 (vacío = enlace relativo). | `auth/services.py` |
| 5 | CSRF exento en todos los blueprints; la API depende solo de la cookie de sesión (SameSite por defecto del navegador). | `app/__init__.py` |
| 6 | Contraseña de SMTP guardada en claro en BD (la de LDAP se vació y quedó obsoleta en FNC-043). | `smtp_config` |
| 7 | ~~LDAP con TLS sin validar certificado (`CERT_NONE`)~~ Resuelta: login (FNC-042), prueba y búsqueda (FNC-043) usan el cliente validado. | — |
| 8 | ~~Borrado automático de la cuenta local si no aparece en el directorio~~ Resuelta en FNC-042. | `auth/services.py` |
| 9 | `run.py` usa `debug=True` y escucha en todas las interfaces; `PORT_APP` no se lee. | `run.py` |
| 10 | `DB_ENGINE` distinto de `mysql` cae a SQLite (no hay rama PostgreSQL aunque `psycopg2-binary` está en dependencias). | `app/__init__.py` |
| 11 | Dependencias sin versión fijada (`cryptography`, `ldap3`, `Flask-Mail`, `pandas`, `redis`, `gunicorn`, etc.); algunas sin uso aparente (`Flask-Mail`, `pexpect`, `openpyxl`, `xlrd`, `pandas`, `psycopg2-binary`). | `requirements.txt` |
| 12 | Redis conectado pero sin uso. | `app/utils/redis_client.py` |
| 13 | ~~`user_platforms` se edita sin efecto~~ Resuelta en FNC-065: endpoints en `410` y tabla obsoleta (P4: sus filas se descartan, sin migrar); borrado de la tabla en FNC-107. | `users/api.py`, `platforms/api.py` |
| 14 | `POST /notifications/read` marca como leídas las notificaciones globales para todos los usuarios. | `notifications/api.py` |
| 15 | Control de migraciones resuelto con Alembic (FNC-039). Pruebas del backend completas: suite base (FNC-019), protección por rol (FNC-020), alcance por área (FNC-021), autenticación (FNC-022) y servicios, respaldo, heredadas, CSRF y arranque (FNC-023). | — |
| 16 | ~~`purge_inactive_users` de `auth/services.py` duplicaba la purga de la API~~ Resuelta en FNC-030: la heredada se borró y la única vive en `users/services.py`. | `users/services.py`, `users/higiene_api.py` |
| 17 | ~~`utils/seed_users.py` usa roles que el código ya no reconoce~~ Resuelta en FNC-028: script borrado. | — |
| 18 | Mensajes de error que devuelven el texto de la excepción al cliente (LDAP, SMTP, respaldo). | `notifications/api.py`, `settings/respaldo_api.py` |
