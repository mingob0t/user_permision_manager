# FNC-044 — Roles: solo el superadmin crea o eleva admins y asigna las áreas administradas

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios-roles |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-15 |
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
| `app/authz.py` | `can_manage_user`: admin de área solo sobre rol `usuario`; `normalized_role` público |
| `app/modules/api/crud.py` | `POST/PUT/DELETE /users`: reglas de rol, campos no permitidos, contraseña, 404 fuera de alcance; sin copia a áreas administradas; `_error` con `code` |
| `app/modules/api/helpers.py` (nuevo) | `error_response` (D-03) |
| `app/modules/users/api.py` (nuevo) | `PUT /users/<id>/managed-areas` (blueprint `api_users`) |
| `app/modules/users/roles.py` (nuevo) | Roles asignables, campos no permitidos, `cambiar_rol` auditado |
| `app/modules/users/areas_administradas.py` (nuevo) | Validación de `area_ids` y asignación auditada por área |
| `app/modules/users/serializacion.py` (nuevo) | `usuario_gestionado` (`ManagedUser`) |
| `app/modules/api/routes.py` | `GET /users` usa `usuario_gestionado` (misma salida) |
| `app/modules/audit/services.py` | `add_audit_log(..., commit=True)`: `commit=False` para la misma transacción |
| `app/__init__.py` | Registro del blueprint `api_users` (exento de CSRF como el resto de la API v1) |
| `tests/users/test_roles_y_areas_administradas.py` (nuevo) | 47 pruebas |
| `tests/matriz_proteccion.py` | Caso de `PUT /users/<id>/managed-areas`; `admin_objetivo_id` en el escenario |
| `tests/test_proteccion_por_rol.py`, `tests/test_alcance_por_area.py` | Sin `xfail` de SEG-05/SEG-09; códigos del contrato |

## Reutilización
- `is_admin`, `is_area_admin`, `managed_area_ids`, `scoped_areas` de `app/authz.py`
- `add_audit_log` + `Evento` (`rol_cambiado`, `admin_asignado`, `admin_retirado`) de FNC-047
- `error_response` cumple la propuesta D-03 (solo para `crud.py`; `admin.py` sigue con su `_error`)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `can_manage_user` | Autorización | `PUT/DELETE /users/<id>` (`crud.py`), `PUT /users/<id>/platforms` (`crud.py`), `PUT /users/<id>/areas` (`routes.py`); pantalla `/users` | Pruebas en verde; admin de área ya no edita a otros admins (ni a sí mismo por esta vía) |
| `scoped_users` | Autorización | — | Sin cambio (ver Decisiones) |
| Reglas de `POST/PUT /users` | Endpoint | Pantalla `/users` (`users-list.tsx`) | **Rompe el formulario actual**: ver "Impacto en el frontend" |
| `GET /users` (`list_users`) | Endpoint | Pantalla `/users` | Misma salida; `test_humo.py` y `test_alcance_por_area.py` en verde |
| `add_audit_log` | Servicio | 33 llamadas en `app/` | Parámetro nuevo con valor por defecto; llamadas existentes sin cambio |
| `crud._error` | Función local | Solo `crud.py` | Firma compatible (`code` opcional) |

### Salida real de `impacto.py` (2026-10-15, contra `develop`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `_error` | función | `app/modules/api/crud.py` | `app/modules/api/admin.py`, `app/modules/directory/ldap_client.py`, `tests/directory/test_ldap_client.py` | app/modules, tests/directory | ☐ |
| `add_audit_log` | función | `app/modules/audit/services.py` | `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/audit/events.py`, `app/modules/auth/services.py`, `tests/audit/test_inmutabilidad.py`, `tests/audit/test_registro_ampliado.py`, `tests/audit/test_regresion_seg25.py` | app/modules, tests/audit | ☐ |
| `create_user` | función | `app/modules/api/crud.py` | `app/modules/auth/routes.py` | app/modules | ☐ |
| `delete_user` | función | `app/modules/api/crud.py` | `app/modules/users/routes.py` | app/modules | ☐ |
| `list_users` | función | `app/modules/api/routes.py` | `app/modules/auth/routes.py`, `scratch/list_users.py` | app/modules, scratch | ☐ |
| `update_user` | función | `app/modules/api/crud.py` | `app/modules/auth/routes.py` | app/modules | ☐ |

### Lectura (homónimos)
- Real: `add_audit_log` en sus llamadores; firma compatible (`commit=True` por defecto), pruebas de `tests/audit/` en verde.
- Homónimos: `_error` de `admin.py` es su propia función y `_error` de `ldap_client.py` es un método de la clase; `create_user`/`update_user`/`list_users` de `auth/routes.py` y `delete_user` de `users/routes.py` son rutas heredadas (410) distintas; `scratch/list_users.py` es un script manual con su propia función.

## Impacto en el frontend (para FNC-069 / DIS-018 / DIS-019; no se tocó)
- `users-list.tsx:91` envía `auth_source` en el alta → hoy `400 campo_no_permitido`: el alta desde la pantalla falla hasta adaptar el cliente
- `users-list.tsx:115` y `:124` envían `managed_area_ids` → `400`; usar `PUT /users/<id>/managed-areas` (solo superadmin)
- `users-list.tsx:83` reenvía `role` al editar: el rol actual se ignora (no rompe); otro rol de un admin de área → `403 rol_reservado`
- Un admin de área ya no ve cambios sobre otros admins: `PUT/DELETE` → `404`
- Contraseña al editar: admin de área → `403 sin_permiso`; cuenta `ldap`/`sso` → `400 campo_no_permitido`
- Errores traen `code` (aditivo); el cliente actual sigue leyendo `message`

## Variables y configuración
- Ninguna variable nueva. Constantes con nombre: `MAX_AREAS_ADMINISTRADAS = 50` (contrato), `ROLES_DEL_SUPERADMIN`, `ROLES_DEL_ADMIN_DE_AREA`, `CAMPOS_NO_PERMITIDOS`, `ORIGEN_LOCAL`.

## Criterios de aceptación
- [x] Un `admin_area` que intenta crear o elevar un admin recibe 403 (`test_solo_el_superadmin_crea_o_eleva_admins`, antes `xfail`)
- [x] Un `admin_area` no puede editar ni borrar a otro admin (`test_admin_area_no_toma_cuenta_de_otro_admin_area`, antes `xfail`; `test_admin_area_no_gestiona_a_otro_admin`)
- [x] Solo el superadmin cambia `area_admins` (`test_solo_el_superadmin_asigna_areas_administradas`, matriz y `test_admin_area_no_asigna_managed_area_ids`, antes `xfail`)
- [x] No puede existir un segundo `administrador` (`test_no_existe_un_segundo_superadmin`; caso de la matriz RF-04 pasó de 201 a 403)
- [x] Criterios comunes backend: endpoint en la matriz; auditoría en la misma transacción con prueba de rollback; sin IPs ni secretos; tabla de `impacto.py`
- [ ] `auditor-seguridad` en modo cambio (no lanzado por indicación del orquestador)

## Impacto cruzado
- Genera → DIS-016, DIS-019 (y adaptación del cliente en FNC-069)
- Origen ← FNC-037
- Absorbe → FNC-007
- Depende de → FNC-036, FNC-019, FNC-038, FNC-047
- Contrato → docs/contratos/areas-y-roles.md (v1, sin cambios)

## Riesgos y reversión
- Admins de área existentes conservan sus áreas administradas; los creados desde ahora nacen sin ellas y el superadmin las asigna con `PUT /users/<id>/managed-areas`.
- Reversión: revertir la rama; no hay migración.

## Decisiones
- Fuera de alcance en `PUT/DELETE /users/<id>` → `404 no_encontrado` (contrato y SEC-AUTHZ-04); antes `403`. `PUT /users/<id>/platforms` y `/areas` siguen en `403` (fuera del contrato; `/platforms` se retira en FNC-065).
- Enviar el rol actual no es un cambio: se ignora (el formulario lo reenvía; evita que el superadmin no pueda editarse a sí mismo).
- Rol desconocido del superadmin → `403 rol_reservado` (el contrato no lo distingue; valor más seguro).
- Contraseña en `PUT /users/<id>`: solo superadmin y solo cuentas `local` (SEC-AUTH-12, corrección de SEG-05, P8). **Pregunta al dueño:** el Anexo A ("admin: sin contraseña `ldap`/`sso`") sugiere que el admin sí cambia contraseñas locales; se aplicó lo más restrictivo de SEC-AUTH-12. Códigos usados (`sin_permiso`, `campo_no_permitido`) son comunes del README; reflejarlo en el contrato es aditivo.
- `scoped_users` sin cambio: el admin de área sigue **viendo** a otros admins miembros de sus áreas (listado y membresías de área/plataforma); no puede gestionarlos. La membresía ya no da alcance a un admin (usa `area_admins`), y `user_platforms` no restringe visibilidad (deuda 13).
- `POST /users` fija `auth_source = local`; las cuentas del directorio llegan con `POST /users/directory` (FNC-064).
- `password_hash` también se rechaza (lista blanca del README); `is_active` se mantiene en `PUT` (lo usa la pantalla). La lista blanca completa (campos desconocidos) queda para SEC-AUTHZ-09 en otra tarea.
- Auditoría en la misma transacción: `add_audit_log(commit=False)`; un fallo se propaga y no se guarda nada (pruebas de rollback). El registro heredado `EDITAR USUARIO` sigue después del commit, como antes.
- Endpoint en `app/modules/users/api.py` para no hacer crecer `crud.py`.

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/pytest -q` (línea base, antes del cambio) | 526 passed, 35 xfailed, código 0 |
| Pruebas nuevas y convertidas con `app/` de `develop` (stash) | 56 failed, 7 passed, código 1 (regresión que primero falla) |
| `venv/bin/pytest -q tests/users` | 47 passed |
| `venv/bin/pytest -q` (completo, con el cambio) | 587 passed, 27 xfailed, código 0 (8 xfail menos; 0 XPASS) |

- `xfail` retirados (pasan): 2 de RF-04 en `test_proteccion_por_rol.py`, 2 de SEG-09 y 4 de SEG-05 en `test_alcance_por_area.py` (aserciones ajustadas a los códigos del contrato: `400` y `404`).
- No verificado: pantalla `/users` con las reglas nuevas (FNC-069); MySQL real (sin migración, no aplica).

## Commits / PR
- Rama `fnc/FNC-044-roles-superadmin`; commit local `[FNC-044]` (hash en el informe de cierre). Sin push ni PR.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-15 | Aprobada por el dueño (comunicado por el orquestador); implementada por desarrollador en `pokemon-wt-044`; absorbe FNC-007 (SEG-05, SEG-09). Queda En revisión (falta `revisor` y `auditor-seguridad`) |
