# FNC-122 — Preferencias: guardar el tema en la cuenta del usuario

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | preferencias |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |
| **Requiere migración BD** | Sí (columna `pref_theme`) |
| **Requiere auditor-seguridad** | No |

## Contexto
FNC-032 guarda el tema en `localStorage` (por navegador). `PUT /me/preferences` y `GET /me` no tienen campo de tema (`app/modules/api/crud.py`, `routes.py`, `auth/models.py`).

## Alcance
- Columna `pref_theme` con migración Alembic, validada contra la lista de temas; expuesta en `/me` y `/me/preferences`.
- Contrato en `docs/contratos/`; luego una tarea web vinculada para sincronizar el selector con la cuenta.

## Impacto cruzado
- Origen ← FNC-032

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta desde FNC-032 |

- 2026-10-27: renumerada de FNC-120 a FNC-122 por colisión de ID (FNC-120 ya es la lista blanca estricta, de FNC-119).
