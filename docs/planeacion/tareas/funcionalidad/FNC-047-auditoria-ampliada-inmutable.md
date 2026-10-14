# FNC-047 — Auditoría ampliada: registro inmutable con detalle del cambio, actor, área y plataforma

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auditoria |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-047-auditoria-ampliada-inmutable` |
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
| `add_audit_log` | Servicio compartido | 40 llamadas en `api/admin.py`, `api/auth.py`, `api/crud.py`, `auth/services.py` | Pendiente |
| `AuditLog.to_dict` | Serialización | `GET /api/v1/audit`, pantalla `/audit` | Pendiente |
| `ProxyFix` en `create_app` | Arranque | Toda petición (`request.remote_addr`) | Pendiente |

## Variables y configuración
- `TRUSTED_PROXIES` pasa a usarse también para `ProxyFix`: registrar el cambio de significado en `HISTORIAL.md`.

## Criterios de aceptación
- [ ] Las 40 llamadas existentes siguen funcionando (prueba de humo por módulo)
- [ ] Un correo de 120 caracteres en un login fallido queda registrado (prueba de regresión)
- [ ] La IP registrada es la del cliente detrás del proxy de confianza y no se acepta `X-Forwarded-For` de otro origen (prueba)
- [ ] No existe ruta que modifique o borre registros (prueba de la matriz de rutas)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → FNC-060
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039

## Riesgos y reversión
- Volumen de la tabla: índices y retención documentados.
- Reversión: bajar la migración (las columnas nuevas se pierden).

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
