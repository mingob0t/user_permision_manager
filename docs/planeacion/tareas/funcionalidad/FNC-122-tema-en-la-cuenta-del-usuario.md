# FNC-122 — Preferencias: guardar el tema en la cuenta del usuario

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | preferencias |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Rama** | `fnc/FNC-122-tema-en-la-cuenta` |
| **Creada** | 2026-10-27 |
| **Requiere migración BD** | Sí (columna `pref_theme`) |
| **Requiere auditor-seguridad** | No |

## Contexto
FNC-032 guarda el tema en `localStorage` (por navegador). `PUT /me/preferences` y `GET /me` no tienen campo de tema (`app/modules/api/crud.py`, `routes.py`, `auth/models.py`).

## Alcance
- Columna `pref_theme` con migración Alembic, validada contra la lista de temas; expuesta en `/me` y `/me/preferences`.
- No hay contrato de preferencias en `docs/contratos/`; la forma queda en `docs/backend/README.md`. Tarea web vinculada: FNC-123.

## Impacto cruzado
- Origen ← FNC-032
- Genera → FNC-123 (web, Propuesta): el selector lee y guarda el tema en la cuenta

## Implementación
- `app/modules/users/temas.py`: `TEMA_POR_DEFECTO` y `TEMAS_VALIDOS` (ids de `frontend/src/lib/tema.ts`: sistema, claro, oscuro, esmeralda, obsidiana, rosa, violeta).
- `User.pref_theme` (`auth/models.py`): texto, no nulo, `'sistema'` por defecto; migración `0011_tema_en_la_cuenta.py` (con `downgrade`).
- `PUT /me/preferences` (`users/preferencias_api.py`): acepta `theme`; valor fuera de la lista o que no es texto → `422 validacion` con `fields.theme`, antes de aplicar cualquier otra preferencia. Responde `preferences.theme`.
- `GET /me` (`api/routes.py`): `preferences.theme`.
- Decisiones del orquestador (pendiente de validar en la prueba de concepto): la columna se llama `pref_theme` (convención `pref_*` y la ficha) y la clave de la API es `theme`; los valores válidos son los ids reales del frontend (en español), no `light`/`dark`; no nulo con `'sistema'` para que las cuentas existentes no tengan `null`; la tarea web es FNC-123 (carril FNC); sin contrato nuevo (no existía uno de preferencias); sin tocar la lista blanca general (FNC-120).
- Variables: ninguna (la lista de temas es una constante de código, no configurable); sin `.env.example` ni `HISTORIAL.md`.

## Impacto en elementos compartidos
| Elemento | Definido en | Usado en | Validar |
|---|---|---|---|
| `User` (columna nueva `pref_theme`) | `app/modules/auth/models.py` | todo el backend que lee usuarios; `test_migraciones` (compara modelo y migraciones) | `alembic upgrade head` en un entorno con datos |
| `GET /me` (clave nueva `preferences.theme`) | `app/modules/api/routes.py` | frontend (sesión del usuario); la clave es aditiva | que el frontend ignore claves desconocidas (no se tocó) |
| `PUT /me/preferences` (acepta `theme`; `422` nuevo) | `app/modules/users/preferencias_api.py` | `tests/test_auditoria_crud.py`, `test_cuerpo_validado.py`, `matriz_proteccion.py`; pantalla de Ajustes | sin cambio para los clientes que no envían `theme` |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta desde FNC-032 |

- 2026-10-27: renumerada de FNC-120 a FNC-122 por colisión de ID (FNC-120 ya es la lista blanca estricta, de FNC-119).

- 2026-10-27: implementada. Pruebas escritas primero (fallaban por `ModuleNotFoundError: temas`): `tests/users/test_tema_en_la_cuenta.py` (guardar, leer, inválido, usuario A/B, sin tema) y `tests/test_migracion_0011.py`. Estatus: En revisión.

## Verificación
- Nuevas + `test_migraciones.py`: 25 passed.
- Pytest completo (salida a archivo, luego `echo $?`): 2423 passed, 14 xfailed, código de salida 0, 19 min.
- `impacto.py`: `/me` y `User` (tabla en *Impacto en elementos compartidos*); sin validar en navegador.
- Sin `tester`, `revisor` ni `auditor-seguridad` (no se lanzaron desde este agente); la tarea toca datos de usuario: revisión independiente pendiente.
- No verificado: frontend (fuera de alcance), migración sobre PostgreSQL (las pruebas usan SQLite).

- 2026-10-27: `auditor-seguridad` Aprobado con observaciones: sin IDOR (solo `current_user`), sin asignación masiva nueva, lista blanca estricta, migración 0011 correcta; 225 + 947 pruebas en verde. Observación previa (no la introduce el cambio): `PUT /me/preferences` sin `@escritura_del_portal`, riesgo bajo sin CORS; anotada en FNC-008. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto). Pendiente: migración en MySQL real.
