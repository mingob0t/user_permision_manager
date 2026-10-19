# FNC-045 — Áreas: el admin da de alta sus áreas y queda como su administrador

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | areas |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local (sin push) |
| **Rama** | `fnc/FNC-045-areas-por-admin` (worktree `pokemon-wt-045`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- Hoy solo el superadmin crea áreas (`POST /areas` con `admin_required`, `crud.py:35`)
- F-AREA-01 pide que el admin dé de alta las suyas y quede asignado automáticamente
- Requerimientos: F-AREA-01, RF-01

## Objetivo
- Permitir a un `admin_area` crear un área, que queda en sus `area_admins`; edición en su alcance; baja según la decisión del dueño (pregunta P11)

## Alcance
- **Incluye:**
  - `POST /areas` con `any_admin_required`; si lo crea un admin de área, se agrega a `area_admins` en la misma transacción
  - `PUT /areas/<id>` sigue con `area_admin_required`
  - `DELETE /areas/<id>`: según P11 (dueño, 2026-10-14): el admin de esas áreas y el superadmin; 409 si tiene plataformas o accesos activos. Agregar el caso a `tests/matriz_proteccion.py`
  - Auditoría del alta con actor y área
- **No incluye:**
  - Asignar admins a un área (FNC-044, superadmin)
  - Acceso automático a plataformas (FNC-055)
  - Pantalla (DIS-016)

## Archivos previstos
- `app/modules/api/crud.py` (solo `create_area` y `delete_area`)
- `tests/areas/`

## Archivos tocados
- Nuevos: `app/modules/areas/api.py` (rutas POST/PUT/DELETE), `validacion.py` (entrada), `baja.py` (409); `tests/areas/test_alta_y_baja_por_admin.py`
- `app/modules/api/crud.py`: salen `create_area`, `update_area`, `delete_area` (no crece)
- `app/modules/api/helpers.py`: constantes `AREA_DUPLICADA`, `AREA_CON_PLATAFORMAS`, `AREA_CON_ACCESOS` (aditivo)
- `app/__init__.py`: registra `areas_api_bp`
- `tests/matriz_proteccion.py`, `tests/test_auditoria_crud.py`: casos ajustados al contrato

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- "Accesos vigentes" = miembros en `user_areas` mientras no existan los accesos de FNC-054/056 (valor más seguro: bloquea la baja); los `area_admins` no cuentan. FNC-054/056 deben ampliar `areas/baja.py`
- `icon`: solo `[A-Za-z0-9_-]`, ≤ 50 (evita marcado en un campo que se pinta)
- `PUT /areas/<id>` también responde 404 en área ajena (contrato y SEC-AUTHZ-04); antes 403
- Validación de POST/PUT pasa de `400` a `422 validacion` con `fields` (contrato)
- `PUT`: un campo reenviado con su valor actual se ignora (áreas heredadas con color fuera de formato siguen editables)
- `area_eliminada` sin `area_id` (la fila se borra y la FK quedaría en NULL); nombre en `target`, estado en `before`
- Nombre único comparado con `casefold` en Python (`lower()` de SQLite no baja "Á")
- (Revisión) Un admin de área no da de baja un área con otros `area_admins` → `409 area_con_otros_admins`; el superadmin sí. Aditivo en el contrato (Historial)

## Reutilización
- `any_admin_required`, `area_admin_required`, `can_manage_area` de `app/authz.py`
- `sanitize_display_name`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `POST/DELETE /api/v1/areas` | Endpoint | Pantalla `/areas` (`areas-list.tsx`) | Pendiente |
| `PUT /api/v1/areas/<id>` | Endpoint | `areas-list.tsx` (ajena 404, inválido 422) | Pendiente |
| Constantes de error de `helpers.py` | Constantes | `areas/api.py`, `areas/baja.py` (aditivo) | Sí (pytest) |
| `crear_actor` (matriz) | Función de prueba | `test_proteccion_por_rol.py` | Sí (pytest) |

### Salida real de `impacto.py`
```
| `/areas` | endpoint | `app/modules/api/crud.py` | `app/modules/api/routes.py`, `app/modules/areas/routes.py`, `app/modules/users/api.py`, `app/modules/users/areas_administradas.py`, `app/modules/users/roles.py`, `app/modules/users/routes.py`, `frontend/src/app/areas/page.tsx`, `frontend/src/components/app-shell.tsx` (+6) | app/modules, frontend/src, frontend/tests, tests, tests/users | ☐ |
| `/areas/<int:area_id>` | endpoint | `app/modules/api/crud.py` | `app/modules/api/routes.py` | app/modules | ☐ |
| `_error` | función | `app/modules/api/crud.py` | `app/modules/api/admin.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☐ |
| `crear_actor` | función | `tests/matriz_proteccion.py` | `tests/test_proteccion_por_rol.py` | tests | ☐ |
| `datos` | función | `tests/test_auditoria_crud.py` | `app/authz.py`, ... (+31) | app, app/modules, ... | ☐ |
| `delete_area` | función | `app/modules/api/crud.py` | `app/modules/areas/routes.py` | app/modules | ☐ |
```
- `/areas`: real solo para POST (frontend `api.createArea`); `routes.py` (GET), `users/*` (`/users/<id>/areas`, `managed-areas`) y `areas/routes.py` (heredada 410) son homónimos por texto
- `/areas/<int:area_id>`: PUT/DELETE reales (frontend `updateArea`/`deleteArea`); `routes.py` es el GET, sin cambio
- `_error`: homónimo; el de `crud.py` no cambió (solo aparece en el contexto del diff) y `admin.py` tiene el suyo
- `crear_actor`: real; el admin de área de la matriz también administra el área vacía (destino de DELETE)
- `datos`: homónimo (variable común); la fixture no cambió
- `delete_area`: real, se movió a `areas/api.py`; el de `areas/routes.py` es la ruta heredada 410 (homónimo)

### Impacto para DIS-016 (sin tocar el frontend)
- `GET /me` sigue con `can_manage_areas = is_admin()`: la pantalla no muestra "Nueva área" al admin de área; ajustar en FNC-069/DIS-016 (usar `is_area_admin` o un permiso nuevo)
- Errores nuevos a mostrar: `422 validacion` con `fields`, `409 area_duplicada`, `409 area_con_plataformas`, `409 area_con_accesos`
- El formulario manda `color` de `<input type="color">` (`#rrggbb`), compatible

## Criterios de aceptación
- [x] Un `admin_area` crea un área y aparece en sus áreas administradas (prueba)
- [x] Un `usuario` recibe 403 (prueba)
- [x] Nombre duplicado responde 409 (prueba)
- [x] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-016
- Genera → FNC-055
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-044, FNC-038, FNC-047
- Contrato → docs/contratos/areas-y-roles.md

## Riesgos y reversión
- Proliferación de áreas: queda auditada. Reversión: revertir la rama.

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/pytest -q tests/areas` (antes de implementar) | 38 failed, 5 passed, código 1 |
| `tests/areas`, `test_proteccion_por_rol.py`, `test_auditoria_crud.py` con `app/` de `develop` (stash) | 44 failed, 241 passed, código 1 (regresión que primero falla) |
| `venv/bin/pytest -q tests/areas` (con el cambio) | 43 passed, código 0 |
| `venv/bin/pytest -q -p no:warnings` (completo) | 812 passed, 17 xfailed, código 0; 0 XPASS |
| Revisión: `venv/bin/pytest -q -p no:warnings tests/areas` antes de corregir | 4 failed, 45 passed, código 1 |
| Revisión: `venv/bin/pytest -q -p no:warnings` (completo) | 818 passed, 17 xfailed, código 0 |

- Criterios: alta por `admin_area` con área en sus administradas, usuario 403, duplicado 409 (también sin distinguir mayúsculas), comunes backend: probados
- Matriz: `POST /areas` y `DELETE /areas/<id>` del admin de área pasan de 403 a 201/200
- No verificado: MySQL real (sin migración); pantalla `/areas` (DIS-016)

## Revisión (2026-10-18)
- `auditor-seguridad`: **Aprobado** con 3 Baja. 1) Auditoría ligada a un id de área reutilizado (SQLite sin FK): corregido, `desligar_auditoria` pone `area_id` en NULL en la misma transacción. 2) Carrera de nombre duplicado (500): corregido, `IntegrityError` → rollback y `409 area_duplicada`. 3) Sin tope de altas por admin: queda como observación
- `revisor`: **Requiere cambios** (faltaba seguridad). Atendido: 409 con otros admins, prueba de rollback de PUT
- Regresiones nuevas: 4 fallaban antes de corregir (otros admins, id reutilizado, carrera en POST y PUT); la de rollback de PUT ya pasaba (cobertura)

## Commits / PR
- Rama `fnc/FNC-045-areas-por-admin`; commit local `0bd558d` (implementación) + commit `[FNC-045]` de correcciones de la revisión. Sin push ni PR

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-18 | Aprobada por el dueño (modo autónomo, vía orquestador); implementada por desarrollador en `pokemon-wt-045`. En revisión (faltan `revisor` y `auditor-seguridad`) |
| 2026-10-18 | `auditor-seguridad` Aprobado (3 Baja: 2 corregidas, tope de altas como observación); `revisor` Requiere cambios. Corregido en commit nuevo; 818 passed, 17 xfailed. Sigue En revisión |
