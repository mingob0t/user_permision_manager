# FNC-043 — Configuración del directorio: esquema de OpenLDAP en la API y credencial de bind fuera de la BD

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-directorio |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Inicio** | 2026-10-18 |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push (worktree `pokemon-wt-043`) |
| **Rama** | `fnc/FNC-043-configuracion-directorio` |
| **Commits / PR** | ver Bitácora (local, sin push ni PR) |
| **Requiere migración BD** | Sí (vaciar y marcar obsoleta `auth_config.ldap_pass`) |
| **Requiere auditor-seguridad** | Sí (secretos) |

## Contexto
- La configuración LDAP vive en `auth_config` con la contraseña de bind en claro (SEG-08) y se edita en `GET/PUT/POST /auth-config` (`app/modules/api/admin.py`), cuyo "probar" combina el host del payload con la contraseña guardada (SEG-22) y devuelve `str(exc)` (SEG-21)
- La cuenta de bind pasa a tener permisos de escritura, por lo que su credencial debe ir a `.env`/Vaultwarden (ADR-004, ADR-005)
- Requerimientos: F-ACC-01, RNF-03

## Objetivo
- Que la API de configuración del directorio muestre la configuración efectiva (sin secretos) y permita al superadmin ajustar solo lo no sensible que ADR-004 deje en BD, con la credencial de bind leída solo del entorno

## Alcance
- **Incluye:**
  - `GET /auth-config`: configuración efectiva del cliente de FNC-040, origen de cada valor y estado de conexión, sin contraseña
  - `PUT /auth-config`: solo campos no sensibles permitidos por ADR-004; rechaza credenciales
  - `POST /auth-config/test`: usa la configuración efectiva, sin aceptar host nuevo con contraseña guardada; mensaje genérico
  - `GET /directory/search` migrado al cliente de FNC-040
  - Migración que vacía `auth_config.ldap_pass` y la marca obsoleta; los campos de mapeo de roles quedan obsoletos (FNC-042)
  - Lo nuevo vive en `app/modules/directory/api.py`; en `admin.py` solo se retiran las rutas movidas (sin refactor del resto)
- **No incluye:**
  - Secretos de SMTP (parte SMTP de FNC-010)
  - Respaldo con hashes (SEG-17, FNC-010)
  - Pantalla (DIS-023)
  - Dividir `admin.py` (FNC-029)

## Hallazgos de seguridad que absorbe
- **FNC-010** parcial: SEG-08 (contraseña de bind) y SEG-22 (prueba LDAP). La parte SMTP y SEG-17 quedan en FNC-010.
- **FNC-017** parcial: SEG-21 en `admin.py:404` y `:637` (prueba LDAP y búsqueda).
- Cierra **FNC-012** junto con FNC-042.

## Archivos previstos
- `app/modules/directory/api.py`
- `app/modules/api/admin.py` (retiro de las rutas movidas)
- `app/modules/auth/models.py` (`AuthConfig`, columnas obsoletas)
- Migración en la carpeta de ADR-002
- `app/__init__.py` (registro del blueprint)
- `tests/directory/test_api.py`

### Archivos reales
- Nuevos: `app/modules/directory/api.py` (rutas), `resumen.py` (vista sin secretos), `depuracion.py` (`DEBUG_LDAP`), `migrations/versions/0004_vaciar_credencial_ldap.py`
- Cambiados: `directory/ldap_client.py` (`buscar_personas`, `LIMITE_BUSQUEDA_PERSONAS`), `api/admin.py` (−rutas LDAP y búsqueda), `auth/services.py` (−`validate_ldap_connection`, −`ldap3`), `auth/models.py` (obsoleta + validador), `app/__init__.py` (blueprint)
- Pruebas: `tests/directory/test_api.py`, `test_aislamiento.py`, `tests/test_migracion_0004.py` (nuevas); `conftest.py`, `matriz_proteccion.py`, `test_respaldo.py`, `test_secretos_en_respuestas.py` (ajustadas)
- Docs: contrato `usuarios-directorio.md` (sección configuración), `VARIABLES.md`, `HISTORIAL.md`, `docs/backend/README.md`, `LINEAMIENTOS.md` §11, CHANGELOG, log

## Reutilización
- Cliente de FNC-040
- `admin_required` de `app/authz.py`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `/api/v1/auth-config` (GET/PUT/POST test) | Endpoints (forma nueva) | Pestaña Directorio (`settings-panel.tsx`, `api.ts`, `types.ts`): **deja de funcionar** hasta DIS-023 (lee `ldap_*`, envía `ldap_pass` y host al probar → 400) | Pendiente (DIS-023) |
| `/api/v1/directory/search` | Endpoint (misma forma) | Alta desde el directorio (`users-list.tsx`): mismos campos `name/email/account/exists`; errores nuevos `409`/`503` y `q` ≤ 64 | Pruebas; pantalla: validar el dueño |
| `AuthConfig` | Modelo | Respaldo `GET/POST /backup` (sin cambios de formato), `tests/directorio_falso.py`, `test_login_directorio.py`, `utils/test_ldap.py`, `utils/nexus_health.py` | Pruebas; `utils/` ver Decisiones |
| `ClienteDirectorio.buscar_personas` (nuevo, solo agregado) | Método | `directory/api.py` | Pruebas |
| `validate_ldap_connection` (retirada) | Función | Solo `utils/test_ldap.py`, `utils/nexus_health.py` (ya fallaban) | FNC-028 |
| `app/__init__.py` | Arranque | Toda la app (una línea de import y el blueprint en la tupla) | Suite completa |
| `tests/conftest.py`, `tests/matriz_proteccion.py` | Base de pruebas | Toda la suite | Suite completa |

### Salida real de `impacto.py` (2026-10-18)
- 9 nombres; reales y homónimos:
  - `/auth-config`, `/auth-config/test`, `/directory/search`: reales; se movieron a `directory/api.py` (misma ruta). Consumidores: `frontend/src/lib/api.ts` (DIS-023) y los `_moved(...)` de `auth/routes.py`, `settings/routes.py`, `users/routes.py` (solo texto, sin cambio)
  - `AuthConfig`: real; consumidores arriba. `frontend` y `tests/audit/test_registro_ampliado.py` son homónimos (tipo TS / diccionario de prueba)
  - `validate_ldap_connection`: real; solo `utils/` (ver Decisiones)
  - `purge_inactive_users`: sin cambios; aparece por el contexto del diff en `auth/services.py`
  - `__init__`, `search`: métodos de `_ConexionLdapFalsa` retirada de `matriz_proteccion.py`; homónimos en el resto
  - `configuracion`: fixture de `test_respaldo.py`; homónimo del módulo `directory/configuracion.py`

## Variables y configuración
- Las de FNC-040 pasan a ser la fuente; `auth_config.ldap_pass` marcada obsoleta en `VARIABLES.md` (configuración en BD) con motivo.
- Hecho: sin variables de entorno nuevas (`.env.example` sin cambios); `auth_config.*` obsoletos en `VARIABLES.md` (sección nueva "Configuración en la BD"); `DEBUG_LDAP` movida; constantes `LIMITE_BUSQUEDA_PERSONAS`, `MIN_BUSQUEDA`, `MAX_BUSQUEDA`; todo en `HISTORIAL.md` con motivo

## Criterios de aceptación
- [x] Ninguna respuesta incluye la credencial (`_sin_credenciales` en GET/PUT/test; `test_secretos_en_respuestas.py`)
- [x] `PUT` con contraseña o `POST /test` con host nuevo se rechazan (`test_put_rechaza_credenciales_y_cualquier_campo`, `test_prueba_no_acepta_un_host_nuevo_con_la_clave_guardada`)
- [x] El respaldo no exporta ni importa `ldap_pass` (`test_exportar_no_incluye_contrasenas_de_servicio` con clave previa por SQL, `test_importar_no_escribe_la_clave_de_bind`)
- [x] Búsqueda con `uid` y entrada escapada (`test_busqueda_por_uid_...`, `test_busqueda_escapa_la_entrada`); OpenLDAP real no verificado
- [ ] Criterios comunes backend (FNC-037): pruebas, errores genéricos, variables e impacto hechos; falta revisor y auditor-seguridad

## Impacto cruzado
- Genera → DIS-023
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-040, FNC-039, FNC-038
- Contrato → docs/contratos/usuarios-directorio.md (sección configuración)

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest -q` (antes, `develop` 636d145) | 771 passed, 17 xfailed, código 0 |
| 8 regresiones contra el código anterior (`git stash -u` de `app/` y `migrations/`) | 8 failed: PUT guarda la clave, prueba con host del cuerpo, `str(exc)` en prueba y búsqueda, `ldap3` y `CERT_NONE` fuera del paquete, migración 0004 ×2 |
| `venv/bin/python -m pytest -q` (después) | 805 passed, 17 xfailed, código 0 (+34 pruebas) |
- Sin `xfail` que quitar: ninguno cubría SEG-08/13/21/22
- No verificado: OpenLDAP real (sin servidor ni valores, ADR-004); el `MOCK_SYNC` no compara valores escapados ni devuelve entradas con `sizeLimitExceeded` (se prueban el filtro y el límite enviados)

## Decisiones y observaciones
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `PUT /auth-config` sin campos editables (ADR-004 deja todo en `.env`); se conserva la ruta para responder `400 campo_no_permitido` en lugar de 405
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `GET /auth-config` no conecta al directorio (evita esperas y carga en cada lectura); el estado de conexión sale de `POST /auth-config/test`
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `POST /auth-config/test` rechaza cualquier campo del cuerpo (SEG-22); `409 directorio_no_configurado` si está inactivo; `503 directorio_no_disponible` genérico si falla (SEG-21)
- Decisión del orquestador (pendiente de validar en la prueba de concepto): no se expone la ruta de `LDAP_CA_CERT_FILE` (solo `custom`/`system`); `bind_dn` sí
- Decisión del orquestador (pendiente de validar en la prueba de concepto): el modelo rechaza escribir `ldap_pass` (validador); la migración la vacía y `downgrade` no la restaura
- Decisión del orquestador (pendiente de validar en la prueba de concepto): búsqueda con `q` de 2–64 caracteres; se mantiene `admin_required` (solo superadmin, como antes); P2 (admin crea cuentas) queda en FNC-064
- Contrato: sección "Configuración del directorio" agregada a `usuarios-directorio.md` (endpoints sin contrato previo); decisión del orquestador (pendiente de validar en la prueba de concepto)
- `DEBUG_LDAP` movida a `directory/depuracion.py` sin cambiar su efecto (SEC-LDAP-01)
- El respaldo sigue exportando/importando `auth_config` (sin `ldap_pass`); quitarlo es SEG-17/FNC-010
- `utils/test_ldap.py` y `utils/nexus_health.py` importan `validate_ldap_connection` (retirada); ya fallaban al llamarla sin argumentos; quedan para FNC-028
- Frontend sin tocar: DIS-023 debe leer la forma nueva de `GET /auth-config`, no enviar campos en `PUT`/test y mostrar `409`/`503`

## Riesgos y reversión
- Entornos que dependían de la configuración por interfaz deben cargar las variables antes de desplegar (RELEASES).
- Reversión: la migración conserva la columna (solo la vacía); bajar restaura la lectura previa sin el valor.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-18 | Aprobada (modo autónomo, vía orquestador); implementada en `fnc/FNC-043-configuracion-directorio`; 805 passed, 17 xfailed, código 0; En revisión (falta revisor y auditor-seguridad) |
