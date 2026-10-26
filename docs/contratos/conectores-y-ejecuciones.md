# Contrato — Conectores y ejecuciones de aprovisionamiento

| Campo | Valor |
|---|---|
| Versión | 1.3 (2026-10-21) |
| Proveedor | backend (FNC-051, FNC-052, FNC-061, FNC-062; base FNC-049, FNC-050) |
| Consumidores | web (FNC-069; pantallas DIS-022, DIS-018) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Cola: Redis + RQ (ADR-003). P9: los tipos `api` (FNC-051) y `ssh` (FNC-052) ya tienen esquema de `params` (§ siguientes); `bd` (FNC-053) espera y agregará el suyo como versión aditiva.

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

## `params` del tipo `api` (FNC-051)
Esquema cerrado: una clave desconocida → `422` con `fields.params.<campo>`.
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `base_path` | string | No | Empieza con `/`; letras, dígitos y `. _ ~ / : -`; sin `..`; sin marcas |
| `auth` | object | Sí | `esquema`: `bearer` (`Authorization: Bearer`), `basic` (`Authorization: Basic`, la credencial debe traer usuario) o `cabecera` (el secreto en la cabecera `nombre`; no puede ser `Host`, `Authorization`, `Content-Type`, etc.) |
| `otorgar`, `revocar` | object | Sí | `metodo` (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`), `ruta` (misma regla que `base_path`, admite marcas), `consulta` (≤ 5 campos de texto con marcas), `cuerpo` (objeto JSON; solo con `POST`/`PUT`/`PATCH`; marcas solo en valores de texto; ≤ 4 niveles), `sin_cambios` (lista de estados 400–499 que cuentan como «ya estaba así») |
| `consultar` | object | No | Igual que `otorgar`; sin él, consultar da `consulta_no_disponible` (permanente) |

- Marcas permitidas (datos del servidor, nunca texto del usuario): `{correo}`, `{nivel}`, `{plataforma}`. Cualquier otra, o una llave suelta → `422`.
- Ejemplo: `{"base_path": "/api/v1", "auth": {"esquema": "bearer"}, "otorgar": {"metodo": "POST", "ruta": "/usuarios", "cuerpo": {"email": "{correo}", "rol": "{nivel}"}}, "revocar": {"metodo": "DELETE", "ruta": "/usuarios/{correo}"}, "consultar": {"metodo": "GET", "ruta": "/usuarios", "consulta": {"email": "{correo}"}}}`.
- Salida: solo HTTPS; el host resuelve a IP públicas y se conecta a la IP validada; sin redirecciones; TLS validado (CA del sistema o `CONNECTOR_HTTP_CA_FILE`).
- Estados: 2xx éxito; `sin_cambios` (por defecto `[404, 410]` al revocar); 408, 425, 429, 500, 502, 503 y 504 transitorios; 3xx y el resto, permanentes. `consultar`: 2xx presente, 404 ausente.
- Motivos nuevos en la bitácora (mensaje genérico; detalle solo `HTTP <estado>`): `configuracion_invalida`, `valor_no_valido` (cuenta o nivel vacíos, `.`/`..` o con segmento así; `{correo}` sin `@`), `destino_no_permitido`, `tls_no_valido`, `http_rechazado`, `http_transitorio`, `red_no_disponible`, `redireccion_no_permitida`.

## `params` del tipo `ssh` (FNC-052)
Esquema cerrado: una clave desconocida → `422` con `fields.params.<campo>`.
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `huellas` | lista de texto | Sí, salvo que el despliegue tenga `CONNECTOR_SSH_KNOWN_HOSTS_FILE` | 1–5 huellas `SHA256:<base64>` (`ssh-keygen -lf`) de la llave del host; varias para rotarla. Sin coincidencia → permanente `ssh_huella_no_coincide` (nunca se acepta una llave nueva) |
| `auth` | object | No | `metodo`: `llave` (por defecto) o `contrasena` (solo si la plataforma no admite llave). Usuario y secreto salen de la credencial del gestor (llave privada sin frase de paso o contraseña) |
| `otorgar`, `revocar` | object | Sí | `comando`: lista de 1–8 textos de letras, dígitos y `. _ / = : + -` (≤ 100), el primero una ruta absoluta sin `..`; `sin_cambios` (códigos de salida 1–255 que cuentan como «ya estaba así»); `transitorios` (códigos 1–255 que se reintentan; por defecto `[75]`). Un código no puede estar en dos listas |
| `consultar` | object | No | `comando` y `transitorios` como arriba; `ausente` (códigos que significan «sin acceso»). Sin él, consultar da `consulta_no_disponible` |

- Sin marcas: el comando es **fijo** y no lleva datos de la solicitud. Los datos viajan por la entrada estándar como **una línea JSON** `{"operacion": "otorgar", "correo": "...", "nivel": "...", "plataforma": "7"}` (ASCII, escapada con `json.dumps`).
- Se recomienda en el servidor un comando forzado (`command="..."`, `restrict` en `authorized_keys`) que lea esa línea; el comando enviado queda entonces como información.
- Valores del servidor no vacíos, sin caracteres de control, sin `.`/`..` ni segmentos así, y `{correo}` con `@`; si no → permanente `valor_no_valido` sin conectar.
- Ejemplo: `{"huellas": ["SHA256:..."], "otorgar": {"comando": ["/usr/local/bin/acceso", "otorgar"], "sin_cambios": [3]}, "revocar": {"comando": ["/usr/local/bin/acceso", "revocar"], "sin_cambios": [4]}, "consultar": {"comando": ["/usr/local/bin/acceso", "consultar"], "ausente": [1]}}`.
- Salida: el host resuelve a IP públicas y se conecta a la IP validada; sin agente, túneles, `ProxyJump` ni `ProxyCommand`; sin `ssh-rsa` (SHA-1) ni `ssh-dss`; la llave del host se verifica antes de enviar la credencial.
- Códigos: `0` éxito (`presente` al consultar); `sin_cambios`/`ausente`; `transitorios` y cierre sin código → transitorios; el resto, permanentes. La salida remota nunca se guarda: el detalle es solo `salida <n>`.
- Motivos nuevos en la bitácora (mensaje genérico): `ssh_huella_no_coincide`, `ssh_autenticacion_rechazada`, `ssh_comando_rechazado`, `ssh_comando_transitorio`, `ssh_salida_excesiva`; además se reutilizan `configuracion_invalida`, `valor_no_valido`, `destino_no_permitido`, `credencial_no_encontrada`, `red_no_disponible` y `tiempo_agotado`.

## `DELETE /platforms/<id>/connector`
- `409 plataforma_con_accesos` si hay accesos vigentes. Respuesta `{"status": "success"}`. Auditoría `conector_eliminado`.

## `POST /platforms/<id>/connector/test`
- Cuerpo JSON `{}` (`Content-Type: application/json`, convención de escrituras; sin JSON → `415`; cualquier campo → `400 campo_no_permitido`). Ejecuta `consultar` sin cambios. Respuesta `200`:
```json
{ "status": "success", "result": "ok", "message": "Conexión correcta." }
```
- Fallo: `200` con `"result": "error"` y mensaje genérico ("No se pudo conectar con la plataforma."); el detalle solo al log. Auditoría `conector_probado`.
- Actualiza `credential_status`: `ok` si la prueba tiene éxito; `no_encontrada` si la referencia no existe en el gestor; cualquier otro fallo no lo cambia.

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
- Sin datos: cuerpo JSON `{}` (`Content-Type: application/json`, convención de escrituras; sin JSON → `415`); cualquier campo → `400 campo_no_permitido`. Solo desde `fallido` → `pendiente`; el acceso vuelve a `en_proceso` o `revocando`.
- Un segundo reintento simultáneo, o un otorgar con una revocación posterior de su terna o con el acceso ya no fallido → `409 estado_invalido`.
- Respuesta: `{"status": "success", "job": Job}`. Auditoría `ejecucion_reintentada`.

## Aviso de fallo (P10, 2026-10-14)
- Al agotar reintentos: correo `aprovisionamiento_fallido` a los admins del área y al superadmin (respeta `pref_email_notifications`: respuesta del dueño 2026-10-15); auditoría `acceso_fallido` o `revocacion_fallida`.

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 409 | `plataforma_sin_conector` | La plataforma no usa conector. |
| 409 | `plataforma_con_accesos` | Hay accesos vigentes con este conector. |
| 409 | `conector_concurrente` | Otra petición configuró este conector a la vez; vuelve a intentarlo. (`PUT` que crea; la restricción única de la plataforma) |
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
| 1 | 2026-10-20 | Aclaración (FNC-062): reintento con cuerpo `{}` y casos de `409`; `from`/`to` sin zona en la hora local del proceso, como la auditoría |
| 1 | 2026-10-20 | Aclaración (FNC-061): `DELETE` y `POST .../test` con cuerpo `{}` (convención de escrituras; sin JSON → `415`; cualquier campo → `400 campo_no_permitido`); `PUT` con campo fuera de la lista → `400 campo_no_permitido`; plataforma o configuración inexistente → `404`; cambiar `type` con accesos vigentes → `409 plataforma_con_accesos`; `test` deja `credential_status` en `ok` o `no_encontrada` |
| 1.1 | 2026-10-21 | Aclaración (FNC-061, auditor-seguridad): `POST .../test` exige cuerpo `{}` (sin Content-Type JSON → `415`) y actualiza `credential_status`; error aditivo `409 conector_concurrente` en el `PUT` que crea |
| 1.2 | 2026-10-21 | Aditivo (FNC-051): esquema de `params` del tipo `api` (`422 fields.params.<campo>`) y 8 motivos nuevos en la bitácora de ejecuciones (incluye `valor_no_valido`, auditoría) |
| 1.3 | 2026-10-21 | Aditivo (FNC-052): esquema de `params` del tipo `ssh` (`422 fields.params.<campo>`) y 5 motivos nuevos en la bitácora de ejecuciones |
