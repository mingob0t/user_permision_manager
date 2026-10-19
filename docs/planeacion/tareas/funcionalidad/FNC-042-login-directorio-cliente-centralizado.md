# FNC-042 — Login por directorio sobre el cliente centralizado, sin purga de cuentas y sin elevar rol desde LDAP

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auth |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Inicio** | 2026-10-15 |
| **Finalizada** | 2026-10-18 |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push (worktree `pokemon-wt-042`) |
| **Rama** | `fnc/FNC-042-login-directorio` |
| **Commits / PR** | `6332bdd` [FNC-042] (local, sin push ni PR) + commit de registro del hash |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autenticación y rol) |

## Contexto
- `authenticate_user_ldap` (`app/modules/auth/services.py`) abre su propia conexión sin validar TLS, usa `sAMAccountName`, construye el filtro sin escapar (SEG-12), borra la cuenta local si no aparece en el directorio (SEG-01) y deriva `administrador` por subcadena del DN de grupo (SEG-10)
- Con OpenLDAP como fuente de verdad y "solo el superadmin eleva" (RF-04), el login tiene que pasar al cliente nuevo y dejar de elevar roles
- Requerimientos: F-USR-01, RF-04, OB-01

## Objetivo
- Migrar el login de directorio y la derivación de rol de LDAP y SSO al cliente de FNC-040: el directorio autentica, pero el rol lo asigna solo el superadmin en el portal; ninguna cuenta se borra por no aparecer

## Alcance
- **Incluye:**
  - `authenticate_user_ldap` usa `app/modules/directory`; filtro escapado y mensaje único para usuario inexistente o contraseña incorrecta
  - Se elimina el "protocolo de purga" del login
  - Rol: una cuenta nueva por LDAP o SSO entra como `usuario`; el directorio y `AUTHELIA_GROUP_ADMIN` ya no asignan `administrador` ni `admin_area`; se conserva el rol asignado en el portal
  - Un solo superadmin (comprobación al asignar, coordinada con FNC-044)
  - Pruebas de regresión que primero fallan para SEG-01, SEG-10 y SEG-12
- **No incluye:**
  - Secreto compartido con el proxy (FNC-006)
  - Límite de intentos (FNC-014)
  - CSRF y sesión (FNC-008)
  - Credenciales por defecto `admin/admin123` (FNC-003)

## Hallazgos de seguridad que absorbe
- **FNC-002** completo (SEG-01, SEG-12).
- **FNC-012** (resto: login migrado al cliente con TLS validado).
- **FNC-013** completo (SEG-10).
- No absorbe FNC-006, FNC-008 ni FNC-014 aunque estén en el mismo módulo `auth`: tocan otras funciones. Si el dueño interpreta la regla por módulo completo (pregunta P13), se agregan aquí.

## Archivos previstos
- `app/modules/auth/services.py`
- `app/modules/api/auth.py` (`/sso` y `/login`)
- `app/modules/directory/ldap_client.py` (solo se agrega `verificar_contrasena`)
- `tests/directorio_falso.py`, `tests/test_login_directorio.py`, `tests/test_sso.py`, `tests/test_login_local.py`
- `tests/directory/test_verificar_contrasena.py`

## Reutilización
- `app/modules/directory/ldap_client.py` (FNC-040)
- `add_audit_log` ampliado (FNC-047)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `authenticate_user_ldap` | Servicio | `POST /api/v1/auth/login` (`utils/test_ldap.py` usa solo `validate_ldap_connection`, sin cambios) | Pruebas de login |
| Derivación de rol SSO | Regla de autorización | `POST /api/v1/auth/sso`; todas las pantallas que dependen de `/me.permissions` | Pruebas SSO; pantallas: validar el dueño |
| `AuthConfig.ldap_group_admin`, `ldap_role_mappings` | Configuración en BD | Pestaña Directorio de Ajustes (`settings-panel.tsx`): se siguen guardando pero el login ya no los usa | Pendiente (FNC-043/DIS-023) |
| `ClienteDirectorio.verificar_contrasena` (nuevo, solo agregado) | Método | Login; FNC-041/043 pueden reutilizarlo | Pruebas `tests/directory/test_verificar_contrasena.py` |
| `MENSAJE_CREDENCIALES` (nuevo) | Constante | Login local y de directorio (`api/auth.py`) | Pruebas de login |
| `tests/directorio_falso.py` (`instalar_directorio`, firma compatible) | Doble de pruebas | `test_login_directorio.py`, `test_notificaciones.py` | Suite completa |
| `AUTHELIA_GROUP_ADMIN`, `AUTHELIA_HEADER_GROUPS` (obsoletas) | Variables | Solo `api/auth.py`; `deploy/nginx.conf.tmpl` sigue limpiando `Remote-Groups` (sin cambio) | Pruebas SSO |

### Salida real de `impacto.py` (2026-10-15, tras las correcciones del revisor)
- 16 nombres (el revisor contó 17 en su corrida; `AUTHELIA_ENABLED` ya no aparece); todos homónimos o sin cambio de contrato:
  - `BASE_URL`, `NOTIFY_USER_CREATED`: variables leídas en `auth/services.py`; solo cambia el valor por defecto de `BASE_URL` (IP → vacío)
  - `ConexionFalsa`, `__enter__`, `__exit__`, `__init__`, `buscar`, `conexion`, `search`, `agregar`: métodos del doble viejo/nuevo de `tests/directorio_falso.py`; coinciden en nombre con `smtp_falso.py`, `matriz_proteccion.py`, `admin.py`, frontend, etc.
  - `bind`, `start_tls`: métodos de las conexiones espía de `tests/directory/test_verificar_contrasena.py`; homónimos de los de `ldap3` usados en `configuracion.py`, `test_ldap_client.py` y `test_tls.py`
  - `persona`: fixture local de `test_verificar_contrasena.py`; homónimo del método `DirectorioMock.persona` de `tests/directory/conftest.py`, que no cambió
  - `existe_dn`: sin cambios; aparece por el contexto del diff en `ldap_client.py`
  - `instalar_directorio`: misma firma (más `variables=`); `test_notificaciones.py` pasa sin cambios
  - `login`: la vista `/api/v1/auth/login` ahora responde 401 único en todo fallo (directorio y local, incluida la cuenta desactivada); el frontend no depende del texto ni del 403; los otros usos son homónimos

## Variables y configuración
- `AUTHELIA_GROUP_ADMIN` deja de asignar rol: marcar como *obsoleta* en `VARIABLES.md` con fecha y motivo (RF-04).

## Criterios de aceptación
- [x] Login con doble `MOCK_SYNC`: entra con atributo `uid` (`test_login_de_directorio_crea_usuario_sombra`, `test_busqueda_usa_el_atributo_uid_por_defecto`); OpenLDAP real no verificado
- [x] Una cuenta local cuyo correo no está en el directorio sigue existiendo tras un login de directorio fallido (`test_login_fallido_no_borra_cuentas_locales`, antes xfail)
- [x] Un miembro de un grupo "admin" del directorio entra como `usuario` si el portal no lo elevó (`test_directorio_no_asigna_administrador`, `test_mapeo_de_grupo_exacto_ya_no_asigna_el_rol`)
- [x] Respuesta idéntica para usuario inexistente y contraseña incorrecta, e igual a la del login local (`test_mensaje_uniforme_en_los_fallos`, `test_fallo_de_directorio_responde_igual_que_el_login_local`)
- [ ] Criterios comunes backend (FNC-037): pruebas, servicios, errores genéricos, variables e impacto hechos; queda la re-auditoría del bloqueo

## Impacto cruzado
- Origen ← FNC-037
- Vinculada → FNC-044 (resuelve "un solo superadmin" al asignar roles)
- Genera → deuda en FNC-009 (`BASE_URL` vacío deja relativo el enlace del correo)
- Depende de → FNC-036, FNC-019, FNC-040, FNC-047

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest -q` (antes, `develop` 3059055) | 526 passed, 35 xfailed, código 0 |
| Regresiones nuevas contra el código anterior (worktree temporal en `HEAD`, doble viejo) | 5 failed: cuenta local tomada por uid sin `mail`, rol del portal degradado por LDAP y por SSO, mensaje distinto al local, sin `verificar_contrasena` |
| `test_mapeo_de_grupo_exacto_asigna_el_rol` en el código anterior | passed (el mapeo daba `admin_area`); invertida a `..._ya_no_asigna_el_rol` |
| `venv/bin/python -m pytest -q` (después) | 553 passed, 26 xfailed, código 0 |
| Regresiones de auditor-seguridad contra `dd0a356` | 11 failed (conflicto con cuenta local por directorio ×3 y SSO ×3, contraseña local, cambio de origen, cuenta desactivada en directorio y SSO, `login_user` falso) |
| `venv/bin/python -m pytest -q` (tras corregir) | 565 passed, 26 xfailed, código 0 |
| Regresión del revisor (cuenta local desactivada con contraseña correcta) contra `c0bd3a4` | 1 failed (403 en lugar de 401 único) |
| Regresiones de la re-auditoría (correo con mayúsculas y espacios, directorio y SSO; cuenta nueva normalizada) antes de corregir | 3 failed |
| `venv/bin/python -m pytest -q` (tras revisor y re-auditoría) | 568 passed, 26 xfailed, código 0 |
- `xfail` strict quitados (9, XPASS): `test_login_fallido_no_borra_cuentas_locales`, `test_mensaje_uniforme_en_los_fallos`, `test_filtro_ldap_escapa_comodines`, `test_error_del_directorio_no_se_filtra_al_cliente`, `test_grupo_parecido_no_cambia_el_rol[grupo_admin_heredado, mapeo_json]`, `test_directorio_no_asigna_administrador`, `test_conserva_admin_area_asignado_localmente` (`test_login_directorio.py`); `test_remote_groups_no_asigna_administrador` (`test_sso.py`)
- 18 pruebas nuevas: 11 en `test_login_directorio.py`, 2 en `test_sso.py`, 6 en `tests/directory/test_verificar_contrasena.py` (−1 renombrada)
- No verificado: OpenLDAP real (sin servidor ni valores, ADR-004); StartTLS real (espía de orden StartTLS → bind)
- Veredictos: ver Bitácora

## Decisiones y observaciones
- El directorio no asigna ningún rol; `ldap_role_mappings` y `ldap_group_admin` quedan sin efecto en el login (ficha: "ya no asignan administrador ni admin_area")
- Cuentas existentes conservan su rol, incluso `administrador` asignado antes por LDAP: el superadmin debe revisarlas antes de desplegar (nota de RELEASES)
- Cuenta local buscada solo por `mail` del directorio; sin `mail`, 401 (antes caía a lo escrito y podía tomar la cuenta local `admin`)
- Cuenta existente `local`, con contraseña local o desactivada: login de directorio y SSO responden 401 único, auditan `ACCESO BLOQUEADO` (aviso) y no la modifican; nunca cambia `auth_source` (decisión del dueño 2026-10-15: "bloquear y avisar")
- Decisión tomada (la valida el dueño después): cuentas ya vinculadas (`ldap`/`sso`, sin contraseña) entran aunque sean `administrador` o `admin_area`; el bloqueo por rol aplica solo a las no vinculadas (todas `local`)
- Decisión del dueño (2026-10-15): el login local con cuenta desactivada y contraseña correcta responde 401 `MENSAJE_CREDENCIALES`, no 403 (SEC-AUTH-09)
- Propuesta (requiere migración): vincular por DN del directorio en una columna nueva de `users`, en lugar de `mail`
- Enumeración por tiempo (inexistente vs contraseña errónea): queda para FNC-014
- Correo normalizado (`strip().lower()`) y búsqueda con `lower(email)` en directorio y SSO, como `crud` y `admin`
- Requisito de despliegue: `mail` único y no editable por el usuario en OpenLDAP (`docs/operacion/ENTORNOS.md`)
- "Un solo superadmin al asignar" queda en FNC-044 (no se tocó `crud.py`)
- `ClienteDirectorio.verificar_contrasena` agregado al final de `ldap_client.py` sin cambiar lo existente (una línea de import aparte)
- Login de eventos: se mantienen los textos heredados (`ACCESO DIRECTORIO`, `ACCESO FALLIDO`, `usuario creado`): el catálogo `Evento` no tiene eventos de sesión
- Diferencia de tiempo entre usuario inexistente y contraseña errónea sigue (sin bind en el primer caso): se cubre con el límite de intentos (FNC-014)

## Riesgos y reversión
- Los `administrador` y `admin_area` elevados antes por LDAP/SSO **conservan** el rol (está guardado en la BD): antes de desplegar, el superadmin revisa esas cuentas heredadas (nota en `docs/operacion/RELEASES.md`).
- Reversión: revertir la rama; no hay migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-15 | Aprobada por el dueño (vía orquestador); implementada en `fnc/FNC-042-login-directorio`; 553 passed, 26 xfailed; En revisión (falta revisor y auditor-seguridad) |
- auditor-seguridad (modo cambio, 2026-10-15): **Bloqueante** (Alto: toma de cuenta local por `mail` en directorio y SSO; Bajo: sin `is_active` ni resultado de `login_user`) → corregido con regresiones que primero fallaron; decisión del dueño: bloquear y avisar. Sigue En revisión.
- revisor (2026-10-15): **Requiere cambios** → corregidos: 401 único con cuenta local desactivada (decisión del dueño), interpretación del bloqueo anotada, riesgo de roles heredados corregido + nota en RELEASES, archivos reales, `impacto.py` actual, deuda de `BASE_URL` en FNC-009.
- "Un solo superadmin" (comprobación al asignar) se movió a FNC-044, tarea vinculada que lo resuelve.
- Veredictos: auditor-seguridad Bloqueante → corregido (`c0bd3a4`), queda re-auditoría del bloqueo; revisor Requiere cambios → corregido. Sigue En revisión.
- Re-auditoría de seguridad del bloqueo (2026-10-15): **Aprobado**; Baja (correo sin normalizar) corregida con regresión que primero falló; requisitos de `mail` en ENTORNOS.md. Sigue En revisión.
- Cierre (2026-10-18): Hecha; revisor y auditor-seguridad atendidos; merge local a `develop` aprobado por el dueño.
