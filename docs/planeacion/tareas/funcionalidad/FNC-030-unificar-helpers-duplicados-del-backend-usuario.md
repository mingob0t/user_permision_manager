# FNC-030 — Unificar helpers duplicados del backend (usuario creado, purga, _payload/_error, auditoría)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | api |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | commit local, sin push |
| **Rama** | `fnc/FNC-030-082-helpers-comunes` (junto con FNC-082) |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
Duplicados registrados en `docs/estandarizacion/03-reutilizacion.md`.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-04, H-12, H-13

## Objetivo
Una sola implementación de los helpers duplicados: `_payload`/`_error` (D-03), aviso de usuario creado (D-04) y purga de inactivos (D-05), sin cambiar el comportamiento observable. Se implementa junto con FNC-082.

## Alcance
- **Incluye:** D-03, D-04 y D-05 del catálogo; la lectura del cuerpo y la protección de las variantes de la fase 3 (en FNC-082).
- **No incluye:** dividir `crud.py` y `admin.py` (FNC-029); cambiar la lectura laxa del cuerpo de `crud`/`admin` (propuesta FNC-119).

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [x] Prueba de regresión que primero falla (si corrige un defecto)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Decisiones
Todas: **decisión del orquestador (pendiente de validar en la prueba de concepto)**.
- `_payload` → `json_payload` conserva la lectura laxa (`get_json(silent=True) or {}`) de `crud.py`, `admin.py`: no se valida que sea objeto para no cambiar el comportamiento (un cuerpo no objeto sigue fallando como antes). Pasarlos a `leer_cuerpo` es la propuesta FNC-119.
- `admin._error` no llevaba `code`; `error_response(message, status)` sin `code` produce el mismo cuerpo: se usa directo. `crud._error` era un envoltorio de `error_response` y se borró.
- Aviso de usuario creado: `avisar_usuario_creado(correo, nombre, base_url, url=None)` en `notifications/services.py`. Cada origen conserva su `base_url` y su `url`: SSO (`BASE_URL` o el host de la petición; `url` = base) y directorio (`BASE_URL` o vacío; `url` = `/auth/login`, ruta heredada). Diferencias entre módulos que se conservan y se documentan: el enlace `/auth/login` y el valor por omisión de `BASE_URL`. Cambio menor: el fallo del aviso en SSO ahora queda en el log (antes se ignoraba en silencio); el acceso no se ve afectado. Corregir el enlace heredado: FNC-119.
- Purga: la de `crud.py` (considera cuentas que nunca entraron; contrato vigente) pasa a `users/services.py` (`purgar_inactivos`, `usuarios_inactivos`, `PURGE_MIN_DAYS`); la validación del periodo y las respuestas siguen en la ruta. `purge_inactive_users` de `auth/services.py` (heredada, sin uso, con mensaje de LDAP ajeno y auditoría en minúsculas) se borró; sin referencias en código ni pruebas.
- Auditoría (`_auditar`): los seis `_auditar` locales (areas, access, access_requests, provisioning, users/areas_administradas, users/directory_accounts) tienen campos y estados distintos y todos delegan en `add_audit_log`; no son duplicados reales, no se unifican. Las inconsistencias de H-13 (`except:` desnudo y `print()`) ya no existen en el código (se verificó con grep).

## Verificación
- Línea base antes del cambio: `venv/bin/python -m pytest -q` → 2341 passed, 15 xfailed, código de salida 0.
- Después: `venv/bin/python -m pytest -q -rX -p no:cacheprovider` → **2360 passed, 15 xfailed, código de salida 0** (+19 pruebas nuevas en `tests/api/test_helpers_comunes.py`).
- No ejecutado: revisor ni auditor-seguridad (no se pidieron en esta ejecución); verificación manual en navegador.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `error_response`, `json_payload`, `leer_cuerpo`, `campos_no_permitidos`, `campos_prohibidos` | Helpers compartidos | `app/modules/api/helpers.py` | Los 11 módulos de API de la lista de endpoints de arriba | todos los endpoints `/api/v1` que escriben | ☐ |
| `avisar_usuario_creado` | Función | `app/modules/notifications/services.py` | `api/auth.py` (SSO), `auth/services.py` (login de directorio) | `POST /auth/sso`, `POST /auth/login` (directorio) | ☐ |
| `purgar_inactivos`, `usuarios_inactivos`, `PURGE_MIN_DAYS` | Funciones | `app/modules/users/services.py` | `api/crud.py` | `GET /users/inactive`, `POST /users/purge` | ☐ |
| `BASE_URL`, `NOTIFY_USER_CREATED` | Variables (sin cambio de valor) | `api/auth.py`, `auth/services.py` | `notifications/access_notifications.py` y pruebas | avisos de bienvenida | ☐ |

Salida de `impacto.py` (8 filas): `_error`, `create_user`, `_entrada`, `send_notification_by_slug`, `BASE_URL`, `NOTIFY_USER_CREATED`, más `_explota` y `envios` (funciones de prueba nuevas; falsos positivos por nombre). `_error` y `_entrada` coinciden por nombre con funciones privadas de otros módulos (`connectors/base_de_datos.py`, `audit/api.py`, `connectors/ssh.py`) que no se tocan. Validar: los endpoints listados (códigos HTTP, `code` y `fields` no cambian; lo cubre la suite).

## Impacto cruzado
- Depende de → —
- Se implementa junto con → FNC-082 (misma rama)
- Relacionadas → FNC-029 (división de `crud.py`/`admin.py`), FNC-119 (propuesta)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | En curso → En revisión: D-03, D-04 y D-05 resueltos; 2360 passed, 15 xfailed, salida 0 (línea base 2341). Commit local `[FNC-030]`, sin push |
