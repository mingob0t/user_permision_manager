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
| **Requiere migración BD** | No (P4: las filas se descartan) |
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

## Decisiones
| Tema | Valor aplicado | Fuente |
|---|---|---|
| Datos de `user_platforms` | Se descartan: no se migran a accesos y no hay origen `heredado` ni migración | P4 del dueño (`contratos/README.md`) |
| Decisión anterior del orquestador (migrar a `heredado`, migración 0010, `accesos.md` 1.2) | **Revertida** por P4 del dueño; el primer commit de la rama la implementó y el segundo la quita | Corrección del orquestador |
| Endpoints | `410 endpoint_retirado` (`use: POST /access-requests`); se conserva la protección por rol (401/403) y siguen en la matriz con 410 | Orquestador |
| Tabla | `user_platforms` y `User.platforms` se conservan, obsoletas; borrado en FNC-107 | Alcance de la ficha |
| `Platform.to_dict` | Ya no exponía `user_ids` desde FNC-046; sin cambio | — |
| Transición | Quien veía una plataforma solo por `user_platforms` ya no la ve desde FNC-063; para recuperarla debe solicitar acceso | FNC-063, P4 |

## Archivos tocados (resultado neto frente a `develop`)
| Archivo | Cambio |
|---|---|
| `app/modules/api/helpers.py` | `endpoint_retirado`, `REEMPLAZO_ASIGNACION` |
| `app/modules/api/crud.py`, `app/modules/platforms/api.py` | Las dos rutas responden 410; imports sin uso retirados |
| `app/authz.py` | Solo docstring |
| `docs/contratos/README.md`, `plataformas-integracion.md` | 410 como cambio aditivo (sin cambio de versión); P4 intacta |
| `docs/backend/README.md`, `docs/estandarizacion/03-reutilizacion.md`, `CHANGELOG.md`, `docs/logs/2026-10-21.md` | Documentación |
| `tests/access/test_endpoints_retirados.py` | 4 pruebas nuevas |
| `tests/matriz_proteccion.py` | Los dos casos esperan 410 |
| `tests/test_alcance_por_area.py`, `tests/test_auditoria_crud.py`, `tests/users/test_roles_y_areas_administradas.py`, `tests/authz/test_visibilidad_por_accesos.py` | Se retiran las pruebas de la asignación (el endpoint ya no escribe): 4 casos parametrizados y 2 pruebas de FNC-021, 1 de FNC-044, 1 de FNC-063 y 2 acciones de auditoría; las cubre `test_endpoints_retirados.py` |

## Reutilización
- Modelo de FNC-054

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `PUT /platforms/<id>/users`, `PUT /users/<id>/platforms` | Endpoints retirados (410) | Ninguna llamada en `frontend/src` (ya no existían en DIS-017/DIS-018); `tests/matriz_proteccion.py` | Pruebas en verde |
| `Platform.to_dict` | Serialización | Sin cambio (ya no exponía `user_ids`) | Sí |
| `api/helpers.endpoint_retirado` | Respuesta (nueva) | `api/crud.py`, `platforms/api.py` | Sí |

IMPACTO_AQUI

## Criterios de aceptación
- [x] ~~Conteo de filas migradas~~ No aplica: P4 descarta las filas (sin migración)
- [x] Los endpoints retirados responden 410 (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Genera → FNC-107 (borrar la tabla)
- Depende de → FNC-036, FNC-019, FNC-054, FNC-063, Respuesta a P4

## Riesgos y reversión
- Ninguna pantalla llama ya a los endpoints retirados (DIS-017/DIS-018).
- Reversión: revertir la rama (los endpoints vuelven a escribir en la tabla, que no se tocó).

## Verificación
| Comando | Resultado real |
|---|---|
| `pytest tests/access/test_endpoints_retirados.py` con los endpoints viejos | 2 failed (respondían 200 y escribían); con el 410, 4 passed |
| `venv/bin/python -m pytest -q` (completo, final) | PYTEST_AQUI |

No verificado:
- Pantallas web: ninguna llama a los endpoints retirados.
- `revisor` y `auditor-seguridad` no se lanzaron (indicación del orquestador); quedan pendientes.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-21 | En curso y En revisión (desarrollador). Primer commit: migrar a `heredado` (decisión del orquestador). Revertido en un segundo commit por P4 del dueño: sin migración ni origen `heredado`; quedan los 410 y la tabla obsoleta. Genera FNC-107 |
