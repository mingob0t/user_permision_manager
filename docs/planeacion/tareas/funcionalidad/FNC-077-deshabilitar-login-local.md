# FNC-077 — Deshabilitar el login local (solo Authelia/directorio), salvo acceso de emergencia del superadmin

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auth |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-15 |
| **Inicio** | 2026-10-19 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-077-deshabilitar-login-local` (worktree `pokemon-wt-077`) |
| **Commits / PR** | Ver bitácora (commit `[FNC-077]` local; sin PR) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (pendiente: no se lanzó por instrucción del orquestador) |

## Contexto
- Decisión del dueño (2026-10-15, revisión de FNC-044): la autenticación local se deshabilita; todo va por Authelia.
- Hoy `POST /api/v1/auth/login` acepta `method: local` y `POST/PUT /users` manejan contraseñas locales.
- Se conserva solo el acceso de emergencia del superadmin (ver SEC-AUTH y pregunta 5 de `docs/seguridad/LINEAMIENTOS.md` §12).
- Requisito del dueño: probar en local sin Authelia entrando como `admin`.

## Criterios de aceptación
- [x] `method: local` rechazado para toda cuenta salvo la de emergencia del superadmin
- [x] Alta y edición de cuentas sin contraseña local (revisar `POST/PUT /users`, FNC-044)
- [ ] Contrato y pantalla de login actualizados por tarea vinculada (contrato `areas-y-roles.md` v2 hecho; pantallas: ver impacto en el cliente)
- [x] Prueba de regresión que primero falla

## Implementación
| Archivo | Cambio |
|---|---|
| `app/modules/auth/acceso_local.py` (nuevo) | Política: `es_cuenta_de_emergencia`, `login_local_de_todas_habilitado`, `motivo_rechazo_login_local`, `contrasena_local_permitida` |
| `app/modules/api/auth.py` | `POST /login` local: tras validar la clave, rechaza (401 genérico, motivo auditado) cuentas no locales y no de emergencia |
| `app/modules/api/crud.py` | `POST /users`: sin `nexus123`; `password` → `400 campo_no_permitido` salvo bandera. `PUT /users/<id>`: `password` solo cuenta de emergencia o bandera |
| `docs/contratos/areas-y-roles.md` | v2: regla de `password` |

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Cuenta de emergencia = rol `administrador` + `auth_source` `local` (vacío cuenta como local, igual que `crud.py`) | Sin campo nuevo ni migración; el seed `admin` cumple |
| 2 | Bandera `LOGIN_LOCAL_TODAS_LAS_CUENTAS` solo actúa con `APP_ENV=development`; vacía o cualquier otro valor = ignorada | No existía variable de entorno de la app; `FLASK_ENV` está obsoleta y `.env.example` la trae en `development` (copiarla a un servidor la activaría). Falla cerrada |
| 3 | `password` en `POST /users` → `400 campo_no_permitido` (vacía = ausente); la cuenta nace con `password_hash` nulo | SEG-02; el cliente actual manda `password: ''`, que sigue funcionando |
| 4 | `password` en `PUT /users/<id>`: solo la cuenta de emergencia (de hecho solo el superadmin la alcanza) | SEC-AUTH-12; reemplaza la regla del dueño del 2026-10-15 (admin de área cambiaba claves) por la del login local deshabilitado |
| 5 | Con la bandera efectiva se aceptan contraseñas en `POST/PUT /users` para cuentas locales del alcance | Sin eso la PoC no puede crear cuentas locales que entren |
| 6 | Seed `admin/admin123` sin cambios | Es de FNC-003; el dueño sigue entrando como `admin` (ver `docs/operacion/ENTORNOS.md`) |
| 7 | Contrato `areas-y-roles.md` a v2 | Cambia un permiso (regla del README de contratos) |

## Impacto en el cliente (sin tocar el frontend)
- Pantalla de login (`login-form.tsx`): el acceso local solo sirve a la cuenta de emergencia; conviene presentarlo como "acceso de emergencia" → DIS-018/DIS-019 o la tarea de login que corresponda.
- Alta y edición de usuarios (`users-list.tsx`): quitar el campo de contraseña (en staging/prod da `400 campo_no_permitido` si se llena). Alta útil de cuentas del directorio: FNC-079.
- Una cuenta creada por `POST /users` queda local y sin clave: no entra por login local ni por SSO (`motivo_de_bloqueo`) hasta FNC-079.
- `GET /auth/context` no cambia (no informa si el login local está restringido): si la pantalla lo necesita, se pide por solicitud.

## Verificación
| Comando | Resultado real |
|---|---|
| Regresiones con `auth.py` y `crud.py` de `develop` (`pytest tests/test_login_local.py tests/users/test_contrasenas_locales.py`) | 19 failed, 10 passed, 1 xfailed (fallan las nuevas) |
| Mismas pruebas con el cambio | pasan (incluidas en la suite) |
| `venv/bin/pytest -q -p no:cacheprovider` (suite completa) | 878 passed, 15 xfailed en 458 s; código de salida 0 (base `develop`: 854 passed, 17 xfailed; −2 xfail de SEG-02) |
- `xfail` retirado: `test_cuenta_no_local_no_entra_por_login_local` (SEG-02), ahora con bandera activa y roles `usuario`/`administrador`.
- `tests/matriz_proteccion.py`: la cuenta del caso `POST /auth/login` pasa a ser la de emergencia; `POST /users` sin contraseña.
- No verificado: arranque real con `.env` local y frontend (no se ejecutó la app); auditor-seguridad y revisor (no lanzados por instrucción).

## Impacto en elementos compartidos
Salida real de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `create_user` | función | `app/modules/api/crud.py` | `app/modules/auth/routes.py`, `app/modules/directory/writer.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☐ |
| `datos` | función | `tests/test_auditoria_crud.py` | `app/__init__.py`, `app/authz.py`, `app/modules/api/admin.py`, … (+39) | app, frontend, tests, utils, … | ☐ |
| `hay_auditoria` | función | `tests/peticiones_auth.py` | `tests/test_login_directorio.py`, `tests/test_sso.py` | tests | ☐ |
| `login` | función | `app/modules/api/auth.py` | `app/modules/auth/routes.py`, `frontend/src/components/login-form.tsx`, … (+9) | app, frontend/src, tests | ☐ |
| `update_user` | función | `app/modules/api/crud.py` | `app/modules/auth/routes.py` | app/modules | ☐ |

- Homónimos (sin impacto real): `create_user`/`update_user`/`login` de `auth/routes.py` (rutas heredadas que redirigen o dan 410), `ClienteEscritura.create_user` de `directory/writer.py`; `datos` es un nombre de variable local; `hay_auditoria` no cambió (solo se agregó `activar_login_local_de_todas` en el mismo archivo).
- Impacto real: `POST /api/v1/auth/login` (consumido por `login-form.tsx` vía `api.login`) y `POST/PUT /api/v1/users` (consumidos por `users-list.tsx`): ver "Impacto en el cliente".

## Impacto cruzado
- Origen ← FNC-044 (decisión del dueño)
- Relacionadas → FNC-003 (cierra SEG-02; SEG-03 sigue allí), FNC-042, FNC-078, FNC-079, DIS-018, DIS-019

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-15 | Creada como Propuesta (decisión del dueño en la revisión de FNC-044) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador). Implementada en `pokemon-wt-077`; regresiones fallan sin el cambio; contrato v2; En revisión |
