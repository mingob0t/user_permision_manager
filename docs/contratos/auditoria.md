# Contrato — Auditoría

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-14) |
| Proveedor | backend (FNC-047, FNC-060) |
| Consumidores | web (FNC-069; pantalla DIS-020) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Inmutable: sin rutas de edición ni borrado (SEC-AUD-03).

## Endpoints

| Método y ruta | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| `GET /audit` | 200 (los propios) | 200 (área afectada) | — (no aparecen) | 200 (todo) |
| `GET /audit/users/<id>` | 200 solo si es él; si no 404 | 200 (eventos de sus áreas) | 404 | 200 |
| `GET /audit/platforms/<id>` | 403 | 200 | 404 | 200 |

- "Los propios" del usuario: eventos donde es actor o usuario afectado.
- Admin: eventos con `area_id` de sus áreas (SEG-16); los eventos sin área solo los ve el superadmin.

## Parámetros (los tres endpoints)
| Parámetro | Tipo | Regla |
|---|---|---|
| `action` | enumerado (catálogo) | — |
| `result` | `success` \| `error` \| `warning` \| `info` | — |
| `area_id`, `platform_id`, `user_id` | int | Fuera de alcance → lista vacía |
| `from`, `to` | fecha ISO 8601 | `from ≤ to`; rango ≤ 366 días |
| `q` | texto ≤ 100 | Busca en actor y destino |
| `page`, `per_page` | int | Paginada |

Orden: `time` descendente. `GET /audit?limit=` sigue aceptándose en v1 (cliente actual); `page`/`per_page` tienen prioridad.

## `AuditEntry` (campos existentes + nuevos)
```json
{ "id": 9001, "time": "2026-10-14T15:00:01Z", "user": "sistema", "action": "acceso_otorgado",
  "module": "accesos", "target": "luis@ejemplo.local", "detail": "Acceso admin a Contabilidad",
  "ip": null, "status": "success",
  "actor": null, "area": { "id": 3, "name": "Finanzas" }, "platform": { "id": 12, "name": "Contabilidad" },
  "target_user": { "id": 2, "email": "luis@ejemplo.local" },
  "before": null, "after": { "status": "en_proceso", "level": "admin", "origin": "admin_de_area" } }
```
| Campo | Tipo | Nota |
|---|---|---|
| `id`, `time`, `user`, `action`, `module`, `target`, `detail`, `ip`, `status` | existentes | No se renombran (`types.ts`); `user = "sistema"` si actúa el sistema |
| `actor` | `{id, email}` \| null | null = sistema |
| `area`, `platform` | `{id, name}` \| null | — |
| `target_user` | `{id, email}` \| null | — |
| `before`, `after` | object \| null | Sin contraseñas, tokens ni secretos (SEC-AUD-05) |

`ip` solo se devuelve a admin y superadmin; al usuario, `null`.

## Catálogo de `action` (gestor de accesos)
| `action` | Actor | Ejemplo |
|---|---|---|
| `area_creada` / `area_editada` / `area_eliminada` | admin o superadmin | — |
| `admin_asignado` / `admin_retirado` | superadmin | Área administrada |
| `rol_cambiado` | superadmin | `before.role` → `after.role` |
| `plataforma_creada` | admin X | "admin X dio de alta la plataforma Y" |
| `plataforma_editada` | admin o superadmin | Incluye cambio de DN |
| `solicitud_creada` / `solicitud_aprobada` / `solicitud_rechazada` | usuario / admin | — |
| `acceso_otorgado` | `sistema` o admin | "sistema dio permisos de acceso a admin X" |
| `acceso_activo` / `acceso_fallido` | `sistema` | Resultado del trabajo |
| `acceso_revocado` / `revocacion_fallida` | admin o `sistema` | — |
| `cuenta_directorio_creada` | admin o superadmin | usuarios-directorio.md |
| `conector_configurado` / `conector_eliminado` / `conector_probado` | superadmin | — |
| `ejecucion_reintentada` | superadmin | — |

El catálogo vive en FNC-047; agregar valores es aditivo (misma versión).

## Refresco
- Sin polling; botón de recarga.

## Datos simulados
```json
{ "items": [ { "id": 9000, "time": "2026-10-14T15:00:00Z", "user": "luis@ejemplo.local", "action": "plataforma_creada",
  "module": "plataformas", "target": "Contabilidad", "detail": "Alta de plataforma", "ip": null, "status": "success",
  "actor": { "id": 2, "email": "luis@ejemplo.local" }, "area": { "id": 3, "name": "Finanzas" },
  "platform": { "id": 12, "name": "Contabilidad" }, "target_user": null, "before": null,
  "after": { "name": "Contabilidad", "integration_type": "ldap" } } ], "page": 1, "per_page": 25, "total": 1 }
```
