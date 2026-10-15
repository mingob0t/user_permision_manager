# Catálogo de reutilización

> Actualizado en la auditoría inicial 2026-10-13 (FNC-001). Lista lo que **ya existe y debe reutilizarse**, y al final los duplicados conocidos que deben converger en una sola versión.

## Elementos reutilizables existentes

| Elemento | Tipo | Dónde vive | Para qué | Usado en |
|---|---|---|---|---|
| `Card`, `PanelHeader`, `StatTile`, `Spinner`, `ErrorNote`, `EmptyNote`, `Badge` | Componentes React | `frontend/src/components/ui.tsx:10-105` | Contenedor, KPI, estados de carga, error y vacío, insignias (`nx-badge-<tono>`) | Todas las pantallas |
| `Field`, `TextInput`, `TextArea`, `Select`, `Checkbox`, `Button` | Componentes de formulario | `frontend/src/components/form.tsx:13-95` | Campos y botones estándar | areas, users, platform-admin, settings |
| `Modal` | Componente | `frontend/src/components/form.tsx:96` | Diálogo con bloqueo de scroll y footer | areas-list, users-list, platform-admin |
| `ConfirmDialog` | Componente | `frontend/src/components/form.tsx:162` | Confirmación de acciones destructivas | areas, users, platform-admin, notifications |
| `useAsync` | Hook | `frontend/src/lib/use-async.ts:17` | Carga con `loading/error/data/reload` | Todas las listas |
| `api`, `ApiError` | Cliente HTTP | `frontend/src/lib/api.ts:23,69` | Único punto de `fetch` a `/api/v1` (salvo backup, ver duplicado D-07) | Todo el frontend |
| Tipos de la API | Tipos TS | `frontend/src/lib/types.ts` | Contrato de datos | Todo el frontend |
| `SessionProvider`, `useSession` | Contexto | `frontend/src/components/session-provider.tsx:31,67` | Sesión y rol | `app-shell` y pantallas |
| `AppShell` | Layout | `frontend/src/components/app-shell.tsx` | Cabecera, navegación y guarda de sesión | Todas las páginas |
| Tokens de color y temas | CSS | `frontend/src/styles/tokens.css` (claro `:51`, oscuro `:271` y `:207`) | Única fuente de colores | `tailwind.config.ts` |
| Decoradores de permisos (`admin_required`, `any_admin_required`, `area_admin_required`, `platform_manage_required`, `platform_access_required`) | Decoradores Flask | `app/authz.py` | Reglas de acceso por rol y área | `app/modules/api/*` |
| `scoped_areas`, `scoped_users`, `can_manage_area`, `can_manage_user`, `is_admin` | Funciones | `app/authz.py` | Alcance multitenant por área | `crud.py`, `routes.py` |
| `add_audit_log` | Servicio | `app/modules/audit/services.py` | Única forma de registrar auditoría; desde FNC-047 acepta usuario afectado, área, plataforma, antes/después y `as_system`; `commit=False` (FNC-044) para auditar en la misma transacción | 33 llamadas en `app/` y `users/` |
| `error_response` | Función | `app/modules/api/helpers.py` | Error estándar con `code` y `fields` (contratos) | `crud.py` (`_error`), `users/api.py` |
| `normalized_role` | Función | `app/authz.py` | Rol en minúsculas de cualquier cuenta | `users/` |
| `roles_asignables`, `rol_asignable`, `campos_no_permitidos`, `cambiar_rol` | Funciones | `app/modules/users/roles.py` | Reglas de rol de cuentas y degradación auditada (FNC-044) | `crud.py` |
| `usuario_gestionado` | Serializador | `app/modules/users/serializacion.py` | Forma `ManagedUser` de los contratos | `GET /users`, `users/api.py` |
| `Evento`, `ACTOR_SISTEMA` | Catálogo | `app/modules/audit/events.py` | Valores de `action` del gestor de accesos (contrato `auditoria.md`) | Tareas de la fase 3 |
| `limpiar_detalle` | Utilidad | `app/modules/audit/sanitizar.py` | Quita datos sensibles de antes/después (SEC-AUD-05) | `add_audit_log` |
| `sanitize_display_name` | Función | `app/utils/naming.py` | Normalizar nombres | `crud.py` |
| `redis_registry` | Cliente | `app/utils/redis_client.py` | Registro Redis | `app/__init__.py:93` |
| `ClienteDirectorio`, `escapar_filtro`, `escapar_valor_dn`, `ErrorDirectorio` | Cliente | `app/modules/directory/ldap_client.py` | Única conexión a OpenLDAP (TLS validado, espera, escape); todo uso nuevo de `ldap3` pasa por aquí | (sin llamadores hasta FNC-041/042/043) |
| `cargar_configuracion`, `validar_al_arrancar` | Configuración | `app/modules/directory/configuracion.py` | Configuración del directorio desde `LDAP_*` (ADR-004) | `app/__init__.py`, `ldap_client.py` |
| `construir_uri_bd` | Función | `app/utils/uri_bd.py` | URI de la BD desde `DB_*` | `app/__init__.py`, `migrations/env.py` |
| `send_notification_by_slug` | Servicio | `app/modules/notifications/services.py:191` | Envío de correo por plantilla | auth, SSO, admin |
| `_validate_logo`, `MAX_LOGO_BYTES` | Función/constante | `app/modules/api/admin.py:46,51` | Validar logo (data URI) | settings |
| Fixtures de pruebas (`app`, `client`, `cliente_como`, `cliente_de_rol`, `cliente_admin`, `cliente_admin_area`, `cliente_usuario`) | Fixtures pytest | `tests/conftest.py` | App con BD temporal y clientes con sesión por rol, sin servicios externos | `tests/` |
| `crear_area`, `crear_plataforma`, `crear_usuario`, `crear_usuario_de_rol` | Fábricas de pruebas | `tests/fabricas.py` | Datos de prueba por rol | `tests/` |
| `CASOS`, `crear_escenario`, `crear_actor`, `publica`/`con_sesion`/`administradores`/`solo_superadmin` | Matriz de protección | `tests/matriz_proteccion.py` | Código esperado por rol de cada ruta /api/v1; todo endpoint nuevo agrega aquí su caso | `tests/test_proteccion_por_rol.py`, `tests/test_guardia_rutas.py` |
| `instalar_directorio`, `DirectorioFalso` | Doble de pruebas | `tests/directorio_falso.py` | Simular `ldap3` en el login por directorio, sin red | `tests/test_login_directorio.py` |
| `DirectorioMock`, `directorio`, `crear_directorio` | Doble de pruebas | `tests/directory/conftest.py` | `ldap3` `MOCK_SYNC` para el cliente del directorio, sin red | `tests/directory/` |
| `iniciar_sesion_api`, `usuario_en_sesion`, `hay_auditoria` | Utilidades de pruebas | `tests/peticiones_auth.py` | Login real por API y comprobaciones de sesión y auditoría (`hay_auditoria(..., target=)` desde FNC-047) | `tests/test_login_*.py`, `tests/test_sso.py`, `tests/test_sesion_y_logout.py` |
| `instalar_smtp`, `SmtpFalso` | Doble de pruebas | `tests/smtp_falso.py` | Simular `smtplib` en notificaciones, sin red | `tests/test_notificaciones.py` |
| `parseColor`, `componer`, `razonContraste`, `MIN_TEXTO`, `MIN_NO_TEXTO` | Utilidades de pruebas | `frontend/tests/utils/wcag.ts` | Medir contraste WCAG | `frontend/tests/accesibilidad/` |
| `cargarContextos`, `resolver` | Utilidades de pruebas | `frontend/tests/utils/tokens-css.ts` | Leer los tokens de cada tema de `tokens.css` | `frontend/tests/accesibilidad/` |
| `scripts/lineamientos/comun.py`, `reglas.py` | Utilidades de control | `scripts/lineamientos/` | Controles pre-commit del método | `.githooks/pre-commit` |

## Duplicados conocidos (deben converger)

| Id | Qué se repite | Ubicaciones | Versión única propuesta |
|---|---|---|---|
| D-01 | `_moved()` (410 Gone) | `app/modules/areas/routes.py:14`, `notifications/routes.py:21`, `auth/routes.py:22`, `users/routes.py:15` | Eliminar con los blueprints heredados (ver informe H-01) |
| D-02 | `_frontend(path)` / lectura de `FRONTEND_URL` | `settings/routes.py:16`, `notifications/routes.py:17`, `auth/routes.py:17`, `areas/routes.py:21`, `audit/routes.py:16`, `users/routes.py:22`, `core/routes.py:16`, `app/__init__.py:88` | Se elimina con D-01; si queda uno, `app/config.py` |
| D-03 | `_payload()` y `_error()` | `app/modules/api/crud.py:23,27`; `admin.py:25,29` | `app/modules/api/helpers.py` (`json_payload`, `error_response`); `error_response` creado y usado por `crud._error` (FNC-044); falta `admin.py` y `json_payload` |
| D-04 | Aviso "usuario creado" (con `NOTIFY_USER_CREATED`/`BASE_URL`) | `app/modules/api/auth.py:111-121`; `app/modules/auth/services.py:151-158` | Función única en `notifications/services.py` |
| D-05 | Purga de usuarios inactivos | `app/modules/auth/services.py:172` (heredada, con criterio distinto) y `app/modules/api/crud.py:415-435` | La de `crud.py` (considera nulos) movida a `app/modules/users/services.py` |
| D-06 | Conexión LDAP (`Server`/`Connection`/`Tls`) | `app/modules/auth/services.py:42,213`; `app/modules/api/admin.py:607-614` | `app/modules/directory/ldap_client.py` (creado en FNC-040; migran los llamadores FNC-042 y FNC-043) |
| D-07 | `fetch` directo en `api.ts` | `frontend/src/lib/api.ts:41,199,212` | Un solo `request()` con soporte de blobs |
| D-08 | Botón "Eliminar" en línea (`rounded px-2 py-1 text-xs text-red-600 hover:bg-red-500/10 dark:text-red-300`) | `areas-list.tsx:200`, `platform-admin.tsx:277`, `users-list.tsx:526` | Variante `danger` de `Button` o clase `nx-btn-danger` |
| D-09 | Clase de entrada de texto/selector | `audit-log.tsx:47`, `platform-catalog.tsx:50,58` (y `TextInput` en `form.tsx` ya existe) | Reutilizar `TextInput`/`Select` |
| D-10 | Encabezado y estructura de tabla | `audit-log.tsx:64-65`, `platform-admin.tsx:219-220`, y listas de users/areas | Componente `DataTable` |
| D-11 | Colores de estado (`emerald/red/amber`) con `dark:` | `settings-panel.tsx:17,189,377,617`, `notifications-list.tsx:16-18`, `platform-card.tsx:66`, `platform-admin.tsx:202` | Tonos de `Badge`/mensajes por token |
| D-12 | Color por defecto `#6366f1` | `crud.py:51,165`, `core/models.py:10,47,69`, `routes.py:93`, `platform-admin.tsx:17,137`, `areas-list.tsx:30,86`, `dashboard.tsx:79` | Constante en backend y token en frontend |
| D-13 | Capa de modal duplicada en CSS | `components.css:1551-1621` y `global.css:204-335` (`nexus-modal`, `modal-*`) | Ninguna: ambas son código muerto (el `Modal` usa Tailwind) |
| D-14 | Scripts de BD con la misma cadena de conexión | `scratch/list_dbs.py:5`, `cross_db_search_v2.py:8`, `multi_fix_db.py:8` | Borrar `scratch/` |
| D-15 | Páginas `page.tsx` con la misma estructura | `frontend/src/app/*/page.tsx` (10 archivos, 5 líneas útiles) | Aceptable: patrón de Next.js |
| D-16 | Definición de "color literal" | `frontend/tests/accesibilidad/colores-literales.test.ts:16-25` (hex, rgb/hsl y paleta Tailwind); `scripts/lineamientos/reglas.py:21-23` (hex y rgb/hsl) | Fines distintos (tope en repo vs. bloqueo en pre-commit); mantener alineadas al cambiar una |
