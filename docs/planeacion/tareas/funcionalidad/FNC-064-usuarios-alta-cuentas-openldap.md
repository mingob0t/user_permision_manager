# FNC-064 — Usuarios: crear cuentas en OpenLDAP desde el portal

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-064-alta-cuentas-ldap` (worktree `pokemon-wt-064`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (creación de identidades) |

## Contexto
- `POST /users` (`crud.py:255`) crea la cuenta solo en la BD local y, si no llega contraseña, asigna una fija (SEG-02)
- F-USR-02 pide crearlas en OpenLDAP, fuente de verdad
- Requerimientos: F-USR-02, F-USR-01, RF-02

## Objetivo
- Que el superadmin (y el admin si P2 lo permite) cree la cuenta en OpenLDAP con los atributos de ADR-004 y el usuario local enlazado (`auth_source=ldap`), sin contraseña por defecto, con el flujo de contraseña inicial de P8

## Alcance
- **Incluye:**
  - `POST /users/directory` (o el cambio de `POST /users` que fije el contrato)
  - Validación de identificador único en el directorio y en la BD
  - Sin contraseña por defecto; contraseña inicial según P8
  - Auditoría del alta
- **No incluye:**
  - Borrar o desactivar cuentas en LDAP (fuera de la v1: baja masiva)
  - Elevar a admin (FNC-044)
  - Pantalla (DIS-019)

## Hallazgos de seguridad que absorbe
- **FNC-003** parcial: SEG-02 (contraseña fija en `create_user`). El admin semilla `admin/admin123` (SEG-03) queda en FNC-003.

## Archivos previstos
- `app/modules/users/directory_accounts.py` (nuevo: validación, permisos, alta y fallos)
- `app/modules/users/api.py` (ruta `POST /users/directory`)
- `app/modules/directory/ldap_client.py`: `buscar_por_correo` (FNC-049) registra el fallo sin detalle (firma igual)
- `docs/contratos/usuarios-directorio.md` (correo ≤ 120, ASCII; Historial)
- `tests/users/test_alta_directorio.py`, `tests/matriz_proteccion.py`
- `app/modules/api/crud.py`: sin cambios (la contraseña por defecto ya la retiró FNC-077)

## Reutilización
- `EscritorDirectorio.create_user`, `DatosCuenta`, `PATRON_CORREO` (FNC-041)
- `validar_area_ids`, `correos_registrados`, `usuario_gestionado`, `RESERVED_NAMES`, `normalizar_correo`
- `ClienteDirectorio.buscar_por_correo`, `PersonaAmbigua` (FNC-049); `_CONTROL` de `app/utils/naming.py`
- `sanitize_display_name` (nombre visible), `error_response`/`validation_error`/`json_object`/`is_id_list`

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Tema | Decisión |
|---|---|---|
| D1 | Fallo parcial (directorio creado, `commit` no) | Rollback, log, auditoría `warning` con el DN (entrada para revisión) y `500 error_interno`. Sin borrado en LDAP (v1). Reintento → `409 uid_duplicado` (manda el contrato); la persona se registra como `usuario` sin áreas en su primer login de directorio/SSO (enlace por `mail`). FNC-079 cubre registrar cuentas que ya existen |
| D2 | Directorio sin configurar | `503 directorio_no_disponible` (el contrato no tiene `409` para este endpoint) |
| D3 | Largo del correo | ≤ 120 (columna `users.email` `String(120)`) y solo ASCII; contrato corregido (Historial, cambio restrictivo en v1) |
| D4 | Correo en el directorio | `buscar_por_correo` justo antes de escribir; encontrado o ambiguo (`PersonaAmbigua`) → `409 correo_duplicado` |
| D9 | Concurrencia (seguridad Media) | Reserva del correo con la fila de `users` sin confirmar (`users.email` UNIQUE) antes de buscar y escribir en el directorio: dos altas con el mismo correo se serializan y solo una gana (`IntegrityError` → `409`); la transacción queda abierta durante la escritura LDAP (acotada por `LDAP_TIMEOUT`). Dos uid iguales los resuelve el DN único en LDAP (`YA_ESTABA` → `409`) |
| D5 | "uid único en la BD" | La BD no guarda uid: choca con `RESERVED_NAMES` (`admin`) o con una cuenta heredada cuyo `email` es ese identificador |
| D6 | Admin con área inexistente | `404`, igual que la ajena (no revela qué áreas existen); superadmin → `422` |
| D7 | Nombres | 1–100 sin caracteres de control (`_CONTROL` de `naming.py`); el nombre visible pasa por `sanitize_display_name` |
| D8 | Auditoría | `cuenta_directorio_creada` con el actor de la sesión; éxito en la misma transacción (SEC-AUD-06), detalle con los sistemas (`directorio` y `portal`); `409` y fallo parcial `warning`; fallos del directorio `error` |

## Impacto en elementos compartidos
Salida real de `python3 ~/.claude/agentes/herramientas/impacto.py` (tras el merge de develop y las correcciones):

> **⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 14 elemento(s) usados en otras secciones: app, app/modules, frontend/src, frontend/tests, migrations/versions, scratch, tests, tests/areas, tests/directory, tests/notifications, tests/platforms, tests/provisioning, tests/users. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/users/directory` | endpoint | `app/modules/users/api.py` | `frontend/src/lib/access/users.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☑ consumidor del contrato (FNC-069) |
| `_auditar` | función | `app/modules/users/directory_accounts.py` | `app/modules/areas/api.py`, `app/modules/provisioning/ejecucion.py`, `app/modules/users/areas_administradas.py` | app/modules | ☑ homónimo (privada de cada módulo) |
| `_crear` | función | `tests/users/test_alta_directorio.py` | `tests/directory/test_tls.py`, `tests/test_arranque.py` | tests, tests/directory | ☑ homónimo |
| `_cuenta` | función | `tests/users/test_alta_directorio.py` | `tests/users/test_contrasenas_locales.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/users | ☑ homónimo |
| `_cuerpo` | función | `tests/users/test_alta_directorio.py` | `tests/notifications/test_access_notifications.py`, `tests/test_notificaciones.py` | tests, tests/notifications | ☑ homónimo |
| `_entrada` | función | `tests/users/test_alta_directorio.py` | `app/modules/areas/api.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☑ homónimo |
| `_error` | función | `tests/users/test_alta_directorio.py` | `app/modules/api/admin.py`, `app/modules/api/crud.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☑ homónimo |
| `_eventos` | función | `tests/users/test_alta_directorio.py` | `tests/areas/test_alta_y_baja_por_admin.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/areas, tests/users | ☑ homónimo |
| `_falla` | función | `tests/users/test_alta_directorio.py` | `tests/areas/test_alta_y_baja_por_admin.py`, `tests/conftest.py`, `tests/provisioning/test_ejecucion.py`, `tests/users/test_roles_y_areas_administradas.py` | tests, tests/areas, tests/provisioning, tests/users | ☑ homónimo |
| `_texto` | función | `app/modules/users/directory_accounts.py` | `app/modules/areas/validacion.py`, `app/modules/platforms/validacion.py` | app/modules | ☑ homónimo |
| `buscar_por_correo` | función | `app/modules/directory/ldap_client.py` | `app/modules/provisioning/ldap_provider.py`, `tests/provisioning/test_ldap_provider.py` | app/modules, tests/provisioning | ☑ real: solo cambia el log del fallo (sin detalle); firma y resultado iguales; `tests/provisioning/` en verde |
| `campos_no_permitidos` | función | `app/modules/users/directory_accounts.py` | `app/modules/api/crud.py`, `app/modules/areas/api.py`, `app/modules/areas/validacion.py`, `app/modules/users/roles.py` | app/modules | ☑ homónimo (cada módulo tiene la suya; unificar en FNC-082) |
| `directorio` | función | `tests/users/test_alta_directorio.py` | `app/__init__.py`, `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/api/crud.py`, `app/modules/auth/acceso_local.py`, `app/modules/auth/models.py`, `app/modules/auth/routes.py`, `app/modules/auth/services.py` (+43) | app, app/modules, frontend/src, frontend/tests, migrations/versions, scratch, tests, tests/directory, tests/platforms, tests/provisioning, tests/users | ☑ homónimo (fixture local; la palabra "directorio") |
| `escena` | función | `tests/users/test_alta_directorio.py` | `tests/areas/test_alta_y_baja_por_admin.py`, `tests/users/test_contrasenas_locales.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/areas, tests/users | ☑ homónimo (fixture local) |

- Reales: el endpoint nuevo (cliente web de FNC-069, ya alineado) y `buscar_por_correo` (solo el log).
- Impacto para DIS-019: mostrar `fields` del `422` (incluido correo no ASCII), `404` (área ajena), `409 uid_duplicado`/`correo_duplicado`, `503` y `500`; el admin elige al menos un área; sin campos de contraseña ni de rol.

## Criterios de aceptación
- [x] Alta crea la entrada en el directorio (doble de LDAP) y el usuario local (prueba)
- [x] Sin contraseña no se asigna ninguna por defecto (prueba de regresión SEG-02)
- [x] Identificador duplicado responde 409 (prueba)
- [x] Admin de área según P2 (prueba)
- [x] Criterios comunes backend (FNC-037)

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest -q tests/users/test_alta_directorio.py` sin la ruta (stash de `users/api.py`) | `61 failed` (regresiones fallan primero) |
| `venv/bin/python -m pytest -q tests/users/test_alta_directorio.py` | `61 passed` |
| `venv/bin/python -m pytest -q tests/test_guardia_rutas.py tests/test_proteccion_por_rol.py` | `220 passed` |
| `venv/bin/python -m pytest -q` (completo) | `1035 passed, 15 xfailed` en 487 s; código de salida 0 (línea base develop: 969 passed) |
| Correcciones de revisión: 9 regresiones nuevas antes del cambio (tras merge de develop) | `9 failed, 61 passed` |
| Log de `buscar_por_correo` con el detalle anterior (stash de `ldap_client.py`) | `1 failed` |
| `venv/bin/python -m pytest -q tests/users/test_alta_directorio.py` con las correcciones | `68 passed` (2 pruebas de fallo parcial reemplazadas por la del DN) |
| `venv/bin/python -m pytest -q` (completo, tras correcciones) | `1143 passed, 15 xfailed` en 358 s; código de salida 0 |

- No verificado: OpenLDAP real (solo `MOCK_SYNC`, que no compara valores escapados), ACL de la cuenta de servicio (SEC-LDAP-03), Postgres (D3; la serialización real de D9 por bloqueo de fila: en SQLite la segunda alta recibe `500` por base bloqueada, en Postgres `409`), Authelia (contraseña inicial).

## Revisiones
| Revisor | Veredicto | Atención |
|---|---|---|
| auditor-seguridad | Aprobado (1 Media, 2 Baja) | Media: concurrencia de duplicados → D9; Baja: correo ASCII y auditoría de los `409` → corregidas |
| revisor | Requiere cambios | `buscar_por_correo` en lugar de `busqueda_correo.py`, contrato D3, impacto completo, riesgos, `_CONTROL`, FNC-082 → corregidos |

## Commits / PR
| Commit | Descripción |
|---|---|
| `3299f5b` | `[FNC-064] Alta de cuentas en OpenLDAP desde el portal` — local, sin push ni PR |

## Impacto cruzado
- Genera → DIS-019
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-041, FNC-044, FNC-038, Respuestas a P2 y P8
- Contrato → docs/contratos/usuarios-directorio.md (v1, sin cambios)
- Coordina con → FNC-079 (no implementada aquí; ver D1)

## Riesgos y reversión
- Fallo a mitad (LDAP creado, `commit` no): no es idempotente; el reintento da `409`. La entrada queda auditada (`warning`, con su DN) para revisión y la persona se registra en su primer login (D1).
- Concurrencia: reserva por `users.email` UNIQUE (D9).
- Reversión: revertir la rama; las cuentas creadas quedan en el directorio.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador). Implementada: `POST /users/directory`, validación, 404/409/422/503/500, auditoría, matriz. Decisiones D1–D8. En revisión; sin revisores (por instrucción) |
| 2026-10-19 | Revisión: auditor-seguridad Aprobado (1 Media, 2 Baja), revisor Requiere cambios. Merge de develop; corregidos D9 (reserva por correo), ASCII, 409 auditados, `buscar_por_correo`, contrato, impacto, riesgos, `_CONTROL`; FNC-082 Propuesta. Sigue En revisión |
- Cierre (2026-10-19): revisor y auditor-seguridad atendidos; merge local a `develop` (modo autónomo). Concurrencia verificada solo en SQLite; MySQL pendiente de la PoC.
