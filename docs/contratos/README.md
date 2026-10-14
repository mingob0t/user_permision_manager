# Contratos backend ↔ web

Acuerdos de API `/api/v1` del gestor de accesos (fase 3). Se integran a `develop` antes de implementar. Solo cambian por una solicitud (`docs/coordinacion/SOLICITUDES.md`), nunca de un lado.

## Índice

| Contrato | Versión | Proveedor | Consumidor | Tareas que lo implementan |
|---|---|---|---|---|
| [areas-y-roles.md](areas-y-roles.md) | 1 (2026-10-14) | backend | web | FNC-044, FNC-045, FNC-055 |
| [plataformas-integracion.md](plataformas-integracion.md) | 1 (2026-10-14) | backend | web | FNC-046, FNC-055 |
| [solicitudes.md](solicitudes.md) | 1 (2026-10-14) | backend | web | FNC-056, FNC-057 |
| [accesos.md](accesos.md) | 1 (2026-10-14) | backend | web | FNC-054, FNC-058, FNC-059 |
| [auditoria.md](auditoria.md) | 1 (2026-10-14) | backend | web | FNC-047, FNC-060 |
| [conectores-y-ejecuciones.md](conectores-y-ejecuciones.md) | 1 (2026-10-14) | backend | web | FNC-061, FNC-062 |
| [usuarios-directorio.md](usuarios-directorio.md) | 1 (2026-10-14) | backend | web | FNC-064 |
| [inicio.md](inicio.md) | 1 (2026-10-14) | backend | web | FNC-066 |

Consumidor web: tipos y cliente en FNC-069; refresco en FNC-071.

## Versiones
- Cada contrato lleva `Versión N (AAAA-MM-DD)`.
- Agregar un campo opcional a una respuesta: misma versión, nota en el historial del contrato.
- Quitar o renombrar un campo, cambiar un tipo, un código o un permiso: versión N+1 y solicitud aprobada.
- La ruta sigue en `/api/v1`; una ruptura incompatible se publica como ruta nueva, no se rompe la existente.

## Convenciones comunes (aplican a todos los contratos)

| Tema | Regla |
|---|---|
| Sesión | Cookie de Flask; sin sesión → `401` |
| Rol insuficiente | `403` (SEC-AUTHZ-04) |
| Recurso fuera de alcance (área ajena) | `404`, igual que inexistente (SEC-AUTHZ-03/04) |
| Escrituras | `Content-Type: application/json` (otro → `415`, SEC-SES-05); token CSRF en cabecera y `Origin` del mismo sitio (SEC-SES-04). Nombre de la cabecera y obtención del token: FNC-008 — *Por confirmar (P13)* |
| Lista blanca | Cada endpoint acepta solo los campos de su tabla; `role`, `is_active`, `auth_source`, `password_hash` y campos desconocidos → `400 campo_no_permitido` (SEC-AUTHZ-09) |
| Actor | Siempre de la sesión, nunca del cuerpo |
| Fechas | ISO 8601 en UTC con `Z` (`2026-10-14T15:04:05Z`) |
| Identificadores | Enteros |
| Textos libres | Se recortan espacios; longitudes en cada contrato; constantes con nombre en el backend |
| Auditoría | Cada escritura audita en la misma transacción (SEC-AUD-06); catálogo en [auditoria.md](auditoria.md) |
| Pruebas | Cada endpoint agrega su caso en `tests/matriz_proteccion.py` (401/403/404/2xx por rol) |

### Respuestas
| Tipo | Forma |
|---|---|
| Lectura de un recurso | El objeto (igual que hoy, p. ej. `GET /me`) |
| Lista paginada | `{"items": [...], "page": 1, "per_page": 25, "total": 0}` |
| Escritura correcta | `{"status": "success", "<recurso>": {...}}` (igual que hoy en `crud.py`); `201` al crear |
| Error | `{"status": "error", "message": "texto para el usuario", "code": "codigo_interno"}` |
| Error `500` | `{"status": "error", "message": "Ocurrió un error. Intenta de nuevo.", "code": "error_interno", "correlation_id": "uuid"}`; el detalle solo va al log (SEC-CFG-06) |

- `status` y `message` son los existentes (`_error` de `crud.py`). `code` y `correlation_id` son campos **nuevos y aditivos**: el cliente actual sigue leyendo `message`.
- `message` siempre en español, genérico, sin datos internos.

### Paginación y filtros
| Parámetro | Tipo | Regla |
|---|---|---|
| `page` | int | ≥ 1; por defecto 1 |
| `per_page` | int | 1–100; por defecto 25; fuera de rango → `400 parametro_invalido` |
| Filtros | según contrato | Valor desconocido de un enumerado → `400 parametro_invalido` |
| Orden | fijo por contrato | No se acepta orden libre |

### Códigos de error comunes
| HTTP | `code` | Cuándo |
|---|---|---|
| 400 | `parametro_invalido` | Parámetro de consulta inválido |
| 400 | `campo_no_permitido` | Campo fuera de la lista blanca |
| 401 | `sin_sesion` | Sin sesión o sesión inválida |
| 403 | `sin_permiso` | Rol insuficiente |
| 403 | `csrf_invalido` | Falta token CSRF u `Origin` ajeno |
| 404 | `no_encontrado` | No existe o está fuera de alcance |
| 409 | según contrato | Conflicto de estado |
| 413 | `cuerpo_demasiado_grande` | Cuerpo sobre el límite (SEC-SES-09) |
| 415 | `tipo_no_soportado` | No es JSON |
| 422 | `validacion` | Campo obligatorio, longitud o formato; agrega `"fields": {"campo": "mensaje"}` |
| 429 | `demasiadas_peticiones` | Límite de peticiones |
| 500 | `error_interno` | Error no controlado |
| 503 | `directorio_no_disponible` | OpenLDAP no responde (solo escrituras síncronas al directorio) |

## Refresco (ADR-006)
- Polling HTTP a la misma ruta de lectura; sin SSE ni WebSocket.
- Intervalo: `preferences.refresh_interval` de `GET /me` (15–3600 s).
- Pausa con la pestaña oculta; al volver, una consulta inmediata.
- Error: *backoff* duplicando el intervalo hasta 3600 s; vuelve al intervalo al primer éxito. `401` detiene el polling.
- Tras una escritura propia: recarga inmediata de la lista afectada.
- Cada contrato indica qué pantallas hacen polling.

## Decisiones del dueño reflejadas (FNC-037)
| Pregunta | Decisión | Dónde |
|---|---|---|
| P1 | Catálogo: solo plataformas de las áreas del usuario | solicitudes.md |
| P2 | Superadmin y admins crean cuentas en OpenLDAP (admin, para sus áreas) | usuarios-directorio.md |
| P3 / ADR-004 | Convención LDAP por variables `.env` | plataformas-integracion.md |
| P4 | Accesos actuales (`user_platforms`) se descartan; sin origen `heredado` | accesos.md |
| P5 | Un nivel por plataforma; subir reemplaza | solicitudes.md, accesos.md |
| P6 / P12 | Superadmin con acceso por defecto; alta de plataforma otorga acceso al admin creador con dos eventos de auditoría | plataformas-integracion.md, auditoria.md |
| P9 | Conectores: base primero; tipos después | conectores-y-ejecuciones.md |
| ADR-003 | Redis + RQ | conectores-y-ejecuciones.md |
| ADR-006 | Polling | Todos |

## Por confirmar (valor más seguro aplicado)
| Pregunta | Valor aplicado | Dónde |
|---|---|---|
| P7 motivo al revocar | Obligatorio, 10–500 caracteres | accesos.md |
| P8 contraseña inicial LDAP | Cuenta sin contraseña; el usuario la define con el restablecimiento de Authelia; nunca fija, guardada ni enviada por correo (SEC-LDAP-09) | usuarios-directorio.md |
| P10 aviso de fallo de conector | Correo a admins del área y superadmin, sin depender de `pref_email_notifications`; reintento manual solo superadmin | conectores-y-ejecuciones.md |
| P11 baja de áreas | Solo superadmin; `409` con plataformas o accesos vigentes | areas-y-roles.md |
| P13 regla de absorción | Afecta la implementación, no la forma del contrato; el contrato ya exige CSRF (SEC-SES-04) | README.md |
| P6 (resto) | Nivel del acceso automático del admin creador: `admin`; otros admins del área y revocación al quitarle el área: según FNC-055 | plataformas-integracion.md |
| §12.11 de seguridad | Lista blanca de hosts de conectores fijada por el despliegue (no editable en la interfaz) | conectores-y-ejecuciones.md |
| Superadmin en grupos LDAP | El acceso por defecto del superadmin no genera registros de acceso; si debe estar en los grupos LDAP, se define en FNC-055 | accesos.md |
