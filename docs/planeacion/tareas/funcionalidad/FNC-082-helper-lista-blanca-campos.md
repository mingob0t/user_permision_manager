# FNC-082 — Helper común de lista blanca de campos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | api |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Creada** | 2026-10-19 |
| **Inicio** | 2026-10-27 |
| **Estatus Git** | commit local, sin push |
| **Rama** | `fnc/FNC-030-082-helpers-comunes` (junto con FNC-030) |

## Contexto
- La lista blanca (SEC-AUTHZ-09, `400 campo_no_permitido`) se resuelve en cada módulo con su propia función: `campos_no_permitidos` en `users/roles.py` y `users/directory_accounts.py`, y equivalentes en áreas y plataformas.
- Origen: revisión de FNC-064.

## Criterios de aceptación
- [x] Un helper en `app/modules/api/helpers.py` (campos permitidos → campos rechazados) usado por roles, áreas, directorio y plataformas
- [x] Sin cambio de comportamiento: las pruebas de lista blanca existentes siguen en verde

## Endpoints afectados
Todos leen el cuerpo con `leer_cuerpo(permitidos)` (`400 cuerpo_invalido` / `400 campo_no_permitido`, mismo orden que antes):

| Módulo | Endpoints | Permitidos |
|---|---|---|
| `areas/api.py` | `POST /areas`, `PUT /areas/<id>` | `areas.validacion.CAMPOS_PERMITIDOS` |
| `platforms/api.py` | `POST /platforms`, `PUT /platforms/<id>` | `platforms.validacion.CAMPOS_PERMITIDOS` |
| `users/api.py` | `POST /users/directory` | `directory_accounts.CAMPOS_PERMITIDOS` |
| `access_requests/api.py` | `POST /access-requests`, `approve`, `reject` | `CAMPOS_PERMITIDOS` / campos de la decisión |
| `access/api.py` | revocar | `CAMPOS_REVOCAR` |
| `connectors/api.py` | `PUT`, `DELETE`, `POST .../test` | `CAMPOS_PERMITIDOS` / ninguno |
| `directory/api.py` | `GET /auth-config` (cuerpo), `POST /directory/test` | ninguno |
| `provisioning/api.py` | `POST /jobs/<id>/retry` | ninguno |
| `api/crud.py` | `POST /users`, `PUT /users/<id>` | lista **negra** `roles.CAMPOS_NO_PERMITIDOS` con `campos_prohibidos` |

## Decisiones
Todas: **decisión del orquestador (pendiente de validar en la prueba de concepto)**.
- Un helper `campos_no_permitidos(datos, permitidos=())` (rechazados ordenados) y `leer_cuerpo(permitidos=())` que junta lectura del objeto y lista blanca; sin permitidos equivale al cuerpo `{}` obligatorio (conectores, directorio, reintento).
- `users/roles.py` era lista **negra**; no se mezcla con la blanca: helper aparte `campos_prohibidos(datos, prohibidos)`. Las funciones locales de roles, áreas, plataformas y directorio se borraron y las constantes quedan en su módulo.
- Las variantes locales `_cuerpo_vacio` (conectores, directorio) y la lectura inline de las solicitudes, accesos y reintentos pasan a `leer_cuerpo`. La protección `escritura_del_portal` ya es única (`api/csrf_provisional.py`): no se toca.
- Sin diferencias de comportamiento entre módulos: todos respondían `400 cuerpo_invalido` y `400 campo_no_permitido` con el mismo cuerpo.

## Verificación
- Suite completa: 2360 passed, 15 xfailed, código de salida 0 (línea base 2341); incluye las pruebas de lista blanca existentes y 19 nuevas en `tests/api/test_helpers_comunes.py` (lista blanca, lista negra, `leer_cuerpo`, `json_payload`).
- No ejecutado: revisor ni auditor-seguridad.

## Impacto en elementos compartidos
Ver FNC-030 (misma rama): `api/helpers.py` es compartido; los endpoints afectados son los de la tabla anterior.

## Impacto cruzado
- Origen ← FNC-064
- Relacionadas → FNC-044, FNC-045, FNC-046

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-19 | Creada como Propuesta (revisión de FNC-064) |
| 2026-10-27 | Implementada con FNC-030: `campos_no_permitidos`, `campos_prohibidos` y `leer_cuerpo`; En revisión; commit local `[FNC-082]` |
