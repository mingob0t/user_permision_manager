# FNC-019 — Suite base de pruebas del backend (pytest, fixtures, cliente por rol, excluir utils/test_*)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 2 |
| **Módulo / Área** | pruebas |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-13 |
| **Finalizada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-019-suite-base-pruebas-backend` |
| **Commits / PR** | `e96d406` (más el ajuste con el hash) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (dependencias nuevas de desarrollo y `create_app`): sin hallazgos |

## Contexto
No hay pruebas automatizadas; los scripts `utils/test_*.py` y `scratch/test_*.py` abren conexiones reales si pytest los recoge.

Origen (diagnóstico inicial, FNC-001):
- [`docs/planeacion/diagnostico-pruebas-2026-10-13.md`](../../../planeacion/diagnostico-pruebas-2026-10-13.md): tarea 1

## Objetivo
Tener una base de pytest que corra sin `.env` ni servicios externos, para escribir las pruebas de FNC-020 a FNC-023.

## Alcance
- **Incluye:** `requirements-dev.txt` (pytest, pytest-cov), `pytest.ini` (solo `tests/`), `tests/conftest.py`, `tests/fabricas.py`, pruebas humo.
- **No incluye:** matriz de permisos (FNC-020), alcance por área (FNC-021), autenticación (FNC-022), servicios y arranque (FNC-023), CI (FNC-026).

## Criterios de aceptación
- [x] pytest no recoge `utils/test_*.py` ni `scratch/test_*.py` (`pytest --collect-only -q .` → 10 pruebas, todas de `tests/`)
- [x] Prueba de regresión: no aplica (no corrige un defecto)
- [x] Pruebas humo ejecutadas: 10 passed, código de salida 0
- [x] Cumple `docs/estandarizacion/`; fixtures y fábricas agregadas al catálogo
- [x] Sin direcciones IP ni secretos (valores ficticios en `conftest.py`)

## Cambios
- `app/__init__.py`: `create_app(config_overrides=None)`; aplica las claves antes de iniciar extensiones. Sin argumento, igual que antes.
- `requirements-dev.txt`: pytest 9.1.1, pytest-cov 7.1.0.
- `pytest.ini`: `testpaths = tests`, `norecursedirs` con `utils` y `scratch`.
- `tests/conftest.py`: no carga `.env`, limpia variables de servicios externos, valores ficticios, BD SQLite temporal por prueba (borra el admin semilla), Redis sin conectar, SMTP y LDAP bloqueados; clientes por rol.
- `tests/fabricas.py`: áreas, plataformas y usuarios por rol.
- `tests/test_humo.py`: 10 pruebas humo.

## Verificación
- `venv/bin/pytest; echo EXIT=$?` → `10 passed, 7 warnings`, `EXIT=0`.
- `venv/bin/pytest --collect-only -q .` → `10 tests collected`, `EXIT=0` (no entra a `utils/` ni `scratch/`).
- `venv/bin/pytest --cov=app` → 10 passed, cobertura total 39 %.
- No se crea `instance/nexus.db` al correr la suite (comprobado con `ls`).
- Todos los demás llamadores de `create_app` la llaman sin argumentos (grep).
- No verificado: arranque real con MySQL/Redis (fuera de alcance; no hay servicios en el entorno).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `create_app` | función | `app/__init__.py` | `run.py`, `scratch/*.py`, `utils/*.py`, `utils/migrations` (24 usos) | run.py, scratch, utils, utils/migrations | ☑ todos llaman `create_app()` sin argumentos; el parámetro es opcional |

## Observaciones
- Existe un `.env` en la carpeta superior (`/home/dtovar/bayblade/`); el `load_dotenv()` de la app lo encontraría al subir directorios. Las pruebas lo neutralizan; no se leyó.
- Para FNC-020: CSRF sigue activo con `TESTING=True`; los POST/PUT/DELETE de blueprints no exentos necesitarán token o `WTF_CSRF_ENABLED=False` en la fixture.
- Revisión: `revisor` aprobado con observaciones (corregidas); `auditor-seguridad` modo cambio sin hallazgos.

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-13 | Aprobada por el dueño; implementada y probada (10 passed) |
