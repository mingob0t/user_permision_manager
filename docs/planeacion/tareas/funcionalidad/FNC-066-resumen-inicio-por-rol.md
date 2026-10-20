# FNC-066 — Resumen del inicio por rol: pendientes, accesos y solicitudes

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | estadisticas |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local |
| **Rama** | `fnc/FNC-066-resumen-inicio` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de datos por rol) |

## Contexto
- La tabla de pantallas pide un Inicio distinto por rol (usuario: mis accesos y solicitudes; admin: pendientes y resumen de sus áreas; superadmin: global)
- `GET /stats` (`routes.py`) solo da contadores y visitas
- Requerimientos: Pantalla "Inicio" de REQUERIMIENTOS §4

## Objetivo
- Exponer `GET /home/summary` con los contadores por rol, sin tocar `GET /stats`

## Alcance
- **Incluye:**
  - Usuario: accesos activos, solicitudes por estado
  - Admin: pendientes de sus áreas, accesos fallidos de sus áreas
  - Superadmin: pendientes, fallidos y totales globales
- **No incluye:**
  - Gráficas nuevas
  - Cambiar `GET /stats`
  - Pantalla (DIS-024)

## Archivos previstos
- `app/modules/home/api.py`
- `app/modules/home/services.py`
- `app/__init__.py` (registro)
- `tests/home/`

## Reutilización
- Consultas de FNC-054, FNC-056 y FNC-049

## Criterios de aceptación
- [x] Cada rol recibe solo sus contadores (pruebas, `tests/home/test_resumen.py`)
- [x] Criterios comunes backend (FNC-037): sesión `401`, caso en `tests/matriz_proteccion.py`, sin migración

## Impacto cruzado
- Genera → DIS-024
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-056, FNC-049, FNC-038
- Contrato → docs/contratos/inicio.md
- Genera → FNC-100 (Propuesta)

## Implementación
- `app/modules/home/services.py` (`resumen`) y `api.py` (`GET /api/v1/home/summary`, `@login_required`); registro en `app/__init__.py`.
- `app/modules/access_requests/consultas.py` (`mias`): consulta extraída de `GET /access-requests/mine`, que ahora la usa.
- Reutiliza: `access.consultas.de_usuario`, `access_requests.consultas.mias`, `approvals.bandeja`, `access.inventario.visibles`, `authz.scoped_areas`, `access_requests.serializacion.fecha`.
- `GET /stats` no cambia: endpoint propio (lo dicen la ficha y el contrato `inicio.md`; la forma de `/stats` la usa el panel actual).

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| Tema | Decisión | Motivo |
|---|---|---|
| Contenido | Solo los conteos y la fecha del contrato; sin listas ni nombres | Mínima exposición (SEC-AUTHZ, datos de otras cuentas) |
| `pending_approvals` | Igual al total de `/access-requests/inbox` (`bandeja`): sin las propias ni las de otros admins | Mismo alcance que la bandeja (SEC-AUTHZ-06); probado |
| `failed_access`, `active_access` | Con `inventario.visibles`: admin solo plataformas de sus áreas | Mismo alcance que el inventario |
| `totals.platforms` del admin | Plataformas de las áreas que administra (no las de sus accesos en otras áreas) | "Sus áreas" del contrato |
| `totals.areas`/`platforms` | Incluyen inactivas, como `/stats` | Consistencia con el panel |
| Superadmin | Sin `my_access` ni `my_requests` | Contrato; acceso por defecto (P6) |
| Fallos de aprovisionamiento | No se usan `provisioning/consultas.visibles` ni trabajos: el contrato no tiene ese campo y la consulta es de FNC-062 (no está en `develop`) | Se propone FNC-100 |

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest tests/home -q` antes de implementar | 10 failed (404: la ruta no existía) |
| `venv/bin/python -m pytest tests/home -q` después | 10 passed |
| `venv/bin/python -m pytest -q` (completo) | 1551 passed, 15 xfailed; código de salida 0 |

- Cliente web (`frontend/src/lib/access/home.ts`, tipo `HomeSummary`) revisado a mano: misma forma que la respuesta.
- No verificado: con MySQL (las pruebas usan SQLite); revisor y auditor-seguridad no lanzados (lo pidió el orquestador).

## Impacto en elementos compartidos
**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 4 elemento(s) usados en otras secciones: app/modules, frontend/src, frontend/tests, tests/access, tests/access_requests, tests/areas, tests/authz, tests/users. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/home/summary` | endpoint | `app/modules/home/api.py` | `frontend/src/lib/access/home.ts`, `frontend/tests/lib/access/errores.test.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |
| `escena` | función | `tests/home/test_resumen.py` | `tests/access/conftest.py`, `tests/access/test_api.py`, `tests/access/test_area_admin_sync.py`, `tests/access/test_inventario.py`, `tests/access/test_punta_a_punta.py`, `tests/access/test_puntos_de_extension.py`, `tests/access/test_servicio.py`, `tests/access_requests/conftest.py` (+9) | tests/access, tests/access_requests, tests/areas, tests/authz, tests/users | ☐ |
| `my_requests` | función | `app/modules/access_requests/api.py` | `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/types.ts` | frontend/src | ☐ |
| `resumen` | función | `app/modules/home/services.py` | `app/modules/directory/api.py`, `frontend/tests/lib/access/peticiones.test.ts` | app/modules, frontend/tests | ☐ |

Lectura:
- `/home/summary`: endpoint nuevo; lo consume el cliente web de FNC-069 (forma igual al contrato).
- `my_requests` (`access_requests/api.py`): solo cambia de dónde sale la consulta (`consultas.mias`), misma respuesta; los usos web son el nombre del campo del contrato. Cubierto por `tests/access_requests/`.
- `escena` y `resumen`: coincidencias de nombre (fixtures locales de otras carpetas, `directory.api` usa otro `resumen`); sin relación.

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada por el orquestador (modo autónomo) y En curso |
| 2026-10-20 | Implementada; 10 pruebas nuevas (fallaban antes); suite completa en verde (salida 0). En revisión. Genera FNC-100 |
