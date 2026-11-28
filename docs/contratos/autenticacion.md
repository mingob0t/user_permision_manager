# Contrato — Autenticación (OIDC con Authelia y ruta de emergencia)

| Campo | Valor |
|---|---|
| Versión | 1.1 (2026-11-27) |
| Proveedor | backend (FNC-141) |
| Consumidores | web (FNC-142) |
| Decisión | [ADR-009](../decisiones/ADR-009-inicio-de-sesion-oidc-con-authelia.md) (3B, 4B, 5A, 6A aprobadas el 2026-11-18) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Prefijo `/api/v1/auth`. La sesión es la cookie de Flask-Login; **ningún token de Authelia llega al navegador ni a una URL del portal**.

## Endpoints

| Método y ruta | Acceso | Respuestas |
|---|---|---|
| `GET /auth/context` | público | `200` |
| `GET /auth/oidc/login` | público | `302` a Authelia; `302` a `/login?error=oidc_no_disponible` si OIDC no está configurado |
| `GET /auth/oidc/callback` | público | `302` a `/` (éxito) o a `/login?error=<codigo>` |
| `POST /auth/local` | público | `200`, `400`, `401`, `429` |
| `POST /auth/logout` | con sesión | `200`; sin sesión `401` |
| `POST /auth/sso` | retirado | `410 endpoint_retirado` |
| `POST /auth/login` | retirado | `410 endpoint_retirado` |

## `GET /auth/context`
| Campo | Tipo | Notas |
|---|---|---|
| `oidc_enabled` | bool | `OIDC_*` completas: la web muestra «Entrar con Authelia» |
| `authenticated` | bool | Hay sesión válida |
| `emergency_available` | bool | La ruta `/auth/local` existe (siempre `true`; no hay enlace visible, ADR-009 6A) |
| `local_login` | bool | `true` con `OIDC_HABILITADO=false` (FNC-158): `/login` pide usuario y contraseña y `/auth/local` acepta cualquier cuenta **local** activa; las de directorio u OIDC no entran |
| `authelia_url` | string o `null` | `AUTHELIA_URL` (alias `AUTHELIA_SSO_URL`) o el emisor OIDC |
| `app_name` / `app_title` | string | `APP_NAME` / `APP_TITLE` (por omisión `aduana` / `Aduana`) |
| `domain` | string | `DOMAIN`; vacío si no está |
| `support_email` | string | `SUPPORT_EMAIL` (por omisión el buzón de soporte del portal) |
| `motivos` | objeto | v1.1 (FNC-216): `{solicitud: oculto\|opcional\|obligatorio, rechazo: obligatorio\|opcional\|oculto}` desde `SOLICITUD_MOTIVO` / `RECHAZO_MOTIVO`; ver [solicitudes.md](solicitudes.md) |

Se retiran `sso_enabled`, `sso_user` y `ldap_available`.

## Flujo OIDC
1. El navegador navega (no `fetch`) a `GET /auth/oidc/login`.
2. El backend guarda `state`, `nonce` y `code_verifier` en la **sesión firmada** (cookie `HttpOnly`, nunca en una respuesta ni una URL del portal) y redirige a Authelia con `response_type=code`, `code_challenge_method=S256`, `state`, `nonce` y `scope=openid profile email`.
3. Authelia redirige a `GET /auth/oidc/callback?code=...&state=...`.
4. El backend valida `state`, canjea el `code` con el `code_verifier`, valida el ID token (firma por JWKS, `iss`, `aud`, `exp`, `nonce`) y lee `sub`, `email`, `name` (y `email_verified` si se publica).
5. Vincula o crea la cuenta (abajo), abre la sesión y responde `302 /`. Cualquier fallo: `302 /login?error=<codigo>`, sin detalle y auditado como `ACCESO FALLIDO`.

### Códigos de `?error=`
| Código | Cuándo |
|---|---|
| `oidc_no_disponible` | OIDC sin configurar o Authelia inalcanzable al iniciar |
| `acceso_denegado` | Authelia devolvió `error` (p. ej. la persona negó el acceso) |
| `autenticacion_fallida` | `state`, `nonce`, `code`, firma, `iss`, `aud` o `exp` inválidos |
| `identidad_incompleta` | El token no trae correo o `email_verified` es falso |
| `cuenta_no_disponible` | Cuenta local o desactivada, o el correo ya está vinculado a otra identidad (`sub`) |

### Cuenta
| Regla | Detalle |
|---|---|
| Enlace | Por `sub` (columna `users.oidc_sub`). Sin `sub` vinculado: por correo, con `motivo_de_bloqueo` (cuenta local o desactivada → rechazo auditado); al entrar se guarda el `sub` |
| Cuenta nueva | Rol `usuario`, `auth_source='sso'`, sin contraseña |
| Rol | Nunca sale del token ni de sus grupos (SEG-10); `groups` no se pide |
| Origen | Se conserva `auth_source='sso'` (ADR-009 5A) |

## `POST /auth/local` (cuenta de emergencia)
| Campo | Tipo | Notas |
|---|---|---|
| `email` | string | Obligatorio |
| `password` | string | Obligatorio |

| HTTP | Cuerpo | Cuándo |
|---|---|---|
| 200 | `{"status":"success","role":"administrador"}` | Cuenta de emergencia (o, solo con `APP_ENV=development`, cualquier cuenta local con la bandera de FNC-077) |
| 400 | `{"status":"error","message":"Indica usuario y contraseña."}` | Falta un campo |
| 401 | `{"status":"error","message":"Credenciales incorrectas."}` | Cualquier otro fallo (respuesta única, SEC-AUTH-09); el motivo va solo a la auditoría |
| 429 | `{"status":"error","message":"Demasiados intentos fallidos..."}` | Límite de intentos (FNC-014): por cuenta e IP; la cuenta de emergencia solo por IP (FNC-154) |

## `POST /auth/logout`
- Cuerpo vacío. `200 {"status":"success","redirect": "<url>" | null}`.
- Borra la sesión del portal. `redirect` sale de la configuración (`OIDC_LOGOUT_URL`, o `end_session_endpoint` del descubrimiento), nunca de `Host`; `null` si no hay ninguna.
- La web navega a `redirect` si no es `null`; si es `null`, a `/login`.

## Retirados
- `POST /auth/sso` y `POST /auth/login` (cualquier `method`) responden `410 {"status":"error","message":"...","code":"endpoint_retirado","use":"GET /auth/oidc/login"}`; `/auth/login` indica `use: "POST /auth/local"` para la cuenta de emergencia. Las cabeceras `Remote-*` ya no autentican.

## Datos simulados
```json
{ "oidc_enabled": true, "authenticated": false, "emergency_available": true }
```

## Refresco
- Sin polling.

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-11-18 | Versión inicial (FNC-140) |
