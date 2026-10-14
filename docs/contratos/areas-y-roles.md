# Contrato — Áreas y roles

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-14) |
| Proveedor | backend (FNC-044, FNC-045, FNC-055) |
| Consumidores | web (FNC-069; pantallas DIS-016, DIS-019) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Sin cambios: `GET /areas`, `GET /areas/<id>`, `PUT /areas/<id>/users`.

## Endpoints

| Método y ruta | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| `POST /areas` | 403 | 201 (queda como admin del área) | — | 201 |
| `PUT /areas/<id>` | 403 | 200 | 404 | 200 |
| `DELETE /areas/<id>` | 403 | 200 | 404 | 200 |
| `PUT /users/<id>/managed-areas` | 403 | 403 | 403 | 200 |
| `POST /users` (rol) | 403 | 201 con `usuario`; otro → 403 `rol_reservado` | — | 201 `usuario` o `admin_area` |
| `PUT /users/<id>` (rol) | 403 | 200 sin `role` o con `usuario`; otro → 403 `rol_reservado` | 404 | 200 |

### `POST /areas` · `PUT /areas/<id>`
Entrada (lista blanca):

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `name` | string | Sí en POST | 2–100; único (sin distinguir mayúsculas) |
| `description` | string \| null | No | ≤ 500 |
| `icon` | string | No | ≤ 50; nombre de ícono |
| `color` | string | No | Hex de 7 caracteres |
| `status` | string | No | `Activo` \| `Inactivo` |

- Admin de área en POST: se agrega a `area_admins` en la misma transacción; auditoría `area_creada`.
- Respuesta: `{"status": "success", "area": Area}` (tipo `Area` existente).

### `DELETE /areas/<id>` (P11, 2026-10-14)
- Admin (sus áreas) o superadmin; `409` si tiene plataformas o accesos vigentes.
- Respuesta: `{"status": "success"}`; auditoría `area_eliminada`.

### `PUT /users/<id>/managed-areas`
Asigna las áreas que administra un `admin_area` (`area_admins`). Reemplaza la lista completa.

```json
{ "area_ids": [3, 7] }
```

| Campo | Tipo | Regla |
|---|---|---|
| `area_ids` | int[] | 0–50 ids existentes, sin repetidos |

- El usuario destino debe tener rol `admin_area`; si no → 409 `rol_no_admin`.
- Efecto en accesos automáticos: FNC-055 (`sync_area_admin_grants`).
- Respuesta: `{"status": "success", "user": ManagedUser}`; auditoría `admin_asignado` / `admin_retirado` por área.

### Rol en `POST /users` y `PUT /users/<id>`
| Campo | Tipo | Regla |
|---|---|---|
| `role` | `"usuario"` \| `"admin_area"` | Solo superadmin; `administrador` nunca es asignable (SEC-AUTH-07) |

- `managed_area_ids` en `POST /users` o `PUT /users/<id>` → `400 campo_no_permitido`. La única vía para asignar áreas administradas es `PUT /users/<id>/managed-areas` (superadmin).
- `POST /users` con `admin_area` ya **no** copia `area_ids` a las áreas administradas (cambio respecto a hoy); nace sin áreas administradas.
- `auth_source` → `400 campo_no_permitido`; lo fija el servidor.
- Degradar `admin_area` → `usuario` borra sus áreas administradas en la misma transacción; auditoría `rol_cambiado` con antes y después.
- Un admin de área solo gestiona cuentas `usuario` de sus áreas (SEC-AUTHZ-06); sobre otro admin o el superadmin → 404.
- Nadie cambia su propio rol (SEC-AUTHZ-08) → 403 `operacion_propia`.

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 409 | `area_duplicada` | Ya existe un área con ese nombre. |
| 409 | `area_con_plataformas` | El área tiene plataformas; muévelas o elimínalas antes. |
| 409 | `area_con_accesos` | El área tiene accesos vigentes. |
| 409 | `rol_no_admin` | El usuario no es administrador de área. |
| 403 | `rol_reservado` | Ese rol no se puede asignar. |
| 400 | `campo_no_permitido` | Hay campos que no se pueden enviar. |
| 403 | `operacion_propia` | No puedes cambiar tu propio rol. |
| 422 | `validacion` | Revisa los campos marcados. |

## Refresco
- Sin polling; recarga tras cada escritura propia.

## Datos simulados
```json
{ "status": "success", "area": { "id": 3, "name": "Finanzas", "description": "Sistemas contables", "icon": "wallet", "color": "#2563eb", "status": "Activo", "platforms_count": 0, "users_count": 0 } }
```

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038) |
