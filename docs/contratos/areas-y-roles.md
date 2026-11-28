# Contrato — Áreas y roles

| Campo | Valor |
|---|---|
| Versión | 3.5 (2026-11-28) |
| Proveedor | backend (FNC-044, FNC-045, FNC-055, FNC-161, FNC-185) |
| Consumidores | web (FNC-069; pantallas DIS-016, DIS-019) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Sin cambios: `GET /areas`, `GET /areas/<id>`. `PUT /areas/<id>/users` y `PUT /users/<id>/areas` cambian en FNC-152 (abajo).

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
- **Activación (v3.5, FNC-220):** un área no se activa sin al menos un admin de área. `POST` con `status` `Activo` (o ausente, que equivale a `Activo`) sin admin → `409 area_sin_admin`; el admin de área que crea el área sí pasa (queda como su admin), y el superadmin debe enviar `status: "Inactivo"` o asignar admin después. `PUT` que cambia de `Inactivo` a `Activo` sin admin → `409 area_sin_admin` y no cambia nada. Editar otros campos o un área ya activa sin admin no se bloquea. Quitar el último admin de un área activa **no** se bloquea (decisión del dueño, 2026-11-28).
- Respuesta: `{"status": "success", "area": Area}` (tipo `Area` existente).

### `DELETE /areas/<id>` (P11, 2026-10-14)
- Admin (sus áreas) o superadmin; `409` si tiene plataformas o accesos vigentes.
- Admin de área sobre un área con otros admins → `409 area_con_otros_admins`; el superadmin sí puede (FNC-045, decisión del orquestador pendiente de validar en la prueba de concepto).
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
- Efecto en accesos automáticos (FNC-055, en la misma transacción): cada área agregada otorga al admin un acceso `admin_de_area` nivel `admin` (`en_proceso`) en cada plataforma `ldap` con grupo o `conector` de esa área (FNC-185; si ya tenía uno de `usuario`, sube: el de `usuario` pasa a `revocando`; `ldap` sin grupo admin queda en `usuario`); cada área quitada baja sus automáticos `admin` `activo` a `usuario` (el `admin` pasa a `revocando`, motivo `ya_no_administra_el_area`, actor `sistema`, y se otorga el de `usuario`; si no tenía acceso, queda con `usuario`; solo si es miembro del área, si no se revoca: P1); uno `en_proceso` se ajusta al confirmarse. Repetir la misma lista no cambia nada.
- Respuesta: `{"status": "success", "user": ManagedUser}`; auditoría `admin_asignado` / `admin_retirado` por área.

### Rol en `POST /users` y `PUT /users/<id>`
| Campo | Tipo | Regla |
|---|---|---|
| `role` | `"usuario"` \| `"admin_area"` | Superadmin: `usuario` o `admin_area`; admin: solo `usuario`; `administrador` nunca (SEC-AUTH-07) |

- `managed_area_ids` en `POST /users` o `PUT /users/<id>` → `400 campo_no_permitido`. La única vía para asignar áreas administradas es `PUT /users/<id>/managed-areas` (superadmin).
- `POST /users` con `admin_area` ya **no** copia `area_ids` a las áreas administradas (cambio respecto a hoy); nace sin áreas administradas.
- `auth_source` → `400 campo_no_permitido`; lo fija el servidor.
- Degradar `admin_area` → `usuario` borra sus áreas administradas en la misma transacción; auditoría `rol_cambiado` con antes y después; sus accesos automáticos bajan a nivel `usuario` y se conservan, como al quitarle las áreas (FNC-055, FNC-185).
- Un admin de área solo gestiona cuentas `usuario` de sus áreas (SEC-AUTHZ-06); sobre otro admin o el superadmin → 404.
- Nadie cambia su propio rol (SEC-AUTHZ-08) → 403 `operacion_propia`.
- `password` en `POST /users` (v2, FNC-077): el portal no fija contraseñas locales → `400 campo_no_permitido` (vacía = ausente; la cuenta nace sin clave); solo se acepta en desarrollo con la bandera. En `PUT /users/<id>` rige la regla de v3 (abajo); sin rol de admin → `403 sin_permiso`.
- **`PUT /users/<id>` con `password` según el origen (v3, FNC-161; sustituye a las dos reglas de `PUT` anteriores):**
  - `local`: hash en la BD, para cualquier cuenta local que quien edita pueda gestionar (cuenta de emergencia incluida). Solo se exige que sea texto no vacío (`400 contrasena_invalida`).
  - `ldap` y `sso` (v3.1, FNC-165: la cuenta `sso` nace al primer login por Authelia, que autentica contra el mismo OpenLDAP): solo el superadmin (admin de área → `403 solo_superadmin`). Debe cumplir la política `PASSWORD_POLICY_*` (`400 contrasena_invalida` con la regla incumplida) y se cambia en OpenLDAP con Password Modify; **nunca** se guarda hash en la BD. La cuenta se ubica por el `uid` de su entrega de credenciales o, si no hay, por su correo bajo `LDAP_USERS_BASE_DN` (se usa el DN encontrado). Si el directorio la rechaza por su `ppolicy` → `400 contrasena_rechazada` (sin el texto del servidor); directorio inactivo, caído o ambiguo → `503 directorio_no_disponible`; sin cuenta en el directorio → `409 cuenta_no_encontrada_en_directorio`. Si falla, no se aplica ningún otro campo del mismo `PUT`.
  - cualquier otro origen: `400 campo_no_permitido`.
  - La contraseña nunca se registra, audita ni devuelve. «Reenviar credenciales» (`POST /users/<id>/credentials`) se retiró (`410`, [usuarios-directorio.md](usuarios-directorio.md) v3).
- Origen en `POST /users` (v2, FNC-077): fuera de desarrollo la cuenta nace `auth_source=sso` (v3.2, FNC-168; antes `ldap`) sin contraseña y se vincula cuando la persona entra por directorio o SSO con ese correo; con la bandera de desarrollo, `local`. El rol sigue las reglas de arriba.

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 409 | `area_duplicada` | Ya existe un área con ese nombre. |
| 409 | `area_sin_admin` | Asigna al menos un administrador antes de activar el área. (FNC-220) |
| 409 | `area_con_plataformas` | El área tiene plataformas; muévelas o elimínalas antes. |
| 409 | `area_con_accesos` | El área tiene accesos vigentes. |
| 409 | `area_con_otros_admins` | El área tiene otros administradores; solo el superadmin puede darla de baja. |
| 409 | `rol_no_admin` | El usuario no es administrador de área. |
| 403 | `rol_reservado` | Ese rol no se puede asignar. |
| 400 | `campo_no_permitido` | Hay campos que no se pueden enviar. |
| 403 | `operacion_propia` | No puedes cambiar tu propio rol. |
| 403 | `solo_superadmin` | Solo el superadmin puede cambiar la contraseña de una cuenta del directorio. (FNC-161) |
| 400 | `contrasena_invalida` | La regla de la política que incumple, o «La contraseña no es válida.» (FNC-161) |
| 400 | `contrasena_rechazada` | El directorio rechazó la contraseña por su política de seguridad. (FNC-161) |
| 409 | `cuenta_no_encontrada_en_directorio` | No se encontró la cuenta en el directorio. (FNC-161) |
| 503 | `directorio_no_disponible` | No se pudo actualizar la contraseña en el directorio. (FNC-161) |
| 503 | `sin_permiso_en_directorio` | La cuenta de servicio del portal no tiene permiso para esta operación en el directorio (contraseña o grupo del rol; con el rol, «El rol no se cambió.»). (FNC-206) |
| 403 | `sin_permiso` | Rol insuficiente (común, README). |
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
| 1 | 2026-10-15 | Aditivo (FNC-044): regla de `password` en `PUT /users/<id>` con `400 campo_no_permitido` (cuenta no local) y `403 sin_permiso` |
| 1 | 2026-10-18 | Aditivo (FNC-045): `409 area_con_otros_admins` en `DELETE /areas/<id>` para el admin de área (decisión del orquestador, pendiente de validar en la PoC) |
| 2 | 2026-10-19 | FNC-077 (decisión del dueño 2026-10-15: sin login local): `password` → `400 campo_no_permitido` en `POST /users` y en `PUT /users/<id>` salvo la cuenta de emergencia; excepción de desarrollo; `POST /users` crea cuentas `ldap` fuera de desarrollo. Cliente: DIS-018/DIS-019 (decisión del orquestador, pendiente de validar en la PoC) |
| 2.1 | 2026-10-20 | Aditivo (FNC-055): efecto en los accesos automáticos de `PUT /users/<id>/managed-areas` y de degradar a `usuario`. Sin cambios de forma |
| 3 | 2026-11-19 | FNC-161 (pedido del dueño): `password` en `PUT /users/<id>` según `auth_source`: `local` guarda hash para toda cuenta gestionable (antes solo emergencia: **más permisivo**); `ldap` cambia en OpenLDAP, solo superadmin, con la política (antes `400 campo_no_permitido`); `sso`/`oidc` sin cambio. Códigos nuevos `solo_superadmin`, `contrasena_invalida`, `contrasena_rechazada`, `cuenta_no_encontrada_en_directorio`. Decisión del orquestador (pendiente de validar). Cliente: `user-form.tsx` |

## Salida de un área (FNC-152)
- Quien deja de pertenecer a un área (`PUT /areas/<id>/users` o `PUT /users/<id>/areas`) pierde sus accesos por solicitud en las plataformas de esa área, en la misma petición.
- Se revocan como el sistema con motivo `ya_no_pertenece_al_area`: `activo` → `revocando` (trabajo `revocar`); sin conector, `en_proceso`/`activo`/`fallido` → `revocado`.
- Un acceso `en_proceso` con LDAP o conector no se toca (su trabajo `otorgar` sigue); los automáticos de admin de área los resincroniza `area_admin_sync` (los que conservó como `usuario` al dejar de administrar sí se revocan al salir del área, FNC-185).
| 3.1 | 2026-11-24 | FNC-165 (pedido del dueño): `password` en `PUT /users/<id>` para cuentas `sso` sigue la regla de `ldap` (antes `400 campo_no_permitido`: **más permisivo**, solo superadmin). La búsqueda por correo usa el DN real. Cliente: `user-form.tsx` (FNC-166) |
| 3.2 | 2026-11-24 | FNC-168 (decisión del dueño: las cuentas viven en LDAP y entran por Authelia): las altas son `auth_source=sso`; `ldap` queda como origen heredado y la migración 0019 convierte las existentes. **Incompatible** para quien filtre por `ldap`: el cliente usa `lib/origen-cuenta.ts` (FNC-169) |
| 3.3 | 2026-11-24 | FNC-185 (dueño): efecto en accesos de asignar/quitar áreas y de degradar el rol: nivel `admin` al ser admin, regreso a `usuario` (conservado) al dejar de serlo. Sin cambios de forma |
| 3.4 | 2026-11-25 | FNC-206 (**aditivo**): `503 sin_permiso_en_directorio` al cambiar contraseña o rol cuando LDAP rechaza por permisos (antes `directorio_no_disponible` o `grupo_no_actualizado`). Sin cambios de forma |
| 3.5 | 2026-11-28 | FNC-220 (dueño): `409 area_sin_admin` al crear un área activa o activar una inactiva sin admin de área. Cambia el alta del superadmin: sin `status` equivale a `Activo` y ahora falla sin admin (la web debe enviar `Inactivo`). Importación masiva de áreas: nacen `Inactivo` |