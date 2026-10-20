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
| `email` | string | Sí | Correo válido, solo ASCII, ≤ 120 (columna `users.email` `String(120)`); único en la BD y en el directorio |
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

## Configuración del directorio (FNC-043; consumidor DIS-023)
Solo superadmin (resto: 401/403). Fuente única: variables `LDAP_*` (ADR-004); sin edición desde la interfaz.

| Método y ruta | Respuesta |
|---|---|
| `GET /auth-config` | `200` `{active, source: "env", editable: false, config, origins, variables, error}` |
| `PUT /auth-config` | `{}` → `200 {"status": "success", "config": <igual que GET>}`; cualquier campo → `400 campo_no_permitido` |
| `POST /auth-config/test` | Sin cuerpo. `200 {"status": "success", "message"}`; campos → `400 campo_no_permitido`; inactivo → `409 directorio_no_configurado`; fallo → `503 directorio_no_disponible` |
| `GET /directory/search?q=` | `q` 2–64 → `200 {count, users: [{name, email, account, exists}]}` (máx. 50); fuera de rango → `400 parametro_invalido`; `409`/`503` como la prueba |

- `config` (o `null` si inactivo o inválido): `url`, `host`, `port`, `tls` (`ldaps`/`starttls`), `ca_cert` (`custom`/`system`), `bind_dn`, `users_base_dn`, `groups_base_dn`, `user_attr`, `group_object_class`, `group_member_attr`, `timeout_seconds`, `user_object_classes[]`, `placeholder_member`.
- `origins`: por campo, `env` o `default`; `variables`: campo → nombre de la variable `LDAP_*`.
- `error`: `null` o `configuracion_invalida` (el detalle va al log).
- Nunca incluye la contraseña de bind ni la ruta de la CA (SEC-LDAP-11).

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038) |
| 1 | 2026-10-18 | Sección "Configuración del directorio" agregada (FNC-043): documenta endpoints que no tenían contrato. **Aditivo** para el contrato (sigue v1): no cambia ningún endpoint ya contratado. Sí cambia la forma heredada de NEXUS que lee `settings-panel.tsx`; la adapta DIS-023. Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| 1 | 2026-10-19 | `email` ≤ 120 en lugar de ≤ 254 (motivo: `users.email` es `String(120)`; más largo daría 500 en Postgres), solo ASCII y único también en el directorio (FNC-064, revisión de seguridad). **Restrictivo** (un valor antes válido ahora da `422`/`409`); sigue v1 porque ningún cliente lo usaba en producción (FNC-069 solo en simulado). Decisión del orquestador (pendiente de validar en la prueba de concepto) |
