# FNC-058 — Accesos: consulta por usuario, mis accesos y revocación manual

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en la rama, sin push |
| **Rama** | `fnc/FNC-058-consulta-revocacion-accesos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- F-ACC-02 pide revocar manualmente desde el portal (sacar del grupo o ejecutar el conector), y la pantalla "Usuarios y accesos" necesita ver los accesos de un usuario; el usuario ve los suyos en el Inicio y en Mis solicitudes
- Requerimientos: F-ACC-02, RF-03, pantallas "Usuarios y accesos" e "Inicio"

## Objetivo
- Exponer los accesos con alcance por rol y la revocación con motivo según P7

## Alcance
- **Incluye:**
  - `GET /me/access`: accesos propios
  - `GET /users/<id>/access`: superadmin todos; admin solo los de plataformas de sus áreas
  - `POST /access/<id>/revoke` (motivo según P7): superadmin o admin del área de la plataforma; un admin no revoca accesos de otras áreas
  - Blueprint en `app/modules/access/api.py`
- **No incluye:**
  - Otorgar manualmente sin solicitud (no pedido)
  - Baja masiva de un usuario (fuera de la v1)
  - Pantallas (DIS-014, DIS-018)

## Archivos previstos
- `app/modules/access/api.py`
- `app/__init__.py` (registro del blueprint)
- `tests/access/test_api.py`

## Archivos tocados
- Nuevos: `app/modules/access/api.py`, `app/modules/access/serializacion.py`, `tests/access/test_api.py`
- Tras la auditoría: `app/modules/api/csrf_provisional.py` (nuevo), `app/modules/access_requests/api.py` (usa el helper, sin cambiar su comportamiento), `app/modules/access/services.py` (`_tomar_activo`)
- Cambiados: `app/__init__.py` (import y registro, exento de CSRF como el resto de la API v1), `app/modules/access/consultas.py` (función nueva `de_usuario`, sin cambiar las existentes), `tests/matriz_proteccion.py` (3 casos, preparación `_con_acceso_activo` y un caso 400)
- Sin migración

## Reutilización
- Servicio de FNC-054
- `any_admin_required`, `can_manage_platform`, `scoped_users`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `app/__init__.py` | Arranque | Toda la app (import y registro del blueprint `api_access`) | Sí: suite completa |
| `tests/matriz_proteccion.py` | Prueba compartida | `test_proteccion_por_rol.py`, `test_guardia_rutas.py` | Sí: suite completa |
| `app/modules/access/consultas.py` | Consulta | Solo se agregó `de_usuario` | Sí |

Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `area_tiene_vigentes` | función | `app/modules/access/consultas.py` | `app/modules/areas/baja.py`, `tests/areas/test_alta_y_baja_por_admin.py` | app/modules, tests/areas | ☑ falso positivo: no cambió (la función nueva va después en el mismo archivo) |
| `de_usuario` | función | `app/modules/access/consultas.py` | `app/modules/audit/api.py`, `app/modules/audit/queries.py` | app/modules | ☑ falso positivo: homónimo de `audit.queries.de_usuario`, que no se tocó |

Segunda salida de `impacto.py` (tras la auditoría y el merge de develop; resumida):

| Elemento modificado | Usado en (fuera de la tarea) | ¿Validado? |
|---|---|---|
| `services.revocar` (UPDATE condicional) | `access/area_admin_sync.py` (retiro de accesos automáticos), `access/api.py` | ☑ suite completa (`tests/access`, `tests/platforms`, `tests/users`) |
| `POST /access-requests` (usa `escritura_del_portal`) | `frontend/src/lib/access/requests.ts`, `tests/access_requests/` | ☑ mismo comportamiento: `tests/access_requests` en verde |
| `/me/access` | `frontend/src/lib/access/grants.ts`, `types.ts` (cliente FNC-069) | ☑ según contrato `accesos.md` 1.1; sin cambios en el cliente |
| `_ids`, `_invalido`, `_persona`, `area_tiene_vigentes`, `de_usuario`, `my_access`, `user_access`, `test_solo_se_revoca_un_acceso_activo` | homónimos en otros módulos | ☑ falsos positivos: no se modificaron funciones existentes con ese nombre |

## Criterios de aceptación
- [x] Matriz 401/403/200 por endpoint y rol (pruebas)
- [x] Un admin no revoca accesos de un área ajena (prueba)
- [x] Revocar deja el acceso en `revocando` y encola el trabajo (prueba)
- [x] Criterios comunes backend (FNC-037), salvo CSRF (FNC-008, ver decisiones)

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- Del dueño: la revocación es manual desde el portal y la hace el admin del área o el superadmin.
- `GET /users/<id>/access`: el admin consulta las cuentas que administra (`can_manage_user`) y la suya; otro admin, el superadmin o una cuenta de otra área → 404. Solo ve accesos de plataformas de sus áreas (mismo criterio que `GET /audit/users/<id>`).
- `POST /access/<id>/revoke`: el alcance (`rules.validar_revocacion`) se comprueba antes del cuerpo, para que un acceso ajeno dé 404 aunque el cuerpo sea inválido.
- Lista blanca del cuerpo: solo `reason`; otro campo → `400 campo_no_permitido`; cuerpo no objeto → `400 cuerpo_invalido`.
- Choque simultáneo (`IntegrityError` al confirmar): rollback y `409 estado_invalido`.
- `last_job_id`: se omite solo para el rol usuario (en `/me/access` y donde aplique); los administradores lo reciben.
- CSRF: la API v1 está exenta hasta FNC-008 (P13). Tras la auditoría (H1), `POST /access/<id>/revoke` usa el helper compartido `api.csrf_provisional.escritura_del_portal` (extraído de FNC-056): no JSON → 415, `cross-site` → 403. La prueba `xfail(strict=True)` del CSRF real (token y `Origin`) sigue para FNC-008.
- Concurrencia (H2): `services.revocar` toma el acceso con `UPDATE ... WHERE status = 'activo'` (vale también con READ COMMITTED); la segunda revocación da 409 sin sobrescribir `revoked_by` ni `revoke_reason`.
- Paginación: se reutiliza `audit.parametros.leer_paginacion` (convención común de contratos).

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest -q tests/access/test_api.py tests/test_guardia_rutas.py` antes de implementar | 30 failed, 3 passed, 1 xfailed (regresión: fallan primero) |
| `venv/bin/python -m pytest -q tests/access/test_api.py tests/test_guardia_rutas.py tests/test_proteccion_por_rol.py` | 271 passed, 1 xfailed |
| `venv/bin/python -m pytest -q` (suite completa) | 1352 passed, 15 xfailed, código de salida 0 (antes: 1309 passed, 14 xfailed) |
| `venv/bin/python -m pytest -q` tras merge de develop, H1 y H2 | 1429 passed, 15 xfailed, código de salida 0 |

- No verificado: navegador/cliente web (sin pantallas en esta tarea), MySQL real (pruebas en SQLite), revisor y auditor-seguridad (no se lanzaron por indicación del orquestador).

## Impacto cruzado
- Genera → DIS-014, DIS-018
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-038
- Contrato → docs/contratos/accesos.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada (modo autónomo) y En curso |
| 2026-10-20 | Implementada; En revisión. Pendientes revisor y auditor-seguridad |
| 2026-10-20 | auditor-seguridad aprobado. Merge de develop (FNC-056). H1: helper `api/csrf_provisional.py` en `access_requests` y `revoke`. H2: UPDATE condicional en `services.revocar`. Regresiones: 3 failed antes (2 de H1 sin el decorador, 1 de H2), pasan después |
