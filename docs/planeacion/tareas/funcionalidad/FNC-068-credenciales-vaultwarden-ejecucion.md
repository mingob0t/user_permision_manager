# FNC-068 — Credenciales de conectores y del bind LDAP desde Vaultwarden en staging y producción

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 3 |
| **Módulo / Área** | secretos |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | commit local, sin push |
| **Rama** | `fnc/FNC-068-vaultwarden` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (gestión de secretos) |

## Contexto
- Las credenciales de los conectores y la de bind con escritura en OpenLDAP no pueden estar en el repositorio ni en la BD (RNF-03)
- ADR-005 decide cómo las obtiene la app en ejecución
- Requerimientos: F-CON-01, RNF-03

## Objetivo
- Preparar en staging y producción el acceso de la app a Vaultwarden (cuenta de servicio de mínimo privilegio o inyección al `EnvironmentFile`, según ADR-005), con su rotación documentada

## Alcance
- **Incluye:**
  - Cuenta de servicio o mecanismo de ADR-005 con acceso solo a la colección del portal
  - Procedimiento de alta de un ítem de conector y de rotación en `docs/operacion/`
  - Verificación de que el agente ni el repositorio contienen valores
- **No incluye:**
  - Crear los ítems de cada plataforma (lo hace el superadmin)
  - Código del resolvedor (FNC-050)

## Archivos previstos
- `deploy/` (solo lo que ADR-005 requiera)
- `docs/operacion/ENTORNOS.md`
- `docs/operacion/SECRETOS.md` (nuevo, sin valores)

## Reutilización
- Vaultwarden existente del dueño

## Variables y configuración
- Las de ADR-005, marcadas como sensibles en `VARIABLES.md`.

## Criterios de aceptación
- [ ] La app de staging resuelve una credencial de prueba sin que su valor aparezca en logs (evidencia)
- [ ] Procedimiento de rotación probado una vez
- [ ] Criterios comunes infra (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, ADR-005, FNC-050

## Riesgos y reversión
- Reversión: retirar la cuenta de servicio.

## Requisitos de seguridad heredados de FNC-050 (auditor-seguridad)
- Al rotar una credencial, llamar a `connectors.credenciales.limpiar_cache()` (o esperar `CONNECTOR_CREDENTIAL_CACHE_SECONDS`) para no seguir usando el valor anterior (B4).
- Implementar `ProveedorSecretosVaultwarden.obtener` respetando el mapeo de errores: no encontrada → `CredencialNoEncontrada`; caído → `GestorNoDisponible`; sin configurar → `GestorNoConfigurado`; nunca el valor en el texto.

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| D1 | ADR-005 A con la API HTTP compatible con Bitwarden y **descifrado del lado del cliente** en Python (`cryptography`, ya dependencia); sin CLI `bw` ni SDK | Vaultwarden cifra de extremo a extremo: la llave de API solo autentica. `bw` exige sesión desbloqueada y Node (ADR-005 B, frágil); el SDK de Bitwarden apunta a Secrets Manager, que Vaultwarden no tiene. Sin dependencias nuevas |
| D2 | Credencial de arranque: llave de API **personal** + contraseña maestra de una cuenta de servicio con solo lectura de **una** colección, en el `.env` del servidor (600) | Único medio con systemd 239 (Rocky 8, sin `LoadCredential=`); nunca en el repo; la pone una persona |
| D3 | Ítem = tipo *login* cuyo nombre es exactamente la referencia, filtrado además por `VAULTWARDEN_COLLECTION_ID`; nombre repetido = no encontrada | Mínimo privilegio también del lado del cliente; no se adivina |
| D4 | Solo `https` con nombre de host, TLS 1.2+ validado, sin proxies del entorno ni redirecciones, 5 s por operación, respuesta ≤ 8 MiB, KDF dentro de `LIMITES_KDF`, tipos cifrados autenticados (2, 3, 4) | Valores más seguros de `docs/seguridad/LINEAMIENTOS.md` (SEC-CON-06, SEC-CFG-02, falla cerrado) |
| D5 | Bind LDAP: fuera de dev, `LDAP_BIND_PASSWORD_REF` **o** `LDAP_BIND_PASSWORD` (ambas o la referencia en dev = no arranca); la contraseña se pide al conectar, con la caché de credenciales | El pedido dice «pueda venir»: se conserva ADR-005 C y no se rompe dev; pedirla al conectar evita depender de Vaultwarden para arrancar |
| D6 | Vaultwarden caído en el bind → `ErrorDirectorio` con causa `LDAPCommunicationError` (transitorio) | El ejecutor reintenta en vez de marcar fallo permanente |
| D7 | Caché de credenciales acotada a `MAXIMO_EN_CACHE` = 128 | «Caché acotada» del pedido; más que las referencias previstas |
| D8 | `deploy/secretos.sh` compartido por preflight e install; solo nombres y formato, nunca valores ni `source` del `.env` | Mismo criterio que REDIS_PASS (FNC-067) y que la corrección de inyección |

## Implementación (2026-10-21)
- Nuevo módulo `app/modules/secretos/`: `configuracion.py` (`VAULTWARDEN_*`), `cifrado.py` (Bitwarden del lado del cliente), `vaultwarden.py` (`ClienteVaultwarden`, transporte HTTPS).
- `connectors/credenciales.py`: `ProveedorSecretosVaultwarden` real con mapeo de errores de la ficha (no encontrada → `CredencialNoEncontrada`; caído → `GestorNoDisponible`; sin configurar → `GestorNoConfigurado`), caché acotada, `resolver_en_gestor()`.
- `directory/configuracion.py` (`LDAP_BIND_PASSWORD_REF`, campo `bind_password_ref`) y `directory/ldap_client.py` (`_contrasena_bind()`, enmascara también la contraseña del gestor).
- `app/__init__.py`: valida `VAULTWARDEN_*` al arrancar (sin conectar).
- `deploy/secretos.sh` (nuevo), `deploy/preflight.sh`, `deploy/install.sh`.
- Pruebas: `tests/secretos/` (servidor simulado que cifra de verdad, sin red), `tests/connectors/test_credenciales_vaultwarden.py`, `tests/directory/test_bind_desde_gestor.py`, `tests/deploy/test_secretos_sh.py`; `tests/conftest.py` quita `VAULTWARDEN_*` del entorno heredado.
- Docs: `docs/operacion/SECRETOS.md` (nuevo: preparación, alta de ítems, rotación con `limpiar_cache()`, reversión), `ENTORNOS.md`, `VARIABLES.md`, `HISTORIAL.md`, `.env.example`, `docs/backend/README.md`, `deploy/README.md`, catálogo de reutilización.
- No se tocaron los archivos de FNC-051 (`api_http.py`, `destino_seguro.py`, `http_transporte.py`, `connectors/__init__.py`, `provisioning/saneo.py`).

## Correcciones de auditor-seguridad (aprobado, solo hallazgos bajos)
| Hallazgo | Corrección | Prueba de regresión (falló primero) |
|---|---|---|
| B1 excepciones sin traducir | `http.client.HTTPException` → `GestorCaido`; `RecursionError` de `json` → `GestorMalConfigurado`; `UnsupportedAlgorithm` de Argon2id → `ErrorDeCifrado` (→ `GestorMalConfigurado`); en `ldap_client._contrasena_bind` cualquier error → `ErrorDirectorio` genérico | `tests/secretos/test_auditoria_fnc068.py::test_b1_*` |
| B2 ilegible + legible con el mismo nombre = ambiguo | Solo cuentan los ítems legibles y con contraseña; dos legibles = ambiguo; solo ilegibles = `GestorMalConfigurado` | `test_b2_*` |
| B3 bind LDAP enviable a un conector | `credenciales.referencia_reservada()`: `validacion.py` responde `MENSAJE_REFERENCIA_RESERVADA` al guardar y `provider.py` falla permanente (`credencial_no_encontrada`) sin resolver al ejecutar | `test_b3_validacion_*`, `tests/connectors/test_referencia_reservada.py` |
| FNC-108 | `VAULTWARDEN_CLIENT_SECRET` y `VAULTWARDEN_MASTER_PASSWORD` en `saneo.VARIABLES_SECRETAS`; FNC-108 cerrada como «resuelta en FNC-068» | `test_fnc108_*` |

Antes de corregir: 10 failed, 3 passed (los 3 ya cubiertos: `RemoteDisconnected` es `OSError`, solo ilegibles y el control). Conflicto con FNC-051 en `saneo.py`: ninguno textual previsto (FNC-051 cambia otro bloque, desde la línea 54).

## Verificación
| Comando | Resultado |
|---|---|
| Pruebas nuevas de `tests/connectors/test_credenciales_vaultwarden.py` y `tests/directory/test_bind_desde_gestor.py` **antes** de cambiar `credenciales.py` y el directorio | 15 failed, 4 passed (las 4 que pasan: falla cerrada que ya existía) |
| `pytest tests/secretos` | 47 passed |
| `pytest tests/connectors` | 146 passed |
| `pytest tests/directory tests/secretos tests/connectors/test_credenciales_vaultwarden.py` | 266 passed |
| `pytest tests/deploy/test_secretos_sh.py` (`.env` sintéticos; el secreto ficticio nunca aparece en la salida) | 10 passed |
| `bash -n deploy/preflight.sh deploy/install.sh deploy/secretos.sh` | sin errores |
| `pytest tests` (completo) | **1824 passed, 15 xfailed, código de salida 0** (955 s) |

**No verificado:**
- Contra un Vaultwarden real (sin red en dev; pendiente de la PoC en staging): forma exacta de la respuesta del token en su versión, alta del dispositivo y criterios «credencial de prueba en staging» y «rotación probada una vez».
- `shellcheck` no está instalado; solo `bash -n`.
- `preflight.sh`/`install.sh` completos no se ejecutaron (son para Rocky 8 y como root); se probó `revisar_vaultwarden` por separado.
- Sin revisor ni auditor-seguridad (no se lanzaron por instrucción del orquestador); auditor-seguridad es obligatorio antes de cerrar.

## Impacto en elementos compartidos
**Ronda de correcciones de auditoría:** `impacto.py` sube a 23 elementos, casi todos coincidencias por nombre. Cambios reales nuevos:
- `connectors.validacion.validar_configuracion`: `credential_ref` igual a `LDAP_BIND_PASSWORD_REF` da error de campo (lo usan `PUT /platforms/<id>/connector` (FNC-061) y DIS-022).
- `ProveedorConector._credencial`: la referencia reservada da fallo permanente `credencial_no_encontrada` sin resolverla (ejecutor y prueba de conexión).
- `saneo.VARIABLES_SECRETAS`: dos variables más que se borran de la bitácora de ejecuciones (FNC-049/062).
- `secretos`: `ClienteVaultwarden.leer` y `derivar_clave_maestra`, usados solo por `credenciales.py`.
- Pytest completo tras las correcciones: **1837 passed, 15 xfailed, código de salida 0**.

**Primera ronda:**
**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 6 elemento(s) usados en otras secciones: app/modules, app/utils, frontend/tests, tests, tests/access, tests/areas, tests/connectors, tests/directory, tests/platforms, tests/provisioning, tests/users. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `__init__` | función | `app/modules/connectors/credenciales.py` | `app/modules/access/errores.py`, `app/modules/audit/parametros.py`, `app/modules/connectors/base.py`, `app/modules/connectors/provider.py`, `app/modules/directory/writer.py`, `app/modules/notifications/services.py`, `app/modules/platforms/api.py`, `app/modules/provisioning/ldap_provider.py` (+12) | app/modules, app/utils, tests, tests/areas, tests/directory, tests/provisioning | ☐ |
| `cargar_configuracion` | función | `app/modules/directory/configuracion.py` | `app/modules/connectors/configuracion.py`, `app/modules/connectors/provider.py`, `app/modules/connectors/validacion.py`, `app/modules/directory/resumen.py`, `app/modules/platforms/grupos.py`, `app/modules/provisioning/cli.py`, `app/modules/provisioning/configuracion.py`, `app/modules/provisioning/ejecucion.py` (+17) | app/modules, tests, tests/access, tests/connectors, tests/directory, tests/platforms, tests/provisioning | ☐ |
| `conexion_servicio` | función | `app/modules/directory/ldap_client.py` | `app/modules/directory/api.py`, `app/modules/directory/writer.py`, `tests/directory/test_ldap_client.py`, `tests/directory/test_writer.py`, `tests/provisioning/test_ldap_provider.py`, `tests/users/test_alta_directorio.py` | app/modules, tests/directory, tests/provisioning, tests/users | ☐ |
| `obtener` | función | `app/modules/connectors/credenciales.py` | `app/utils/redis_client.py`, `frontend/tests/utils/tokens-css.ts`, `tests/connectors/test_proveedor_conector.py` | app/utils, frontend/tests, tests/connectors | ☐ |
| `registrar_error` | función | `app/modules/directory/ldap_client.py` | `app/modules/directory/writer.py`, `tests/directory/test_ldap_client.py`, `tests/directory/test_writer.py` | app/modules, tests/directory | ☐ |
| `resolver` | función | `app/modules/connectors/credenciales.py` | `app/modules/connectors/provider.py`, `frontend/tests/accesibilidad/medir.ts`, `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/components/connectors/jobs-log.test.tsx`, `frontend/tests/components/users/directory-account-form.test.tsx`, `frontend/tests/components/users/user-access-panel.test.tsx`, `frontend/tests/lib/use-polling.test.ts`, `frontend/tests/utils/tokens-css.ts` | app/modules, frontend/tests | ☐ |

Lectura: `__init__`, `obtener` y `resolver` son coincidencias por nombre (otras clases y el frontend), no usos reales. Cambios reales a validar:
- `directory.configuracion.cargar_configuracion`: campo nuevo `bind_password_ref` y regla de bind fuera de dev. Con `LDAP_BIND_PASSWORD` como hoy, el comportamiento no cambia (dev, login, `/auth-config`, escritura, worker).
- `ClienteDirectorio.conexion_servicio` / `registrar_error`: contraseña pedida al conectar con la referencia; enmascara también esa contraseña. Lo usan login, `/directory/search`, la prueba de conexión, `writer.py` y `ldap_provider.py`.
- `credenciales.ResolvedorCredenciales.resolver`: caché con tope de 128 (afecta al proveedor `conector` y la prueba de conexión de FNC-061).
- `app/__init__.py` (`create_app`): fuera de dev, `VAULTWARDEN_*` incompleta detiene el arranque de API y worker.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Recomendaciones de auditor-seguridad sobre FNC-050 agregadas (sección «Requisitos de seguridad heredados de FNC-050») |
| 2026-10-21 | Aprobada por el orquestador (modo autónomo) y En curso; implementada; En revisión |
| 2026-10-21 | auditor-seguridad aprobado; corregidos B1, B2 y B3 y resuelta FNC-108, con regresiones que fallaron primero |
