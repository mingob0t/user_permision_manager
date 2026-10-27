# FNC-031 — Corregir notificaciones globales marcadas como leídas para todos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | notifications |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | rama local, sin push |
| **Rama** | `fnc/FNC-031-notificaciones-globales` |
| **Commits / PR** | |
| **Requiere migración BD** | Sí (0010) |
| **Requiere auditor-seguridad** | No |

## Contexto
`POST /notifications/read` marca las notificaciones globales como leídas para todos los usuarios.

Origen (diagnóstico inicial, FNC-001):
- [`docs/backend/README.md`](../../../backend/README.md): funcionales

## Objetivo
Marcar una notificación global como leída la marca solo para quien la leyó, con estado de lectura por usuario.

## Alcance
- **Incluye:** tabla `notification_reads` (migración 0010), `GET` y `POST /notifications/read` con lectura por usuario.
- **No incluye:** cambio del frontend (la forma de la respuesta no cambia), migrar el estado anterior de las globales, borrado de globales.

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [x] Prueba de regresión que primero falla (si corrige un defecto)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- Tabla aparte `notification_reads` (notificación, usuario, único el par, `CASCADE`) en vez de cambiar `is_read`: las propias siguen usando `is_read`.
- La respuesta mantiene la forma: `is_read` se calcula por usuario; el frontend (`AppNotification`, `notifications-list.tsx`) no cambia y cuenta las no leídas desde ese campo.
- Sin migración de datos: las globales con `is_read` verdadero eran efecto del defecto; parten sin leer para todos. `is_read` de una global ya no se consulta ni se escribe.
- Marcar dos veces una global es idempotente (no duplica filas).

## Impacto en elementos compartidos
| Elemento | Definido en | Usado en | Validar |
|---|---|---|---|
| `InAppNotification.to_dict(leida=None)` (parámetro opcional) | `notifications/models.py` | solo `notifications/api.py` | ninguno: sin argumento se comporta igual |
| `GET` y `POST /api/v1/notifications/read` (misma forma de respuesta) | `notifications/api.py` | `frontend/src/components/notifications-list.tsx` (`api.notifications`) | pantalla Notificaciones: contador y marcado de globales |
| `notification_reads` (tabla nueva) | migración 0010 | solo `notifications/api.py` | restaurar respaldo no la incluye |

## Impacto cruzado
- Depende de → —
- Genera → ninguna: el frontend no cambia.

## Verificación
- Antes: 4 pruebas rojas (leer global no la marca para otros, contador, marcado por id, bandera compartida).
- Después: `tests/test_notificaciones.py` 42 passed; sin el cambio en `api.py`, 4 rojas.
- Pytest completo (`pytest.main` desde Python con la ruta del worktree; salida a archivo): `PYTEST_EXIT=0`, 2403 passed, 14 xfailed, 0 fallos, 12 min 28 s.
- Nota: `python -m pytest` lanzado sin `cd` importa `app` de la carpeta base; una primera corrida dio 3 fallos por eso. Se corrigió con `sys.path` al worktree.
- Prueba: Flask-Login cachea al usuario en `g`; en pruebas de dos usuarios se limpia con `_por_usuario`.
- No verificado: la pantalla Notificaciones en navegador; PostgreSQL real (la cascada `ON DELETE` y la migración se probaron en SQLite con `test_migraciones.py`).

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | Implementada: `notification_reads`, migración 0010, pruebas de lectura por usuario |

- 2026-10-27: cierre del orquestador: lectura por usuario en `notification_reads` (migración 0010 con `downgrade`), misma forma de respuesta; pytest 2403 passed, 14 xfailed, código 0 (xfail de FNC-031 retirado). Sin auditor-seguridad: no toca autenticación ni permisos (cada usuario solo marca lo que ve). Pendiente: validar la migración en MySQL real (como FNC-039) y la pantalla Notificaciones en navegador. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
