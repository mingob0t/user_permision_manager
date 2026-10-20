# FNC-056 — Solicitudes: catálogo solicitable, crear solicitud y mis solicitudes

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en `fnc/FNC-056-solicitudes`, sin push |
| **Rama** | `fnc/FNC-056-solicitudes` |
| **Requiere migración BD** | Sí (`0008_solicitudes`, tabla `platform_access_requests`) |
| **Requiere auditor-seguridad** | Sí (entrada de usuario, autorización) |

## Contexto
- El catálogo existe pero no permite solicitar (F-SOL-01) y el flujo de solicitudes se retiró (F-SOL-02; referencia de solo lectura `nexus_master/app/modules/requests/routes.py`)
- Un admin solicita accesos de áreas ajenas como usuario (RF-03)
- Requerimientos: F-SOL-01, F-SOL-02, RF-03

## Objetivo
- Crear `app/modules/access_requests/` con la solicitud (usuario, plataforma, nivel, justificación, estado, decisión) y los endpoints del solicitante

## Alcance
- **Incluye:**
  - Tabla `platform_access_requests` (nunca `access_requests`, ver FNC-039): estados `pendiente`, `aprobada`, `rechazada`; `decided_by`, `decided_at`, `rejection_reason`
  - `GET /access-requests/catalog`: plataformas activas solicitables según P1, con el estado del solicitante (sin acceso, pendiente, con acceso y nivel)
  - `POST /access-requests`: nivel `usuario` o `admin`, justificación obligatoria con longitud mínima y máxima; rechaza duplicado pendiente, acceso vigente del mismo nivel, plataforma inactiva o sin grupos, y solicitudes de un admin sobre sus propias áreas
  - `GET /access-requests/mine` paginado
  - Aviso `solicitud_nueva` (FNC-048) y auditoría
- **No incluye:**
  - Bandeja y decisión (FNC-057)
  - Cancelar una solicitud (no pedido; sugerencia)
  - Recordatorios y escalamiento (fuera de la v1)
  - Pantallas (DIS-013, DIS-014)

## Archivos previstos
- `app/modules/access_requests/models.py`
- `app/modules/access_requests/services.py`
- `app/modules/access_requests/api.py`
- Migración (ADR-002)
- `app/__init__.py` (registro)
- `tests/access_requests/`

## Reutilización
- Servicio de accesos de FNC-054 (consulta de vigentes)
- Avisos de FNC-048
- `sanitize_display_name` o equivalente para normalizar texto

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `app/__init__.py` | Arranque | Toda la app (registro y exención CSRF del blueprint nuevo) | Sí: pytest completo en verde |
| `tests/matriz_proteccion.py` | Matriz de pruebas | `test_proteccion_por_rol.py`, `test_guardia_rutas.py` (3 casos y 4 casos 400 nuevos) | Sí |
| Contrato `solicitudes.md` 1.1 | Contrato | Web: `frontend/src/lib/access/requests.ts`, `types.ts:71,87` (`justification: string`) → FNC-090; DIS-013, DIS-014 | Pendiente (FNC-090) |
| `notificar_solicitud_nueva`, `acceso_a_reemplazar`, `leer_filtros`/`leer_paginacion`, `ErrorDeAcceso` | Reutilizados sin cambios | notificaciones, accesos, auditoría | No se modificaron |

Salida de `impacto.py` (contra `develop`). Las filas de funciones (`acceso`, `crear`, `estado`, `_nombre`…) son coincidencias de nombre con funciones nuevas de este módulo, no usos reales; los endpoints sí los consume el cliente web (FNC-069):

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 27 elemento(s) usados en otras secciones: app, app/modules, app/utils, frontend/src, frontend/tests, migrations, migrations/versions, scripts/lineamientos, tests, tests/access, tests/areas, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/provisioning, tests/users, utils. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/access-requests` | endpoint | `app/modules/access_requests/api.py` | `frontend/src/lib/access/requests.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |
| `/access-requests/catalog` | endpoint | `app/modules/access_requests/api.py` | `frontend/src/lib/access/requests.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |
| `/access-requests/mine` | endpoint | `app/modules/access_requests/api.py` | `frontend/src/lib/access/requests.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |
| `_codigo` | función | `tests/access_requests/test_crear.py` | `tests/access/test_servicio.py`, `tests/areas/test_alta_y_baja_por_admin.py`, `tests/directory/test_api.py`, `tests/platforms/test_integracion_y_grupos.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/access, tests/areas, tests/directory, tests/platforms, tests/users | ☐ |
| `_fk` | función | `migrations/versions/0008_solicitudes.py` | `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0007_accesos_otorgados.py` | migrations/versions | ☐ |
| `_invalido` | función | `app/modules/access_requests/api.py` | `app/modules/audit/api.py`, `tests/audit/test_api.py` | app/modules, tests/audit | ☐ |
| `_nombre` | función | `app/modules/access_requests/serializacion.py` | `app/modules/areas/validacion.py`, `app/modules/notifications/access_notifications.py`, `frontend/tests/lib/access/peticiones.test.ts`, `tests/directory/test_writer.py` | app/modules, frontend/tests, tests/directory | ☐ |
| `_para` | función | `tests/access_requests/test_aviso.py` | `tests/notifications/test_access_notifications.py` | tests/notifications | ☐ |
| `acceso` | función | `app/modules/access_requests/catalogo.py` | `app/authz.py`, `app/modules/access/errores.py`, `app/modules/access/manejadores.py`, `app/modules/access/models.py`, `app/modules/access/rules.py`, `app/modules/access/services.py`, `app/modules/access/tipos.py`, `app/modules/api/auth.py` (+30) | app, app/modules, frontend/src, frontend/tests, migrations/versions, scripts/lineamientos, tests, tests/access, tests/areas, tests/audit, tests/notifications, tests/platforms, utils | ☐ |
| `activa` | función | `app/modules/access_requests/catalogo.py` | `app/modules/auth/acceso_local.py`, `app/modules/directory/api.py`, `app/modules/notifications/services.py`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/access/client.ts`, `frontend/src/styles/tokens.css`, `frontend/tests/accesibilidad/pares-contraste.ts`, `frontend/tests/lib/access/simulados.test.ts` (+1) | app/modules, frontend/src, frontend/tests, tests | ☐ |
| `catalog` | función | `app/modules/access_requests/api.py` | `frontend/src/app/platforms/page.tsx`, `frontend/src/lib/access/requests.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |
| `correo` | función | `tests/access_requests/test_aviso.py` | `app/modules/api/admin.py`, `app/modules/api/crud.py`, `app/modules/audit/models.py`, `app/modules/audit/queries.py`, `app/modules/audit/services.py`, `app/modules/auth/acceso_local.py`, `app/modules/auth/services.py`, `app/modules/directory/ldap_client.py` (+38) | app/modules, frontend/src, frontend/tests, migrations/versions, tests, tests/access, tests/audit, tests/directory, tests/notifications, tests/provisioning, tests/users, utils | ☐ |
| `crear` | función | `app/modules/access_requests/services.py` | `app/authz.py`, `app/modules/access/models.py`, `app/modules/core/routes.py`, `app/modules/users/directory_accounts.py`, `frontend/src/components/platform-admin.tsx`, `frontend/tests/lib/access/peticiones.test.ts`, `tests/conftest.py`, `tests/test_rutas_heredadas.py` (+2) | app, app/modules, frontend/src, frontend/tests, tests, tests/users, utils | ☐ |
| `downgrade` | función | `migrations/versions/0008_solicitudes.py` | `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `migrations/versions/0007_accesos_otorgados.py`, `tests/notifications/test_migracion_plantillas.py` (+3) | migrations/versions, tests, tests/notifications, tests/platforms | ☐ |
| `escena` | función | `tests/access_requests/conftest.py` | `tests/access/conftest.py`, `tests/access/test_punta_a_punta.py`, `tests/access/test_puntos_de_extension.py`, `tests/access/test_servicio.py`, `tests/areas/test_alta_y_baja_por_admin.py`, `tests/users/test_alta_directorio.py`, `tests/users/test_contrasenas_locales.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/access, tests/areas, tests/users | ☐ |
| `estado` | función | `app/modules/access_requests/catalogo.py` | `app/modules/access/manejadores.py`, `app/modules/access/models.py`, `app/modules/access/services.py`, `app/modules/areas/api.py`, `app/modules/audit/inmutabilidad.py`, `app/modules/audit/services.py`, `app/modules/auth/services.py`, `app/modules/core/models.py` (+31) | app/modules, frontend/src, frontend/tests, migrations/versions, tests/access, tests/provisioning | ☐ |
| `estado_auditado` | función | `app/modules/access_requests/services.py` | `app/modules/access/services.py` | app/modules | ☐ |
| `estados` | función | `app/modules/access_requests/catalogo.py` | `app/modules/access/rules.py`, `frontend/src/styles/tokens.css`, `frontend/tests/accesibilidad/pares-contraste.ts`, `frontend/tests/accesibilidad/texto-de-marca.test.ts`, `frontend/tests/components/audit-log.test.tsx`, `frontend/tests/components/platform-admin.test.tsx`, `tests/access/test_servicio.py`, `tests/provisioning/test_encolado.py` | app/modules, frontend/src, frontend/tests, tests/access, tests/provisioning | ☐ |
| `fecha` | función | `app/modules/access_requests/serializacion.py` | `app/modules/audit/parametros.py`, `migrations/versions/0002_auditoria_ampliada.py`, `tests/audit/test_registro_ampliado.py` | app/modules, migrations/versions, tests/audit | ☐ |
| `my_requests` | función | `app/modules/access_requests/api.py` | `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/types.ts` | frontend/src | ☐ |
| `pedir` | función | `tests/access_requests/conftest.py` | `app/authz.py`, `app/modules/provisioning/worker.py`, `frontend/src/components/login-form.tsx`, `frontend/src/components/platform-catalog.tsx`, `tests/provisioning/test_mensajes_rq.py`, `tests/provisioning/test_worker.py` | app, app/modules, frontend/src, tests/provisioning | ☐ |
| `plataformas` | función | `app/modules/access_requests/catalogo.py` | `app/authz.py`, `app/modules/access/consultas.py`, `app/modules/api/crud.py`, `app/modules/api/helpers.py`, `app/modules/api/routes.py`, `app/modules/areas/baja.py`, `app/modules/core/models.py`, `app/modules/platforms/api.py` (+32) | app, app/modules, app/utils, frontend/src, frontend/tests, migrations/versions, tests, tests/access, tests/platforms | ☐ |
| `sin_permiso` | función | `app/modules/access_requests/errores.py` | `frontend/tests/lib/access/errores.test.ts` | frontend/tests | ☐ |
| `solicitud` | función | `app/modules/access_requests/serializacion.py` | `app/modules/access/rules.py`, `app/modules/access/tipos.py`, `frontend/src/lib/access/types.ts`, `frontend/src/styles/components.css`, `frontend/tests/lib/access/errores.test.ts`, `frontend/tests/lib/access/peticiones.test.ts`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py` (+4) | app/modules, frontend/src, frontend/tests, migrations/versions, tests/access, tests/audit, tests/notifications | ☐ |
| `solicitud_duplicada` | función | `app/modules/access_requests/errores.py` | `frontend/tests/lib/access/errores.test.ts` | frontend/tests | ☐ |
| `upgrade` | función | `migrations/versions/0008_solicitudes.py` | `migrations/env.py`, `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `migrations/versions/0007_accesos_otorgados.py` (+4) | migrations, migrations/versions, tests, tests/notifications, tests/platforms | ☐ |
| `validar_datos` | función | `app/modules/access_requests/services.py` | `app/modules/access/rules.py`, `app/modules/access/services.py` | app/modules | ☐ |

## Variables y configuración
- `ACCESS_REQUEST_JUSTIFICATION_MAX_LENGTH` = 500, `ESTADO_ACTIVO`, `FORMATO_FECHA` (constantes registradas en VARIABLES.md e HISTORIAL.md).
- `ACCESS_REQUEST_JUSTIFICATION_MIN_LENGTH` no se crea: el dueño decidió no pedir justificación (2026-10-20).
- Sin variables de entorno nuevas.

## Decisiones
| Decisión | Origen |
|---|---|
| `justification` opcional, ≤ 500, sin mínimo; contrato 1.1 | Dueño (2026-10-20) |
| El admin pide en área ajena como cualquier usuario (ambos niveles); en su área → `409 ya_administra_area` | Dueño / RF-03 |
| Aviso a todos los admins del área (`notificar_solicitud_nueva` sin cambios); superadmin → FNC-089 | Dueño |
| Catálogo: `user_areas` + áreas administradas (solo ver); solo plataformas y áreas `Activo` | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Nivel solicitable solo si está integrado (DN del nivel o conector configurado) | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Fuera de sus áreas `404`; en su área pero inactiva `409 plataforma_no_disponible` | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Subir con el acceso aún no `activo` → `409 estado_invalido` (reglas P5 de `acceso_a_reemplazar`) | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Duplicado pendiente: restricción única en la BD (`slot_pendiente`); carrera → `409 solicitud_duplicada` | Encargo |
| CSRF mientras FNC-008: JSON obligatorio (`415`) y `Sec-Fetch-Site: cross-site` → `403 csrf_invalido` | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| `user_id`/`platform_id` sin `ON DELETE` (como los accesos); 409 de baja en FNC-083 | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Lista blanca con el patrón actual (FNC-082 aún Propuesta) | Encargo |

## Criterios de aceptación
- [x] Matriz 401/403/201/400/409 (pruebas)
- [x] Duplicado pendiente responde 409 (prueba; también con la restricción de la BD)
- [x] Un admin no puede solicitar en un área que administra (prueba)
- [x] Justificación demasiado larga responde 422 `validacion`; vacía se acepta (decisión del dueño)
- [x] Se notifica a los admins del área (prueba con SMTP simulado)
- [ ] Criterios comunes backend (FNC-037): falta revisor y auditor-seguridad

## Impacto cruzado
- Genera → FNC-057, DIS-013, DIS-014
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, FNC-046, FNC-047, FNC-048, FNC-054, FNC-038, Respuesta a P1
- Contrato → docs/contratos/solicitudes.md

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest -q tests/access_requests` | 53 passed |
| Mutación: sin restricción única y sin la regla P5 | 5 failed (`test_la_bd_impide_dos_pendientes`, `test_carrera_responde_409_y_no_500`, `test_mismo_nivel_vigente_es_409`, `test_nivel_inferior_al_vigente_es_409`, `test_subir_con_acceso_aun_en_proceso_es_409`); restaurado → 53 passed |
| `test_guardia_rutas` antes de la matriz | 1 failed (rutas nuevas sin caso); después en verde |
| `venv/bin/python -m pytest -q` (antes del merge de develop) | 1360 passed, 14 xfailed, código de salida 0 |

No verificado: MySQL real (solo SQLite); revisor y auditor-seguridad no ejecutados (fuera del encargo).

## Riesgos y reversión
- Reversión: bajar la migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo; En curso (desarrollador) |
| 2026-10-20 | Implementada: módulo `access_requests`, migración 0008 (encadenada a 0007), matriz, contrato 1.1; genera FNC-088, FNC-089, FNC-090. En revisión |
