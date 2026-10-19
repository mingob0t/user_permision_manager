# Contrato — Conectores y ejecuciones de aprovisionamiento

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-14) |
| Proveedor | backend (FNC-061, FNC-062; base FNC-049, FNC-050) |
| Consumidores | web (FNC-069; pantallas DIS-022, DIS-018) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Cola: Redis + RQ (ADR-003). P9: los tipos `api`, `ssh` y `bd` (FNC-051 a FNC-053) esperan; su esquema de `params` se agrega como versión aditiva.

## Endpoints

| Método y ruta | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| `GET /platforms/<id>/connector` | 403 | 403 | 403 | 200 |
| `PUT /platforms/<id>/connector` | 403 | 403 | 403 | 200 |
| `DELETE /platforms/<id>/connector` | 403 | 403 | 403 | 200 |
| `POST /platforms/<id>/connector/test` | 403 | 403 | 403 | 200 |
| `GET /provisioning/jobs` | 403 | 200 (sus áreas, lectura) | — (no aparecen) | 200 |
| `GET /provisioning/jobs/<id>` | 403 | 200 | 404 | 200 |
| `POST /provisioning/jobs/<id>/retry` | 403 | 403 (P10) | 403 | 200 |

Conectores: solo superadmin (SEC-CON-11).

## `PUT /platforms/<id>/connector` (crea o reemplaza)
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `type` | `"api"` \| `"ssh"` \| `"bd"` | Sí | `noop` solo en dev y pruebas; tipo sin implementar → 422 |
| `host` | string | Sí | Nombre de host de la lista blanca del despliegue (SEC-CON-07; *Por confirmar* §12.11); IP literal → 422 |
| `port` | int | Sí | 1–65535 |
| `params` | object | Sí | Validado por el esquema del tipo; sin secretos |
| `credential_ref` | string | Sí | Referencia del ítem en Vaultwarden (ADR-005), ≤ 200; nunca el valor |
| `active` | boolean | No | Por defecto `true` |

- La plataforma debe tener `integration_type = "conector"` → si no, 409.
- Cambiar `host` invalida la verificación de la credencial (SEC-CON-07).
- Respuesta: `{"status": "success", "connector": Connector}`. Auditoría `conector_configurado`.

### `Connector`
```json
{ "platform_id": 12, "type": "api", "host": "erp.ejemplo.local", "port": 443,
  "params": { "base_path": "/usuarios" }, "credential_ref": "pokemon/contabilidad-api",
  "credential_status": "ok", "active": true, "updated_at": "2026-10-14T14:00:00Z" }
```
`credential_status`: `ok` \| `no_encontrada` \| `sin_verificar`. Nunca se devuelve el valor de la credencial.

## `DELETE /platforms/<id>/connector`
- `409 plataforma_con_accesos` si hay accesos vigentes. Respuesta `{"status": "success"}`. Auditoría `conector_eliminado`.

## `POST /platforms/<id>/connector/test`
- Sin cuerpo. Ejecuta `consultar` sin cambios. Respuesta `200`:
```json
{ "status": "success", "result": "ok", "message": "Conexión correcta." }
```
- Fallo: `200` con `"result": "error"` y mensaje genérico ("No se pudo conectar con la plataforma."); el detalle solo al log. Auditoría `conector_probado`.

## `GET /provisioning/jobs`
| Parámetro | Tipo |
|---|---|
| `status` | `pendiente` \| `en_ejecucion` \| `reintentando` \| `exitoso` \| `fallido` \| `cancelado` |
| `operation` | `otorgar` \| `revocar` |
| `provider` | `ldap` \| `conector` |
| `area_id`, `platform_id`, `user_id`, `access_id` | int |
| `from`, `to` | fecha ISO 8601 |
| `page`, `per_page` | int |

Orden: `created_at` descendente. Respuesta paginada de `Job` (sin `attempts`).

### `Job` (detalle con `attempts`)
```json
{ "id": 301, "status": "fallido", "operation": "otorgar", "provider": "conector",
  "access_id": 77, "user": { "id": 8, "name": "Ana Ruiz" }, "platform": { "id": 12, "name": "Contabilidad" },
  "area": { "id": 3, "name": "Finanzas" }, "attempts_count": 5, "max_attempts": 5,
  "next_attempt_at": null, "created_at": "2026-10-14T15:10:00Z", "finished_at": "2026-10-14T15:40:00Z",
  "attempts": [ { "n": 5, "started_at": "2026-10-14T15:39:58Z", "finished_at": "2026-10-14T15:40:00Z",
                  "result": "error_transitorio", "error": "Tiempo de espera agotado." } ] }
```
| Campo | Tipo |
|---|---|
| `attempts[].result` | `exitoso` \| `sin_cambios` \| `error_transitorio` \| `error_permanente` |
| `attempts[].error` | string \| null; saneado y truncado a 500, sin secretos (SEC-CON-10) |

## `POST /provisioning/jobs/<id>/retry`
- Sin cuerpo. Solo desde `fallido` → `pendiente`; el acceso vuelve a `en_proceso` o `revocando`.
- Respuesta: `{"status": "success", "job": Job}`. Auditoría `ejecucion_reintentada`.

## Aviso de fallo (P10, 2026-10-14)
- Al agotar reintentos: correo `aprovisionamiento_fallido` a los admins del área y al superadmin (respeta `pref_email_notifications`: respuesta del dueño 2026-10-15); auditoría `acceso_fallido` o `revocacion_fallida`.

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 409 | `plataforma_sin_conector` | La plataforma no usa conector. |
| 409 | `plataforma_con_accesos` | Hay accesos vigentes con este conector. |
| 409 | `estado_invalido` | Solo se reintenta una ejecución fallida. |
| 422 | `validacion` | `fields.host`: "Usa un nombre de host autorizado." · `fields.params.<campo>` según el tipo |

## Refresco
| Pantalla | Polling |
|---|---|
| Ejecuciones (lista y detalle) | Sí, mientras haya `pendiente`, `en_ejecucion` o `reintentando` |
| Configuración del conector | No |

## Datos simulados
```json
{ "items": [ { "id": 302, "status": "reintentando", "operation": "revocar", "provider": "ldap", "access_id": 70,
  "user": { "id": 9, "name": "Eva Mora" }, "platform": { "id": 5, "name": "Wiki" }, "area": { "id": 1, "name": "TI" },
  "attempts_count": 2, "max_attempts": 5, "next_attempt_at": "2026-10-14T16:02:00Z",
  "created_at": "2026-10-14T16:00:00Z", "finished_at": null } ], "page": 1, "per_page": 25, "total": 1 }
```

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038) |
| 1 | 2026-10-19 | Aditivo (FNC-049): `status` `cancelado` (un otorgar en espera que una revocación posterior de la misma terna dejó sin efecto; final, no se reintenta) |
| 1 | 2026-10-15 | Redacción: P10 resuelto, el aviso de fallo respeta `pref_email_notifications` (FNC-048) |
