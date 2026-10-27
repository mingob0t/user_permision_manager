# FNC-028 — Limpiar scratch/ y utils/ (PSX5K) y adoptar Alembic con las migraciones 001-004

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | bd |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-26 |
| **Finalizada** | |
| **Estatus Git** | commit local, sin push |
| **Rama** | `fnc/FNC-028-limpiar-scratch-utils` |
| **Commits / PR** | |
| **Requiere migración BD** | No (la línea base `0001` ya cubre 001-004) |
| **Requiere auditor-seguridad** | No |

## Contexto
15 scripts en `scratch/` y 16 en `utils/`, restos de PSX5K; migraciones SQL sueltas sin control; `nexus_structure.sql` y `seed_users.py` obsoletos.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-07, H-08
- [`docs/backend/README.md`](../../../backend/README.md): migraciones

## Objetivo
Retirar los 31 archivos heredados de `scratch/` y `utils/`, decidir qué hacer con los SQL sueltos 001-004 frente a Alembic y evitar que `scratch/` vuelva a versionarse.

## Alcance
- **Incluye:** borrar `scratch/` y `utils/`, ajustar `.gitignore`, `pytest.ini`, deploy y docs que los citaban, y la prueba de cobertura de la línea base.
- **No incluye:** el comando Flask CLI del primer superadmin y del reinicio de la cuenta de emergencia (FNC-003, fase 5); quitar `create_all()` (FNC-003).

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [x] Prueba de regresión que primero falla (si corrige un defecto)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → —

## Decisiones
Todas: decisión del orquestador (pendiente de validar en la prueba de concepto). Usos buscados en código, `deploy/`, README, docs, pruebas y CI: ningún archivo de `scratch/` ni `utils/` se importa ni se ejecuta; solo `pytest.ini` los excluía, `deploy/` los nombraba en textos y `install.sh` excluía `scratch/` al copiar.

| Archivo | Decisión | Motivo |
|---|---|---|
| `scratch/*` (15: `check_admin`, `check_db_states`, `cross_db_search_v2`, `fix_db`, `fix_db_schema`, `inspect_db`, `list_data`, `list_dbs`, `list_users`, `multi_fix_db`, `seed_more_notifications`, `seed_notifications`, `seed_test_areas`, `test_fail_query`, `trace_db`) | Borrar | Sin uso; inspección y arreglos de BD de PSX5K; tres traían URI con `username:password` y uno una IP de ejemplo. `scratch/` va a `.gitignore` |
| `utils/check_db.py`, `db_check.py`, `db_inspector.py`, `db_migrate.py` | Borrar | Inspección y alteración de `psx5k_details`; solapados entre sí; el esquema es de Alembic |
| `utils/nexus_health.py` | Borrar | Importa `psx5k_cmd` y `validate_ldap_connection` (retirada en FNC-043); ya fallaba |
| `utils/test_ldap.py` | Borrar | Importaba `validate_ldap_connection` y ya fallaba; la prueba de conexión es `ClienteDirectorio` y su API (`tests/directory/`) |
| `utils/test_smtp.py` | Borrar | Ya existe `POST /api/v1/smtp/test` (superadmin); el script pedía datos por `input` |
| `utils/toggle_authelia.py` | Borrar | Edita el nginx y el `.env` a mano; nginx sale de `deploy/nginx.conf.tmpl` y el SSO se activa con `AUTHELIA_ENABLED`. Baja de `NGINX_CONF_PATH` (único lector) en VARIABLES, HISTORIAL y `.env.example` |
| `utils/seed_users.py` | Borrar | Roles que el código ya no reconoce y contraseña de ejemplo (`Nexus2024!`) |
| `utils/nexus_structure.sql` | Borrar | Volcado parcial sin `areas` ni `platforms`; el esquema es la línea base `0001` |
| `utils/reset_admin.py`, `utils/emergency_reset.py` | Borrar; el comando queda en FNC-003 | Recrean `admin` con `admin123` (SEG-03). Se anotó en la ficha de FNC-003: el comando Flask CLI único cubre primer superadmin y reinicio de la cuenta de emergencia, sin contraseña fija. No se duplicó aquí |
| `utils/migrations/001`, `002`, `004` (.sql) | Retirar | `0001` ya contiene su efecto: columnas `pref_*` en `users`; sin `storage_stats`, `drive_activity`, `access_requests` ni columnas de archivos en `platforms`. Lo prueba `tests/test_linea_base_cubre_sql_heredadas.py` |
| `utils/migrations/003_logo_to_db.py` | Retirar | Era datos, no esquema, de una sola vez y ya aplicada; la API guarda el logo como data URI. Un logo heredado en ruta se vuelve a subir desde Ajustes. Sin migración `0010` |
| A `tests/` | Nada | Los `test_*.py` eran scripts manuales con conexión real, no pruebas. La cobertura de línea base es nueva |
| `pytest.ini` | Quitar `utils` y `scratch` de `norecursedirs` y el comentario | Las carpetas ya no existen |
| `deploy/install.sh` | Sin cambio en `--exclude 'scratch/'` | Inocuo y evita copiar una carpeta local de cada desarrollador |

## Verificación
- Prueba nueva: `tests/test_linea_base_cubre_sql_heredadas.py` (2 pruebas). No es un defecto: documenta una equivalencia que ya se cumplía, por lo que no falla primero.
- Sin migración nueva: el `alembic upgrade`/`downgrade` sobre SQLite lo cubren `tests/test_migraciones.py` y `tests/test_migracion_0004.py`, dentro del pytest completo. No se ejecutó el CLI sobre `instance/nexus.db` para no tocar BD.
- `venv/bin/pytest -q`: 2341 passed, 15 xfailed (conocidos), código de salida 0, 11 min 39 s.
- No verificado: despliegue real con `install.sh`/`preflight.sh` (solo cambiaron textos).

## Impacto en elementos compartidos
`impacto.py` (contra `develop`): ninguno detectado. Cambian `pytest.ini`, `.gitignore`, `.env.example`, `deploy/install.sh`, `deploy/preflight.sh`, `deploy/README.md` (solo textos y `NGINX_CONF_PATH`), sin código de aplicación.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-18 | FNC-043 retiró `validate_ldap_connection`: `utils/test_ldap.py` y `utils/nexus_health.py` la importan (ya fallaban: la llamaban sin argumentos); limpiar o pasar a `ClienteDirectorio` aquí |
| 2026-10-26 | En curso → En revisión: 31 archivos retirados, línea base `0001` verificada contra 001-004 (sin `0010`), docs y deploy ajustados. FNC-043 (`test_ldap`/`nexus_health`) resuelto al borrarlos |
