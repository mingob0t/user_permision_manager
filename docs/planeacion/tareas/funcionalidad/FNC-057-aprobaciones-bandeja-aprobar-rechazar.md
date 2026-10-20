# FNC-057 — Aprobaciones: bandeja por área, aprobar y rechazar con motivo obligatorio

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local, sin push |
| **Rama** | `fnc/FNC-057-aprobaciones` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización de otorgamiento) |

## Contexto
- F-SOL-03 pide una bandeja de aprobación por área con rechazo motivado (RF-06)
- Un admin no aprueba solicitudes de áreas que no gestiona (RF-03)
- Requerimientos: F-SOL-03, RF-03, RF-06, F-NOT-01

## Objetivo
- Exponer la bandeja y las decisiones: aprobar crea el acceso (FNC-054) y encola el aprovisionamiento; rechazar exige motivo

## Alcance
- **Incluye:**
  - `GET /access-requests/inbox`: superadmin todas; admin las de plataformas de sus áreas; filtros por estado y área; paginado
  - `POST /access-requests/<id>/approve` y `POST /access-requests/<id>/reject` (motivo obligatorio, longitud mínima)
  - Solo se decide una solicitud `pendiente` (bloqueo para evitar doble decisión)
  - Regla de auto-aprobación según P12 (recomendado: nadie decide su propia solicitud)
  - Avisos `solicitud_aprobada` / `solicitud_rechazada` y auditoría
- **No incluye:**
  - Aprobación en lote (no pedido)
  - Suplentes y escalamiento (fuera de la v1)
  - Pantalla (DIS-015)

## Archivos previstos
- `app/modules/access_requests/approvals.py`
- `app/modules/access_requests/api.py` (rutas de la bandeja)
- `tests/access_requests/test_approvals.py`

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `app/modules/access_requests/approvals.py` | Nuevo: `bandeja`, `validar_decisor`, `limpiar_motivo_rechazo`, `_tomar_pendiente`, `aprobar`, `rechazar` |
| `app/modules/access_requests/api.py` | `GET /access-requests/inbox`, `POST /access-requests/<id>/approve` y `/reject` |
| `app/modules/access_requests/errores.py` | `solicitud_propia` (403), `solicitud_ya_decidida` (409) |
| `app/modules/access_requests/tipos.py` | `ACCESS_REQUEST_REJECTION_MIN_LENGTH` (10), `ACCESS_REQUEST_REJECTION_MAX_LENGTH` (500) |
| `tests/access_requests/test_approvals.py` | Nuevo: 45 pruebas |
| `tests/matriz_proteccion.py` | 3 casos (inbox, approve, reject) y 2 de `400` |

## Decisiones
| Tema | Decisión | Fuente |
|---|---|---|
| Rechazo sin motivo | `422 validacion` con `fields.reason` (10–500), no `400` como decía el criterio | Contrato `solicitudes.md` 1.1 (prevalece) |
| Admin de otra área | `404 no_encontrado`, no `403` como decía el criterio | Contrato (SEC-AUTHZ-03/07) |
| Propia | `403 solicitud_propia`, antes del alcance | P12, SEC-AUTHZ-08 |
| Quién decide | Superadmin; admin de área con `can_manage_platform` y `can_manage_user` (nunca la de otro admin: 404) | RF-03, SEC-AUTHZ-06; decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Bandeja | Sin las propias ni las que el actor no puede decidir | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Doble decisión | `UPDATE ... WHERE status = 'pendiente'` (como `_tomar_activo`); la segunda → `409 solicitud_ya_decidida` | SEC-AUTHZ-10 |
| Nivel no integrado (o plataforma/área inactiva) | `409 plataforma_no_disponible`, sin cambios | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Nivel ya vigente | `409 nivel_vigente` (reglas de `otorgar`), sin cambios; se puede rechazar | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Cuenta inactiva / ya no del área (P1) | `409 cuenta_inactiva` / `404` (reglas de FNC-054) | FNC-054 |
| `IntegrityError` al confirmar | `409 estado_invalido` y reversión | Mismo criterio que FNC-058 |
| Rechazar | No mira la cuenta ni la integración | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Migración | No requerida | — |

## Reutilización
- `grant()` de FNC-054
- Avisos de FNC-048
- `managed_area_ids`, `can_manage_platform`

## Variables y configuración
- `ACCESS_REQUEST_REJECTION_MIN_LENGTH` (constante registrada).

## Criterios de aceptación
- [x] Un admin de otra área no aprueba: `404` según contrato (`test_admin_de_otra_area_recibe_404`)
- [x] Rechazo sin motivo: `422` según contrato (`test_rechazo_exige_motivo_de_10_a_500`)
- [x] Dos aprobaciones simultáneas producen un solo acceso (`test_segunda_decision_concurrente_409_un_solo_acceso`)
- [x] Aprobar crea el acceso `en_proceso` y el trabajo (`test_aprobar_crea_acceso_en_proceso_trabajo_auditoria_y_aviso`)
- [x] Criterios comunes backend (FNC-037): matriz de protección, lista blanca, CSRF provisional, auditoría antes/después

## Impacto cruzado
- Genera → DIS-015
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-056, FNC-054, FNC-048, Respuesta a P12
- Contrato → docs/contratos/solicitudes.md

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest tests/access_requests/test_approvals.py -q` antes de implementar | Error de colección (`approvals` no existe): falla primero |
| Mismo, con la condición `status = 'pendiente'` quitada del `UPDATE` | 2 failed (las dos pruebas de concurrencia) |
| `venv/bin/python -m pytest tests/access_requests/test_approvals.py -q` | 45 passed |
| `venv/bin/python -m pytest -q` | 1488 passed, 15 xfailed; código de salida 0 |

No verificado: concurrencia real en MySQL (la prueba simula la otra transacción confirmada en SQLite); envío real del correo (avisos simulados; las plantillas son de FNC-048). Pendientes `revisor` y `auditor-seguridad` (requerido): no lanzados por indicación del orquestador.

## Impacto en elementos compartidos
Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/access-requests/inbox` | endpoint | `app/modules/access_requests/api.py` | `frontend/src/lib/access/requests.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☑ nuevo; el cliente web (FNC-069) ya lo consume según contrato |
| `inbox` | función | `app/modules/access_requests/api.py` | `frontend/src/lib/access/requests.ts`, `frontend/tests/lib/access/peticiones.test.ts`, `frontend/tests/lib/access/simulados.test.ts` | frontend/src, frontend/tests | ☑ ídem (coincidencia por nombre) |
| `my_requests` | función | `app/modules/access_requests/api.py` | `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/types.ts` | frontend/src | ☑ sin cambios (solo contexto del diff) |
| `sin_permiso` | función | `app/modules/access_requests/errores.py` | `app/modules/access_requests/services.py`, `frontend/tests/lib/access/errores.test.ts`, `tests/access_requests/test_crear.py` | app/modules, frontend/tests, tests/access_requests | ☑ sin cambios (solo contexto del diff) |

Compartidos usados sin modificar: `access.services.otorgar`, `access.rules`, `api.csrf_provisional.escritura_del_portal`, `audit.parametros` (`leer_filtros`, `leer_paginacion`), `access.serializacion` (no tocado), `notifications.access_notifications`, `authz`. `tests/matriz_proteccion.py`: solo casos nuevos.

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo por el orquestador; En curso |
| 2026-10-20 | Implementada: bandeja, aprobar y rechazar; 45 pruebas; suite 1488 passed. En revisión (pendientes revisor y auditor-seguridad) |
