# FNC-060 — Consulta de auditoría por rol e historial por usuario y por plataforma

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auditoria |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-19 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-060-consulta-auditoria` (worktree `pokemon-wt-060`) |
| **Commits / PR** | `e4bdcbe` (local, sin PR) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de datos por rol) |

## Contexto
- `GET /audit` (`app/modules/api/routes.py:430-440`) filtra al admin por actor y no por área: ve lo que sus usuarios hicieron en otras áreas (SEG-16)
- No hay historial por usuario ni por plataforma (F-AUD-03)
- Requerimientos: F-AUD-03, F-AUD-04, RF-05

## Objetivo
- Mover la consulta a `app/modules/audit/api.py` con filtros (fecha, evento, usuario, plataforma, área), paginación y visibilidad superadmin todo, admin por área afectada, usuario sus registros; y agregar el historial por usuario y por plataforma

## Alcance
- **Incluye:**
  - `GET /audit` con filtros y paginación (contrato)
  - `GET /audit/users/<id>` y `GET /audit/platforms/<id>`
  - Alcance por `area_id` de FNC-047
- **No incluye:**
  - Exportar (sugerencia)
  - Retención (FNC-018)
  - Pantalla (DIS-020)

## Requisitos de FNC-047 (revisión 2026-10-14)
- Requisito previo de FNC-054 y FNC-056: no se registran eventos con antes/después de accesos sin esta consulta por alcance
- Admin: `area_id IN managed_area_ids()`; eventos sin área solo para el superadmin (SEG-16)
- `before`/`after` solo para el superadmin o dentro del alcance del admin
- `ip` = null para el usuario normal
- `time` en UTC (SEC-AUD-02): pendiente de decisión del dueño (hoy hora local)
- `page` (lista paginada) según el contrato `auditoria.md`

## Hallazgos de seguridad que absorbe
- **FNC-015** (resto): SEG-16. Con FNC-047 cierra FNC-015.

## Archivos previstos
- `app/modules/audit/api.py`
- `app/modules/audit/queries.py`
- `app/modules/audit/parametros.py` (validación de parámetros; agregado)
- `app/modules/api/routes.py` (retiro de `GET /audit`)
- `app/__init__.py` (registro)
- `tests/audit/test_api.py`
- `tests/test_alcance_por_area.py`, `tests/matriz_proteccion.py` (agregados)

## Reutilización
- Modelo de FNC-047
- `managed_area_ids`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `GET /api/v1/audit` | Endpoint | Pantalla `/audit` (`audit-log.tsx`), `lib/api.ts` (`api.audit`), `lib/access/audit.ts` (FNC-069) | Pruebas backend; pantalla sin validar (DIS-020) |

## Variables y configuración
- `AUDIT_PAGE_SIZE_MAX` (500) y `LIMITE_POR_DEFECTO` (100): constantes en `audit/parametros.py`, registradas.
- Alta: `POR_PAGINA_POR_DEFECTO` 25, `POR_PAGINA_MAX` 100, `LARGO_MAX_BUSQUEDA` 100, `RANGO_MAX_DIAS` 366, `MAX_DIGITOS_ENTERO` 9 (VARIABLES.md e HISTORIAL.md).
- Sin variables de entorno nuevas (`.env.example` sin cambios).

## Criterios de aceptación
- [x] Admin del área X no ve eventos del área Y de un usuario compartido (prueba de regresión SEG-16)
- [x] Usuario ve solo los suyos (prueba)
- [x] El historial por plataforma de un área ajena responde **404** al admin (prueba; ver decisiones)
- [x] Criterios comunes backend (FNC-037): matriz de protección, `400 parametro_invalido`, `404 no_encontrado`

## Impacto cruzado
- Genera → DIS-020
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-047, FNC-038
- Contrato → docs/contratos/auditoria.md

## Riesgos y reversión
- La pantalla actual usa `?limit=`: se mantiene compatible hasta DIS-020.
- Reversión: revertir la rama.

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| Tema | Decisión (lo más seguro de `docs/seguridad/LINEAMIENTOS.md`) |
|---|---|
| Plataforma de área ajena | `404`, no `403`: el contrato y SEC-AUTHZ-04 prevalecen sobre el criterio de la ficha |
| Admin y eventos sin área | Solo el superadmin; el admin tampoco ve sus propios logins (Anexo A: "área afectada") |
| Usuario: `before`/`after` | `null`, igual que `ip` (requisito de FNC-047: solo superadmin o admin en su alcance) |
| Usuario: registros anteriores a FNC-047 | Sin coincidencia por correo; solo los ve el superadmin (SEG-060-01). No hay corte fijo seguro: el id y la fecha de la migración `0002` cambian por entorno, y aun con corte las filas heredadas de una cuenta borrada pasarían a quien reciba su correo |
| `GET /audit/users/<id>` del admin | Él mismo o cuentas que `can_manage_user` (SEC-AUTHZ-06); otras → `404` |
| `time` en UTC | Sin cambio (hora local `AAAA-MM-DD HH:MM:SS`): pendiente del dueño; `from`/`to` con zona se convierten a hora local |
| Filtros | Se aplican también sin `page`; `400` incluye `fields` (aditivo); `limit` < 1 se acota a 1 |

## Verificación
- Regresión que primero falla: con `app/__init__.py` y `api/routes.py` de `develop`, `tests/audit/test_api.py` + pruebas de auditoría de `test_alcance_por_area.py`: **54 failed, 16 passed** (código 1); `test_admin_area_no_ve_eventos_de_otra_area_de_un_usuario_compartido` falló antes y pasa después.
- xfail de SEG-16 retirado. Nota: aquel xfail fallaba por un artefacto de la prueba (Flask-Login guarda el usuario en `g`, compartido por el app context de la prueba), no por SEG-16 en sí; se limpia `g._login_user` y se agregó la regresión real del usuario compartido.
- Pytest completo (`venv/bin/python -m pytest -q`): **1144 passed, 14 xfailed**, código 0 (294 s). Antes (develop): 1070 passed, 15 xfailed.
- No verificado: pantalla `/audit` en navegador (no se tocó el frontend; DIS-020) y MySQL (pruebas en SQLite).

## Hallazgos de auditor-seguridad (Aprobado)
| ID | Severidad | Estado |
|---|---|---|
| SEG-060-01 | Media | Corregido: coincidencia por correo retirada (`queries.de_usuario` solo por id). Regresión `test_correo_reutilizado_no_ve_eventos_de_la_cuenta_borrada` (falló antes) |
| SEG-060-02 | Baja | Corregido: `OverflowError` de `from`/`to` → `400 parametro_invalido`. Regresión `test_fechas_en_el_limite_no_dan_500` (3 casos; antes 500) |
| SEG-060-03 | — | Endurecimiento pendiente: `from` o `to` solos dejan el rango abierto (el tope de 366 días solo aplica con ambos) |

## Impacto en elementos compartidos (salida real de `impacto.py`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/audit` | endpoint | `app/modules/api/routes.py` | `app/modules/audit/events.py`, `app/modules/audit/routes.py`, `frontend/src/app/audit/page.tsx`, `frontend/src/components/app-shell.tsx`, `frontend/src/lib/access/audit.ts`, `frontend/src/lib/api.ts`, `frontend/tests/accesibilidad/pares-contraste.ts`, `frontend/tests/components/audit-log.test.tsx` (+5) | app/modules, frontend/src, frontend/tests, tests, tests/audit, tests/users | ☐ |
| `_registrar` | función | `tests/test_alcance_por_area.py` | `tests/provisioning/conftest.py` | tests/provisioning | ☐ |
| `auditoria` | función | `tests/test_alcance_por_area.py` | `app/modules/audit/events.py`, `frontend/src/lib/access/audit.ts`, `frontend/src/lib/access/types.ts`, `tests/areas/test_alta_y_baja_por_admin.py`, `tests/audit/test_registro_ampliado.py`, `tests/users/test_roles_y_areas_administradas.py` | app/modules, frontend/src, tests/areas, tests/audit, tests/users | ☐ |
| `list_audit` | función | `app/modules/api/routes.py` | `app/modules/audit/routes.py` | app/modules | ☐ |
| `stats` | función | `app/modules/api/routes.py` | `app/modules/core/routes.py`, `frontend/src/components/dashboard.tsx`, `frontend/src/lib/api.ts`, `frontend/tests/lib/api.test.ts` | app/modules, frontend/src, frontend/tests | ☐ |

Lectura:
- `/audit` (real): misma ruta `/api/v1/audit`, movida a `audit/api.py`; compatible sin `page` (`audit-log.tsx`, `api.audit`) y con `page` (`lib/access/audit.ts`). Cambia el alcance del admin (solo sus áreas): validar en DIS-020. `events.py` y `audit/routes.py` solo la mencionan en texto o son la ruta heredada `/audit` (410).
- `list_audit`: homónimo; la de `audit/routes.py` es la ruta heredada (410). La nueva vive en `audit/api.py` con el mismo nombre.
- `stats`: homónimo de contexto; no cambió (solo el comentario de sección vecino). `core/routes.py` y el frontend usan su propio `stats`/`/stats`.
- `_registrar` y `auditoria`: funciones locales de `test_alcance_por_area.py`; las de `provisioning/conftest.py` y los demás archivos son homónimos sin relación (o la palabra "auditoría").

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-14 | Requisitos agregados por la revisión de FNC-047 |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador). Implementada en `fnc/FNC-060-consulta-auditoria`: `audit/api.py`, `queries.py`, `parametros.py`; `GET /audit` sale de `api/routes.py`; matriz con los 2 endpoints nuevos; cierra SEG-16 (FNC-015). Sin migración. Sin revisores (por instrucción) |
| 2026-10-20 | auditor-seguridad Aprobado; SEG-060-01 y 02 corregidos con regresiones (4 failed antes); 03 anotado. `merge --no-ff develop` (FNC-064, `514e87f`) |
