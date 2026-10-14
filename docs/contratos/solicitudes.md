# Contrato — Solicitudes de acceso

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-14) |
| Proveedor | backend (FNC-056, FNC-057) |
| Consumidores | web (FNC-069; pantallas DIS-013, DIS-014, DIS-015) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Tabla `platform_access_requests`.

## Estados
| Estado | Siguiente | Quién |
|---|---|---|
| `pendiente` | `aprobada` \| `rechazada` | Admin del área de la plataforma o superadmin, nunca el solicitante |
| `aprobada` | — (final; genera un acceso, ver accesos.md) | — |
| `rechazada` | — (final) | — |

Solo se decide una solicitud `pendiente`, con bloqueo de fila (SEC-AUTHZ-10).

## Endpoints

| Método y ruta | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| `GET /access-requests/catalog` | 200 | 200 (solo ver) | 200 (puede solicitar) | 200 (solo ver) |
| `POST /access-requests` | 201 | 409 `ya_administra_area` | 201 | 403 |
| `GET /access-requests/mine` | 200 | 200 | 200 | 200 (vacío) |
| `GET /access-requests/inbox` | 403 | 200 (sus áreas) | — (no aparecen) | 200 (todas) |
| `POST /access-requests/<id>/approve` | 403 | 200 | 404 | 200 |
| `POST /access-requests/<id>/reject` | 403 | 200 | 404 | 200 |

Propia solicitud en approve/reject → 403 `solicitud_propia` (SEC-AUTHZ-08).

## `GET /access-requests/catalog`
- P1: plataformas con `status = Activo` de las áreas a las que pertenece el actor (`user_areas`). Superadmin: todas, `can_request = false`.
- Filtros: `area_id` (int), `q` (texto, ≤ 100). Sin paginar (acotado por áreas del usuario). Orden: área, nombre.

```json
[ { "platform": { "id": 12, "name": "Contabilidad", "description": "ERP contable", "icon": "box" },
    "area": { "id": 3, "name": "Finanzas" },
    "my_level": "usuario", "my_access_status": "activo", "pending_request_id": null,
    "can_request": true, "requestable_levels": ["admin"] } ]
```
| Campo | Tipo |
|---|---|
| `my_level` | `"usuario"` \| `"admin"` \| null |
| `my_access_status` | estado del acceso (accesos.md) \| null |
| `pending_request_id` | int \| null |
| `can_request` | boolean (false si es su área administrada, superadmin, pendiente, plataforma sin grupos ni conector, o ya tiene `admin`) |
| `requestable_levels` | (`"usuario"` \| `"admin"`)[]; P5: solo niveles superiores al vigente |

## `POST /access-requests`
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `platform_id` | int | Sí | En el catálogo del actor |
| `level` | `"usuario"` \| `"admin"` | Sí | P5: un nivel por plataforma; pedir `admin` con `usuario` vigente es subir (reemplaza al aprobarse) |
| `justification` | string | Sí | 10–500 caracteres |

Respuesta `201`: `{"status": "success", "request": AccessRequest}`. Auditoría `solicitud_creada`; correo `solicitud_nueva` a los admins del área (FNC-048).

## `GET /access-requests/mine` · `GET /access-requests/inbox`
| Parámetro | Tipo | mine | inbox |
|---|---|---|---|
| `status` | `pendiente` \| `aprobada` \| `rechazada` | Sí | Sí (por defecto `pendiente`) |
| `area_id` | int | No | Sí (fuera de alcance → lista vacía) |
| `platform_id` | int | Sí | Sí |
| `page`, `per_page` | int | Sí | Sí |

Orden: `created_at` descendente (inbox `pendiente`: ascendente, la más antigua primero). Respuesta paginada de `AccessRequest`.

### `AccessRequest`
```json
{ "id": 41, "status": "pendiente", "level": "admin", "justification": "Cierre mensual",
  "requester": { "id": 8, "name": "Ana Ruiz", "email": "ana@ejemplo.local" },
  "platform": { "id": 12, "name": "Contabilidad" }, "area": { "id": 3, "name": "Finanzas" },
  "current_level": "usuario",
  "created_at": "2026-10-14T15:04:05Z", "decided_at": null,
  "decided_by": null, "rejection_reason": null, "access": null }
```
| Campo | Tipo |
|---|---|
| `current_level` | nivel vigente del solicitante al crear la solicitud \| null |
| `decided_by` | `{ "id": int, "name": string }` \| null |
| `access` | `{ "id": int, "status": string }` \| null (tras aprobar) |

## `POST /access-requests/<id>/approve`
- Sin cuerpo (`{}`).
- Efecto: estado `aprobada` + acceso `en_proceso` + trabajo encolado, en una transacción (accesos.md). Si sube de nivel, el acceso anterior pasa a `revocando`.
- Respuesta: `{"status": "success", "request": AccessRequest}`. Auditoría `solicitud_aprobada`; correo `solicitud_aprobada`.

## `POST /access-requests/<id>/reject`
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `reason` | string | Sí | 10–500 caracteres (RF-06) |

Respuesta: `{"status": "success", "request": AccessRequest}`. Auditoría `solicitud_rechazada`; correo `solicitud_rechazada` con el motivo.

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 403 | `solicitud_propia` | No puedes decidir tu propia solicitud. |
| 409 | `solicitud_duplicada` | Ya tienes una solicitud pendiente para esta plataforma. |
| 409 | `nivel_vigente` | Ya tienes ese nivel o uno superior. |
| 409 | `ya_administra_area` | Ya administras esta área; tienes acceso automático. |
| 409 | `plataforma_no_disponible` | La plataforma está inactiva o sin integración configurada. |
| 409 | `solicitud_ya_decidida` | La solicitud ya fue decidida. |
| 422 | `validacion` | `fields.justification` / `fields.reason`: "Escribe entre 10 y 500 caracteres." |

## Refresco
| Pantalla | Polling |
|---|---|
| Mis solicitudes (`mine`) | Sí, mientras haya `pendiente` o accesos `en_proceso` |
| Aprobaciones (`inbox`) | Sí |
| Catálogo | No; recarga tras solicitar |

## Datos simulados
```json
{ "items": [ { "id": 41, "status": "rechazada", "level": "usuario", "justification": "Consulta de pólizas",
  "requester": { "id": 8, "name": "Ana Ruiz", "email": "ana@ejemplo.local" },
  "platform": { "id": 12, "name": "Contabilidad" }, "area": { "id": 3, "name": "Finanzas" },
  "current_level": null, "created_at": "2026-10-13T10:00:00Z", "decided_at": "2026-10-13T12:30:00Z",
  "decided_by": { "id": 2, "name": "Luis Paz" }, "rejection_reason": "Usa el reporte compartido del área.", "access": null } ],
  "page": 1, "per_page": 25, "total": 1 }
```

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038) |
