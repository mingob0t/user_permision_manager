# FNC-059 — Inventario de permisos: quién tiene qué plataforma, nivel, desde cuándo y quién aprobó

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local |
| **Rama** | `fnc/FNC-059-inventario-permisos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de datos por rol) |

## Contexto
- F-AUD-02 pide un inventario de permisos; hoy no existe y los datos nacen con FNC-054
- Requerimientos: F-AUD-02, F-AUD-04, RF-05

## Objetivo
- Exponer `GET /access/inventory` con filtros (área, plataforma, usuario, nivel, estado, origen) y paginación, con alcance superadmin todo, admin sus áreas y usuario lo suyo

## Alcance
- **Incluye:**
  - Consulta paginada y filtrable desde `platform_access_grants`
  - Columnas: usuario, plataforma, área, nivel, origen, desde, quién aprobó, estado
  - Alcance por rol
- **No incluye:**
  - Exportar a CSV o Excel (sugerencia fuera de alcance)
  - Conciliación con LDAP (RF-05)
  - Pantalla (DIS-021)

## Archivos previstos
- `app/modules/access/inventory.py`
- `app/modules/access/api.py` (una ruta)
- `tests/access/test_inventory.py`

Realizados (FNC-058 trabaja `access/api.py` en paralelo: blueprint propio):
- `app/modules/access/inventario.py` (consulta: `visibles`, `filtrar`, `ordenados`)
- `app/modules/access/inventario_api.py` (ruta y parámetros, `ACCESS_INVENTORY_PAGE_SIZE_MAX`)
- Forma `Access`: `access/serializacion.py` (`accesos_publicos`, FNC-058); la provisional `inventario_serializacion.py` se borró al integrar FNC-058 (FNC-095 resuelta aquí)
- `app/modules/audit/parametros.py`: `q` con caracteres de control → `400` (SEG-FNC059-01)
- `app/__init__.py` (registro del blueprint), `tests/matriz_proteccion.py` (caso y 400)
- `tests/access/test_inventario.py`

## Reutilización
- Modelo de FNC-054
- `scoped_platforms` o `managed_area_ids` de `app/authz.py`

## Variables y configuración
- `ACCESS_INVENTORY_PAGE_SIZE_MAX` (constante registrada).

## Decisiones
| Tema | Decisión | Fuente |
|---|---|---|
| Usuario | Sin inventario: `403` (usa `/me/access`); reemplaza "usuario lo suyo" del objetivo | Dueño; contrato `accesos.md` 1.1 |
| Admin | Accesos de las plataformas de las áreas que administra (incluye los de otros admins del área); sin áreas, lista vacía | Dueño; Anexo A |
| Filtro fuera de alcance (`area_id`, `platform_id`, `user_id` ajenos) | `200` con lista vacía, no `404`: es una lista (contrato: "no aparecen"), igual que `GET /audit`. El `404` de SEC-AUTHZ-04 aplica a recursos por id, que aquí no hay | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| `status` por defecto | `vigente` (excluye `revocado`) | Contrato |
| `q` | Nombre o correo del usuario, sin distinguir mayúsculas, comodines literales, ≤ 100 | Contrato; `leer_filtros` |
| `per_page` máx. | `ACCESS_INVENTORY_PAGE_SIZE_MAX` = `POR_PAGINA_MAX` (100) | Convenciones `README.md`; decisión del orquestador (pendiente de validar en la prueba de concepto) |
| `last_job_id` | Se incluye (solo lo ven admins y superadmin) | Contrato |
| CSV | No se exporta (fuera de alcance de la ficha) | Ficha |

## Criterios de aceptación
- [x] Un admin no ve accesos de áreas ajenas, ni filtrando por ellas (prueba `test_admin_no_ve_lo_ajeno_ni_filtrando`)
- [x] Un usuario no tiene inventario: `403` (decisión del dueño; prueba `test_usuario_no_tiene_inventario`)
- [x] Paginación con límite máximo como constante registrada (`ACCESS_INVENTORY_PAGE_SIZE_MAX`)
- [x] Criterios comunes backend (FNC-037): protección explícita, matriz de protección, `400 parametro_invalido`, formato paginado estándar, solo lectura (sin auditoría de escritura)

## Impacto cruzado
- Genera → DIS-021
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-038
- Contrato → docs/contratos/accesos.md

## Impacto en elementos compartidos
Salida de `impacto.py`:

**Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 15 archivos cambiados).

Revisado a mano (no son elementos de UI, pero se comparten):
- `app/__init__.py`: una línea de import y el blueprint en la tupla de la API v1. Afecta el arranque de toda la app (suite completa en verde). Puede chocar al integrar con FNC-058, que también registra blueprints.
- `tests/matriz_proteccion.py`: un `Caso` y dos `CASOS_400` nuevos. Lo usan `test_proteccion_por_rol.py` y `test_guardia_rutas.py`.
- `app/modules/audit/parametros.py` (`leer_filtros`, SEG-FNC059-01): lo usan `audit/api.py` (`/audit`, `/audit/users/<id>`, `/audit/platforms/<id>`), `access_requests/api.py` (`/access-requests/catalog`, `/mine`) y `access/inventario_api.py`. Solo cambia `q`, que con caracteres de control ahora responde 400.
- `access/serializacion.py` (FNC-058) se reutiliza sin cambios. `authz.py`, sin cambios.

Salida de `impacto.py` tras integrar FNC-058:

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 12 elemento(s) usados en otras secciones: app, app/modules, app/utils, frontend/src, frontend/tests, migrations/versions, tests, tests/access, tests/directory. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/access/inventory` | endpoint | `app/modules/access/inventario_api.py` | `frontend/src/lib/access/inventory.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |
| `_acceso` | función | `app/modules/access/inventario_serializacion.py` | `tests/access/test_api.py` | tests/access | ☐ |
| `_actores` | función | `app/modules/access/inventario_serializacion.py` | `app/modules/access/serializacion.py` | app/modules | ☐ |
| `_ids` | función | `tests/access/test_inventario.py` | `tests/access/test_api.py`, `tests/test_alcance_por_area.py` | tests, tests/access | ☐ |
| `_invalido` | función | `app/modules/access/inventario_api.py` | `app/modules/access_requests/api.py`, `app/modules/audit/api.py` | app/modules | ☐ |
| `_nombre` | función | `app/modules/access/inventario_serializacion.py` | `app/modules/access_requests/serializacion.py`, `app/modules/areas/validacion.py`, `app/modules/notifications/access_notifications.py`, `frontend/tests/lib/access/peticiones.test.ts`, `tests/directory/test_writer.py` | app/modules, frontend/tests, tests/directory | ☐ |
| `accesos_publicos` | función | `app/modules/access/inventario_serializacion.py` | `app/modules/access/api.py`, `app/modules/access/serializacion.py` | app/modules | ☐ |
| `filtrar` | función | `app/modules/access/inventario.py` | `app/authz.py`, `app/modules/audit/api.py`, `app/modules/audit/queries.py`, `frontend/src/app/error.tsx` | app, app/modules, frontend/src | ☐ |
| `inventario` | función | `tests/access/test_inventario.py` | `app/modules/access/models.py`, `frontend/src/lib/access/types.ts`, `frontend/tests/lib/access/peticiones.test.ts`, `migrations/versions/0007_accesos_otorgados.py` | app/modules, frontend/src, frontend/tests, migrations/versions | ☐ |
| `leer_filtros` | función | `app/modules/audit/parametros.py` | `app/modules/access_requests/api.py`, `app/modules/audit/api.py` | app/modules | ☐ |
| `ordenados` | función | `app/modules/access/inventario.py` | `app/modules/audit/api.py`, `app/modules/audit/queries.py`, `app/modules/users/directory_accounts.py`, `app/modules/users/roles.py` | app/modules | ☐ |
| `visibles` | función | `app/modules/access/inventario.py` | `app/authz.py`, `app/modules/api/routes.py`, `app/modules/audit/api.py`, `app/modules/audit/queries.py`, `app/utils/naming.py`, `frontend/src/components/areas/area-admins-panel.tsx`, `tests/test_alcance_por_area.py` | app, app/modules, app/utils, frontend/src, tests | ☐ |

Lectura de la tabla: `impacto.py` empareja por nombre.
- Reales: `/access/inventory`, que consume `frontend/src/lib/access/inventory.ts` (FNC-069, para DIS-021; el contrato no cambia), y `leer_filtros`, descrito arriba.
- Coincidencias de nombre sin relación: `_acceso`, `_actores`, `_nombre`, `_ids`, `_invalido`, `filtrar`, `ordenados`, `visibles` e `inventario` son privadas o locales a sus módulos.
- `inventario_serializacion.py` ya no existe: se borró en esta tarea.

## Seguridad
- auditor-seguridad: aprobado.
- SEG-FNC059-01 (Baja), corregido: `leer_filtros` rechaza en `q` NUL y cualquier carácter Unicode `Cc` (ESC, DEL, C1...) con `400 parametro_invalido`. Se revisa el valor sin recortar, porque `strip` quitaría los controles de los extremos.
  - Impacto: `GET /audit` (incluidos `/audit/users/<id>` y `/audit/platforms/<id>`), `GET /access/inventory` y `GET /access-requests/catalog`, que comparten `leer_filtros`. Un `q` con tabulador o salto de línea ahora responde 400.
  - Regresiones: 5 casos en `tests/audit/test_api.py::test_parametros_invalidos` y 2 en `tests/access/test_inventario.py`. Fallaron 7 antes de la corrección y pasan después.

## Verificación
| Comando | Resultado |
|---|---|
| `pytest tests/access/test_inventario.py` sin la ruta registrada | 19 failed (404): las regresiones fallan primero |
| `pytest tests/test_proteccion_por_rol.py tests/test_guardia_rutas.py` sin la ruta registrada | 7 failed |
| `pytest tests/test_proteccion_por_rol.py tests/test_guardia_rutas.py tests/access` | 357 passed |
| `pytest` completo (antes de integrar FNC-058) | 1408 passed, 14 xfailed, salida 0 |
| Regresiones SEG-FNC059-01 antes de la corrección | 7 failed |
| `pytest tests/audit tests/access tests/access_requests` tras la corrección | 299 passed, 1 xfailed |
| `pytest` completo (con FNC-058 integrada y SEG-FNC059-01) | 1461 passed, 15 xfailed, salida 0 |

auditor-seguridad: aprobado. `revisor`: no se lanzó, por indicación del orquestador. No hay migraciones, así que tampoco se probó MySQL real.

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada (modo autónomo) e implementada en blueprint propio; usuario 403; serialización provisional hasta FNC-095. En revisión; pendientes revisor y auditor-seguridad |
| 2026-10-20 | Merge de develop (FNC-058); usa `accesos_publicos` y se borra `inventario_serializacion.py` (FNC-095 resuelta). SEG-FNC059-01 corregido en `leer_filtros` |
