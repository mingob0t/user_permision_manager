# Auditoría de seguridad inicial: proyecto completo (2026-10-13)

- **Modo:** proyecto (auditoría completa).
- **Rama:** `fnc/FNC-001-incorporacion-metodo` (base: clon de NEXUS, commit `0bf71e8`).
- **Tarea:** FNC-001, diagnóstico inicial. No se modificó código.
- **Auditor:** `auditor-seguridad`.
- **Método:** análisis estático de `app/`, `frontend/src/`, `deploy/`, `utils/`, `run.py`, `requirements.txt`, `.env.example`, `.gitignore` y del historial de git, más `validar_proyecto.py`. El comportamiento de Next.js se contrastó con el código de `next@15.5.7` instalado en otro proyecto local, que es la misma versión. **No se levantó la aplicación ni se hizo ninguna petición** (no hubo autorización para pruebas locales), así que ningún hallazgo se reprodujo en ejecución. Los escenarios se basan en la lectura del código.
- **No se leyeron** `.env`, `secret.key` ni llaves. Los posibles secretos del historial se citan solo por su ubicación.

## 1. Resumen por severidad

| Severidad | Cantidad | IDs |
|---|---|---|
| Crítica | 4 | SEG-20261013-01 a 04 |
| Alta | 4 | SEG-20261013-05 a 08 |
| Media | 12 | SEG-20261013-09 a 20 |
| Baja | 9 | SEG-20261013-21 a 29 |

Comparación con la auditoría anterior: **no existe** auditoría de seguridad previa en `docs/seguridad/auditorias/`. La auditoría de estandarización del mismo día (`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`, H-02, H-07 y H-19) ya señalaba las credenciales por defecto, la IP en el código y la `SECRET_KEY` por defecto, y las escalaba a esta auditoría. Aquí se confirman y se clasifican.

### Riesgos sospechados por el solicitante: resultado de la verificación

| Riesgo sospechado | Resultado | ID |
|---|---|---|
| Usuario semilla `admin/admin123` | **Confirmado**, Crítica. También está en `utils/nexus_structure.sql` y en `utils/emergency_reset.py` | 03 |
| Contraseña por defecto `nexus123` | **Confirmado y peor de lo previsto**, Crítica: la interfaz importa a los usuarios del directorio sin contraseña, así que todos reciben `nexus123` | 02 |
| Contraseñas SMTP y bind LDAP en claro en la BD | **Confirmado**, Alta | 08 |
| `Tls(validate=CERT_NONE)` en LDAP | **Confirmado**, Media (3 sitios) | 13 |
| El login LDAP borra la cuenta local si no existe en LDAP | **Confirmado y explotable sin autenticación**, Crítica | 01 |
| Confianza en `Remote-*` (TRUSTED_PROXIES) | **Hay una vía de evasión**: nginx no limpia las cabeceras en `location /` y el rewrite de Next.js reenvía a Flask desde loopback. Crítica cuando el SSO está activo | 04 |
| `_check_role` permite a `admin_area` asignar `admin_area` | **Confirmado**, Media (incumple RF-04). Además, un `admin_area` puede tomar la cuenta de otro `admin_area` (Alta) | 09, 05 |
| `GET /settings` solo con sesión | **No es hallazgo**: solo devuelve la identidad visual del portal (nombre, colores y logo), sin secretos | — |
| CSRF en la API | **Confirmado**, Alta: hay endpoints que cambian estado y se pueden invocar con un formulario entre sitios, entre ellos la importación del respaldo, que crea un superadmin | 06 |
| Reemplazo de variables en las plantillas de correo | **Confirmado**, Baja hoy (sin escape HTML). Sube cuando existan F-NOT-01 y F-SOL-02 | 23 |

## 2. Hallazgos

### Críticos

#### SEG-20261013-01: Cualquiera puede borrar cuentas locales, incluida la del superadmin, sin autenticarse
- **Categoría:** autenticación (purga y sincronización).
- **Ubicación:** `app/modules/auth/services.py:53-70`, invocado desde `app/modules/api/auth.py:138-140`.
- **Escenario:** con el directorio configurado (`auth_config.ldap_host` definido), un atacante anónimo envía `POST /api/v1/auth/login` con `{"email":"admin","password":"x","method":"directory"}`. La búsqueda `(<ldap_user_attr>=admin)` no encuentra nada, así que el código busca `User.email == "admin"` y lo **borra** (`db.session.delete(local_user)`). Hace lo mismo con cualquier cuenta cuyo correo no coincida con el atributo del directorio, y por defecto `ldap_user_attr` es `sAMAccountName` (o `uid`), no el correo. Así, `juan@empresa.com` se borra aunque `uid=juan` exista. Con un bucle sobre correos se vacía la tabla de usuarios, junto con sus áreas, accesos y favoritos.
- **Impacto:** borrado de datos ajenos sin autenticación y denegación de servicio del portal. También borra al superadmin local.
- **Corrección:** quitar el "protocolo de purga" del flujo de login. La conciliación con el directorio, si se quiere, debe ser un proceso administrativo, con vista previa, que nunca borre cuentas `local` y que nunca dependa de lo que escribe quien intenta entrar. Ver también la SEG-12 (filtro sin escapar).
- **Tarea:** propuesta T-01.

#### SEG-20261013-02: Todo usuario dado de alta sin contraseña (incluidos los importados del directorio) acepta `nexus123` en el login local
- **Categoría:** autenticación y credenciales por defecto.
- **Ubicación:** `app/modules/api/crud.py:283`; `frontend/src/components/users-list.tsx:89-91` y `:166-170` (el alta desde el directorio deja `password: ''` con `auth_source: 'ldap'`); `app/modules/api/auth.py:152-160` (el login local acepta a cualquier usuario con hash, sin mirar `auth_source`).
- **Escenario:** el superadmin o un admin de área importa a una persona desde la búsqueda del directorio, que es el flujo normal. La cuenta queda con `password_hash = hash('nexus123')`. Un atacante anónimo que conoce o adivina el correo envía `POST /api/v1/auth/login` con `{"email":"<correo>","password":"nexus123","method":"local"}` y entra como esa persona. Si se importó como `admin_area` o `administrador`, obtiene ese rol. El login LDAP posterior no borra el hash (`services.py:107-110`), así que la puerta queda abierta para siempre.
- **Impacto:** toma de cuentas sin privilegios, potencialmente de administradores.
- **Corrección:** no asignar nunca una contraseña por defecto. Las cuentas `ldap`/`sso` se guardan con `password_hash = NULL`, y las `local` se crean con una contraseña obligatoria o con un enlace de activación de un solo uso. El login local solo se acepta para `auth_source == 'local'`. Además, hay que anular los hashes existentes de las cuentas no locales (migración).
- **Tarea:** propuesta T-02.

#### SEG-20261013-03: El superadmin semilla `admin` / `admin123` se crea automáticamente
- **Categoría:** credenciales por defecto.
- **Ubicación:** `app/__init__.py:160-167` (y además imprime la contraseña en consola); `utils/nexus_structure.sql:176-177` (hash de `admin123`); `utils/emergency_reset.py:33-39`; `utils/seed_users.py:31` (otra contraseña fija para usuarios semilla).
- **Escenario:** en un despliegue nuevo, la primera vez que arranca Gunicorn crea `admin/admin123` con rol `administrador`. Cualquiera que llegue al login entra como superadmin con `method: local` mientras nadie la cambie, y no hay nada que obligue a cambiarla. Lo mismo ocurre si se carga `nexus_structure.sql` o si se ejecuta el reset de emergencia.
- **Impacto:** escalada a superadmin sin privilegios: configuración de LDAP y SMTP, todas las áreas, todos los usuarios y el respaldo con hashes.
- **Corrección:** quitar la siembra automática. Crear el primer superadmin con un comando explícito (por ejemplo `flask crear-superadmin`) que pida la contraseña o la tome de Vaultwarden. Quitar el `INSERT` del SQL y la contraseña fija del reset. Si se conserva una cuenta local de emergencia, exigir cambio de contraseña en el primer acceso.
- **Tarea:** propuesta T-02.

#### SEG-20261013-04: Suplantación por SSO: las cabeceras `Remote-*` del cliente llegan a Flask desde loopback a través de Next.js
- **Categoría:** SSO por cabeceras.
- **Ubicación:** `deploy/nginx.conf.tmpl:70-72` (limpieza de `Remote-*` a nivel de `server`) y `:115-120` (`location /` define sus propios `proxy_set_header`); `frontend/next.config.ts:15-20` (rewrites `/api/:path*` y `/auth/:path*` hacia `127.0.0.1:5001`, activos también en producción con `output: standalone`); `app/modules/api/auth.py:27-34` y `:70-107`.
- **Por qué ocurre:**
  1. En nginx, `proxy_set_header` se hereda del nivel superior **solo si** el bloque actual no define ninguno. `location /` define `Upgrade` y `Connection`, así que no hereda los `Remote-* ""` (tampoco `X-Forwarded-For` ni `Host`). Las cabeceras del cliente pasan intactas a Next.js.
  2. Las rutas de Next.js **no distinguen mayúsculas** por defecto: en `next@15.5.7`, `experimental.caseSensitiveRoutes: false` (`server/config-shared.js`) y se pasa a `getPathMatch(..., { sensitive: false })` en `server/lib/router-utils/filesystem.js`. En cambio, `location /api/` de nginx sí las distingue.
  3. Next.js reenvía todas las cabeceras con `http-proxy` y la conexión a Flask sale de `127.0.0.1`, que está en `TRUSTED_PROXIES` por defecto.
- **Escenario:** con `AUTHELIA_ENABLED=true` (OB-01 lo hace obligatorio), un atacante, o cualquier usuario que ya pasó por Authelia si `auth_request` se activa a nivel de `server`, envía `POST /API/v1/auth/sso` con `Remote-Email: <correo del superadmin>` y `Remote-Groups: administrador`. nginx lo manda a `location /` sin limpiar cabeceras, Next.js lo reescribe a `http://127.0.0.1:5001/api/v1/auth/sso` y Flask lo acepta como si viniera del proxy. Resultado: sesión como cualquier usuario y, si no existe, la crea con rol `administrador`.
- **Impacto:** toma de cualquier cuenta y escalada a superadmin.
- **Estado:** cadena verificada por lectura de código (nginx y Next 15.5.7). **No se reprodujo** en local. Hoy está latente porque `.env.example` trae `AUTHELIA_ENABLED=false`, y se vuelve explotable en cuanto se active el SSO. `docs/operacion/ENTORNOS.md` afirma que "nginx las borra si las manda el cliente", lo cual es incorrecto para `location /`.
- **Corrección:**
  - **infra:** repetir `proxy_set_header Remote-Email/Name/Groups ""` (y las de `auth_request_set`) dentro de **cada** `location`, o mejor, con un `include` común. Hacer que nginx responda 404 a `/api` y `/auth` sin importar las mayúsculas (`location ~* ^/(api|auth)(/|$)`), para que nada que parezca API llegue a Next.js.
  - **web:** dejar los `rewrites` solo en desarrollo (`process.env.NODE_ENV !== 'production'`).
  - **backend:** no confiar solo en la IP de origen; exigir además una cabecera con un secreto compartido que solo nginx inyecta, o un socket o puerto dedicado al proxy.
- **Tarea:** propuestas T-03 (infra), T-04 (web) y T-05 (backend).

### Altos

#### SEG-20261013-05: Un admin de área puede tomar la cuenta de otro admin de área y heredar sus áreas
- **Categoría:** autorización y escalada de privilegios.
- **Ubicación:** `app/authz.py:398-414` (`can_manage_user` solo excluye al superadmin y compara las áreas de **membresía** del destino); `app/modules/api/crud.py:295-318` (cambio de contraseña, rol e `is_active`) y `:332-349` (borrado).
- **Escenario:** A administra el área X; B administra X y además Y. `create_user` hace que los `admin_area` sean miembros de sus áreas (`crud.py:284-286`), así que B es miembro de X. A envía `PUT /api/v1/users/<id de B>` con `{"password":"Nueva!"}` y luego `POST /api/v1/auth/login` con `{"email":"<B>","password":"Nueva!","method":"local"}`, y entra como B con acceso a Y. Puede hacer lo mismo con cuentas `ldap` o `sso` de su área: les crea una contraseña local y entra como esos usuarios, que pueden pertenecer a otras áreas. También puede degradar o borrar a B.
- **Impacto:** escalada horizontal entre tenants y toma de cuentas.
- **Corrección:** un `admin_area` no administra a otros `admin_area`. Nadie salvo el propio usuario o el superadmin cambia una contraseña local, y nunca la de cuentas `ldap`/`sso`. Agregar pruebas de permisos por rol (RNF-05).
- **Tarea:** propuesta T-06.

#### SEG-20261013-06: CSRF: la API está exenta y la cookie no tiene `SameSite`; un formulario externo puede crear un superadmin
- **Categoría:** CSRF.
- **Ubicación:** `app/__init__.py:134-138` (`csrf.exempt` de todos los blueprints de la API) y `:44-49` (sin `SESSION_COOKIE_SAMESITE` ni `REMEMBER_COOKIE_SAMESITE`); `app/modules/api/admin.py:474-572` (`POST /backup`, multipart); `app/modules/api/crud.py:456-480` (`POST /users/purge`, sin cuerpo usa `days=30`).
- **Escenario:** el superadmin, con sesión abierta, visita una página del atacante. Puede ser cualquier sitio externo en navegadores sin `Lax` por defecto (Firefox) o, en cualquier navegador, una plataforma interna del mismo dominio registrable con un XSS, porque es *same-site*. La página envía un formulario `multipart/form-data` (el archivo se fija con `DataTransfer`) a `/api/v1/backup` con un ZIP cuyo `nexus_config.json` contiene `{"users":[{"email":"x@atacante","password_hash":"<hash conocido>","role":"administrador"}]}`. La importación crea la cuenta y el atacante entra como superadmin. Variante destructiva: un formulario vacío a `/api/v1/users/purge` borra todas las cuentas sin actividad en 30 días. Los endpoints que leen JSON (`get_json` sin `force`) no son alcanzables con formularios simples, y no hay CORS, así que el riesgo se concentra en multipart y en los POST sin cuerpo.
- **Impacto:** escalada a superadmin o borrado masivo, con una sola visita de un administrador.
- **Corrección:** exigir un token CSRF (cabecera `X-CSRFToken` con Flask-WTF, o doble envío) en todo método que no sea GET, o como mínimo verificar `Origin`/`Sec-Fetch-Site`. Además, `SESSION_COOKIE_SAMESITE='Strict'` (o `Lax`), `Secure` y `HttpOnly` explícitos. La importación debe validar que `role` no sea `administrador` y pedir confirmación.
- **Tarea:** propuesta T-07.

#### SEG-20261013-07: `SECRET_KEY` con valor por defecto en el código
- **Categoría:** secretos y configuración.
- **Ubicación:** `app/__init__.py:34` (`os.getenv('SECRET_KEY', 'nexus-premium-secret-key')`).
- **Escenario:** si el despliegue arranca sin `SECRET_KEY` (por un error en `.env`, o en staging o prod sin cargar el secreto desde Vaultwarden), la clave es pública porque está en el repo. El atacante firma una cookie `nexus_session` con `_user_id=1` usando `itsdangerous` y entra como el superadmin. `preflight.sh` lo avisa, pero la aplicación arranca de todos modos.
- **Impacto:** toma de cualquier cuenta sin credenciales.
- **Corrección:** abortar el arranque si `SECRET_KEY` (y las demás variables de seguridad) falta o tiene un valor conocido. Registrar el cambio en `docs/configuracion/HISTORIAL.md`.
- **Tarea:** propuesta T-08.

#### SEG-20261013-08: Contraseñas de SMTP y de bind LDAP guardadas en claro en la base de datos
- **Categoría:** secretos y criptografía (RNF-03).
- **Ubicación:** `app/modules/notifications/models.py:251` (`password` en claro, con el comentario "Should be encrypted in production"); `app/modules/auth/models.py:298` (`ldap_pass`); escritura en `app/modules/api/admin.py:199-200` y `:368-369`.
- **Escenario:** quien tenga lectura de la BD obtiene ambas contraseñas: un respaldo de MySQL (`docs/operacion/RESPALDOS.md`), una cuenta SQL de solo lectura o una inyección futura. Con el bind LDAP, que con F-ACC-01 necesitará **escritura** en grupos de OpenLDAP, puede agregarse a cualquier grupo y conseguir acceso a todas las plataformas.
- **Impacto:** exposición de credenciales de servicio con alto privilegio.
- **Corrección:** las credenciales de servicio salen del entorno o de Vaultwarden (como ya hace `SMTP_FORCE_ENV`), no de la BD. Si se deben poder editar desde la interfaz, se cifran con una clave que vive fuera de la BD. Ver también la SEG-22.
- **Tarea:** propuesta T-09.

### Medios

| ID | Categoría | Ubicación | Escenario | Corrección | Tarea |
|---|---|---|---|---|---|
| SEG-20261013-09 | Autorización (RF-04) | `app/modules/api/crud.py:236-252`, `:268`, `:304-311`, `:320-324` | Un `admin_area` crea con `POST /api/v1/users` `{"role":"admin_area"}`, o promueve con `PUT`, a un cómplice como admin de sus áreas. El alcance queda acotado a sus áreas, pero viola "solo el superadmin crea o eleva admins" | `_check_role`: solo el superadmin asigna `admin_area` o `administrador` | T-06 |
| SEG-20261013-10 | Derivación de rol | `app/modules/api/auth.py:41-48` y `:103-104`; `app/modules/auth/services.py:117-139`; `.env.example:29` | Todo miembro de un grupo listado en `AUTHELIA_GROUP_ADMIN`, o cuyo DN de grupo **contenga** como subcadena el texto de `ldap_group_admin` o de un mapeo (`m_group in group`), se vuelve `administrador` en cada login. Por ejemplo, `ldap_group_admin="admin"` coincide con `cn=sysadmins-lectura,...`. Contradice "una sola persona" superadmin | Comparar el DN exacto (normalizado), no permitir que el directorio asigne `administrador`, y conservar el rol local asignado por el superadmin | T-10 |
| SEG-20261013-11 | Autenticación | `app/modules/api/auth.py:126-166` | Sin límite de intentos: fuerza bruta contra `method:local` (por ejemplo sobre `admin`) o contra el directorio, que además puede bloquear cuentas de LDAP | Límite por IP y por cuenta (Redis ya está disponible), con retardo progresivo y registro | T-11 |
| SEG-20261013-12 | Inyección LDAP y fuga de información | `app/modules/auth/services.py:53` (filtro sin escapar), `:70` y `:80` (mensajes distintos), `:167` y `:170` (`str(e)`); `app/modules/api/auth.py:147-150` | Un anónimo envía `email:"a*"`: "Contraseña LDAP incorrecta" frente a "Usuario no encontrado" funciona como oráculo para enumerar todo el directorio carácter por carácter. Los errores de LDAP y de BD llegan textuales al cliente | Escapar con `ldap3.utils.conv.escape_filter_chars` (ya existe `_escape_ldap_filter` en `admin.py:579`), mensaje único y errores solo al log | T-01 |
| SEG-20261013-13 | TLS | `app/modules/auth/services.py:36`, `:211`; `app/modules/api/admin.py:611` | `Tls(validate=CERT_NONE)`: quien esté en la red entre el backend y OpenLDAP suplanta al servidor y captura el bind de servicio y la contraseña de cada usuario que inicia sesión. Con `ldap_ssl=false` todo viaja en claro (sin StartTLS) | `CERT_REQUIRED` con una CA configurable, y LDAPS o StartTLS obligatorios. Centralizar la conexión LDAP en una sola función | T-12 |
| SEG-20261013-14 | Sesión | `app/__init__.py:47-53`, `:98-106`; `app/modules/api/auth.py:107`, `:143`, `:157` | La sesión dura 7 días y siempre se usa `remember=True` (cookie de 365 días, sin `Secure`). Desactivar a un usuario no lo saca: `load_user` no comprueba `is_active` y la cookie firmada sigue siendo válida. Una cookie robada sirve durante un año | `load_user` devuelve `None` si `is_active` es falso. `REMEMBER_COOKIE_DURATION` corto o sin *remember*, `Secure`, `SameSite` y un contador de versión de sesión para revocarla | T-07 |
| SEG-20261013-15 | Cabeceras y TLS | `deploy/nginx.conf.tmpl:51-58`; `frontend/next.config.ts` | Sin CSP, HSTS, `X-Frame-Options` ni `X-Content-Type-Options`: las pantallas de administración se pueden enmarcar (*clickjacking* sobre "Purgar" o "Eliminar"). Los certificados están comentados y no hay redirección de HTTP a HTTPS, aunque `install.sh` abre `http` en firewalld | Bloque de cabeceras en nginx, `ssl_protocols TLSv1.2 TLSv1.3` y un `server` en el puerto 80 que solo redirija | T-03 |
| SEG-20261013-16 | IDOR o fuga entre tenants | `app/modules/api/routes.py:430-440` | El admin del área X ve **todos** los registros de auditoría de cualquier usuario que pertenezca a X, también los de lo que hizo en el área Y (por ejemplo, si es admin de Y) | Filtrar la auditoría por área afectada (F-AUD-01/04: área y plataforma como columnas) | T-13 |
| SEG-20261013-17 | Exportación con datos sensibles | `app/modules/api/admin.py:440-457` y `:549-564` | El ZIP de respaldo contiene los `password_hash` de las cuentas locales y se descarga en el equipo del administrador. Si se filtra, permite descifrado *offline*. La importación acepta cualquier `role` | Excluir los hashes (o cifrar el paquete) y no restaurar roles privilegiados sin confirmación | T-09 |
| SEG-20261013-18 | Modo debug | `run.py:6` | `python run.py` levanta el depurador de Werkzeug en `0.0.0.0` con `debug=True`. Si alguien lo usa en un servidor (`docs/operacion/ENTORNOS.md` lo documenta como forma de arrancar en dev), cualquiera en la red alcanza la consola, que solo protege un PIN, y además salta Gunicorn y nginx | `debug` y `host` desde variables con valores seguros (`127.0.0.1`, `False`) | T-08 |
| SEG-20261013-19 | Dependencias | `frontend/package.json` (`next 15.5.7`) | Next 15.5.7 corrige el RCE de RSC de diciembre de 2025, pero hubo avisos posteriores (DoS y exposición de código de Server Functions) corregidos en versiones 15.5.x más altas. **Sin confirmar**: `npm audit` requiere consultar el registro externo y no se ejecutó | Ejecutar `npm audit` y `pip-audit` en CI y actualizar a la última 15.5.x | T-14 |
| SEG-20261013-20 | Secretos en el historial de git | commit `24b12b5`: `scratch/api_example.py` (`API_TOKEN = "nexu…"`) y `migrate_portafolio.py` (`S_PASS = '…'`), borrados después en `a1ecbbe` y `731fc73` | Quien clone el repo recupera esos valores con `git show`. No se pudo determinar si son reales (el control de credenciales bloqueó su caracterización, como corresponde) | Que el dueño confirme si son reales. Si lo son, rotarlos y valorar limpiar el historial antes de publicar el repo | T-15 |

### Bajos

| ID | Categoría | Ubicación | Observación y escenario | Corrección | Tarea |
|---|---|---|---|---|---|
| SEG-20261013-21 | Fuga de información | `app/modules/api/admin.py:243`, `:404`, `:637`; `app/modules/auth/services.py:232` | `str(exc)` devuelto al cliente en las pruebas de SMTP y LDAP y en la búsqueda del directorio. Solo lo ve el superadmin, pero puede incluir hosts y DN internos | Mensaje genérico y detalle al log | T-16 |
| SEG-20261013-22 | Secretos | `app/modules/api/admin.py:226-233`, `:396-402` | Las pruebas de SMTP y LDAP combinan el host del payload con la contraseña guardada: se puede enviar la credencial a un host arbitrario. Solo el superadmin, y sin vía CSRF porque usan JSON | Si cambia el host, exigir que se reescriba la contraseña | T-09 |
| SEG-20261013-23 | Inyección HTML en correo | `app/modules/notifications/services.py:219-222` | Los valores del contexto (nombre de `Remote-Name` o `displayName`) se insertan sin escape en plantillas HTML. Hoy el correo solo le llega al propio usuario. Con F-NOT-01 (la justificación del solicitante llegará a los admins) sirve para *phishing* desde el remitente corporativo | `html.escape` de los valores cuando `is_html` | T-16 |
| SEG-20261013-24 | Validación de URL | `app/modules/api/crud.py:139-142`, `:158-168`; `frontend/src/components/platform-card.tsx:108` | `direct_link` y `logo_url` aceptan cualquier esquema. Hoy React 19.2 bloquea `javascript:`, pero la defensa depende del framework | Aceptar solo `https://` (y `http://` si se justifica) en el backend | T-16 |
| SEG-20261013-25 | Auditoría (no repudio) | `app/modules/audit/services.py:400-404`; `app/modules/audit/models.py:431` | La IP registrada siempre es la del proxy (`127.0.0.1`), porque no hay `ProxyFix`. `action` es `String(50)`: un login fallido con un correo de más de 34 caracteres hace fallar el INSERT en MySQL estricto y el intento no queda registrado | `ProxyFix(x_for=1)` acotado al proxy de confianza, y `action` corta con el correo en `target` | T-13 |
| SEG-20261013-26 | Lineamientos (IPs y hosts) | `app/modules/auth/services.py:152` (IP privada como valor por defecto de `BASE_URL`); `.env.example:24-25` (host real del Authelia corporativo), `:31` (`DEBUG_AUTH=true`, sin uso), `:3` (`FLASK_ENV=development`) | Revela topología interna y contradice RNF-02 | Quitar el valor por defecto y usar un marcador en el ejemplo | T-16 |
| SEG-20261013-27 | Dependencias | `requirements.txt:6-16` | `cryptography`, `ldap3`, `gunicorn`, `redis` y otras sin fijar. `pexpect`, `pandas`, `xlrd`, `openpyxl`, `psycopg2-binary` y `Flask-Mail` sin uso en `app/`, lo que agranda la superficie | Fijar versiones y quitar lo que no se usa | T-14 |
| SEG-20261013-28 | Privacidad | `docs/operacion/RETENCION.md` (tabla vacía); `.claude/seudonimizacion.json` (`"activo": false`) | El portal guarda correos, nombres e IPs (auditoría) sin retención definida, y la purga de cuentas no se aplica a la auditoría | Definir la retención (LFPDPPP) y activar la seudonimización para correos y hosts | T-17 |
| SEG-20261013-29 | Despliegue | `app/__init__.py:95`; `deploy/nginx.conf.tmpl:58` | Redis sin contraseña por defecto (`REDIS_PASS` no está en `.env.example`) y `client_max_body_size 64m` frente a un logo de 512 KB y un ZIP de respaldo pequeño (la importación descomprime en memoria sin límite: posible *zip bomb*, solo para el superadmin) | Contraseña de Redis obligatoria si se usa; límite de 2 MB y comprobar el tamaño descomprimido | T-16 |

## 3. Lo que se revisó y se consideró correcto
- `scoped_*` y los decoradores de `app/authz.py`: el usuario normal no alcanza áreas ni plataformas ajenas. No se encontró IDOR para el rol `usuario` en `routes.py`, `crud.py` ni `admin.py`.
- Los endpoints de configuración (`/smtp`, `/auth-config`, `/templates`, `/backup`, `/directory/search`, `/users/purge`) llevan `@admin_required`, y las contraseñas no se devuelven en `to_dict()`.
- La búsqueda en el directorio escapa el filtro (`admin.py:579-588`).
- No hay `dangerouslySetInnerHTML`, `innerHTML` ni `eval` en `frontend/src`. El SVG del logo se muestra con `<img>`, sin ejecución de script.
- No hay `subprocess`, `os.system` ni `pexpect` en `app/`. Las consultas usan el ORM, sin SQL armado con texto.
- `.gitignore` cubre `.env`, llaves, `*.db` y respaldos. No hay archivos de secretos versionados. `nexus.db` aparece en el historial pero **vacío** (0 bytes). `validar_proyecto.py` da 0 errores.
- Gunicorn y Next.js escuchan solo en loopback. systemd tiene `NoNewPrivileges`, `ProtectSystem=strict` y corre con un usuario sin privilegios.
- No hay CORS habilitado.

## 4. Fuera del análisis
- No hubo ejecución local ni pruebas dinámicas (sin autorización). Hacen falta pruebas de regresión que primero fallen para la SEG-01, 02, 04, 05 y 06.
- Ni `npm audit` ni `pip-audit` se ejecutaron (requieren consultar registros externos), ni `bandit` ni `semgrep` (no están instalados).
- `utils/` y `scratch/` se revisaron solo en lo relativo a credenciales. `install.sh` y `preflight.sh`, solo en lo relativo a secretos y permisos.
- La configuración real de Authelia, OpenLDAP, MySQL y Redis de los servidores (no está en el repo). Los entornos de staging y prod no están definidos.
- Estilos y accesibilidad (corresponden a otros auditores).

## 5. Recomendaciones de endurecimiento
1. Una suite de pruebas de permisos por rol y endpoint (RNF-05) que cubra superadmin, admin_area y usuario, incluidos los cruces entre áreas.
2. Centralizar la conexión LDAP (hoy hay tres) con TLS validado, escape de filtros y errores genéricos antes de F-ACC-01, que añadirá escritura.
3. Diseñar los conectores (F-CON-01) para que nunca construyan comandos SSH ni SQL con texto del usuario, y que tomen sus credenciales de Vaultwarden en tiempo de ejecución.
4. Auditoría inmutable: sin endpoints de borrado, y con la IP real del cliente y el área afectada.
5. Activar MFA en Authelia para el superadmin y los admins (punto abierto en los requerimientos).

## 6. Tareas propuestas (no registradas en el tablero; las crea el orquestador)

| Ref. | Título | Plataforma | Prioridad | Hallazgos |
|---|---|---|---|---|
| T-01 | Login de directorio seguro: quitar la purga, escapar el filtro y unificar los mensajes | backend | Crítica | 01, 12 |
| T-02 | Eliminar credenciales por defecto y crear el primer superadmin con un comando explícito | backend | Crítica | 02, 03 |
| T-03 | nginx: limpiar `Remote-*` en todas las `location`, bloquear `/api` y `/auth` sin distinguir mayúsculas, TLS y cabeceras de seguridad | infra | Crítica | 04, 15 |
| T-04 | Next.js: rewrites solo en desarrollo | web | Crítica | 04 |
| T-05 | SSO: autenticar al proxy con un secreto compartido además de la IP | backend | Alta | 04 |
| T-06 | Alcance del admin de área sobre cuentas (no gestionar otros admins ni contraseñas no locales; solo el superadmin asigna `admin_area`) | backend | Alta | 05, 09 |
| T-07 | CSRF en la API y endurecimiento de la sesión (SameSite, Secure, remember, revocación al desactivar) | backend | Alta | 06, 14 |
| T-08 | Arranque seguro: `SECRET_KEY` y variables de seguridad obligatorias, sin debug ni 0.0.0.0 | backend | Alta | 07, 18 |
| T-09 | Secretos de servicio fuera de la BD; respaldo sin hashes ni roles privilegiados | backend | Alta | 08, 17, 22 |
| T-10 | Derivación de rol desde el directorio con DN exacto y un solo superadmin | backend | Media | 10 |
| T-11 | Límite de intentos en el login | backend | Media | 11 |
| T-12 | LDAP con TLS validado y conexión centralizada | backend | Media | 13 |
| T-13 | Auditoría por área e IP real del cliente | backend | Media | 16, 25 |
| T-14 | Auditoría de dependencias (npm audit y pip-audit), fijar versiones y quitar las que no se usan | infra | Media | 19, 27 |
| T-15 | Revisar y rotar los posibles secretos del historial de git | infra | Media | 20 |
| T-16 | Higiene: errores genéricos, escape en correos, validación de URLs, IP y hosts en código y ejemplo, límites de carga | backend | Baja | 21, 23, 24, 26, 29 |
| T-17 | Retención de datos personales y seudonimización | infra | Baja | 28 |
