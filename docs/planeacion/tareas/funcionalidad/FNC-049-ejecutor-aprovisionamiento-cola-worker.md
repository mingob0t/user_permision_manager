# FNC-049 — Ejecutor de aprovisionamiento: cola, worker, reintentos y bitácora (según ADR-003)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | aprovisionamiento |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Inicio** | 2026-10-19 |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push (worktree `pokemon-wt-049`) |
| **Rama** | `fnc/FNC-049-ejecutor-aprovisionamiento` |
| **Commits / PR** | `7709a09` [FNC-049] (local, sin push ni PR) + commit de registro del hash |
| **Requiere migración BD** | Sí (tablas de ejecuciones e intentos) |
| **Requiere auditor-seguridad** | Sí (ejecución privilegiada en segundo plano) |

## Contexto
- Otorgar o revocar un acceso escribe en OpenLDAP o ejecuta un conector externo: puede tardar o fallar, y no debe hacerse dentro de la petición HTTP (F-CON-01)
- Hoy no hay cola ni worker; Redis está conectado sin uso (`app/utils/redis_client.py`)
- Requerimientos: F-ACC-01, F-ACC-02, F-CON-01, F-NOT-01

## Objetivo
- Crear `app/modules/provisioning/` con un trabajo persistente por operación (otorgar o revocar, destino `ldap` o `conector`), un worker que lo ejecuta con reintentos y *backoff* exponencial con *jitter*, bitácora de cada intento y un mecanismo de aviso del resultado a quien lo encoló, sin depender del módulo de accesos

## Alcance
- **Incluye:**
  - Tablas `provisioning_jobs` (operación, destino, referencias, estado `pendiente`/`en_ejecucion`/`reintentando`/`exitoso`/`fallido`, intentos, próximo intento, clave de idempotencia) y `provisioning_job_attempts` (inicio, fin, resultado, error saneado)
  - Encolado transaccional: el trabajo se inserta en la misma transacción que el cambio de negocio (patrón *outbox*) y el broker de ADR-003 solo despierta al worker
  - Worker como comando (`flask provisioning worker`) con apagado ordenado, bloqueo por trabajo y tiempo de espera por intento
  - Interfaz `Provisioner` y proveedor LDAP que usa FNC-041; registro de proveedores para que FNC-050 agregue los conectores
  - Registro de manejadores de resultado (`on_success`, `on_failure`) para que FNC-054 actualice el acceso sin dependencia circular
  - Aviso `aprovisionamiento_fallido` (FNC-048) al agotar reintentos
  - Auditoría de cada resultado final
- **No incluye:**
  - Conectores API, SSH o BD (FNC-050 a FNC-053)
  - Endpoints de consulta y reintento manual (FNC-062)
  - Unidad systemd y despliegue (FNC-067)
  - Conciliación contra LDAP (fuera de la v1, RF-05)

## Archivos previstos
- `app/modules/provisioning/models.py`
- `app/modules/provisioning/queue.py`
- `app/modules/provisioning/worker.py`
- `app/modules/provisioning/providers.py`
- `app/modules/provisioning/ldap_provider.py`
- `app/modules/provisioning/cli.py`
- Migración (ADR-002)
- `tests/provisioning/`

## Reutilización
- Servicio de escritura de FNC-041
- `redis_registry` de `app/utils/redis_client.py` si ADR-003 elige Redis
- `add_audit_log` ampliado (FNC-047)
- Avisos de FNC-048

## Archivos tocados
- Nuevos: `app/modules/provisioning/` (`__init__`, `tipos`, `reloj`, `config`, `models`, `queue`, `ejecucion`, `worker`, `providers`, `ldap_provider`, `manejadores`, `reintentos`, `saneo`, `cli`), `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `tests/provisioning/` (6 archivos)
- Modificados: `app/__init__.py` (+8: validación `PROVISIONING_*` y comando), `requirements.txt` (`rq==2.12.0`), `.env.example`, `docs/configuracion/VARIABLES.md`, `HISTORIAL.md`, `docs/backend/README.md`, `docs/operacion/ENTORNOS.md`, `docs/estandarizacion/03-reutilizacion.md`, `CHANGELOG.md`, tablero, log
- Archivo previsto `queue.py` mantiene el nombre de la ficha; la ejecución de un trabajo va en `ejecucion.py` y el bucle en `worker.py`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `create_app()` (`app/__init__.py`) | Fábrica de la app | Arranque (`run.py`, Gunicorn), `utils/*.py`, todas las pruebas: valida `PROVISIONING_*` (vacías = por defecto) y registra `flask provisioning` | Sí (pytest completo) |
| `app/utils/redis_client.py` | Cliente compartido | Sin cambios: RQ necesita bytes y el cliente usa `decode_responses=True`; el ejecutor abre su propia conexión | — |
| `EscritorDirectorio`, `ClienteDirectorio.buscar_personas`/`grupos_de_usuario`, `dn_en_base`, `notificar_aprovisionamiento_fallido`, `add_audit_log` | Servicios | Solo se llaman; sin cambios | — |

### Salida real de `impacto.py` (contra `develop`)
```
**Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 33 archivos cambiados).
```
- La herramienta solo detecta cambios en definiciones existentes; `create_app()` cambió por dentro (dos importaciones y dos llamadas), por eso se lista arriba a mano.
- Homónimos: `cargar_configuracion`/`validar_al_arrancar` existen en `directory/configuracion.py` y `provisioning/config.py` (distintos módulos; en `create_app` el segundo se importa como `validar_aprovisionamiento`). `MOTIVO_DATOS_INCOMPLETOS` se reutiliza del directorio, no se duplica.

## Variables y configuración
- `PROVISIONING_MAX_ATTEMPTS`, `PROVISIONING_BACKOFF_BASE_SECONDS`, `PROVISIONING_BACKOFF_MAX_SECONDS`, `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS`, `PROVISIONING_POLL_INTERVAL_SECONDS` (si el worker consulta la tabla) — nombres propuestos, registrar.
- Si ADR-003 elige Redis: `REDIS_PASS` pasa a obligatoria (SEG-29 parcial) y se registra el cambio.

## Integración (lineamiento técnico 11)
- El worker consulta la cola propia (tabla o broker de ADR-003); no recibe cambios de un sistema externo
- Si ADR-003 elige tabla de MySQL, es **polling** interno: intervalo como variable registrada, *backoff* exponencial con *jitter* ante errores, consulta incremental por `next_attempt_at` y bloqueo `SELECT … FOR UPDATE SKIP LOCKED`
- Las llamadas a OpenLDAP y a los conectores son salientes, con tiempo de espera

## Criterios de aceptación
- [x] Un error transitorio se reintenta con *backoff* hasta el máximo y luego queda `fallido` con aviso (`test_transitorio_reintenta_con_backoff_hasta_el_maximo_y_avisa`)
- [x] Un error permanente no se reintenta (`test_permanente_no_se_reintenta`)
- [x] Dos workers no ejecutan el mismo trabajo (`test_dos_workers_no_ejecutan_el_mismo_trabajo`: dos sesiones; `test_reserva_tomada_no_se_ejecuta_dos_veces`)
- [x] Misma clave de idempotencia dos veces → una ejecución (`test_misma_clave_dos_veces_se_ejecuta_una_vez`)
- [x] El error guardado no contiene secretos (`test_el_error_guardado_no_contiene_secretos`, `test_excepcion_del_proveedor_no_guarda_su_texto`)
- [x] Criterios comunes backend: sin endpoints nuevos (sin cambios en la matriz); lógica en el módulo; sin IPs ni secretos; variables registradas; `impacto.py` en la ficha

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest tests/provisioning -q` | 75 passed |
| `venv/bin/python -m pytest tests/test_migraciones.py -q` (0006, una cabeza) | 5 passed |
| `venv/bin/python -m pyflakes app/modules/provisioning tests/provisioning migrations/versions/0006_*` | sin hallazgos |
| `venv/bin/python -m pytest -q -p no:cacheprovider` (completo) | 1019 passed, 17 xfailed, código 0 (795 s) |
- Sin regresión que deba fallar primero: la tarea no corrige un bug; las pruebas nuevas cubren código nuevo
- No verificado: Redis real y un worker RQ real (las pruebas usan la cola en el mismo proceso, sin servicios); el `job_timeout` de RQ por señal (se probó la excepción `JobTimeoutException`, no la alarma); OpenLDAP real (solo `ldap3` `MOCK_SYNC`); MySQL real para 0006 (solo SQLite); `SIGTERM` real durante un intento

## Decisiones y observaciones
Todas: **decisión del orquestador (pendiente de validar en la prueba de concepto)**, con lo más seguro de `docs/seguridad/LINEAMIENTOS.md`:
- Tablas `provisioning_jobs` y `provisioning_job_attempts` (nombres de la ficha) y no el prefijo `platform_access_*` de `docs/backend/README.md` §7
- Reintentos por **barrido de la BD** (no `enqueue_in` del planificador de RQ): la BD es la única fuente de verdad; el reintento sale entre su espera y su espera + `PROVISIONING_POLL_INTERVAL_SECONDS`
- `SimpleWorker` (sin *fork*): misma conexión y contexto de la app; un trabajo a la vez por proceso
- `REDIS_PASS` obligatoria para el worker y para despertarlo; `REDIS_HOST` debe ser nombre de host. La API arranca sin ella (los trabajos esperan)
- Valores por defecto: 5 intentos (ejemplo del contrato), base 60 s, tope 900 s, intento 60 s, barrido 30 s, reserva = intento + 30 s
- Persona LDAP por coincidencia **exacta** de `mail` con el correo de la cuenta (como el login, FNC-042), con `buscar_personas` + filtro exacto, sin cambiar el cliente compartido; ninguna o varias → permanente
- Permanentes (sin reintentos, `fallido` + aviso): conector sin proveedor (`conector_no_disponible`, hasta FNC-050), directorio sin configurar, plataforma sin grupo del nivel o que dejó de ser `ldap`, grupo fuera de la base, persona inexistente (también al revocar: no se da por quitada)
- Excepción inesperada del proveedor o tiempo de espera de RQ → transitorio (acotado por el máximo); su texto nunca se guarda (solo el tipo, al log)
- Manejadores `on_success`/`on_failure` dentro de la transacción del resultado; si fallan, se revierte todo y la reserva vence (idempotente)
- `clave_idempotencia` obligatoria, la define el llamador (≤ 100); dos transacciones simultáneas con la misma clave → la segunda recibe `IntegrityError`
- Auditoría final con actor `sistema`: `acceso_activo`/`acceso_fallido` (otorgar) y `acceso_revocado`/`revocacion_fallida` (revocar), `grant_id` = `access_id`
- Fechas del ejecutor en UTC sin zona (`reloj.ahora`)
- Observación (sin tarea): los avisos de FNC-048 siguen síncronos dentro del worker; moverlos a la cola sería otra tarea si hace falta

## Impacto cruzado
- Genera → FNC-050, FNC-054, FNC-062, FNC-067
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, FNC-041, FNC-047, FNC-048, ADR-003

## Riesgos y reversión
- Trabajos atascados si el worker cae a mitad: recuperación por tiempo de espera de la reserva.
- Reversión: bajar la migración; sin worker los accesos quedan `en_proceso`.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada en `fnc/FNC-049-ejecutor-aprovisionamiento` (worktree `pokemon-wt-049`): módulo `provisioning`, migración 0006, `rq==2.12.0`, 6 variables `PROVISIONING_*`, `REDIS_PASS` obligatoria para el worker. Sin revisores (por instrucción): queda En revisión; pendiente `revisor` y `auditor-seguridad` |
