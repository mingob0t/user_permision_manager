# FNC-065 — Retirar la asignación directa de plataformas (`user_platforms`) y migrarla a accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-065-retirar-user-platforms` |
| **Inicio** | 2026-10-21 |
| **Requiere migración BD** | Sí (0010: datos de `user_platforms` a `platform_access_grants`) |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- `PUT /platforms/<id>/users` y `PUT /users/<id>/platforms` (`crud.py:212`, `:352`) asignan plataformas sin solicitud, sin nivel y sin escribir en LDAP, lo que contradice que otorgar sea agregar al grupo (RF-02). **Tarea condicionada a la respuesta P4.**
- Requerimientos: RF-02, F-ACC-01

## Objetivo
- Si P4 lo aprueba: migrar cada fila de `user_platforms` a un acceso de origen `heredado` (nivel según P4, sin escribir en LDAP), retirar los dos endpoints y marcar la tabla como obsoleta

## Alcance
- **Incluye:**
  - Migración de datos idempotente
  - Retiro de los dos endpoints y de `user_ids` en `Platform.to_dict`
  - Documentación de la tabla obsoleta
- **No incluye:**
  - Borrar la tabla (otra tarea, tras un periodo)
  - Pantallas (las asignaciones desaparecen de DIS-017/DIS-018)

## Decisiones (orquestador, modo autónomo; pendientes de validar en la prueba de concepto)
| Tema | Valor aplicado |
|---|---|
| P4 | Pedía descartar; se migra a origen `heredado` (contrato `accesos.md` 1.2, aditivo) |
| Acceso creado | `heredado`, nivel `usuario`, `activo`, sin otorgante ni solicitud; sin LDAP ni trabajos |
| Se omiten (y se cuentan) | Acceso vigente previo (P5), cuenta inactiva, plataforma inactiva, superadmin (acceso por defecto, P6), cuenta fuera del área (P1) |
| Idempotencia | No repite una pareja con acceso `heredado` (tampoco uno revocado después) |
| Auditoría | Un registro de sistema `migracion_accesos_heredados` con los conteos; por fila no hay actor ni solicitud y el origen los identifica |
| Endpoints | `410 endpoint_retirado` (`use: POST /access-requests`); se conserva la protección por rol y siguen en la matriz con 410 |
| Tabla | `user_platforms` y `User.platforms` se conservan, obsoletas; borrado en FNC-107 |
| Revocar `heredado` | Como cualquier acceso: el admin de área en sus áreas; sin cambios en `rules.validar_revocacion` |
| `Platform.to_dict` | Ya no exponía `user_ids` desde FNC-046; sin cambio |
| Downgrade | Borra los `heredado` `activo` sin trabajo; conserva los usados o revocados; no restaura nada (la tabla no se tocó) |

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `migrations/versions/0010_user_platforms_a_accesos.py` | Migración y `migrar_asignaciones` (sin imports de la app) |
| `app/modules/access/tipos.py` | `ORIGEN_HEREDADO`, `ORIGENES` (+heredado), `ORIGENES_OTORGABLES` |
| `app/modules/access/rules.py` | `validar_datos` solo acepta `ORIGENES_OTORGABLES` |
| `app/modules/api/helpers.py` | `endpoint_retirado`, `REEMPLAZO_ASIGNACION` |
| `app/modules/api/crud.py`, `app/modules/platforms/api.py` | Las dos rutas responden 410; imports sin uso retirados |
| `app/authz.py` | Solo docstring |
| `docs/contratos/` | `accesos.md` 1.2, `README.md`, `plataformas-integracion.md` |
| `docs/backend/README.md`, `docs/estandarizacion/03-reutilizacion.md`, `CHANGELOG.md`, `docs/logs/2026-10-21.md` | Documentación |
| `tests/access/test_migracion_0010.py`, `test_origen_heredado.py`, `test_endpoints_retirados.py` | 9 + 8 + 4 pruebas nuevas |
| `tests/matriz_proteccion.py` | Los dos casos esperan 410 |
| `tests/access/test_inventario.py` | El origen inválido de ejemplo era `heredado` (ahora válido): pasa a `otro` |
| `tests/test_alcance_por_area.py`, `tests/test_auditoria_crud.py`, `tests/users/test_roles_y_areas_administradas.py`, `tests/authz/test_visibilidad_por_accesos.py` | Se retiran las pruebas de la asignación (el endpoint ya no escribe): 4 casos parametrizados y 2 pruebas de FNC-021, 1 de FNC-044, 1 de FNC-063 y 2 acciones de auditoría. Lo cubre `test_endpoints_retirados.py` |

## Reutilización
- Modelo de FNC-054

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `PUT /platforms/<id>/users`, `PUT /users/<id>/platforms` | Endpoints retirados (410) | Ninguna llamada en `frontend/src` (ya no existían en DIS-017/DIS-018); `tests/matriz_proteccion.py` | Pruebas en verde |
| `Platform.to_dict` | Serialización | Sin cambio (ya no exponía `user_ids`) | Sí |
| `ORIGENES`, `ORIGEN_HEREDADO` (`access/tipos.py`) | Constantes | Filtro `origin` del inventario (`inventario_api.py`), `rules.validar_datos` (ahora `ORIGENES_OTORGABLES`) | Pruebas en verde |
| `rules.validar_datos` | Regla compartida | `access/services.py`, `access_requests/services.py` | Pruebas en verde (rechaza `heredado`) |
| `api/helpers.endpoint_retirado` | Respuesta (nueva) | `api/crud.py`, `platforms/api.py` | Sí |

Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `datos` | función | `tests/test_auditoria_crud.py` | `app/__init__.py`, `app/modules/access/api.py`, `app/modules/access/serializacion.py`, `app/modules/access_requests/api.py`, `app/modules/api/admin.py`, `app/modules/api/routes.py`, `app/modules/areas/api.py`, `app/modules/areas/validacion.py` (+76) | app, app/modules, app/utils, frontend, frontend/src, frontend/tests, migrations/versions, scratch, scripts/lineamientos, tests, tests/access, tests/areas, tests/audit, tests/connectors, tests/directory, tests/home, tests/notifications, tests/platforms, tests/provisioning, tests/users, utils, utils/migrations | ☐ |
| `scoped_platforms` | función | `app/authz.py` | `app/modules/api/routes.py` | app/modules | ☐ |
| `validar_datos` | función | `app/modules/access/rules.py` | `app/modules/access/services.py`, `app/modules/access_requests/services.py` | app/modules | ☐ |

- `datos`: falso positivo (palabra común; el fixture solo lo usa su archivo; solo se quitaron dos acciones de la lista).
- `scoped_platforms`: solo cambió el docstring de `authz.py`; sin cambio de comportamiento.
- `validar_datos`: cambio real; ahora rechaza el origen `heredado` (solo lo crea la migración). Lo llaman `access.services.otorgar` y `access_requests.services`, que solo pasan `solicitud` y `admin_de_area`.
- No lo detecta la herramienta: `ORIGENES` (ahora incluye `heredado`; lo usa el filtro del inventario) y los dos endpoints retirados.

## Criterios de aceptación
- [x] Conteo de filas migradas igual al de `user_platforms` menos las omitidas, que se cuentan por motivo (prueba de migración; el conteo literal no aplica: se omiten las filas sin acceso válido)
- [x] Los endpoints retirados responden 410 (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Genera → FNC-107 (borrar la tabla), FNC-108 (reconciliar grupos LDAP con los `heredado`)
- Depende de → FNC-036, FNC-019, FNC-054, FNC-063, Respuesta a P4

## Riesgos y reversión
- El frontend aún llama a los endpoints retirados hasta DIS-017/DIS-018: integrar en el mismo bloque.
- Reversión: bajar la migración de datos.

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest tests/access/test_migracion_0010.py` sin la migración | 9 failed (falta `0010_*.py`); con ella, 9 passed (upgrade con datos de ejemplo, omisiones por motivo, idempotencia, sin resucitar revocados, downgrade y nuevo upgrade) |
| `pytest tests/access/test_origen_heredado.py` sin `ORIGEN_HEREDADO` | Error de colección (`ImportError`); después de agregarlo, 8 passed |
| `pytest tests/access/test_endpoints_retirados.py` con los endpoints viejos | 2 failed (respondían 200 y escribían); con el 410, 4 passed |
| `pytest tests/access/test_inventario.py` tras agregar `heredado` a `ORIGENES` | 1 failed (el origen inválido de ejemplo era `heredado`); corregido el ejemplo |
| `venv/bin/python -m pytest -q` (completo, final) | 1924 passed, 15 xfailed; código de salida 0 (11 min 27 s) |
| Subconjunto tras los docstrings finales (`tests/access`, `tests/authz`, guardia, migraciones, auditoría CRUD, `tests/platforms`) | 306 passed, 1 xfailed; código 0 |
| Migración upgrade con datos de ejemplo y downgrade | Cubierta por `test_migracion_0010.py` en SQLite (ver arriba) |

No verificado:
- MySQL: las pruebas de migración usan SQLite. Se usa SQL portable de SQLAlchemy Core, sin dialecto propio; la columna `user` de `audit_logs` la cita SQLAlchemy.
- Datos reales de NEXUS: no hay copia en esta tarea; se validará en la prueba de concepto (decisión del orquestador).
- Membresía en los grupos LDAP de los accesos `heredado`: no se escribe ni se comprueba (FNC-108).
- Pantallas web: ninguna llama a los endpoints retirados.
- `revisor` y `auditor-seguridad` no se lanzaron (indicación del orquestador); quedan pendientes, sobre todo la autorización de la migración y de la revocación de `heredado`.
- Las pruebas de `heredado` que no fallaron antes de la implementación: las 8 de `test_origen_heredado.py` se corrieron por primera vez con `ORIGEN_HEREDADO` ya agregado (antes fallaban por el `ImportError`); `revocar` y `inventario` reutilizan código existente, por lo que pasan sin cambios de lógica.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-21 | En curso y En revisión (desarrollador): migración 0010, origen `heredado`, endpoints en 410; genera FNC-107 y FNC-108 |
