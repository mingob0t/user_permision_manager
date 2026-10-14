# ADR-002 — Migraciones versionadas de MySQL

- **Estatus:** Aceptada · **Fecha:** 2026-10-13 · **Tarea:** FNC-037 → FNC-039

## Contexto
- `create_all()` no altera tablas; `utils/migrations/` se aplica a mano sin registro
- La fase 3 altera `platforms`, `audit_logs`, `auth_config` y crea 5 tablas

## Alternativas
- **A. Alembic (Flask-Migrate)** ahora, adelantando esa parte de FNC-028: versiones, bajada, autogeneración
- **B. SQL numerado** en `utils/migrations/` + tabla `schema_migrations` propia: sin dependencia nueva, más manual

## Recomendación
- A; `create_all()` y el admin semilla se quedan hasta FNC-003/FNC-028

## Consecuencias
- FNC-028 conserva solo la limpieza de `scratch/` y `utils/`
- `RELEASES.md` agrega el paso de migración

## Decisión del dueño (2026-10-14)
- Alembic (Flask-Migrate o Alembic directo); cada cambio de tablas queda versionado.
