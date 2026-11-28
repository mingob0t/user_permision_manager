# Contrato — Solicitudes de acceso

| Campo | Valor |
|---|---|
| Versión | 1.6 (2026-11-28) |
| Proveedor | backend (FNC-056, FNC-057) |
| Consumidores | web (FNC-069; pantallas DIS-013, DIS-014, DIS-015, DIS-131) |
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
| `GET /access-requests/inbox/stats` | 403 | 200 (sus áreas) | — (no cuentan) | 200 (todas) |
| `POST /access-requests/<id>/approve` | 403 | 200 | 404 | 200 |
| `POST /access-requests/<id>/reject` | 403 | 200 | 404 | 200 |

Propia solicitud en approve/reject → 403 `solicitud_propia` (SEC-AUTHZ-08).

## `GET /access-requests/catalog`
- P1: plataformas con `status = Activo` de las áreas `Activo` a las que pertenece el actor (`user_areas`); un admin de área ve además las que administra (`can_request = false`). Superadmin: todas, `can_request = false`.
- Filtros: `area_id` (int), `q` (texto, ≤ 100). Sin paginar (acotado por áreas del usuario). Orden: área, nombre.

```json
[ { "platform": { "id": 12, "name": "Contabilidad", "description": "ERP contable", "icon": "box" },
    "area": { "id": 3, "name": "Finanzas" },
    "my_level": "usuario", "my_access_status": "activo", "pending_request_id": null,
    "can_request": true, "requestable_levels": ["usuario"] } ]
```
| Campo | Tipo |
|---|---|
| `my_level` | `"usuario"` \| `"admin"` \| null |
| `my_access_status` | estado del acceso (accesos.md) \| null |
| `pending_request_id` | int \| null |
| `can_request` | boolean (false si es su área administrada, superadmin, pendiente, o ya tiene `admin`; desde 1.2 no depende de grupos ni conector) |
| `requestable_levels` | `["usuario"]` o `[]` (v1.3, FNC-199: el nivel admin no se solicita; lo otorga un administrador) |

## `POST /access-requests`
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `platform_id` | int | Sí | En el catálogo del actor |
| `level` | `"usuario"` | No (por omisión `usuario`) | v1.3, FNC-199: `"admin"` → `422 validacion` |
| `justification` | string \| null | Según `motivos.solicitud` | v1.5: `oculto` (por omisión) la descarta y guarda null sin validarla; `opcional` ≤ 500, recortada, vacía → null; `obligatorio` no vacía y ≤ 500, si no `422 validacion` con `fields.justification` |

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

## `GET /access-requests/inbox/stats` (FNC-200, v1.3)
Resumen para la pantalla Solicitudes (DIS-131). Mismo alcance que `inbox` (`approvals.bandeja`: sin las propias), **todos los estados**, sin parámetros ni paginación.

```json
{ "total": 12,
  "by_status": { "pendiente": 3, "aprobada": 7, "rechazada": 2 },
  "by_area": [ { "area_id": 3, "area": "Finanzas", "count": 8 } ],
  "by_platform": [ { "platform_id": 12, "platform": "Contabilidad", "area": "Finanzas", "count": 5 } ],
  "pending_by_area": [ { "area_id": 3, "area": "Finanzas", "count": 2 } ],
  "pending_by_platform": [ { "platform_id": 12, "platform": "Contabilidad", "area_id": 3, "area": "Finanzas", "count": 2 } ] }
```
| Campo | Regla |
|---|---|
| `by_status` | Siempre las 3 claves (0 si no hay) |
| `by_area`, `by_platform` | Solo con `count > 0`; orden `count` descendente y nombre ascendente; sin límite (la web recorta) |
| `total` | Suma de `by_status` |
| `pending_by_area` | v1.4 (FNC-212): como `by_area`, pero solo `pendiente` (por aprobar); lo usa la tarjeta de área |
| `pending_by_platform` | v1.6 (FNC-219): solo `pendiente`, por plataforma, con `area_id` y `area`; solo `count > 0`, mismo orden y alcance que `by_platform`; lo usa Gestión > área > plataformas (DIS-161) |

## `POST /access-requests/<id>/approve`
- Sin cuerpo (`{}`).
- Efecto: estado `aprobada` + acceso `en_proceso` + trabajo encolado, en una transacción (accesos.md). Si sube de nivel, el acceso anterior pasa a `revocando`.
- Respuesta: `{"status": "success", "request": AccessRequest}`. Auditoría `solicitud_aprobada`; correo `solicitud_aprobada`.

## `POST /access-requests/<id>/reject`
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `reason` | string \| null | Según `motivos.rechazo` | v1.5: `obligatorio` (por omisión) 10–500 caracteres, recortado (RF-06); `opcional` vacío o ausente → null, si viene 10–500; `oculto` se descarta (null) |

Respuesta: `{"status": "success", "request": AccessRequest}`. Auditoría `solicitud_rechazada`; correo `solicitud_rechazada` con el motivo (sin el párrafo «Motivo» si no hay; también sin motivo se audita).

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 403 | `solicitud_propia` | No puedes decidir tu propia solicitud. |
| 409 | `solicitud_duplicada` | Ya tienes una solicitud pendiente para esta plataforma. |
| 409 | `nivel_vigente` | Ya tienes ese nivel o uno superior. |
| 409 | `ya_administra_area` | Ya administras esta área; tienes acceso automático. |
| 409 | `plataforma_no_disponible` | La plataforma o su área están inactivas. (Desde 1.2 ya no se responde por falta de grupos o conector: toda plataforma activa es solicitable en ambos niveles, FNC-196.) |
| 409 | `solicitud_ya_decidida` | La solicitud ya fue decidida. |
| 409 | `estado_invalido` | Subir de nivel con el acceso actual aún no `activo` (accesos.md) |
| 422 | `validacion` | `fields.justification`: "Escribe como máximo 500 caracteres." o, con `obligatorio` y vacía, "Escribe el motivo de tu solicitud."; `fields.reason`: "Escribe entre 10 y 500 caracteres." (cuando `reason` se exige o, si es opcional, cuando viene) |

## Modos de motivo (v1.5, FNC-216)
Decisión del dueño (2026-11-27): se controla desde `.env` (`SOLICITUD_MOTIVO`, `RECHAZO_MOTIVO`), no desde una pantalla. Modifica RF-06.
- Se exponen en `GET /api/v1/auth/context` (público) como `"motivos": {"solicitud": "oculto|opcional|obligatorio", "rechazo": "obligatorio|opcional|oculto"}`. Cambiarlos exige reiniciar el backend.
- **Web (FNC-217):** lee `motivos` y, por modo: `oculto` no muestra el campo; `opcional` lo muestra sin marca de requerido; `obligatorio` lo muestra requerido y bloquea el envío vacío. El backend valida siempre y es quien manda: un `422 validacion` con `fields.justification` o `fields.reason` se pinta en el campo. En el rechazo, con `opcional` el diálogo permite confirmar vacío y con `oculto` no se muestra el campo.
- `rejection_reason` y `justification` de `AccessRequest` pueden ser `null` (ya lo eran `justification` y, para pendientes/aprobadas, `rejection_reason`; ahora también en rechazadas). La web debe mostrar el motivo solo si existe.

## Refresco
| Pantalla | Polling |
|---|---|
| Mis solicitudes (`mine`) | Sí, mientras haya `pendiente` o accesos `en_proceso` |
| Aprobaciones (`inbox`) | Sí |
| Resumen (`inbox/stats`) | Sí, con el mismo intervalo que la bandeja |
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
| 1.1 | 2026-10-20 | `justification` opcional, sin mínimo (decisión del dueño); catálogo solo de áreas `Activo` y admin ve sus áreas sin solicitar; `409 estado_invalido` al subir con acceso no activo (FNC-056) |
| 1.2 | 2026-11-24 | FNC-196 (dueño): toda plataforma activa de un área activa es solicitable en ambos niveles; el acceso se da por el grupo `app-{plataforma}-{nivel}` y, si hay conector, además por su alta. `plataforma_no_disponible` solo por plataforma o área inactivas. Sin cambios de forma |
| 1.3 | 2026-11-24 | FNC-199 (dueño): solo se solicita el nivel `usuario`; `level` opcional (por omisión `usuario`), `admin` → `422`. `requestable_levels` ⊆ `["usuario"]` |
| 1.4 | 2026-11-26 | FNC-212: `inbox/stats` agrega `pending_by_area` (solo pendientes por área). Campo nuevo, sin cambios de forma en lo existente |
| 1.5 | 2026-11-27 | FNC-216 (dueño): motivo de solicitud y de rechazo configurables por `.env`; `GET /auth/context` agrega `motivos`; `rejection_reason` puede ser null también en rechazadas. Campos existentes sin cambio de forma |
| 1.6 | 2026-11-28 | FNC-219: `inbox/stats` agrega `pending_by_platform` (pendientes por plataforma, con `area_id`). Campo nuevo, sin cambios de forma en lo existente. Coordinación: FNC-218 (otra sesión) también toca este contrato; quien integre segundo toma la versión siguiente (1.7) y conserva ambas filas |
