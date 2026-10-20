# FNC-054 — Accesos otorgados: modelo con origen y estados, y servicio de otorgar y revocar

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
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-054-accesos-otorgados` (worktree `pokemon-wt-054`) |
| **Requiere migración BD** | Sí (tabla `platform_access_grants`) |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- No existe registro de quién tiene qué plataforma y nivel, desde cuándo ni por qué; `user_platforms` es una relación sin nivel ni origen que además no limita la visibilidad (deuda 13)
- Es la base del inventario (F-AUD-02) y de la revocación (F-ACC-02)
- Requerimientos: F-ACC-01, F-ACC-02, F-AUD-02, RF-02, RF-05

## Objetivo
- Crear `app/modules/access/` con el acceso otorgado (usuario, plataforma, nivel, origen, solicitud, quién aprobó, fechas, estado) y el servicio `grant()`/`revoke()` que valida reglas, encola el trabajo en FNC-049 y actualiza el estado con el resultado

## Alcance
- **Incluye:**
  - Tabla `platform_access_grants`: `user_id`, `platform_id`, `level` (`usuario`/`admin`), `origin` (`solicitud`/`admin_de_area`/`heredado`), `request_id`, `granted_by`, `granted_at`, `status`, `revoked_by`, `revoked_at`, `revoke_reason`; un acceso vigente por usuario, plataforma y nivel
  - Regla de niveles según P5 (recomendado: excluyentes; pasar de `usuario` a `admin` quita del grupo de usuario)
  - `grant()` y `revoke()` en una transacción con el trabajo de aprovisionamiento; manejadores de resultado registrados en FNC-049
  - Estados `en_proceso` → `activo`/`fallido` y `revocando` → `revocado`/`fallo_revocacion`
  - Auditoría con antes y después en cada cambio
- **No incluye:**
  - Endpoints (FNC-058, FNC-059)
  - Acceso automático de admins (FNC-055)
  - Aprobación de solicitudes (FNC-057)
  - Visibilidad del catálogo (FNC-063)
  - Retirar `user_platforms` (FNC-065)
  - Accesos temporales con vencimiento (fuera de la v1)

## Archivos previstos
- `app/modules/access/models.py`
- `app/modules/access/services.py`
- `app/modules/access/rules.py`
- Migración (ADR-002)
- `tests/access/`

## Reutilización
- `queue.enqueue` y manejadores de FNC-049
- `can_manage_platform` de `app/authz.py`
- `add_audit_log` ampliado

## Criterios de aceptación
- [x] Otorgar crea el acceso `en_proceso` y un trabajo en la misma transacción (prueba)
- [x] El resultado del worker lleva el acceso a `activo` o `fallido` (prueba)
- [x] No se duplica un acceso vigente (prueba; también en la BD)
- [x] Revocar un acceso ya revocado no encola nada (prueba)
- [x] La regla de niveles de P5 tiene pruebas de permitido y denegado
- [x] Criterios comunes backend (FNC-037): sin endpoints nuevos (matriz sin cambios)

## Impacto cruzado
- Genera → FNC-083, FNC-055, FNC-056, FNC-057, FNC-058, FNC-059, FNC-063, FNC-065
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, FNC-046, FNC-047, FNC-049, Respuesta a P5

## Riesgos y reversión
- Desfase entre portal y LDAP si alguien cambia grupos a mano: aceptado por RF-05 (sin conciliación).
- Reversión: bajar la migración.

## Implementación
| Archivo | Qué |
|---|---|
| `app/modules/access/` | `tipos.py`, `models.py` (`PlatformAccessGrant`), `rules.py` (transiciones, alcance, P5), `errores.py` (`ErrorDeAcceso`), `services.py` (`otorgar`, `revocar`, `reabrir_acceso`), `manejadores.py` (resultado del ejecutor), `consultas.py` |
| `migrations/versions/0007_accesos_otorgados.py` | Tabla `platform_access_grants` (down_revision `0006`, una cabeza) |
| `app/__init__.py` | Registra los manejadores en `create_app` (web y worker) |
| `app/modules/platforms/estado.py` | `accesos_vigentes` real |
| `app/modules/areas/baja.py` | `tiene_accesos_vigentes` real (ya no `user_areas`) |
| `app/modules/provisioning/models.py` | Solo el docstring de `access_id` |
| `tests/access/` | 65 pruebas; `tests/areas/test_alta_y_baja_por_admin.py` ajustada |

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- Origen según contrato v1: `solicitud` \| `admin_de_area` (sin `heredado`, P4).
- Unicidad en BD: `slot_vigente` (usuario, plataforma, nivel) y `slot_ocupante` (usuario, plataforma; P5). El que sale (`revocando`) libera el lugar del nuevo nivel.
- Solo se sube de nivel; el `usuario` reemplazado debe estar `activo` (si no, `409 estado_invalido`); mismo nivel o superior vigente → `409 nivel_vigente`.
- Revocar solo desde `activo` (contrato); `fallo_revocacion` → `revocando` y `fallido` → `en_proceso` solo por reintento (`reabrir_acceso`, para FNC-062).
- Otorgar por solicitud: `request_id` obligatorio; quien otorga administra la plataforma **y** la cuenta (`can_manage_user`: nunca a otro admin) y la cuenta pertenece al área (P1); propio → `403 operacion_propia`.
- `admin_de_area`: solo el sistema (`actor=None`), nivel `usuario`, a un admin del área; un admin no lo revoca (404), el superadmin sí.
- Superadmin destinatario → `409 acceso_por_defecto` solo si el actor es superadmin; un admin de área recibe `404` (no revela quién es el superadmin; auditor-seguridad). Código nuevo del servicio; FNC-057 decide si lo expone.
- Cuenta inactiva → `409 cuenta_inactiva` (defensa en profundidad; sin código en el contrato). Por solicitud se comprueba tras el alcance del actor; para el acceso automático, primero.
- `user_id`/`platform_id` sin `ON DELETE`: MySQL impide borrar cuentas o plataformas con accesos (queda gente en grupos sin rastro). `last_job_id` y `provisioning_jobs.access_id` sin FK (ciclo).
- Auditoría: el servicio registra `acceso_otorgado` y `acceso_revocado` (solicitado) con antes/después; el resultado lo audita el ejecutor (`acceso_activo`…, actor `sistema`, `grant_id`): los manejadores no duplican eventos.
- `revoked_by`/`revoke_reason` al pedir; `revoked_at` al confirmar (SEC-CON-09).
- Un resultado que no admite la transición (p. ej. tardío) no cambia el acceso: solo log.

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest -q tests/access` | 65 passed, código 0 |
| Regresión: `tests/access/test_puntos_de_extension.py` con `estado.py` y `baja.py` de `develop` | 8 failed, 1 passed (fallan antes) |
| `venv/bin/python -m pytest -q` (completo) | 1135 passed, 15 xfailed, código 0 (653 s); base `develop`: 1070 passed, 15 xfailed |
| `venv/bin/python -m pytest -q tests/access tests/areas tests/platforms` (tras auditor-seguridad, 2026-10-20) | 210 passed, código 0 |
| `git ls-files app/modules/access migrations/versions/0007_accesos_otorgados.py tests/access` | 13 archivos versionados |

No verificado: MySQL real (únicos con NULL, FK sin `ON DELETE`), Redis real y LDAP real (se usó `MOCK_SYNC` y cola falsa). Sin revisores (por instrucción): pendientes `revisor` y `auditor-seguridad` (autorización).

## Impacto en elementos compartidos
Salida real de `impacto.py` (contra `develop`):

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 23 elemento(s) usados en otras secciones: app, app/modules, app/utils, frontend/src, frontend/tests, migrations, migrations/versions, scratch, scripts/lineamientos, tests, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/provisioning, tests/users, utils. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `__init__` | función | `app/modules/access/errores.py` | `app/modules/directory/ldap_client.py`, `app/modules/directory/writer.py`, `app/modules/notifications/services.py`, `app/modules/platforms/api.py`, `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py`, `app/modules/provisioning/worker.py`, `app/utils/redis_client.py` (+8) | app/modules, app/utils, tests, tests/directory, tests/provisioning | ☐ |
| `_actor` | función | `app/modules/access/models.py` | `app/modules/audit/services.py`, `app/modules/platforms/api.py` | app/modules | ☐ |
| `_auditar` | función | `app/modules/access/services.py` | `app/modules/areas/api.py`, `app/modules/provisioning/ejecucion.py`, `app/modules/users/areas_administradas.py` | app/modules | ☐ |
| `_codigo` | función | `tests/access/test_servicio.py` | `tests/directory/test_api.py`, `tests/platforms/test_integracion_y_grupos.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/directory, tests/platforms, tests/users | ☐ |
| `_falla` | función | `tests/access/test_servicio.py` | `tests/conftest.py`, `tests/provisioning/test_ejecucion.py`, `tests/users/test_roles_y_areas_administradas.py` | tests, tests/provisioning, tests/users | ☐ |
| `_fk` | función | `migrations/versions/0007_accesos_otorgados.py` | `migrations/versions/0002_auditoria_ampliada.py` | migrations/versions | ☐ |
| `_miembros` | función | `tests/access/test_punta_a_punta.py` | `tests/directory/test_writer.py` | tests/directory | ☐ |
| `acceso` | función | `tests/access/test_puntos_de_extension.py` | `app/authz.py`, `app/modules/api/auth.py`, `app/modules/auth/routes.py`, `app/modules/auth/services.py`, `app/modules/platforms/tipos.py`, `app/modules/provisioning/ejecucion.py`, `app/modules/provisioning/providers.py`, `frontend/src/app/requests/page.tsx` (+20) | app, app/modules, frontend/src, frontend/tests, migrations/versions, scripts/lineamientos, tests, tests/audit, tests/notifications, tests/platforms, utils | ☐ |
| `accesos_vigentes` | función | `app/modules/platforms/estado.py` | `app/modules/core/models.py`, `app/modules/platforms/api.py`, `tests/platforms/test_integracion_y_grupos.py` | app/modules, tests/platforms | ☐ |
| `clave_idempotencia` | función | `app/modules/access/services.py` | `app/modules/provisioning/ejecucion.py`, `app/modules/provisioning/providers.py`, `app/modules/provisioning/queue.py`, `tests/provisioning/test_ejecucion.py`, `tests/provisioning/test_ldap_provider.py` | app/modules, tests/provisioning | ☐ |
| `cola_falsa` | función | `tests/access/conftest.py` | `tests/provisioning/conftest.py`, `tests/provisioning/test_encolado.py`, `tests/provisioning/test_ldap_provider.py`, `tests/provisioning/test_worker.py` | tests/provisioning | ☐ |
| `directorio` | función | `tests/access/test_punta_a_punta.py` | `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/api/crud.py`, `app/modules/auth/acceso_local.py`, `app/modules/auth/models.py`, `app/modules/auth/routes.py`, `app/modules/auth/services.py`, `app/modules/directory/api.py` (+43) | app/modules, frontend/src, frontend/tests, migrations/versions, scratch, tests, tests/directory, tests/platforms, tests/provisioning, tests/users | ☐ |
| `downgrade` | función | `migrations/versions/0007_accesos_otorgados.py` | `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `tests/notifications/test_migracion_plantillas.py`, `tests/platforms/test_migracion_0005.py` (+2) | migrations/versions, tests, tests/notifications, tests/platforms | ☐ |
| `escena` | función | `tests/access/conftest.py` | `tests/users/test_contrasenas_locales.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/users | ☐ |
| `operacion_propia` | función | `app/modules/access/errores.py` | `app/modules/api/helpers.py`, `tests/users/test_roles_y_areas_administradas.py` | app/modules, tests/users | ☐ |
| `otorgar` | función | `app/modules/access/services.py` | `app/modules/notifications/access_notifications.py`, `app/modules/provisioning/ejecucion.py`, `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py`, `app/modules/provisioning/queue.py`, `app/modules/provisioning/tipos.py`, `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/types.ts` (+6) | app/modules, frontend/src, tests/notifications, tests/provisioning | ☐ |
| `proveedor_simulado` | función | `tests/access/conftest.py` | `tests/provisioning/conftest.py`, `tests/provisioning/test_ejecucion.py`, `tests/provisioning/test_encolado.py`, `tests/provisioning/test_orden_y_reserva.py`, `tests/provisioning/test_reauditoria.py` | tests/provisioning | ☐ |
| `recargar` | función | `tests/access/conftest.py` | `frontend/src/components/favorites-list.tsx`, `frontend/src/lib/use-polling.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |
| `registrar` | función | `app/modules/access/manejadores.py` | `app/modules/auth/services.py`, `migrations/env.py` | app/modules, migrations | ☐ |
| `respuesta` | función | `app/modules/access/errores.py` | `app/modules/api/auth.py`, `app/modules/areas/api.py`, `app/modules/auth/acceso_local.py`, `app/modules/directory/api.py`, `app/modules/directory/ldap_client.py`, `app/modules/directory/resumen.py`, `app/modules/notifications/access_notifications.py`, `app/modules/platforms/api.py` (+34) | app/modules, frontend/src, frontend/tests, tests, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/provisioning, tests/users | ☐ |
| `revocar` | función | `app/modules/access/services.py` | `app/modules/notifications/access_notifications.py`, `app/modules/provisioning/ejecucion.py`, `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py`, `app/modules/provisioning/tipos.py`, `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/types.ts`, `frontend/tests/lib/access/peticiones.test.ts` (+6) | app/modules, frontend/src, frontend/tests, tests/provisioning | ☐ |
| `upgrade` | función | `migrations/versions/0007_accesos_otorgados.py` | `migrations/env.py`, `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `tests/notifications/test_migracion_plantillas.py` (+3) | migrations, migrations/versions, tests, tests/notifications, tests/platforms | ☐ |
| `validacion` | función | `app/modules/access/errores.py` | `app/modules/api/helpers.py`, `app/modules/api/routes.py`, `app/modules/areas/api.py`, `app/modules/core/models.py`, `app/modules/platforms/api.py`, `frontend/src/components/areas/area-errors.ts`, `frontend/src/lib/api.ts`, `frontend/src/lib/enlace-seguro.ts` (+8) | app/modules, frontend/src, frontend/tests, tests, tests/platforms, tests/users | ☐ |

Lectura: los compartidos reales son `accesos_vigentes` (→ `Platform.to_dict()['active_grants']` en todas las listas de plataformas, una consulta por plataforma; y el `409 plataforma_con_accesos` de `PUT /platforms`), `tiene_accesos_vigentes` (baja de áreas: un área con miembros y sin accesos ya se puede borrar) y `create_app` (registra manejadores globales del ejecutor). El resto son **homónimos** (`__init__`, `_actor`, `_auditar`, `_codigo`, `otorgar`/`revocar` de los proveedores, `upgrade`/`downgrade` de cada migración, fixtures de prueba con el mismo nombre): funciones distintas en otros módulos, no se modificaron.

## Propuestas registradas
- FNC-083: `DELETE /platforms/<id>` y baja de cuentas con accesos: hoy MySQL lo rechaza por FK (500); falta `409` explícito.
- Nota (sin tarea): `active_grants` en listas hace una consulta por plataforma (N+1); agrupar en FNC-063 si pesa.

## Revisiones
| Fecha | Revisor | Veredicto | Estado |
|---|---|---|---|
| 2026-10-20 | auditor-seguridad | 3 hallazgos (vía orquestador) | Corregido: alcance del actor antes de `is_admin(usuario)` (404 a un admin), `409 cuenta_inactiva`, contrato `accesos.md` 1.1 (nivel `usuario` del acceso automático; también el ejemplo de `auditoria.md`); FNC-083 ampliada (purga de inactivos y `DELETE /platforms`). Regresiones: 5 failed antes |

## Commits / PR
- `9aa3c5c` (local, sin push ni PR)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Correcciones de auditor-seguridad (3 hallazgos) en un commit nuevo; sigue En revisión. Impacto cruzado web: `frontend/src/lib/access/mocks.ts:37` aún usa `level: 'admin'` en el acceso automático (solicitud para FNC-069) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada en `fnc/FNC-054-accesos-otorgados`; En revisión, sin revisores (por instrucción) |
| 2026-10-13 | Creada como Propuesta (FNC-037) |
