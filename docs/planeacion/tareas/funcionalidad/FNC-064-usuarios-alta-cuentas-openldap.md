# FNC-064 — Usuarios: crear cuentas en OpenLDAP desde el portal

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
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
- `app/modules/directory/busqueda_correo.py` (nuevo: `mail` en el directorio; `ldap_client.py` sin tocar)
- `tests/users/test_alta_directorio.py`, `tests/matriz_proteccion.py`
- `app/modules/api/crud.py`: sin cambios (la contraseña por defecto ya la retiró FNC-077)

## Reutilización
- `EscritorDirectorio.create_user`, `DatosCuenta`, `PATRON_CORREO` (FNC-041)
- `validar_area_ids`, `correos_registrados`, `usuario_gestionado`, `RESERVED_NAMES`, `normalizar_correo`
- `sanitize_display_name` (nombre visible), `error_response`/`validation_error`/`json_object`/`is_id_list`

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Tema | Decisión |
|---|---|---|
| D1 | Fallo parcial (directorio creado, BD no) | Rollback, log, auditoría `warning` y `500 error_interno`. Sin borrado en LDAP (v1). Reintento → `409 uid_duplicado` (manda el contrato); la persona se registra como `usuario` sin áreas en su primer login de directorio/SSO (enlace por `mail`). FNC-079 cubre registrar cuentas que ya existen |
| D2 | Directorio sin configurar | `503 directorio_no_disponible` (el contrato no tiene `409` para este endpoint) |
| D3 | Largo del correo | ≤ 120 (columna `users.email`) en lugar de 254 del contrato; evita 500 en Postgres |
| D4 | Correo en el directorio | También se busca `mail` en la OU de personas → `409 correo_duplicado` (evita dos entradas con el mismo correo, que el login enlaza por `mail`) |
| D5 | "uid único en la BD" | La BD no guarda uid: choca con `RESERVED_NAMES` (`admin`) o con una cuenta heredada cuyo `email` es ese identificador |
| D6 | Admin con área inexistente | `404`, igual que la ajena (no revela qué áreas existen); superadmin → `422` |
| D7 | Nombres | 1–100 sin caracteres de control; el nombre visible pasa por `sanitize_display_name` |
| D8 | Auditoría | `cuenta_directorio_creada` con el actor de la sesión; éxito en la misma transacción (SEC-AUD-06), detalle con los sistemas (`directorio` y `portal`); fallos del directorio `error` y fallo parcial `warning` |

## Impacto en elementos compartidos
Salida real de `python3 ~/.claude/agentes/herramientas/impacto.py`:

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/users/directory` | endpoint | `app/modules/users/api.py` | `frontend/src/lib/access/users.ts`, `frontend/tests/lib/access/peticiones.test.ts` | frontend/src, frontend/tests | ☐ |

- No es homónimo: es el endpoint nuevo y sus usos son el cliente web de FNC-069 (`createDirectoryAccount`), que ya envía el cuerpo del contrato; no cambia nada existente.
- `users/api.py` (blueprint `api_users`) solo agrega la ruta; `PUT /users/<id>/managed-areas` no cambia.
- Impacto para DIS-019: mostrar `fields` del `422`, `404` (área ajena), `409 uid_duplicado`/`correo_duplicado`, `503` y `500`; el admin debe elegir al menos un área; no hay campo de contraseña ni de rol.

## Criterios de aceptación
- [x] Alta crea la entrada en el directorio (doble de LDAP) y el usuario local (prueba)
- [x] Sin contraseña no se asigna ninguna por defecto (prueba de regresión SEG-02)
- [x] Identificador duplicado responde 409 (prueba)
- [x] Admin de área según P2 (prueba)
- [x] Criterios comunes backend (FNC-037); falta `auditor-seguridad` (requerido; no lanzado por instrucción del orquestador)

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest -q tests/users/test_alta_directorio.py` sin la ruta (stash de `users/api.py`) | `61 failed` (regresiones fallan primero) |
| `venv/bin/python -m pytest -q tests/users/test_alta_directorio.py` | `61 passed` |
| `venv/bin/python -m pytest -q tests/test_guardia_rutas.py tests/test_proteccion_por_rol.py` | `220 passed` |
| `venv/bin/python -m pytest -q` (completo) | `1035 passed, 15 xfailed` en 487 s; código de salida 0 (línea base develop: 969 passed) |

- No verificado: OpenLDAP real (solo `MOCK_SYNC`, que no compara valores escapados), ACL de la cuenta de servicio (SEC-LDAP-03), Postgres (D3), Authelia (contraseña inicial).

## Commits / PR
| Commit | Descripción |
|---|---|
| (ver bitácora) | `[FNC-064] Alta de cuentas en OpenLDAP desde el portal` — local, sin push ni PR |

## Impacto cruzado
- Genera → DIS-019
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-041, FNC-044, FNC-038, Respuestas a P2 y P8
- Contrato → docs/contratos/usuarios-directorio.md (v1, sin cambios)
- Coordina con → FNC-079 (no implementada aquí; ver D1)

## Riesgos y reversión
- Fallo a mitad (LDAP creado, BD no): se crea primero en LDAP y se enlaza de forma idempotente al reintentar.
- Reversión: revertir la rama; las cuentas creadas quedan en el directorio.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador). Implementada: `POST /users/directory`, validación, 404/409/422/503/500, auditoría, matriz. Decisiones D1–D8. En revisión; sin revisores (por instrucción) |
