# FNC-044 — Roles: solo el superadmin crea o eleva admins y asigna las áreas administradas

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios-roles |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-15 |
| **Finalizada** | 2026-10-18 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-044-roles-superadmin` (worktree `pokemon-wt-044`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- Un `admin_area` puede crear o elevar a otro `admin_area` (`crud.py:236-252`, SEG-09) y tomar la cuenta de otro admin (`authz.py:180-200`, SEG-05)
- Un admin nuevo administra "las mismas áreas a las que pertenece", sin decisión explícita
- RF-04 exige que solo el superadmin cree o eleve admins, y F-AREA-02 que solo él asigne admins a un área
- Requerimientos: F-AREA-02, F-USR-03, RF-04

## Objetivo
- Que solo el superadmin asigne los roles `admin_area` y `administrador` y las filas de `area_admins`; que un admin de área no gestione cuentas de otros admins; y exponer un endpoint explícito para asignar las áreas que administra un admin

## Alcance
- **Incluye:**
  - `can_manage_user`: un admin de área solo gestiona cuentas con rol `usuario` de sus áreas
  - `POST/PUT /users`: el rol solo lo cambia el superadmin; un admin de área no puede crear ni editar admins
  - Nuevo `PUT /users/<id>/managed-areas` (superadmin) para `area_admins`; quitar el rol borra sus áreas administradas
  - Un solo `administrador`: no se puede crear un segundo (coherente con FNC-042)
  - Pruebas de escalada (la base viene de FNC-021)
- **No incluye:**
  - Acceso automático a las plataformas de un área al asignarla (FNC-055)
  - Alta de cuentas en LDAP (FNC-064)
  - Alta de áreas por el admin (FNC-045)
  - Pantallas (DIS-016, DIS-019)

## Hallazgos de seguridad que absorbe
- **FNC-007** completo (SEG-05, SEG-09): corregidos y con regresión.

## Archivos
| Archivo | Cambio |
|---|---|
| `app/authz.py` | `can_manage_user` y `scoped_users`: admin de área solo sobre rol `usuario` de sus áreas; `normalized_role` público |
| `app/modules/api/crud.py` | `POST/PUT/DELETE /users`: reglas de rol, campos no permitidos, contraseña, 404 fuera de alcance; sin copia a áreas administradas; `_error` con `code` |
| `app/modules/api/helpers.py` (nuevo) | `error_response`, `validation_error`, `json_object`, `is_id_list` y errores del contrato centralizados (D-03) |
| `app/modules/users/api.py` (nuevo) | `PUT /users/<id>/managed-areas` (blueprint `api_users`) |
| `app/modules/users/roles.py` (nuevo) | Roles asignables, campos no permitidos, `cambiar_rol` auditado |
| `app/modules/users/areas_administradas.py` (nuevo) | Validación de `area_ids` y asignación auditada por área |
| `app/modules/users/serializacion.py` (nuevo) | `usuario_gestionado` (`ManagedUser`) |
| `app/modules/api/routes.py` | `GET /users` usa `usuario_gestionado`; `PUT /users/<id>/areas` → 404 fuera de alcance y 400 con cuerpo no válido; `GET /audit` del admin incluye sus propios eventos |
| `app/modules/audit/services.py` | `add_audit_log(..., commit=True)`: `commit=False` para la misma transacción |
| `app/__init__.py` | Registro del blueprint `api_users` (exento de CSRF como el resto de la API v1) |
| `tests/users/test_roles_y_areas_administradas.py` (nuevo) | 61 pruebas |
| `tests/matriz_proteccion.py` | Caso de `PUT /users/<id>/managed-areas`; `admin_objetivo_id` en el escenario |
| `tests/test_proteccion_por_rol.py`, `tests/test_alcance_por_area.py` | Sin `xfail` de SEG-05/SEG-09; códigos del contrato; `scoped_users` y `stats.users` del admin sin él mismo |

## Reutilización
- `is_admin`, `is_area_admin`, `managed_area_ids`, `scoped_areas` de `app/authz.py`
- `add_audit_log` + `Evento` (`rol_cambiado`, `admin_asignado`, `admin_retirado`) de FNC-047
- `error_response` cumple la propuesta D-03 (solo para `crud.py`; `admin.py` sigue con su `_error`)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `can_manage_user` | Autorización | `PUT/DELETE /users/<id>` (`crud.py`), `PUT /users/<id>/platforms` (`crud.py`), `PUT /users/<id>/areas` (`routes.py`); pantalla `/users` | Pruebas en verde; admin de área ya no edita a otros admins (ni a sí mismo por esta vía) |
| `scoped_users` | Autorización | `GET /users`, `GET /stats` (`users`), `GET /audit` (admin de área), `PUT /areas/<id>/users`, `PUT /platforms/<id>/users` | Admin de área: lista y contador sin otros admins ni él mismo; `/audit` suma sus propios eventos; no saca ni mete a otros admins en membresías |
| Reglas de `POST/PUT /users` | Endpoint | Pantalla `/users` (`users-list.tsx`) | **Rompe el formulario actual**: ver "Impacto en el frontend" |
| `GET /users` (`list_users`) | Endpoint | Pantalla `/users` | Misma salida; `test_humo.py` y `test_alcance_por_area.py` en verde |
| `add_audit_log` | Servicio | 33 llamadas en `app/` | Parámetro nuevo con valor por defecto; llamadas existentes sin cambio |
| `crud._error` | Función local | Solo `crud.py` | Firma compatible (`code` opcional) |

### Salida real de `impacto.py` (2026-10-15, tras la revisión, contra `develop`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `_error` | función | `app/modules/api/crud.py` | `app/modules/api/admin.py`, `app/modules/directory/ldap_client.py`, `tests/directory/test_ldap_client.py` | app/modules, tests/directory | ☐ |
| `_falla` | función | `tests/users/test_roles_y_areas_administradas.py` | `tests/conftest.py` | tests | ☐ |
| `_payload` | función | `app/modules/api/crud.py` | `app/modules/api/admin.py` | app/modules | ☐ |
| `add_audit_log` | función | `app/modules/audit/services.py` | `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/audit/events.py`, `app/modules/auth/services.py`, `tests/audit/test_inmutabilidad.py`, `tests/audit/test_registro_ampliado.py`, `tests/audit/test_regresion_seg25.py` | app/modules, tests/audit | ☐ |
| `como` | función | `tests/users/test_roles_y_areas_administradas.py` | `app/modules/api/admin.py`, `app/modules/audit/sanitizar.py`, `app/modules/directory/ldap_client.py`, `app/modules/notifications/services.py`, `frontend/src/components/favorites-list.tsx`, `frontend/src/components/login-form.tsx`, `frontend/src/components/notifications-list.tsx`, `frontend/src/components/session-provider.tsx` (+15) | app/modules, frontend, frontend/src, frontend/tests, scripts/lineamientos, tests, tests/audit, tests/directory, utils, utils/migrations | ☐ |
| `create_user` | función | `app/modules/api/crud.py` | `app/modules/auth/routes.py` | app/modules | ☐ |
| `delete_user` | función | `app/modules/api/crud.py` | `app/modules/users/routes.py` | app/modules | ☐ |
| `list_audit` | función | `app/modules/api/routes.py` | `app/modules/audit/routes.py` | app/modules | ☐ |
| `list_users` | función | `app/modules/api/routes.py` | `app/modules/auth/routes.py`, `scratch/list_users.py` | app/modules, scratch | ☐ |
| `update_user` | función | `app/modules/api/crud.py` | `app/modules/auth/routes.py` | app/modules | ☐ |

### Lectura (homónimos)
- Real: `add_audit_log` en sus llamadores; firma compatible (`commit=True` por defecto), pruebas de `tests/audit/` en verde. `list_audit` = `GET /api/v1/audit` (pantalla `/audit`): el admin de área conserva sus propios eventos.
- Homónimos: `_error`/`_payload` de `admin.py` son sus propias funciones y `_error` de `ldap_client.py` es un método; `_falla` de `conftest.py` es otra función local; `como` es un fixture local que coincide con la palabra "como" en textos y comentarios; `create_user`/`update_user`/`list_users`/`list_audit` de `auth/routes.py` y `audit/routes.py` y `delete_user` de `users/routes.py` son rutas heredadas (410); `scratch/list_users.py` es un script manual.

## Impacto en el frontend (para FNC-069 / DIS-018 / DIS-019; no se tocó)
- `users-list.tsx:91` envía `auth_source` en el alta → hoy `400 campo_no_permitido`: el alta desde la pantalla falla hasta adaptar el cliente
- `users-list.tsx:115` y `:124` envían `managed_area_ids` → `400`; usar `PUT /users/<id>/managed-areas` (solo superadmin)
- `users-list.tsx:83` reenvía `role` al editar: el rol actual se ignora (no rompe); otro rol de un admin de área → `403 rol_reservado`
- Un admin de área ya no ve cambios sobre otros admins: `PUT/DELETE` → `404`
- Contraseña al editar: cuenta `ldap`/`sso` → `400 campo_no_permitido` (superadmin y admin de área sobre `usuario` locales de sus áreas sí pueden)
- Un admin de área ya no se ve a sí mismo ni a otros admins en `GET /users`; `stats.users` cuenta solo cuentas `usuario`
- Errores traen `code` (aditivo); el cliente actual sigue leyendo `message`

## Variables y configuración
- Ninguna variable nueva. Constantes con nombre: `MAX_AREAS_ADMINISTRADAS = 50` (contrato), `ROLES_DEL_SUPERADMIN`, `ROLES_DEL_ADMIN_DE_AREA`, `CAMPOS_NO_PERMITIDOS`, `ORIGEN_LOCAL`.

## Criterios de aceptación
- [x] Un `admin_area` que intenta crear o elevar un admin recibe 403 (`test_solo_el_superadmin_crea_o_eleva_admins`, antes `xfail`)
- [x] Un `admin_area` no puede editar ni borrar a otro admin (`test_admin_area_no_toma_cuenta_de_otro_admin_area`, antes `xfail`; `test_admin_area_no_gestiona_a_otro_admin`)
- [x] Solo el superadmin cambia `area_admins` (`test_solo_el_superadmin_asigna_areas_administradas`, matriz y `test_admin_area_no_asigna_managed_area_ids`, antes `xfail`)
- [x] No puede existir un segundo `administrador` (`test_no_existe_un_segundo_superadmin`; caso de la matriz RF-04 pasó de 201 a 403)
- [x] Criterios comunes backend: endpoint en la matriz; auditoría en la misma transacción con prueba de rollback; sin IPs ni secretos; tabla de `impacto.py`
- [x] `auditor-seguridad` en modo cambio: Aprobado con hallazgos (Media: `scoped_users`; Baja: 404/400 en `/users/<id>/areas` y `/platforms`), corregidos

## Impacto cruzado
- Genera → DIS-016, DIS-019 (y adaptación del cliente en FNC-069), FNC-077, FNC-078, FNC-079
- Origen ← FNC-037
- Absorbe → FNC-007
- Depende de → FNC-036, FNC-019, FNC-038, FNC-047
- Contrato → docs/contratos/areas-y-roles.md (v1, sin cambios)

## Riesgos y reversión
- Admins de área existentes conservan sus áreas administradas; los creados desde ahora nacen sin ellas y el superadmin las asigna con `PUT /users/<id>/managed-areas`.
- Reversión: revertir la rama; no hay migración.

## Decisiones
- Fuera de alcance en `PUT/DELETE /users/<id>`, `PUT /users/<id>/areas` y `/platforms` → `404 no_encontrado` (SEC-AUTHZ-04); antes `403`. Cuerpo no objeto o ids no enteros → `400 cuerpo_invalido` (antes 500); `cuerpo_invalido` es un código nuevo, aditivo al README.
- Enviar el rol actual no es un cambio: se ignora (el formulario lo reenvía; evita que el superadmin no pueda editarse a sí mismo).
- Rol desconocido del superadmin → `403 rol_reservado` (el contrato no lo distingue; valor más seguro).
- Contraseña en `PUT /users/<id>` (decisión del dueño 2026-10-15): superadmin, o admin de área sobre cuentas `usuario` locales de sus áreas; nunca `ldap`/`sso` (`400 campo_no_permitido`). Reflejado en `areas-y-roles.md` (aditivo en v1) y en FNC-037. El login local se deshabilitará (FNC-077).
- `scoped_users` aplica el mismo filtro que `can_manage_user` (revisión de seguridad): cierra el residual de SEG-05 en `PUT /areas/<id>/users` y `PUT /platforms/<id>/users`. Para no perder visibilidad, `GET /audit` del admin suma sus propios eventos.
- `POST /users` fija `auth_source = local`; las cuentas del directorio llegan con `POST /users/directory` (FNC-064).
- `password_hash` también se rechaza; `is_active` se mantiene en `PUT` (lo usa la pantalla). Lista blanca completa: FNC-078. Alta de cuentas `ldap` del importador: FNC-079.
- Errores y mensajes del contrato centralizados en `api/helpers.py` (sin constantes duplicadas en `crud.py` ni `users/api.py`).
- Segundo superadmin por SSO/LDAP/respaldo: fuera de esta tarea, ya en FNC-013 y FNC-010 (FNC-042 resuelve SSO/LDAP).
- Auditoría en la misma transacción: `add_audit_log(commit=False)`; un fallo se propaga y no se guarda nada (pruebas de rollback). El registro heredado `EDITAR USUARIO` sigue después del commit, como antes.
- Endpoint en `app/modules/users/api.py` para no hacer crecer `crud.py`.

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/pytest -q` (línea base, antes del cambio) | 526 passed, 35 xfailed, código 0 |
| Pruebas nuevas y convertidas con `app/` de `develop` (stash) | 56 failed, 7 passed, código 1 (regresión que primero falla) |
| `venv/bin/pytest -q tests/users` | 47 passed |
| Revisión: regresiones nuevas con `app/` del commit `203b276` (stash) | 13 failed, 3 passed, código 1 |
| Revisión: `venv/bin/pytest -q` (completo) | 600 passed, 27 xfailed, código 0; 0 XPASS |
| `venv/bin/pytest -q` (completo, con el cambio) | 587 passed, 27 xfailed, código 0 (8 xfail menos; 0 XPASS) |

- `xfail` retirados (pasan): 2 de RF-04 en `test_proteccion_por_rol.py`, 2 de SEG-09 y 4 de SEG-05 en `test_alcance_por_area.py` (aserciones ajustadas a los códigos del contrato: `400` y `404`).
- No verificado: pantalla `/users` con las reglas nuevas (FNC-069); MySQL real (sin migración, no aplica).

## Revisión (2026-10-15)
- `auditor-seguridad`: **Aprobado** con hallazgos. Media: `scoped_users` del admin incluía a otros admins (residual de SEG-05 en membresías). Baja: `/users/<id>/areas` y `/platforms` daban 403 fuera de alcance y 500 con cuerpo no objeto. Corregidos con regresión.
- `revisor`: **Requiere cambios**. Regla de contraseñas del dueño + contrato, tareas FNC-077/078/079, errores centralizados en `helpers.py`, salida real de `impacto.py`, texto del catálogo. Corregidos.
- Segundo superadmin por SSO/LDAP/respaldo: referido a FNC-013, FNC-010 y FNC-042 (sin cambio aquí).

## Commits / PR
- Rama `fnc/FNC-044-roles-superadmin`; commit local `203b276` (implementación) + commit `[FNC-044]` de correcciones de la revisión. Sin push ni PR.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-15 | Aprobada por el dueño (comunicado por el orquestador); implementada por desarrollador en `pokemon-wt-044`; absorbe FNC-007 (SEG-05, SEG-09). Queda En revisión (falta `revisor` y `auditor-seguridad`) |
| 2026-10-15 | `auditor-seguridad` Aprobado con hallazgos; `revisor` Requiere cambios. Corregidos en un commit nuevo; decisión del dueño sobre contraseñas; creadas FNC-077, FNC-078, FNC-079. 600 passed, 27 xfailed. Sigue En revisión |
| 2026-10-18 | Hecha: revisor y auditor-seguridad atendidos; merge local a `develop` aprobado por el dueño |
