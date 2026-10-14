# Contrato — Alta de cuentas en OpenLDAP

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-14) |
| Proveedor | backend (FNC-064; cliente FNC-040, FNC-041) |
| Consumidores | web (FNC-069; pantalla DIS-019) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). P2: superadmin y admins (para sus áreas). `POST /users` (cuenta local) no cambia aquí; el rol: [areas-y-roles.md](areas-y-roles.md).

## Endpoints

| Método y ruta | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| `POST /users/directory` | 403 | 201 | 404 (`area_ids` ajenas) | 201 |

## `POST /users/directory`
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `uid` | string | Sí | 3–64; `^[a-z][a-z0-9._-]*$`; único en el directorio y en la BD |
| `email` | string | Sí | Correo válido, ≤ 254; único en la BD |
| `given_name` | string | Sí | 1–100 |
| `surname` | string | Sí | 1–100 |
| `area_ids` | int[] | Sí para admin | 1–50; todas en alcance del actor (superadmin: cualquiera, puede ir vacío) |

- Rol siempre `usuario`; `auth_source = "ldap"`; `password_hash` NULL (SEC-AUTH-04). Elevar: solo superadmin, aparte.
- Entrada en la OU de personas de la convención `LDAP_*` (ADR-004); DN escapado (SEC-LDAP-06).
- Contraseña (P8, 2026-10-14): el portal no maneja contraseñas de cuentas LDAP; la contraseña la maneja Authelia. `password` → `400 campo_no_permitido`.
- Escritura síncrona al directorio; si falla, no se crea nada en la BD.
- Respuesta `201`: `{"status": "success", "user": ManagedUser}`. Auditoría `cuenta_directorio_creada` (sin datos sensibles).

```json
{ "uid": "ana.ruiz", "email": "ana@ejemplo.local", "given_name": "Ana", "surname": "Ruiz", "area_ids": [3] }
```

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 409 | `uid_duplicado` | Ese identificador ya existe en el directorio o en el portal. |
| 409 | `correo_duplicado` | El correo ya está registrado. |
| 422 | `validacion` | `fields.uid`: "Usa minúsculas, números, punto, guion o guion bajo." |
| 503 | `directorio_no_disponible` | No se pudo crear la cuenta en el directorio; intenta más tarde. |

## Refresco
- Sin polling; recarga de la lista de usuarios tras el alta.

## Datos simulados
```json
{ "status": "success", "user": { "id": 31, "email": "ana@ejemplo.local", "name": "Ana Ruiz", "role": "usuario",
  "is_active": true, "auth_source": "ldap", "areas": [ { "id": 3, "name": "Finanzas" } ], "managed_areas": [],
  "last_login_at": null } }
```

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038) |
