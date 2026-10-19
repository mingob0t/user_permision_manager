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
| **Commits / PR** | `7709a09`, `305e028`, `69dafb5` (revisión), `684fffa` y `03d94f5` (re-auditoría) [FNC-049], locales, sin push ni PR |
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
- Nuevos: `app/modules/provisioning/` (`__init__`, `tipos`, `reloj`, `configuracion`, `models`, `queue`, `ejecucion`, `worker`, `providers`, `ldap_provider`, `manejadores`, `reintentos`, `saneo`, `cli`), `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `tests/provisioning/` (9 archivos)
- Modificados: `app/__init__.py` (+8: validación `PROVISIONING_*` y comando), `requirements.txt` (`rq==2.12.0`), `.env.example`, `docs/configuracion/VARIABLES.md`, `HISTORIAL.md`, `docs/backend/README.md`, `docs/operacion/ENTORNOS.md`, `docs/estandarizacion/03-reutilizacion.md`, `CHANGELOG.md`, tablero, log
- Archivo previsto `queue.py` mantiene el nombre de la ficha; la ejecución de un trabajo va en `ejecucion.py` y el bucle en `worker.py`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `create_app()` (`app/__init__.py`) | Fábrica de la app | Arranque (`run.py`, Gunicorn), `utils/*.py`, todas las pruebas: valida `PROVISIONING_*` (vacías = por defecto) y registra `flask provisioning` | Sí (pytest completo) |
| *Listeners* `after_commit` y `after_soft_rollback` sobre el `db.session` global (`provisioning/queue.py`) | Eventos de SQLAlchemy | Todos los módulos que hacen `commit`/`rollback` (API, auditoría, login, `utils/*`, pruebas). Sin trabajos encolados en la sesión solo hacen un `pop` del diccionario `session.info`; con trabajos, tras el commit intentan avisar a Redis (≤ 2 × 0,5 s si Redis no responde) | Sí (pytest completo) |
| `Evento` (`audit/events.py`) | Catálogo | Valor nuevo `ejecucion_cancelada` (aditivo; contrato `auditoria.md`); filtros de `GET /audit` y el frontend lo ven como texto | Sí (pytest completo); web pendiente |
| `ClienteDirectorio` (`directory/ldap_client.py`) | Cliente | Método nuevo `buscar_por_correo` y excepción `PersonaAmbigua` (subclase de `ErrorDirectorio`); `ATRIBUTOS_PERFIL` sin cambio de valor. Lo usan login, búsqueda, escritura y plataformas, que no cambian | Sí (pytest completo) |
| `app/utils/redis_client.py` | Cliente compartido | Sin cambios: RQ necesita bytes y el cliente usa `decode_responses=True`; el ejecutor abre su propia conexión | — |
| `EscritorDirectorio`, `ClienteDirectorio.buscar_personas`/`grupos_de_usuario`, `dn_en_base`, `notificar_aprovisionamiento_fallido`, `add_audit_log` | Servicios | Solo se llaman; sin cambios | — |

### Salida real de `impacto.py` (contra `develop`, tras la revisión)
**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 32 elemento(s) usados en otras secciones: app, app/modules, app/utils, frontend, frontend/src, frontend/tests, migrations, migrations/versions, scratch, scripts/lineamientos, tests, tests/areas, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/users, utils, utils/migrations. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Evento` | clase | `app/modules/audit/events.py` | `app/modules/areas/api.py`, `app/modules/audit/models.py`, `app/modules/audit/services.py`, `app/modules/notifications/access_notifications.py`, `app/modules/platforms/api.py`, `app/modules/users/areas_administradas.py`, `app/modules/users/roles.py`, `tests/audit/test_registro_ampliado.py` (+1) | app/modules, tests/audit, tests/notifications | ☐ |
| `__init__` | función | `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/worker.py`, `tests/provisioning/conftest.py`, `tests/provisioning/test_worker.py` | `app/modules/directory/writer.py`, `app/modules/notifications/services.py`, `app/modules/platforms/api.py`, `app/utils/redis_client.py`, `tests/areas/test_alta_y_baja_por_admin.py`, `tests/directorio_falso.py`, `tests/directory/conftest.py`, `tests/directory/test_tls.py` (+1) | app/modules, app/utils, tests, tests/areas, tests/directory | ☐ |
| `_auditar` | función | `app/modules/provisioning/ejecucion.py` | `app/modules/areas/api.py`, `app/modules/users/areas_administradas.py` | app/modules | ☐ |
| `_falla` | función | `tests/provisioning/test_ejecucion.py` | `tests/areas/test_alta_y_baja_por_admin.py`, `tests/conftest.py`, `tests/users/test_roles_y_areas_administradas.py` | tests, tests/areas, tests/users | ☐ |
| `_grupo` | función | `app/modules/provisioning/ldap_provider.py` | `tests/platforms/test_integracion_y_grupos.py` | tests/platforms | ☐ |
| `_referencia` | función | `app/modules/provisioning/models.py`, `migrations/versions/0006_ejecuciones_aprovisionamiento.py` | `app/modules/audit/models.py` | app/modules | ☐ |
| `_registrar` | función | `tests/provisioning/conftest.py` | `tests/test_alcance_por_area.py` | tests | ☐ |
| `_secretos` | función | `app/modules/provisioning/saneo.py` | `scripts/lineamientos/reglas.py` | scripts/lineamientos | ☐ |
| `_siguiente` | función | `tests/provisioning/conftest.py` | `tests/fabricas.py` | tests | ☐ |
| `ahora` | función | `app/modules/provisioning/reloj.py` | `app/decorators.py`, `app/modules/core/routes.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `tests/audit/test_registro_ampliado.py`, `tests/directory/test_tls.py` | app, app/modules, migrations/versions, tests/audit, tests/directory | ☐ |
| `auditorias` | función | `tests/provisioning/test_ejecucion.py` | `frontend/tests/accesibilidad/pares-contraste.ts` | frontend/tests | ☐ |
| `avisos` | función | `tests/provisioning/conftest.py` | `app/modules/notifications/access_notifications.py`, `app/modules/platforms/api.py`, `app/modules/platforms/grupos.py`, `tests/notifications/test_access_notifications.py`, `tests/test_notificaciones.py` | app/modules, tests, tests/notifications | ☐ |
| `cola` | función | `app/modules/provisioning/queue.py` | `app/modules/notifications/access_notifications.py` | app/modules | ☐ |
| `consultar` | función | `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py`, `tests/provisioning/conftest.py` | `app/authz.py`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/use-polling.ts` | app, frontend/src | ☐ |
| `datos` | función | `tests/provisioning/conftest.py` | `app/authz.py`, `app/modules/api/admin.py`, `app/modules/api/helpers.py`, `app/modules/api/routes.py`, `app/modules/areas/api.py`, `app/modules/areas/validacion.py`, `app/modules/audit/services.py`, `app/modules/directory/api.py` (+47) | app, app/modules, app/utils, frontend, frontend/src, frontend/tests, migrations/versions, scratch, scripts/lineamientos, tests, tests/areas, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/users, utils, utils/migrations | ☐ |
| `directorio` | función | `tests/provisioning/test_ldap_provider.py` | `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/api/crud.py`, `app/modules/auth/models.py`, `app/modules/auth/routes.py`, `app/modules/auth/services.py`, `app/modules/directory/api.py`, `app/modules/directory/configuracion.py` (+31) | app/modules, frontend/src, frontend/tests, migrations/versions, scratch, tests, tests/directory, tests/platforms | ☐ |
| `downgrade` | función | `migrations/versions/0006_ejecuciones_aprovisionamiento.py` | `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `tests/notifications/test_migracion_plantillas.py`, `tests/platforms/test_migracion_0005.py`, `tests/test_migracion_0004.py` (+1) | migrations/versions, tests, tests/notifications, tests/platforms | ☐ |
| `enviar` | función | `app/modules/provisioning/queue.py` | `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/api/helpers.py`, `app/modules/auth/services.py`, `app/modules/directory/errors.py`, `app/modules/notifications/access_notifications.py`, `app/modules/notifications/services.py`, `frontend/src/components/settings-panel.tsx` (+2) | app/modules, frontend/src, migrations/versions, tests | ☐ |
| `escenario` | función | `tests/provisioning/test_ldap_provider.py` | `tests/matriz_proteccion.py`, `tests/notifications/test_access_notifications.py`, `tests/test_alcance_por_area.py` | tests, tests/notifications | ☐ |
| `esperar` | función | `app/modules/provisioning/worker.py` | `frontend/tests/lib/use-polling.test.ts` | frontend/tests | ☐ |
| `exito` | función | `app/modules/provisioning/providers.py` | `app/modules/directory/errors.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☐ |
| `ids` | función | `tests/provisioning/conftest.py` | `app/authz.py`, `app/modules/api/admin.py`, `app/modules/areas/baja.py`, `app/modules/users/areas_administradas.py`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/api.ts`, `frontend/tests/accesibilidad/contraste.test.ts`, `tests/audit/test_inmutabilidad.py` (+8) | app, app/modules, frontend/src, frontend/tests, tests, tests/audit, tests/users | ☐ |
| `miembros` | función | `tests/provisioning/test_ldap_provider.py` | `app/modules/directory/writer.py`, `tests/directory/conftest.py`, `tests/directory/test_config.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☐ |
| `operacion` | función | `tests/provisioning/test_ldap_provider.py` | `app/modules/directory/writer.py`, `app/modules/notifications/access_notifications.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `tests/audit/test_inmutabilidad.py`, `tests/directory/test_writer.py` | app/modules, migrations/versions, tests/audit, tests/directory | ☐ |
| `otorgar` | función | `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py`, `tests/provisioning/conftest.py` | `app/modules/notifications/access_notifications.py`, `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/types.ts`, `tests/notifications/test_access_notifications.py` | app/modules, frontend/src, tests/notifications | ☐ |
| `pedir` | función | `app/modules/provisioning/worker.py` | `app/authz.py`, `frontend/src/components/login-form.tsx`, `frontend/src/components/platform-catalog.tsx` | app, frontend/src | ☐ |
| `permanente` | función | `app/modules/provisioning/providers.py` | `app/modules/directory/errors.py`, `frontend/src/components/users-list.tsx` | app/modules, frontend/src | ☐ |
| `ping` | función | `tests/provisioning/test_worker.py` | `app/utils/redis_client.py`, `frontend/src/styles/components.css` | app/utils, frontend/src | ☐ |
| `procesar` | función | `tests/provisioning/conftest.py` | `frontend/src/app/globals.css` | frontend/src | ☐ |
| `reintentable` | función | `app/modules/provisioning/providers.py` | `app/modules/directory/errors.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☐ |
| `revocar` | función | `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py`, `tests/provisioning/conftest.py` | `app/modules/notifications/access_notifications.py`, `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/types.ts`, `frontend/tests/lib/access/peticiones.test.ts` | app/modules, frontend/src, frontend/tests | ☐ |
| `upgrade` | función | `migrations/versions/0006_ejecuciones_aprovisionamiento.py` | `migrations/env.py`, `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `tests/notifications/test_migracion_plantillas.py`, `tests/platforms/test_migracion_0005.py` (+2) | migrations, migrations/versions, tests, tests/notifications, tests/platforms | ☐ |

- Elementos realmente compartidos que cambian: `Evento` (valor nuevo `ejecucion_cancelada`, aditivo), `ClienteDirectorio` (método nuevo `buscar_por_correo`, `PersonaAmbigua`, constante `ATRIBUTO_CORREO`; la herramienta no lo lista), `create_app()` y los *listeners* de la sesión (filas de arriba).
- El resto son **homónimos**: funciones nuevas del módulo o de sus pruebas (`ahora`, `cola`, `enviar`, `otorgar`, `revocar`, `consultar`, `permanente`, `datos`, `directorio`, `_referencia`, `upgrade`/`downgrade`…) con el mismo nombre que otras del proyecto; no se modificó ninguna de esas.

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
| `venv/bin/python -m pytest -q -p no:cacheprovider` (completo, commit `7709a09`) | 1019 passed, 17 xfailed, código 0 (795 s) |
| Regresiones de la revisión **antes** de corregir | `test_versionado.py` 1 failed (`config.py` ignorado); `test_mensajes_rq.py` 9 failed, 1 passed; `test_orden_y_reserva.py` 5 failed, 1 passed (el que pasa es de no regresión); exactitud por `mail` 3 failed; tiempo corto de despertar 1 failed |
| `venv/bin/python -m pytest tests/provisioning -q` (tras corregir) | 96 passed |
| Regresiones de la re-auditoría **antes** de corregir (`test_reauditoria.py`) | 5 failed |
| `venv/bin/python -m pytest tests/provisioning -q` (tras la re-auditoría) | 101 passed |
| `git ls-files app/modules/provisioning` | los 14 `.py` del módulo (todos los del disco), incluido `configuracion.py` |
| `venv/bin/python -m pytest -q -p no:cacheprovider` (completo, tras la re-auditoría) | 1045 passed, 17 xfailed, código 0 (476 s) |
| `venv/bin/python -m pytest -q -p no:cacheprovider` (completo, tras la revisión) | 1040 passed, 17 xfailed, código 0 (449 s; una corrida previa dio 1 failed en `test_el_catalogo_coincide_con_el_contrato` por editar `auditoria.md` durante la corrida: 10 passed al repetirla) |
- Implementación inicial sin regresiones (código nuevo); cada defecto de la revisión tiene su regresión, que falló antes de corregir (fila de arriba)
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
- Revisión: una revocación **cancela** los otorgar en espera de su terna (estado `cancelado`, auditoría `ejecucion_cancelada` en la transacción del llamador); un otorgar ya en ejecución no se cancela: la revocación espera. Los trabajos de una terna (usuario, plataforma, nivel) corren en orden de creación
- Revisión: reintento manual (FNC-062) con `ejecucion.reabrir(trabajo, cfg)`: solo desde `fallido`, conserva la bitácora y **sube** `max_attempts` en `PROVISIONING_MAX_ATTEMPTS` (no reinicia el contador). El tope de intentos al reservar solo aplica a reservas vencidas
- Re-auditoría: `reabrir` de un otorgar con una revocación posterior de su terna → `EstadoInvalido` (FNC-062 responde 409); el orden por terna bloquea también si **cualquier** trabajo de la terna está en ejecución. Carrera residual documentada en `bloqueado_por_anterior` (dos workers con un trabajo recién reabierto)
- Revisión: mensajes RQ en JSON; el worker descarta sin ejecutar (log y borrado) todo mensaje que no sea `ejecutar_trabajo(<int>)` o que traiga *callbacks* de RQ
- Revisión: despertar desde la web con `TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS` = 0,5 s. Riesgo: con Redis caído, cada commit que encola tarda hasta ~1 s más; los trabajos esperan al barrido
- Revisión: `redis==8.1.0` fijada (la que resuelve `rq==2.12.0`); `croniter` y `click` siguen como dependencias transitivas de `rq`
- Impacto cruzado (web): el contrato agrega `cancelado` a `status` de `Job` y `ejecucion_cancelada` al catálogo de auditoría; `frontend/src/lib/access/types.ts` (`JobStatus`, FNC-069/DIS-022) debe incluirlo: solicitud para la base

## Revisiones
| Fecha | Revisor | Veredicto | Estado |
|---|---|---|---|
| 2026-10-19 | auditor-seguridad | **Bloqueante** (1 Bloqueante, 2 Media, 2 Baja) | Corregido: `config.py` ignorado → `configuracion.py`; JSON + rechazo de mensajes ajenos; cancelar otorgar y orden por terna; cierre con `locked_by`; filtro exacto `(mail=…)`; `redis` fijado |
| 2026-10-19 | auditor-seguridad (re-auditoría) | **Aprobado** con 1 Media y 1 Baja | Corregido: `reabrir` rechaza un otorgar con revocación posterior de la terna y un reabierto espera a cualquier trabajo de su terna en ejecución; mensajes RQ con *callbacks* se rechazan |
| 2026-10-19 | revisor | Requiere cambios (1 Media, 1 Baja, documentación) | Corregido: tope solo en reservas vencidas + `reabrir`; timeout corto al despertar; impacto real y fila de *listeners*; hashes en el tablero |

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
| 2026-10-19 | Re-auditoría de seguridad: Aprobado con 1 Media y 1 Baja, corregidas en un commit nuevo; sigue En revisión |
| 2026-10-19 | Correcciones de auditor-seguridad (Bloqueante) y revisor en un commit nuevo; sigue En revisión |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada en `fnc/FNC-049-ejecutor-aprovisionamiento` (worktree `pokemon-wt-049`): módulo `provisioning`, migración 0006, `rq==2.12.0`, 6 variables `PROVISIONING_*`, `REDIS_PASS` obligatoria para el worker. Sin revisores (por instrucción): queda En revisión; pendiente `revisor` y `auditor-seguridad` |
