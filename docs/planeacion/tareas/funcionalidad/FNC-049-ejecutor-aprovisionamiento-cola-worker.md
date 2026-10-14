# FNC-049 — Ejecutor de aprovisionamiento: cola, worker, reintentos y bitácora (según ADR-003)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | aprovisionamiento |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-049-ejecutor-aprovisionamiento-cola-worker` |
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

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `app/utils/redis_client.py` | Cliente compartido | `app/__init__.py` (solo si ADR-003 elige Redis) | Pendiente |

## Variables y configuración
- `PROVISIONING_MAX_ATTEMPTS`, `PROVISIONING_BACKOFF_BASE_SECONDS`, `PROVISIONING_BACKOFF_MAX_SECONDS`, `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS`, `PROVISIONING_POLL_INTERVAL_SECONDS` (si el worker consulta la tabla) — nombres propuestos, registrar.
- Si ADR-003 elige Redis: `REDIS_PASS` pasa a obligatoria (SEG-29 parcial) y se registra el cambio.

## Integración (lineamiento técnico 11)
- El worker consulta la cola propia (tabla o broker de ADR-003); no recibe cambios de un sistema externo
- Si ADR-003 elige tabla de MySQL, es **polling** interno: intervalo como variable registrada, *backoff* exponencial con *jitter* ante errores, consulta incremental por `next_attempt_at` y bloqueo `SELECT … FOR UPDATE SKIP LOCKED`
- Las llamadas a OpenLDAP y a los conectores son salientes, con tiempo de espera

## Criterios de aceptación
- [ ] Un error transitorio se reintenta con *backoff* hasta el máximo y luego queda `fallido` con aviso (prueba con proveedor simulado)
- [ ] Un error permanente no se reintenta (prueba)
- [ ] Dos workers no ejecutan el mismo trabajo (prueba de concurrencia o de bloqueo)
- [ ] El mismo trabajo encolado dos veces con la misma clave de idempotencia se ejecuta una vez (prueba)
- [ ] El error guardado no contiene secretos (prueba)
- [ ] Criterios comunes backend (FNC-037)

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
