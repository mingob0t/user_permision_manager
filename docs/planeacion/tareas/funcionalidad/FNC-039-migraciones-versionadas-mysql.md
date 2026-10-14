# FNC-039 — Migraciones versionadas de MySQL para la fase 3 (según ADR-002)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | bd |
| **Prioridad** | Alta |
| **Estatus** | En revisión (falta la prueba del dueño en MySQL real) |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-039-migraciones-alembic` |
| **Requiere migración BD** | Sí |
| **Requiere auditor-seguridad** | Sí (dependencia nueva) — Aprobado |

## Contexto
- Los cambios de esquema se aplican a mano desde `utils/migrations/` sin registro de cuáles se aplicaron, y `db.create_all()` (`app/__init__.py`) no altera tablas existentes (`docs/backend/README.md` §7)
- La fase 3 agrega columnas a `platforms`, `audit_logs` y `auth_config`, y cinco tablas nuevas; sin control de versiones no es repetible en staging y producción
- Además, `004_drop_access_requests.sql` borra una tabla `access_requests`: las tablas nuevas **no** deben llamarse así
- Requerimientos: RNF-04

## Objetivo
- Dejar un mecanismo de migraciones versionado y repetible (el que decida ADR-002) con la línea base del esquema actual, para que cada tarea de la fase agregue su migración

## Alcance
- **Incluye:**
  - Mecanismo elegido en ADR-002 (recomendado: Alembic con Flask-Migrate) y su línea base del esquema actual de MySQL
  - Registro de las migraciones heredadas 001 a 004 como ya aplicadas o reproducidas
  - Comando documentado para aplicar y revertir en dev, staging y producción
  - Convención de nombres de tablas nuevas (prefijo `platform_access_*`, nunca `access_requests`)
- **No incluye:**
  - Retirar `db.create_all()` ni el admin semilla de `create_app()` (FNC-003, FNC-028, fase 4/5) salvo que ADR-002 lo exija
  - Limpiar `scratch/` y `utils/` (FNC-028)
  - Tablas de la fase 3 (cada tarea agrega la suya)

## Hallazgos de seguridad que absorbe
- Adelanta la parte "adoptar Alembic" de FNC-028 si ADR-002 lo aprueba; FNC-028 conserva la limpieza de `scratch/` y `utils/`.

## Archivos previstos
- `migrations/` (o la carpeta que fije ADR-002)
- `requirements.txt` (solo la dependencia de migraciones)
- `docs/backend/README.md` §7
- `docs/operacion/RELEASES.md` (paso de migración en el despliegue)

## Reutilización
- `db` de Flask-SQLAlchemy y los modelos existentes como fuente de la línea base

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `requirements.txt` (+`alembic==1.20.0`) | Dependencias | Backend completo, `deploy/install.sh` | Sí: venv nuevo y suite completa |
| `create_app()` (URI vía `construir_uri_bd()`) | Fábrica de la app | Toda la app, `run.py`, `utils/*.py`, pruebas | Sí: `test_arranque.py` (URI SQLite y MySQL) |
| Esquema de la BD | Datos | Todos los módulos | Sin cambios de esquema; línea base = modelos |

Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `DB_ENGINE` | variable de entorno | `app/__init__.py` | `tests/conftest.py`, `tests/test_arranque.py` | tests | Sí (suite en verde) |
| `DB_USER` | variable de entorno | `app/__init__.py` | `tests/test_arranque.py` | tests | Sí (suite en verde) |
| `SECRET_KEY` | variable de entorno | `app/__init__.py` | `tests/conftest.py`, `tests/test_arranque.py` | tests | No cambió |

- `DB_ENGINE`/`DB_USER`: su lectura se movió a `app/utils/uri_bd.py`, misma regla; las pruebas que los usan pasan.
- `SECRET_KEY`: falso positivo; está en las líneas de contexto del bloque editado, no se modificó.
- No los detecta la herramienta: `requirements.txt` y `create_app()` (en la tabla de arriba).

## Variables y configuración
- Ninguna variable nueva; `.env.example` sin cambios.
- `DB_*` se leen ahora en `app/utils/uri_bd.py` (mismos valores); constantes `SQLITE_URI_POR_DEFECTO` y `CARPETA_INSTANCIA` registradas; HISTORIAL con motivo.

## Decisiones de implementación
- Alembic directo (no Flask-Migrate): `flask db` llama a `create_app()`, que ejecuta `create_all()` y crea el admin semilla antes de migrar.
- `create_all()` se queda (ADR-002, alcance); se documenta el orden "migrar antes de arrancar" y el `stamp` si la app arrancó primero.
- URI extraída a `construir_uri_bd()` para no duplicar la regla entre app y Alembic; el cambio en `app/__init__.py` es solo ese (no agrega ni empeora hallazgos SEG).
- `env.py` importa todo `app/modules/*/models.py`; `render_as_batch` activo para que las migraciones corran en SQLite.
- `utils/migrations/001-004` quedan como histórico (la línea base ya refleja su resultado); su retiro sigue en FNC-028.

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/pytest tests/test_migraciones.py -q` | 5 passed |
| Mismo, con una columna agregada a `Platform` sin migración | 3 failed (las pruebas detectan el desfase); revertido |
| `venv/bin/pytest -q -p no:warnings` | 431 passed, 35 xfailed, código 0 (antes 426 + 5 nuevas) |
| `DB_ENGINE=sqlite alembic upgrade head` / `current` / `check` / `downgrade base` | `0001 (head)`; "No new upgrade operations detected."; queda solo `alembic_version` |
| `create_app()` primero y luego `alembic upgrade head` | Falla "table areas already exists" (esperado); `alembic stamp 0001` + `check` sin diferencias |
| `DB_ENGINE=mysql` (valores ficticios) `alembic upgrade head --sql` | DDL MySQL válido (`AUTO_INCREMENT`, `VARCHAR(n)`), sin conectarse |
- No verificado: MySQL real (vacía y copia de NEXUS con `stamp`); lo hace el dueño con `docs/backend/README.md` §7.
- No ejecutados: `revisor`, `auditor-seguridad` (nueva dependencia, SEC-DEP-02), por indicación del orquestador.

## Criterios de aceptación
- [ ] Migración de línea base aplicada en una BD MySQL de prueba vacía y en una copia con datos heredados, sin pérdida — **pendiente del dueño** (sin MySQL ni credenciales en esta sesión); verificado en SQLite y con el SQL de MySQL generado sin conexión
- [x] Bajada (downgrade) probada (SQLite: prueba automática y CLI)
- [x] Prueba automatizada que verifica que el esquema de los modelos y el de las migraciones coinciden (`tests/test_migraciones.py`)
- [ ] Criterios comunes backend (FNC-037) — sin endpoints nuevos; revisor y auditor-seguridad no lanzados (indicación del orquestador)

Salida actual de `impacto.py` (2026-10-14, 7 elementos):
- `DB_ENGINE`, `DB_HOST`, `DB_NAME`, `DB_USER` (definidas ahora en `app/utils/uri_bd.py`): misma regla de antes; las validan `tests/conftest.py` y `tests/test_arranque.py`.
- `SECRET_KEY`: falso positivo (líneas de contexto del bloque editado; no cambió).
- `columnas`, `migrar`: funciones locales de `tests/test_migraciones.py` con el mismo nombre que código de `app/modules/audit/services.py`, `utils/db_inspector.py` y `utils/migrations/003_logo_to_db.py`: homónimos, sin impacto.

## Impacto cruzado
- Genera → Base de FNC-043, FNC-046, FNC-047, FNC-048, FNC-049, FNC-050, FNC-054, FNC-056, FNC-065
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, ADR-002 aceptado

## Riesgos y reversión
- Desfase entre `create_all()` y las migraciones: se documenta el orden (migrar primero) y se prueba en BD vacía.
- Reversión: bajar a la línea base; respaldo de la BD antes de aplicar (docs/operacion/RESPALDOS.md).

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-14 | Aprobada por el dueño; En curso en `fnc/FNC-039-migraciones-alembic` |
| 2026-10-14 | Hecha: Alembic 1.20.0, línea base `0001`, `tests/test_migraciones.py`; 431 passed, 35 xfailed; MySQL real pendiente del dueño |
- auditor-seguridad (modo cambio, 2026-10-14): Aprobado. Sin secretos ni IPs; la URL no se registra en logs; `pip-audit` sin avisos en alembic, Mako ni SQLAlchemy.
- revisor (2026-10-14): Requiere cambios de proceso y documentación (seguridad, estatus, impacto); corregidos. Sugerencias no aplicadas: probar `importar_modelos()` y `url_bd()` sin la fixture `app`, y subir el import de `construir_uri_bd` al inicio de `app/__init__.py` (estilo).
- Cierre: queda En revisión hasta que el dueño ejecute `alembic upgrade head` en su MySQL nuevo (docs/backend/README.md §7).
