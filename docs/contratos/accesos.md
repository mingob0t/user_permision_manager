# Contrato — Accesos otorgados e inventario

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-14) |
| Proveedor | backend (FNC-054, FNC-058, FNC-059) |
| Consumidores | web (FNC-069; pantallas DIS-014, DIS-018, DIS-021) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Tabla `platform_access_grants`.

## Estados del acceso
| Estado | Significa | Siguiente |
|---|---|---|
| `en_proceso` | Otorgamiento encolado | `activo` \| `fallido` |
| `activo` | Confirmado en LDAP o por el conector (SEC-CON-09) | `revocando` |
| `fallido` | El otorgamiento agotó reintentos | `en_proceso` (reintento, conectores-y-ejecuciones.md) |
| `revocando` | Revocación encolada | `revocado` \| `fallo_revocacion` |
| `revocado` | Final | — |
| `fallo_revocacion` | La revocación agotó reintentos | `revocando` (reintento) |

| Campo | Valores |
|---|---|
| `level` | `usuario` \| `admin` (P5: uno vigente por usuario y plataforma; subir reemplaza) |
| `origin` | `solicitud` \| `admin_de_area` (P4: sin `heredado`; los accesos de NEXUS se descartan) |

- Vigente = `en_proceso`, `activo`, `revocando`, `fallido` o `fallo_revocacion`.
- Subir a `admin`: el acceso `usuario` pasa a `revocando` (motivo `reemplazado_por_nivel_superior`) y el nuevo `admin` a `en_proceso`, en una transacción.
- Superadmin: acceso por defecto, sin registros aquí. Si debe estar en los grupos LDAP: *Por confirmar* (FNC-055).

## Endpoints

| Método y ruta | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| `GET /me/access` | 200 | 200 | 200 | 200 (vacío) |
| `GET /users/<id>/access` | 403 (usa `/me/access`) | 200 (solo plataformas de sus áreas) | 404 | 200 |
| `POST /access/<id>/revoke` | 403 | 200 | 404 | 200 |
| `GET /access/inventory` | 403 | 200 (sus áreas) | — (no aparecen) | 200 (todo) |

- Revocar un acceso propio → 403 `operacion_propia` (SEC-AUTHZ-08).
- Un admin no revoca accesos de otros admins del área ni accesos de origen `admin_de_area` → 404 (SEC-AUTHZ-06); el superadmin sí.

## `GET /me/access` · `GET /users/<id>/access`
| Parámetro | Tipo | Regla |
|---|---|---|
| `status` | estado o `vigente` | Por defecto `vigente` |
| `page`, `per_page` | int | Paginada |

Orden: `granted_at` descendente. Respuesta paginada de `Access`.

### `Access`
```json
{ "id": 77, "status": "activo", "level": "usuario", "origin": "solicitud",
  "user": { "id": 8, "name": "Ana Ruiz", "email": "ana@ejemplo.local" },
  "platform": { "id": 12, "name": "Contabilidad", "integration_type": "ldap" },
  "area": { "id": 3, "name": "Finanzas" },
  "request_id": 41, "granted_by": { "id": 2, "name": "Luis Paz" }, "granted_at": "2026-10-14T15:10:00Z",
  "revoked_by": null, "revoked_at": null, "revoke_reason": null, "last_job_id": 301 }
```
| Campo | Tipo |
|---|---|
| `granted_by` | `{id, name}` \| null (null = `sistema`, origen `admin_de_area`) |
| `revoked_by` | `{id, name}` \| null |
| `last_job_id` | int \| null (ver conectores-y-ejecuciones.md); se omite en `/me/access` para el rol usuario |

## `POST /access/<id>/revoke`
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `reason` | string \| null | No (P7, 2026-10-14) | ≤ 500 si llega; sin mínimo |

- Solo desde `activo` → `revocando` + trabajo encolado, en una transacción.
- Respuesta: `{"status": "success", "access": Access}`. Auditoría `acceso_revocado` (solicitado) y luego `revocacion_fallida` o el resultado final del trabajo.

## `GET /access/inventory`
F-AUD-02: quién tiene qué plataforma, nivel, desde cuándo y quién aprobó.

| Parámetro | Tipo |
|---|---|
| `area_id`, `platform_id`, `user_id` | int |
| `level` | `usuario` \| `admin` |
| `origin` | `solicitud` \| `admin_de_area` |
| `status` | estado o `vigente` (por defecto `vigente`) |
| `q` | texto ≤ 100 (nombre o correo del usuario) |
| `page`, `per_page` | int |

Orden: área, plataforma, usuario. Respuesta paginada de `Access` (mismos campos).

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 403 | `operacion_propia` | No puedes revocar tu propio acceso. |
| 409 | `estado_invalido` | Solo se revoca un acceso activo. |
| 422 | `validacion` | `fields.reason`: "Máximo 500 caracteres." |

## Refresco
| Pantalla | Polling |
|---|---|
| Mis accesos (`/me/access`) | Sí, mientras haya `en_proceso` o `revocando` |
| Usuarios y accesos (`/users/<id>/access`) | Sí, mientras haya `en_proceso` o `revocando` |
| Inventario | No; botón de recarga |

## Datos simulados
```json
{ "items": [ { "id": 78, "status": "en_proceso", "level": "admin", "origin": "admin_de_area",
  "user": { "id": 2, "name": "Luis Paz", "email": "luis@ejemplo.local" },
  "platform": { "id": 12, "name": "Contabilidad", "integration_type": "conector" },
  "area": { "id": 3, "name": "Finanzas" }, "request_id": null, "granted_by": null,
  "granted_at": "2026-10-14T15:00:00Z", "revoked_by": null, "revoked_at": null,
  "revoke_reason": null, "last_job_id": 300 } ], "page": 1, "per_page": 25, "total": 1 }
```

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038) |
