# FNC-029 — Dividir app/modules/api/admin.py, crud.py y create_app

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | api |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-029-119-dividir-monolitos` |
| **Commits / PR** | `[FNC-029]` y `[FNC-119]` en la rama (ver bitácora), sin push |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
`admin.py` 645 líneas con 7 responsabilidades; `crud.py` 480 con 3 entidades; `create_app` 183 líneas.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-05

## Objetivo
Dividir `api/admin.py`, `api/crud.py` y `create_app` en unidades de una responsabilidad, sin cambio observable: mismas rutas, métodos, protección, códigos HTTP, `code` y `fields`. Se implementa junto con FNC-119 (misma rama).

## Alcance
- **Incluye:** mover cada grupo de rutas al módulo de dominio, borrar `admin.py` y `crud.py` y partir `create_app` en funciones.
- **No incluye:** cambiar reglas de permisos o respuestas; refactorizar `routes.py`, `auth.py` ni `platforms/api.py`.

## Nueva estructura
| Antes | Ahora | Blueprint |
|---|---|---|
| `crud.py`: `PUT /areas/<id>/users` | `areas/api.py` | `api_areas` (existente) |
| `crud.py`: alta, edición, baja de cuentas y `PUT /users/<id>/platforms` (410) | `users/api.py` | `api_users` (existente) |
| `crud.py`: `PUT /me/preferences` | `users/preferencias_api.py` | `api_preferences` (nuevo) |
| `crud.py`: `/users/inactive`, `/users/purge` | `users/higiene_api.py` | `api_hygiene` (nuevo) |
| `crud.py`: `RESERVED_NAMES` | `users/roles.py` | — |
| `admin.py`: `/settings` | `settings/api.py` (+ `settings/logo.py`) | `api_settings` (nuevo) |
| `admin.py`: `/smtp`, `/templates`, `/notifications` | `notifications/api.py` | `api_notifications` (nuevo) |
| `admin.py`: `/backup` | `settings/respaldo_api.py` | `api_backup` (nuevo) |
| `create_app` (183 líneas) | `_configurar`, `_validar_configuracion`, `_iniciar_extensiones`, `_registrar_blueprints`, `_registrar_cli_y_manejadores`, `_crear_tablas`, `_registrar_manejadores_de_error` en `app/__init__.py`; `create_app` queda de 10 líneas | — |

## Decisiones
Todas: **decisión del orquestador (pendiente de validar en la prueba de concepto)**.
- Los blueprints nuevos (`preferencias`, `higiene`, `settings`, `notifications`, `respaldo`) se crean porque no había un módulo de API de esa entidad; los demás reutilizan `users_api_bp` y `areas_api_bp`.
- Cambia el nombre de endpoint de Flask de las rutas movidas (`api_crud.create_user` → `api_users.create_user`, etc.). Nada del código, las pruebas ni el frontend usa esos nombres (`grep`).
- El orden de registro de blueprints cambia (las rutas movidas se registran donde estaban `crud_bp` y `admin_bp`, junto a `api_bp`); no hay rutas que se solapen: Werkzeug ordena por especificidad y `/users/inactive` no choca con `/users/<int:user_id>`. Se verificó con la comparación de `url_map`.
- El orden de los pasos de `create_app` se conserva (configurar → validar variables → extensiones → blueprints → CLI y manejadores de eventos → tablas → manejadores de error); la importación de modelos y la creación de tablas van juntas en `_crear_tablas`.
- Los dos `import json` locales de `respaldo` y el resto del código de las rutas se movieron sin cambios; no se separó la lógica de respaldo en un servicio (fuera de alcance, sin cambio de comportamiento).
- `RESERVED_NAMES` pasa a `users/roles.py` porque `users/directory_accounts.py` lo importaba de `api/crud.py` (dependencia de un módulo de dominio hacia la capa de rutas).
- Cada archivo nuevo queda entre 18 y 330 líneas (`users/api.py` el mayor: alta, edición, baja, `managed-areas` y alta de directorio; es una sola entidad).

## Comparación de `app.url_map` (antes y después)
- Antes: `29e96f4` (develop) exportado con `git archive`; después: la rama. Script: `app.url_map.iter_rules()` con `(regla, métodos sin HEAD/OPTIONS)` ordenado.
- **68 reglas en ambos; el listado de ruta y método es idéntico** (`diff` vacío).
- Con el nombre del endpoint, difieren 29 líneas, todas por el cambio de blueprint de las rutas movidas (tabla de arriba); ninguna ruta se perdió ni se agregó.
- Blueprints antes: `api_admin` y `api_crud` existían; ahora no, y aparecen `api_settings`, `api_notifications`, `api_backup`, `api_preferences`, `api_hygiene`. Manejadores de error (400, 404, 500), cookie `nexus_session`, sesión de 7 días y comando `provisioning` idénticos.
- La guardia de rutas y la matriz de protección (`tests/test_guardia_rutas.py`, `tests/matriz_proteccion.py`) pasan sin cambios.

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [x] Prueba de regresión que primero falla (si corrige un defecto)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Verificación
- Línea base (`29e96f4`, copia exportada): `2360 passed, 15 xfailed, código de salida 0 (cifra registrada al cerrar FNC-030 sobre `29e96f4`; la corrida propia de línea base se perdió al cortarse la sesión y no se repitió)`
- Después: ``venv/bin/python -m pytest -q -p no:cacheprovider -rX` → **2393 passed, 15 xfailed, código de salida 0** (2360 + 33 pruebas nuevas)`
- No ejecutado: revisor (no se lanza en esta ejecución, por indicación), navegador. Auditor-seguridad: no requerido (sin cambio de reglas); la matriz de protección cubre las rutas movidas.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/areas/<int:area_id>/users` (PUT) | endpoint | `app/modules/areas/api.py` (antes `api/crud.py`) | `tests/matriz_proteccion.py` | tests | ☐ |
| `/users` (POST), `/users/<int:user_id>` (PUT, DELETE), `/users/<int:user_id>/platforms` (PUT, retirado) | endpoints | `app/modules/users/api.py` (antes `api/crud.py`) | `access/api.py`, `api/routes.py`, `audit/api.py`, `platforms/api.py`, `frontend/src/app/users/page.tsx` y 39 más (la ruta `/users` es compartida por nombre con otros módulos) | app/modules, frontend/src, tests | ☐ |
| `create_app` | función | `app/__init__.py` | `run.py`, `migrations/env.py`, `app/utils/uri_bd.py`, `connectors/*`, `provisioning/*` y 8 más (menciones por nombre) | arranque de la app, migraciones, pruebas | ☐ |
| `leer_cuerpo`, `json_payload` | funciones | `app/modules/api/helpers.py` | 6 módulos de API y `tests/api/test_helpers_comunes.py` | todo endpoint que lee cuerpo | ☐ |
| `BASE_URL` | variable | `app/modules/auth/services.py` | `api/auth.py`, `notifications/access_notifications.py` y pruebas | avisos de bienvenida | ☐ |
| `create_user` | función | `app/modules/users/api.py` | `directory/writer.py`, `tests/directory/test_writer.py` (coincide por nombre con otra función; no se tocó) | — | ☐ |
| `SECRET_KEY` | variable | `app/__init__.py` | `provisioning/saneo.py`, pruebas (sin cambio de valor) | — | ☐ |

Salida de `impacto.py` (10 filas, ejecutada el 2026-10-27 antes del commit). Validar: los endpoints movidos (nombres de endpoint de Flask cambian de blueprint: `api_crud.*` → `api_users.*`, `api_areas.*`, `api_preferences.*`, `api_hygiene.*`; `api_admin.*` → `api_settings.*`, `api_notifications.*`, `api_backup.*`; las rutas, métodos, códigos, `code` y `fields` no).

## Impacto cruzado
- Depende de → Después de FNC-020
- Se implementa junto con → FNC-119 (misma rama)
- Genera → FNC-120 (propuesta, ver FNC-119)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | Propuesta → En curso → En revisión: `admin.py` y `crud.py` divididos por dominio, `create_app` en funciones; `url_map` idéntico (68 reglas). Commit `[FNC-029]` local, sin push |
