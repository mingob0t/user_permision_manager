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
- **Creación de esquema:** el esquema se versiona con Alembic (§7). `create_app()` sigue ejecutando `db.create_all()` en cada arranque y, si no existe ningún usuario, crea un administrador inicial con credenciales por defecto conocidas (ver deuda).
- **URI de la BD:** `construir_uri_bd()` (`app/utils/uri_bd.py`) la arma desde `DB_*`; la usan `create_app()` y `migrations/env.py`.

### Estructura

```text
app/
├── __init__.py        # create_app(): config, extensiones, blueprints, create_all
├── authz.py           # Autorización centralizada: roles, alcance por área, decoradores
├── decorators.py      # Compatibilidad: reexporta decoradores de authz
├── utils/
│   ├── naming.py      # sanitize_display_name(): limpia nombres visibles (máx. 100)
│   ├── uri_bd.py      # construir_uri_bd(): URI de la BD desde DB_* (app y Alembic)
│   └── redis_client.py# Cliente Redis global (sin uso funcional)
└── modules/
    ├── api/           # API v1 que consume el frontend
    │   ├── routes.py  # Lectura: me, áreas, plataformas, favoritos, usuarios, stats, auditoría
    │   ├── crud.py    # Escritura: áreas, usuarios, preferencias, purga
    │   ├── admin.py   # Sistema (superadmin): portal, SMTP, plantillas, respaldo; notificaciones in-app
    │   ├── auth.py    # /api/v1/auth: contexto, SSO Authelia, login, logout
    │   └── helpers.py # error_response(), validation_error(), json_object(), is_id_list() y errores del contrato (FNC-044)
    ├── auth/          # Modelos User/AuthConfig (obsoleto) y login; rutas heredadas (redirigen/410)
    ├── directory/     # OpenLDAP: configuración LDAP_*, cliente, escritura, api.py (/auth-config, /directory/search; FNC-043); único que importa ldap3
    ├── core/          # Modelos Area/Platform; rutas heredadas
    ├── platforms/     # api.py (escritura de plataformas), validacion.py, grupos.py (DN), tipos.py, estado.py (puntos de extensión FNC-050/054) (FNC-046)
    ├── audit/         # Modelo AuditLog y add_audit_log(); rutas heredadas
    ├── notifications/ # Modelos SMTP/plantillas/in-app, servicios de correo y avisos del gestor (access_notifications.py); rutas heredadas
    ├── settings/      # Modelo SystemConfig; rutas heredadas
    ├── users/         # api.py (managed-areas), roles.py, areas_administradas.py, serializacion.py (FNC-044), correos.py (FNC-043); routes.py heredadas
    └── areas/         # Solo rutas heredadas
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

- **Alcance por fila:** `scoped_areas()`, `scoped_platforms()`, `scoped_users()` devuelven queries ya filtradas según el usuario. Para un admin de área, `scoped_users()` solo devuelve cuentas `usuario` de sus áreas (FNC-044); `GET /audit` le suma sus propios eventos.
- **Permisos sobre objetos:** `can_access_platform`, `can_manage_area`, `can_manage_platform`, `can_manage_user` (admin de área: solo rol `usuario` de sus áreas).
- **Roles asignables** (`users/roles.py`, FNC-044): superadmin `usuario` o `admin_area`; admin de área solo `usuario`; `administrador` nunca por la API.
- **Decoradores:** `admin_required` (solo superadmin), `any_admin_required` (superadmin o admin de área; la vista debe acotar con `scoped_*`), `area_admin_required('area_id')`, `platform_access_required`, `platform_manage_required`. Al denegar responden `403` JSON si la petición es de API.

## 3. Modelo de datos

Las tablas las crean las migraciones de Alembic (§7); `db.create_all()` sigue activo al arrancar. `utils/nexus_structure.sql` es un volcado parcial (no incluye `areas`, `platforms` ni las tablas de relación).

| Tabla | Modelo | Campos clave |
|---|---|---|
| `users` | `auth.models.User` | `id`, `email` (único; también guarda identificadores sin `@`, p. ej. el admin inicial), `nombre`, `password_hash` (nulo en LDAP), `role`, `auth_source` (`local` / `ldap` / `sso`), `is_active`, `created_at`, `last_login_at`, preferencias `pref_notifications`, `pref_email_notifications`, `pref_refresh_interval` (15–3600 s), `pref_tour_enabled` |
| `areas` | `core.models.Area` | `id`, `name` (único), `description`, `icon`, `color` (hex), `status` (`Activo` / otro) |
| `platforms` | `core.models.Platform` | `id`, `name`, `description` (obligatoria), `area_id` (FK obligatoria), `direct_link`, `icon`, `logo_url`, `bg_color`, `text_color`, `status`, `visits`, `created_at`; FNC-046 (0005): `integration_type` (`ldap`/`conector`), `ldap_group_user_dn`, `ldap_group_admin_dn` (512), `groups_status` (`ok`/`no_existe`/`sin_verificar`) |
| `user_areas` | tabla de relación | `user_id`, `area_id`: pertenencia de un usuario a un área |
| `area_admins` | tabla de relación | `user_id`, `area_id`: áreas que administra un `admin_area` |
| `user_platforms` | tabla de relación | `user_id`, `platform_id`: acceso explícito a plataforma (se edita, pero `scoped_platforms` **no** lo usa para filtrar) |
| `user_favorites` | tabla de relación | `user_id`, `platform_id` |
| `audit_logs` | `audit.models.AuditLog` | `timestamp`, `user` (correo o `sistema`, 255), `action` (150), `module`, `target` (255), `detail`, `ip_address`, `status` (`success`/`error`/`warning`/`info`); FNC-047: `actor_id`, `target_user_id`, `area_id`, `platform_id` (FK `SET NULL`), `before_state`/`after_state` (JSON), `request_id`, `grant_id`; índices por fecha, actor, usuario afectado, área y plataforma. Inmutable desde el ORM |
| `auth_config` | `auth.models.AuthConfig` | **Obsoleta** (FNC-043): nada la lee; solo viaja en el respaldo. `ldap_pass` vacía (migración 0004) y el modelo rechaza escribirla. Resto: `ldap_host`, `ldap_port`, `ldap_ssl`, `ldap_base_dn`, `ldap_user`, `ldap_user_attr`, `ldap_group_admin`, `ldap_group_user`, `ldap_role_mappings` |
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
| `POST /sso` | Pública; exige `AUTHELIA_ENABLED=true` y origen en `TRUSTED_PROXIES` | Crea o actualiza el usuario a partir de las cabeceras de Authelia (nuevo: rol `usuario`; existente: conserva su rol; `Remote-Groups` no se usa, FNC-042), inicia sesión y audita. Si es nuevo, envía la plantilla `usuario_creado`. |
| `POST /login` | Pública | `method=directory` → LDAP (`authenticate_user_ldap`); `method=local` → contraseña local. Audita éxitos y fallos (el motivo solo en la auditoría). Todo fallo, incluida la cuenta desactivada, responde 401 `Credenciales incorrectas.` (FNC-042). |
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
| `PUT /users/<id>/areas` | `any_admin_required` + `can_manage_user` (fuera de alcance → `404`) | Reasigna áreas dentro del alcance; conserva las que el solicitante no administra. Cuerpo no objeto o `area_ids` no lista de enteros → `400 cuerpo_invalido`. |
| `GET /stats` | Sesión (alcance) | Contadores, top 5 de visitas, plataformas por área; `users` solo para administradores. |
| `GET /audit?limit=` | Sesión (alcance) | Superadmin: todo; admin de área: eventos de sus usuarios; usuario: los propios. Máximo 500. Arreglo de `AuditEntry` con `actor`, `area`, `platform`, `target_user`, `before`, `after` (FNC-047); `page` y alcance por área llegan con FNC-060. |

### 4.3 Escritura — `app/modules/api/crud.py` (`/api/v1`)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `POST /areas` | `admin_required` | Crea área. |
| `PUT /areas/<id>` | `area_admin_required` | Edita área. |
| `DELETE /areas/<id>` | `admin_required` | Borra área; `409` si tiene plataformas. |
| `PUT /areas/<id>/users` | `area_admin_required` | Define los miembros del área dentro del alcance. |
| `POST /users` | `any_admin_required` | Alta de cuenta local (`auth_source` lo fija el servidor). Rol fuera de lo asignable → `403 rol_reservado`; `managed_area_ids`, `auth_source`, `password_hash` → `400 campo_no_permitido`. `admin` es identificador reservado. Si no llega contraseña, se asigna una por defecto (ver deuda). Un `admin_area` nace sin áreas administradas. |
| `PUT /users/<id>` | `any_admin_required` + `can_manage_user` (fuera de alcance → `404`) | Edita usuario. Mismas reglas de rol y campos; el rol actual reenviado se ignora; el propio → `403 operacion_propia`. Degradar borra las áreas administradas y audita `rol_cambiado`. Contraseña: superadmin o admin de área (cuentas `usuario` de sus áreas), solo cuentas `local` (si no, `400 campo_no_permitido`). |
| `DELETE /users/<id>` | `any_admin_required` + `can_manage_user` (fuera de alcance → `404`) | Borra usuario; no permite borrarse a sí mismo ni la cuenta maestra `admin`. |
| `PUT /users/<id>/platforms` | `any_admin_required` + `can_manage_user` (fuera de alcance → `404`) | Define `user_platforms` con plataformas en alcance. Cuerpo no válido → `400 cuerpo_invalido`. |
| `PUT /me/preferences` | Sesión | Guarda preferencias propias. |
| `GET /users/inactive?days=` | `admin_required` | Usuarios sin acceso en N días (mínimo `PURGE_MIN_DAYS` = 7), excluye superadmins. |
| `POST /users/purge` | `admin_required` | Elimina esos usuarios y audita. |

### 4.3.0 Plataformas — `app/modules/platforms/api.py` (`/api/v1`, FNC-046)

Contrato `docs/contratos/plataformas-integracion.md`. Respuesta de `POST`/`PUT`: `{"status", "platform", "warnings": []}`.

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `POST /platforms` | `any_admin_required`; área inexistente o ajena → `404` | Alta con lista blanca (`400 campo_no_permitido`); `name`, `description`, `area_id`, `integration_type` obligatorios (`422 validacion`). URL solo `https://`. `ldap`: DN bajo `LDAP_GROUPS_BASE_DN` o derivados de `LDAP_PLATFORM_GROUP_TEMPLATE`; sin directorio o sin DN → `422`; iguales → `409 grupos_iguales`. Audita `plataforma_creada` ("admin X dio de alta la plataforma Y") en la misma transacción. |
| `PUT /platforms/<id>` | `any_admin_required` + `can_manage_platform` (ajena → `404`) | Mismas reglas, campos parciales. DN solo superadmin (`403 dn_solo_superadmin`). Cambiar tipo, grupos o área con `accesos_vigentes > 0` → `409 plataforma_con_accesos`. Pasar a `conector` borra los DN. Audita `plataforma_editada` con antes/después de lo que cambió. |
| `DELETE /platforms/<id>` | `platform_manage_required` | Borra plataforma (movida de `crud.py` sin cambios). |
| `PUT /platforms/<id>/users` | `platform_manage_required` | Define `user_platforms` (movida sin cambios; se retira en FNC-065). |

- Grupos: existencia con `ClienteDirectorio.existe_dn`; no existe → aviso `grupo_no_existe` y `groups_status: no_existe`; directorio sin respuesta → `directorio_no_disponible` y `sin_verificar`. Nunca es error.
- `Platform.to_dict` agrega `integration_type`, los DN, `groups_status`, `has_connector` y `active_grants`; ya no expone `user_ids`. `GET /platforms` (`routes.py`) no cambia (FNC-063).
- Puntos de extensión en `platforms/estado.py`: `accesos_vigentes` (FNC-054) y `tiene_conector` (FNC-050), hoy `0`/`False`.

### 4.3.1 Cuentas — `app/modules/users/api.py` (`/api/v1`, FNC-044)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `PUT /users/<id>/managed-areas` | `admin_required` | Reemplaza `area_admins` de un `admin_area` con `{"area_ids": [...]}` (0–50, existentes, sin repetidos; si no → `422 validacion`). Destino sin rol `admin_area` → `409 rol_no_admin`. Audita `admin_asignado`/`admin_retirado` por área en la misma transacción. Responde `{"status": "success", "user": ManagedUser}`. |

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
| `GET /backup` | `admin_required` | Descarga ZIP `nexus_config.json` con portal, LDAP, SMTP (sin contraseñas), plantillas y usuarios locales con su hash. |
| `POST /backup` | `admin_required` | Restaura desde ese ZIP; solo agrega usuarios que no existan. |

### 4.4.1 Directorio — `app/modules/directory/api.py` (`/api/v1`, FNC-043)

| Método y ruta | Protección | Qué hace |
|---|---|---|
| `GET /auth-config` | `admin_required` | Configuración efectiva de `LDAP_*`: `active`, `editable: false`, `config` (sin contraseña ni ruta de CA), `origins` (`env`/`default`) y `variables`; `error: configuracion_invalida` si no carga. No conecta. |
| `PUT /auth-config` | `admin_required` | Sin campos editables (ADR-004): cualquier campo → `400 campo_no_permitido`; `{}` → 200 con la configuración. |
| `POST /auth-config/test` | `admin_required` | Bind de la cuenta de servicio con la configuración efectiva; cuerpo con campos → `400`; inactivo → `409 directorio_no_configurado`; fallo → `503 directorio_no_disponible` genérico. Audita `PRUEBA LDAP`. |
| `GET /directory/search?q=` | `admin_required` | `buscar_personas` (atributo `LDAP_USER_ATTR`, `mail`, `cn`, `displayName`; filtro escapado); `q` de 2–64 caracteres (`400 parametro_invalido`); máx. 50; marca `exists`. `409`/`503` como la prueba. |

### 4.5 Rutas heredadas

Los blueprints `auth` (`/auth`), `core` (`/`), `audit` (`/audit`), `settings` (`/settings`), `notifications`, `users_module` (`/admin`) y `areas_module` (`/admin/areas`) ya no procesan datos: las rutas de pantalla redirigen a `FRONTEND_URL + <ruta>` y las de datos responden `410` con el endpoint que las reemplaza.

## 5. Integraciones

### Cliente OpenLDAP centralizado (`app/modules/directory/`, FNC-040)
- Activo solo con `LDAP_URL`; la configuración (`LDAP_*`, ver `VARIABLES.md`) se valida en `create_app()` y, si falla, la app no arranca.
- TLS obligatorio: `ldaps://` o `ldap://` + StartTLS antes del bind; `CERT_REQUIRED`, nombre del host verificado, CA de `LDAP_CA_CERT_FILE` o del sistema.
- `ClienteDirectorio`: `conexion_servicio(solo_lectura=True)` (escritura solo desde `writer.py`), `buscar_usuario()`, `grupos_de_usuario()` (búsqueda bajo `LDAP_GROUPS_BASE_DN`, sin overlay `memberOf`), `existe_dn()`, `verificar_contrasena()` (bind de la persona; vacía = `False` sin conectar; FNC-042), `buscar_personas(texto, limite)` (FNC-043).
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
- Sin llamadores hasta FNC-049 (ejecutor) y FNC-064 (alta de cuentas); que el grupo pertenezca a una plataforma lo valida el llamador.

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
- `utils/test_ldap.py` y `utils/nexus_health.py` aún la importan (ya fallaban: la llamaban sin argumentos); limpieza en FNC-028.

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
- Plantilla usada por el código: `usuario_creado` (alta por LDAP o SSO, si `NOTIFY_USER_CREATED` no es `false`). Variables: `nombre`, `usuario`, `base_url`, `url`.
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
  - `tests/test_proteccion_por_rol.py`: matriz ruta × rol (401/403/2xx), entradas inválidas (400) y RF-04 (sin `xfail` desde FNC-044).
  - `tests/test_alcance_por_area.py` (FNC-021): alcance por área con áreas A y B y 5 actores, y escalada con ids ajenos (SEG-05 y SEG-09 sin `xfail` desde FNC-044; queda el de FNC-015).
  - Roles y áreas administradas (FNC-044): `tests/users/test_roles_y_areas_administradas.py`.
  - Plataformas (FNC-046): `tests/platforms/` (tipo, DN, derivación, avisos, 409, auditoría; regresión SEG-24).
  - Autenticación (FNC-022): `test_login_local.py`, `test_login_directorio.py`, `test_sso.py`, `test_sesion_y_logout.py`; 4 `xfail` con su tarea (FNC-003, 006, 014); los 9 de FNC-002 y FNC-013 pasaron a pruebas normales en FNC-042.
  - `tests/directorio_falso.py`: `instalar_directorio(monkeypatch, variables=None, **config)` activa `LDAP_*` ficticias y conecta el cliente centralizado a `MOCK_SYNC` (personas, grupos, filtros recibidos); `config` crea `auth_config` (FNC-042).
  - Directorio (FNC-043): `tests/directory/test_api.py` (configuración, prueba, búsqueda y escape, modelo sin clave), `tests/directory/test_aislamiento.py` (SEC-LDAP-01/02), `tests/test_migracion_0004.py`. El `MOCK_SYNC` no compara valores escapados ni devuelve entradas con `sizeLimitExceeded`: esas pruebas revisan el filtro y el límite pedidos.
  - `tests/directory/conftest.py`: `directorio` / `crear_directorio(**LDAP_*)` usan `ldap3` `MOCK_SYNC` con el cliente centralizado; `tests/directory/test_tls.py` abre TLS real solo hacia `localhost`.
  - `tests/peticiones_auth.py`: `iniciar_sesion_api`, `usuario_en_sesion`, `hay_auditoria` (con `target=` para el correo).
  - Auditoría (FNC-047): `tests/audit/` (registro ampliado, inmutabilidad y regresión de SEG-25).
  - Servicios (FNC-023): `test_notificaciones.py`, `test_auditoria_crud.py`, `test_respaldo.py`, `test_secretos_en_respuestas.py`, `test_rutas_heredadas.py`, `test_csrf.py`, `test_arranque.py`; 13 `xfail` con su tarea (lista en la ficha).
  - `tests/smtp_falso.py`: `instalar_smtp(monkeypatch)` simula `smtplib` (mensajes enviados, conexiones, logins, fallo con `.error`).
  - `test_arranque.py` llama `create_app()` sin overrides; `instance/` va a un directorio temporal.
  - SSO en pruebas: el cliente llega desde loopback (de confianza por defecto); otro origen se simula con `TRUSTED_PROXIES` y `REMOTE_ADDR` ficticios.
  - `utils/test_*.py` y `scratch/test_*.py` son scripts manuales con conexiones reales: pytest no los recoge.
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

### BD existente de NEXUS (creada con `create_all()` + `utils/migrations/`)
- Respaldo previo (`docs/operacion/RESPALDOS.md`).
- Confirmar que 001, 002 y 004 están aplicadas (columnas `pref_*` en `users`; sin `storage_stats`, `drive_activity` ni `access_requests`).
- `venv/bin/alembic stamp 0001`: registra la línea base sin tocar tablas.
- `venv/bin/alembic check`: si reporta diferencias, se abre una tarea con una migración que las corrija (no se edita `0001`).

### Convivencia con `create_all()`
- `create_all()` sigue en `create_app()` hasta FNC-003/FNC-028 (ADR-002); crea tablas que falten, nunca altera.
- Orden obligatorio: **migrar primero, arrancar después**. Si la app arrancó antes en una BD nueva, `upgrade` falla con "table already exists": usar `alembic stamp head` (las tablas ya coinciden con los modelos).
- Una migración que cree una tabla nueva falla si la app arrancó con ese modelo antes de migrar: en despliegues, `upgrade head` va antes de reiniciar el servicio (`docs/operacion/RELEASES.md`).

### Reglas para nuevas migraciones
- Una migración por tarea, en su rama; `alembic check` vacío antes del commit.
- Tablas nuevas de la fase 3 con prefijo `platform_access_*`; nunca `access_requests` (la borra 004).
- Cada migración con `downgrade()` real; si es irreversible, se dice en su docstring.
- Dos ramas con migraciones en paralelo: el integrador fusiona cabezas (`alembic merge heads`); la prueba `test_hay_una_sola_cabeza` lo exige.
- Pruebas: `tests/test_migraciones.py` (upgrade sobre SQLite vacío = modelos, autogenerate vacío, downgrade a `base`, una sola cabeza).

### Histórico (`utils/migrations/`, ya no se usan)
Quedan como referencia; la línea base `0001` ya refleja su resultado. FNC-028 decide su retiro.

| Archivo | Tipo | Qué hizo |
|---|---|---|
| `001_user_prefs.sql` | SQL (MySQL) | Agregó las columnas `pref_*` a `users`. |
| `002_drop_drive.sql` | SQL (MySQL) | Eliminó `storage_stats`, `drive_activity` y columnas de archivos de `platforms`. Irreversible sin respaldo. |
| `003_logo_to_db.py` | Python | Pasa el logo del portal de archivo a data URI en `system_config` (datos, no esquema). Idempotente. |
| `004_drop_access_requests.sql` | SQL (MySQL) | Eliminó la tabla huérfana `access_requests`. |

## 8. Deuda conocida

| # | Deuda | Dónde |
|---|---|---|
| 1 | Usuario administrador inicial creado en cada BD vacía con credenciales por defecto conocidas e impresas en consola. | `app/__init__.py` |
| 2 | `SECRET_KEY` tiene valor por defecto en código si falta la variable. | `app/__init__.py` |
| 3 | Contraseña por defecto fija cuando el alta de usuario no la incluye. | `api/crud.py` `create_user` |
| 4 | ~~IP literal como valor por defecto de `BASE_URL` en el correo de bienvenida LDAP~~ Resuelta en FNC-042 (vacío = enlace relativo). | `auth/services.py` |
| 5 | CSRF exento en todos los blueprints; la API depende solo de la cookie de sesión (SameSite por defecto del navegador). | `app/__init__.py` |
| 6 | Contraseña de SMTP guardada en claro en BD (la de LDAP se vació y quedó obsoleta en FNC-043). | `smtp_config` |
| 7 | ~~LDAP con TLS sin validar certificado (`CERT_NONE`)~~ Resuelta: login (FNC-042), prueba y búsqueda (FNC-043) usan el cliente validado. | — |
| 8 | ~~Borrado automático de la cuenta local si no aparece en el directorio~~ Resuelta en FNC-042. | `auth/services.py` |
| 9 | `run.py` usa `debug=True` y escucha en todas las interfaces; `PORT_APP` no se lee. | `run.py` |
| 10 | `DB_ENGINE` distinto de `mysql` cae a SQLite (no hay rama PostgreSQL aunque `psycopg2-binary` está en dependencias). | `app/__init__.py` |
| 11 | Dependencias sin versión fijada (`cryptography`, `ldap3`, `Flask-Mail`, `pandas`, `redis`, `gunicorn`, etc.); algunas sin uso aparente (`Flask-Mail`, `pexpect`, `openpyxl`, `xlrd`, `pandas`, `psycopg2-binary`). | `requirements.txt` |
| 12 | Redis conectado pero sin uso. | `app/utils/redis_client.py` |
| 13 | `user_platforms` se edita pero no restringe la visibilidad. | `authz.scoped_platforms` |
| 14 | `POST /notifications/read` marca como leídas las notificaciones globales para todos los usuarios. | `api/admin.py` |
| 15 | Control de migraciones resuelto con Alembic (FNC-039). Pruebas del backend completas: suite base (FNC-019), protección por rol (FNC-020), alcance por área (FNC-021), autenticación (FNC-022) y servicios, respaldo, heredadas, CSRF y arranque (FNC-023). | — |
| 16 | `purge_inactive_users` de `auth/services.py` devuelve un mensaje de error de LDAP no relacionado; la API usa su propia implementación en `crud.py` (duplicado). | `auth/services.py`, `api/crud.py` |
| 17 | `utils/seed_users.py` usa roles `admin`/`user` que el código ya no reconoce. | `utils/seed_users.py` |
| 18 | Mensajes de error que devuelven el texto de la excepción al cliente (LDAP, SMTP, respaldo). | `api/admin.py` |
