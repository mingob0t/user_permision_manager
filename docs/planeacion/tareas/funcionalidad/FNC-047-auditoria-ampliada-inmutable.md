# FNC-047 — Auditoría ampliada: registro inmutable con detalle del cambio, actor, área y plataforma

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auditoria |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-047-auditoria-ampliada` (worktree `pokemon-wt-047`) |
| **Requiere migración BD** | Sí (columnas e índices en `audit_logs`) |
| **Requiere auditor-seguridad** | Sí (no repudio, datos personales) |

## Contexto
- `AuditLog` (`app/modules/audit/models.py`) guarda el actor como texto, sin FK ni área ni plataforma, sin antes/después (F-AUD-01)
- `action` es `String(50)` y un login con correo largo hace fallar el INSERT (SEG-25); la IP es siempre la del proxy porque no hay `ProxyFix` (SEG-25)
- Todas las tareas de la fase registran eventos con estos datos
- Requerimientos: F-AUD-01, RF-05

## Objetivo
- Ampliar el registro con `actor_id`, `target_user_id`, `area_id`, `platform_id`, `event` (catálogo cerrado), `before`/`after` (JSON), `request_id`/`grant_id` opcionales, IP real, y garantizar que no se modifica ni se borra desde la aplicación

## Alcance
- **Incluye:**
  - Columnas nuevas, índices por área, plataforma, usuario objetivo y fecha
  - `add_audit_log` compatible hacia atrás con parámetros nuevos opcionales
  - Catálogo de eventos del gestor de accesos (solicitud creada, aprobada, rechazada, acceso otorgado, fallido, revocado, admin asignado, rol cambiado, conector configurado…)
  - `action` ampliado y el correo en `target`
  - IP real del cliente con `ProxyFix` limitado a `TRUSTED_PROXIES`
  - Inmutabilidad: sin endpoints de edición ni borrado; el modelo rechaza `UPDATE`/`DELETE` (y, si el dueño lo aprueba, permisos de BD de solo INSERT/SELECT para el usuario de la app)
  - Actualizar `docs/operacion/RETENCION.md` con los datos nuevos (antes/después contienen datos personales)
- **No incluye:**
  - Consultas y visibilidad por rol (FNC-060)
  - Política de retención y seudonimización (FNC-018)
  - Migrar las 40 llamadas existentes a los campos nuevos (se ajustan solo las que toque cada tarea)

## Hallazgos de seguridad que absorbe
- **FNC-015** parcial: SEG-25 (longitud de `action`, IP real). SEG-16 lo cierra FNC-060.

## Archivos previstos
- `app/modules/audit/models.py`
- `app/modules/audit/services.py`
- `app/modules/audit/events.py` (nuevo, catálogo)
- `app/__init__.py` (solo `ProxyFix`)
- Migración (ADR-002)
- `docs/operacion/RETENCION.md`
- `tests/audit/`

## Reutilización
- `add_audit_log` (única forma de registrar, 40 llamadas)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `add_audit_log` | Servicio compartido | 33 llamadas en `api/admin.py`, `api/auth.py`, `api/crud.py`, `auth/services.py` | Pruebas existentes en verde; firma compatible |
| `AuditLog` / `to_dict` | Modelo y serialización | `GET /api/v1/audit` (`api/routes.py`), pantalla `/audit` (`audit-log.tsx`) | Arreglo igual + 6 campos nuevos; validar la pantalla (FNC-069) |
| Acción de los eventos de sesión (`api/auth.py`) | Datos | Filtro de texto de `audit-log.tsx`; pruebas de login | `ACCESO LOCAL: <correo>` → `ACCESO LOCAL` + correo en `target`; validar búsqueda en la pantalla |
| `ProxyFix` en `create_app` | — | — | No se aplicó (ver Decisiones) |

### Salida real de `impacto.py` (2026-10-14, contra `develop`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `AuditLog` | clase | `app/modules/audit/models.py` | `app/__init__.py`, `app/modules/api/routes.py`, `frontend/src/app/audit/page.tsx`, `frontend/src/components/audit-log.tsx`, `frontend/tests/components/audit-log.test.tsx`, `scratch/check_db_states.py`, `tests/test_alcance_por_area.py`, `tests/test_auditoria_crud.py` (+2) | app, app/modules, frontend/src, frontend/tests, scratch, tests | ☐ |
| `_usuario` | función | `app/modules/audit/models.py` | `tests/test_alcance_por_area.py` | tests | ☐ |
| `add_audit_log` | función | `app/modules/audit/services.py` | `app/modules/api/admin.py`, `app/modules/api/crud.py`, `app/modules/auth/services.py` | app/modules | ☐ |
| `downgrade` | función | `migrations/versions/0002_auditoria_ampliada.py` | `migrations/versions/0001_linea_base_esquema_actual.py`, `tests/test_migraciones.py` | migrations/versions, tests | ☐ |
| `login` | función | `app/modules/api/auth.py` | `app/__init__.py`, `app/modules/auth/routes.py`, `app/modules/auth/services.py`, `app/modules/notifications/services.py`, `frontend/src/app/login/page.tsx`, `frontend/src/components/login-form.tsx`, `frontend/src/components/logout-view.tsx`, `frontend/src/components/session-provider.tsx` (+6) | app, app/modules, frontend/src, frontend/tests, scripts/lineamientos, tests | ☐ |
| `logout` | función | `app/modules/api/auth.py` | `app/modules/auth/routes.py`, `frontend/src/app/logout/page.tsx`, `frontend/src/components/app-shell.tsx`, `frontend/src/components/logout-view.tsx`, `frontend/src/lib/api.ts`, `tests/matriz_proteccion.py` | app/modules, frontend/src, tests | ☐ |
| `registro` | función | `tests/audit/test_inmutabilidad.py` | `app/modules/audit/routes.py`, `frontend/src/components/audit-log.tsx`, `tests/directorio_falso.py`, `tests/fabricas.py`, `tests/smtp_falso.py`, `tests/test_alcance_por_area.py`, `tests/test_auditoria_crud.py` | app/modules, frontend/src, tests | ☐ |
| `to_dict` | función | `app/modules/audit/models.py` | `app/modules/api/admin.py`, `app/modules/api/crud.py`, `app/modules/api/routes.py`, `app/modules/auth/models.py`, `app/modules/core/models.py`, `app/modules/notifications/models.py`, `app/modules/settings/models.py` | app/modules | ☐ |
| `upgrade` | función | `migrations/versions/0002_auditoria_ampliada.py` | `migrations/env.py`, `migrations/versions/0001_linea_base_esquema_actual.py`, `tests/test_migraciones.py` | migrations, migrations/versions, tests | ☐ |

### Lectura (homónimos)
- Reales: `AuditLog` (modelo) en `api/routes.py`, pruebas y `scratch/` (script manual); `add_audit_log` en sus módulos llamadores; `AuditLog.to_dict` solo en `api/routes.py` (`GET /audit`); `login`/`logout` = rutas `POST /api/v1/auth/login|logout` que consume el frontend (contrato sin cambios).
- Homónimos: `AuditLog` en el frontend es el componente React (consume la API; solo recibe campos nuevos); `_usuario` de `test_alcance_por_area.py` es otra función local; `to_dict` de otros modelos; `login`/`logout` en `auth/services.py`, `notifications`, `scripts/lineamientos` son textos o funciones distintas; `upgrade`/`downgrade` son las de cada migración (Alembic); `registro` es un fixture local de la prueba.

## Variables y configuración
- `TRUSTED_PROXIES`: también decide si se confía en `X-Forwarded-For` para la auditoría (`HISTORIAL.md`).
- Constantes nuevas o con nombre: `ACTOR_SISTEMA` (`SYSTEM` → `sistema`, según contrato), `IP_INTERNA`, `FRAGMENTOS_SENSIBLES`, `VALOR_OMITIDO`, `AL_BORRAR_REFERENCIA`, largos de `audit_logs` (`VARIABLES.md` + `HISTORIAL.md`).

## Criterios de aceptación
- [x] Las llamadas existentes siguen funcionando: `test_auditoria_crud.py` (api/crud), `test_login_*`, `test_sso`, `test_sesion_y_logout` (api/auth), `test_respaldo.py` (api/admin), `test_llamada_heredada_sigue_funcionando`
- [x] Un correo de 120 caracteres en un login fallido queda registrado (`test_login_fallido_con_correo_de_120_caracteres_queda_registrado`)
- [x] IP del cliente detrás del proxy de confianza; `X-Forwarded-For` de otro origen se ignora (`test_ip_real_...`, `test_x_forwarded_for_de_otro_origen_se_ignora`)
- [x] Ninguna ruta modifica o borra registros (`test_ninguna_ruta_modifica_ni_borra_auditoria`)
- [x] Criterios comunes backend (FNC-037): sin endpoints nuevos; lógica en el servicio del módulo; sin IPs ni secretos; variables registradas; tabla de `impacto.py`
- [ ] `auditor-seguridad` en modo cambio (la ficha lo exige; no lanzado por instrucción del orquestador)

## Impacto cruzado
- Genera → FNC-060
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039

## Riesgos y reversión
- Volumen de la tabla: índices y retención documentados.
- Reversión: bajar la migración (las columnas nuevas se pierden).

## Decisiones
- Sin `ProxyFix` global: cambiaría `request.remote_addr`, que `_trusted_proxy()` (SSO, `api/auth.py`) compara con `TRUSTED_PROXIES`; tras nginx el SSO dejaría de funcionar. La IP real se calcula solo para la auditoría (`audit/ip_cliente.py`, equivale a `x_for=1` y reutiliza `_trusted_proxy`).
- nginx usa `$proxy_add_x_forwarded_for`: se toma el último salto (el que agrega nginx), no el primero que manda el cliente. SEC-AUD-04 pide que nginx sobrescriba la cabecera: queda para infra (FNC-004/017).
- `action` 150 y `user`/`target` 255, y además recorte al largo de la columna en `add_audit_log`: un INSERT nunca falla por largo.
- FK con `ON DELETE SET NULL`: borrar usuario, área o plataforma conserva el evento (sin cascada); `actor = null` con `user` distinto de `sistema` = actor borrado.
- Columnas `before_state`/`after_state` (`BEFORE` es palabra reservada de MySQL); en la API se llaman `before`/`after`.
- `request_id`/`grant_id` sin FK: las tablas llegan con FNC-054/056, que agregan la FK.
- Catálogo `Evento` = contrato; las 33 llamadas heredadas siguen con texto libre (fuera de alcance).
- Inmutabilidad en el ORM (por objeto y masivos); SQL crudo y permisos de BD solo INSERT/SELECT: pendiente de aprobación del dueño.
- `timestamp` sigue en hora local (`datetime.now`): SEC-AUD-02 pide UTC, pero cambiarlo mezcla registros viejos y nuevos y la ficha no lo incluye; se propone al dueño.
- Defecto encontrado y corregido: fuera de una petición `add_audit_log` fallaba en silencio (`current_user` sin contexto) y no registraba; ahora registra `sistema` + `INTERNAL` (`test_fuera_de_peticion_actua_el_sistema`).
- `test_alcance_por_area.py`: los `xfail` de SEG-16 siguen (los cierra FNC-060); ningún `xfail` pasó a XPASS.

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest -q tests/audit/test_regresion_seg25.py` antes del cambio | 3 failed, 2 passed (acción con correo; recorte sin registro; IP del proxy) |
| `venv/bin/python -m pytest -q tests/audit tests/test_migraciones.py` | 30 passed |
| `venv/bin/python -m pytest -q` (completo) | 456 passed, 35 xfailed, código de salida 0 (antes: 431 passed, 35 xfailed) |
| `alembic upgrade 0001:0002 --sql` y `downgrade 0002:0001 --sql` con dialecto MySQL (BD ficticia, sin conexión) | SQL generado; índices antes de FK y FK antes de índices al bajar |

- No verificado: migración contra un MySQL real (sin acceso; pendiente del dueño, como FNC-039); permisos de BD; pantalla `/audit` con los campos nuevos (FNC-069).

## Commits / PR
- Rama `fnc/FNC-047-auditoria-ampliada`; commit local `[FNC-047] Auditoría ampliada e inmutable` (hash en el tablero y en el informe). Sin push ni PR.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-14 | Aprobada por el dueño (comunicado por el orquestador); implementada por desarrollador en `pokemon-wt-047`; queda En revisión (falta `auditor-seguridad` y revisor) |
