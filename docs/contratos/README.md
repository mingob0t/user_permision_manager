# Contratos backend ↔ web

Acuerdos de API `/api/v1` del gestor de accesos (fase 3). Se integran a `develop` antes de implementar. Solo cambian por una nueva versión aprobada por el dueño (tarea en el tablero), nunca de un lado.

## Índice

| Contrato | Versión | Proveedor | Consumidor | Tareas que lo implementan |
|---|---|---|---|---|
| [areas-y-roles.md](areas-y-roles.md) | 2 (2026-10-19) | backend | web | FNC-044, FNC-045, FNC-055 |
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
- Agregar un campo opcional a una respuesta: misma versión, nota en la sección **Historial** del contrato.
- Quitar o renombrar un campo, cambiar un tipo, un código o un permiso: versión N+1 aprobada por el dueño.
- La ruta sigue en `/api/v1`; una ruptura incompatible se publica como ruta nueva, no se rompe la existente.

## Convenciones comunes (aplican a todos los contratos)

| Tema | Regla |
|---|---|
| Sesión | Cookie de Flask; sin sesión → `401` |
| Rol insuficiente | `403` (SEC-AUTHZ-04) |
| Recurso fuera de alcance (área ajena) | `404`, igual que inexistente (SEC-AUTHZ-03/04) |
| Escrituras | `Content-Type: application/json` (otro → `415`, SEC-SES-05); token CSRF en cabecera y `Origin` del mismo sitio (SEC-SES-04). Nombre de la cabecera y obtención del token: FNC-008 — *Por confirmar (P13)* |
| Lista blanca | Cada endpoint acepta solo los campos de su tabla; `is_active`, `auth_source`, `password_hash`, `managed_area_ids` y campos desconocidos → `400 campo_no_permitido` (SEC-AUTHZ-09). `auth_source` lo fija el servidor |
| Excepción `role` | Solo en `POST /users` y `PUT /users/<id>` ([areas-y-roles.md](areas-y-roles.md)): superadmin `usuario` \| `admin_area`; admin solo `usuario` (o sin `role`); cualquier otro valor de un admin, o `administrador` de cualquiera → `403 rol_reservado`. En los demás endpoints `role` → `400 campo_no_permitido` |
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
| P7 (2026-10-14) | Revocar no requiere motivo | accesos.md |
| P8 (2026-10-14) | El portal no maneja contraseñas de cuentas LDAP; la contraseña la maneja Authelia | usuarios-directorio.md |
| P10 (2026-10-14) | Aviso de fallo a admins del área y superadmin; reintento manual solo superadmin | conectores-y-ejecuciones.md |
| P10 (2026-10-15) | El aviso de fallo respeta `pref_email_notifications` | conectores-y-ejecuciones.md |
| P11 (2026-10-14) | Baja de áreas: admin (sus áreas) y superadmin; `409` con plataformas o accesos vigentes | areas-y-roles.md |

## Endpoints retirados en v1
| Endpoint | Motivo | Tarea |
|---|---|---|
| `PUT /platforms/<id>/users` | P4: los accesos de NEXUS (`user_platforms`) se descartan; el acceso sale de solicitudes | FNC-065 |
| `PUT /users/<id>/platforms` | Igual | FNC-065 |

## Por confirmar (valor más seguro aplicado)
| Pregunta | Valor aplicado | Dónde |
|---|---|---|
| P13 regla de absorción | Afecta la implementación, no la forma del contrato; el contrato ya exige CSRF (SEC-SES-04) | README.md |
| P6 (resto) | Nivel del acceso automático del admin creador: `admin`; otros admins del área y revocación al quitarle el área: según FNC-055 | plataformas-integracion.md |
| §12.11 de seguridad | Lista blanca de hosts de conectores fijada por el despliegue (no editable en la interfaz) | conectores-y-ejecuciones.md |
| Superadmin en grupos LDAP | El acceso por defecto del superadmin no genera registros de acceso; si debe estar en los grupos LDAP, se define en FNC-055 | accesos.md |

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038); respuestas P7, P8, P10 y P11 y correcciones de revisión incorporadas antes del merge |
| areas-y-roles 2 | 2026-10-19 | `password` en `POST/PUT /users` (FNC-077) |
