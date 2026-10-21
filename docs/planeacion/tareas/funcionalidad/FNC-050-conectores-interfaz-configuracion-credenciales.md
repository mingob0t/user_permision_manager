# FNC-050 — Conectores: interfaz, registro, configuración por plataforma y credenciales desde Vaultwarden (según ADR-005)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en `fnc/FNC-050-conectores-base`, sin push |
| **Rama** | `fnc/FNC-050-conectores-base` |
| **Requiere migración BD** | Sí (tabla `platform_connectors`) |
| **Requiere auditor-seguridad** | Sí (credenciales de sistemas externos) |

## Contexto
- Las plataformas sin Authelia necesitan que el portal cree o quite la cuenta con un conector (API, SSH o BD) (F-CON-01)
- Las credenciales no pueden estar en el repositorio ni en claro en la BD (RNF-03, SEG-08)
- Requerimientos: F-CON-01, RNF-03

## Objetivo
- Definir la interfaz común de conector (`grant`, `revoke`, `check` opcional), su registro por tipo, el modelo de configuración por plataforma (tipo, nombre de host, parámetros no sensibles, **referencia** al ítem de Vaultwarden) y el resolvedor de credenciales en ejecución que decida ADR-005, conectado al ejecutor de FNC-049 como proveedor `conector`

## Alcance
- **Incluye:**
  - Tabla `platform_connectors` (una por plataforma `conector`): tipo, host por nombre, puerto, parámetros JSON validados por esquema del tipo, referencia de credencial, activo
  - `base.py` (interfaz y resultado tipificado igual que FNC-041), `registry.py`, `credentials.py` (resolvedor por ADR-005, con caché breve en memoria y sin registrar valores)
  - Proveedor `conector` del ejecutor que carga la configuración y llama al tipo correspondiente
  - Un conector de prueba (`noop`) solo para pruebas y dev
- **No incluye:**
  - Tipos concretos API, SSH, BD (FNC-051 a FNC-053)
  - Endpoints de configuración (FNC-061)
  - Configuración de Vaultwarden en servidores (FNC-068)

## Archivos previstos
- `app/modules/connectors/models.py`
- `app/modules/connectors/base.py`
- `app/modules/connectors/registry.py`
- `app/modules/connectors/credenciales.py` (el control de lineamientos bloquea el nombre `credentials.py` como archivo de secretos)
- `app/modules/connectors/provider.py`
- Migración (ADR-002)
- `tests/connectors/`

## Reutilización
- Registro de proveedores y resultado tipificado de FNC-049

## Variables y configuración
- Las de ADR-005 para acceder a Vaultwarden (p. ej. `VAULTWARDEN_URL`, identificador y secreto de la cuenta de servicio, sensibles) y `CONNECTOR_CREDENTIAL_CACHE_SECONDS` — registrar.

## Integración (lineamiento técnico 11)
- Llamadas salientes del portal a cada plataforma (no se reciben cambios); no aplica webhook ni polling
- Tiempo de espera por tipo de conector como variable registrada

## Criterios de aceptación
- [x] La tabla no guarda secretos, solo referencias (prueba de esquema)
- [x] Una referencia inexistente en Vaultwarden da error permanente sin exponer detalles (prueba con resolvedor simulado)
- [x] El conector `noop` recorre el flujo completo otorgar → revocar con el ejecutor (prueba)
- [x] Ningún valor de credencial aparece en logs, auditoría ni respuestas (prueba)
- [x] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → FNC-051, FNC-052, FNC-053, FNC-061, FNC-068
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-049, FNC-046, ADR-005

## Riesgos y reversión
- Disponibilidad de Vaultwarden en el camino crítico: error transitorio con reintento.
- Reversión: bajar la migración; las plataformas `conector` quedan sin aprovisionar.

## Implementación
- `app/modules/connectors/`: `tipos.py`, `configuracion.py` (`CONNECTOR_*`, validadas en `create_app()`), `models.py` (`PlatformConnector`), `base.py` (`Conector`, `Destino`, `SolicitudConector`), `registry.py`, `validacion.py`, `credenciales.py`, `consultas.py`, `provider.py` (`ProveedorConector`), `noop.py`, `__init__.py` (`registrar(app)`).
- Migración `migrations/versions/0009_conectores.py` (down `0008`).
- Reutiliza de FNC-049: `Provisioner`, `registrar_proveedor`, `ResultadoProveedor`, `permanente`/`transitorio`, `mensaje_de_error`/`sanear_error` (vía el ejecutor), `LARGO_MINIMO_SECRETO`; de FNC-040 `es_ip_literal`; de FNC-047 `FRAGMENTOS_SENSIBLES` y `VALOR_OMITIDO`.
- Cambios fuera del módulo: `app/__init__.py` (validación y registro), `platforms/estado.py` (`tiene_conector`), `provisioning/saneo.py` (5 motivos y mensajes, aditivo), `provisioning/__init__.py` (comentario), `tests/conftest.py` (prefijo `CONNECTOR_` fuera del entorno heredado).
- No se tocó `provisioning/api.py`, `consultas.py`, `serializacion.py`, `reintento.py`, `ejecucion.reabrir` ni `queue.encolar` (FNC-062 en paralelo).

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Base |
|---|---|---|
| D1 | La cuenta que recibe el conector es el correo de la cuenta del portal en minúsculas, no el uid del directorio; el mapeo a la cuenta de cada plataforma lo decide cada tipo (P9) | SEC-CON-03 (dato del servidor, nunca texto del usuario) |
| D2 | Fuente de credenciales por `APP_ENV`: solo `development` lee el entorno; cualquier otro valor o vacío usa Vaultwarden (hoy *stub* → permanente `gestor_no_configurado`) | SEC-CON-02, ADR-005 |
| D3 | `CONNECTOR_ALLOWED_HOSTS` vacía = ningún destino; el host se revalida en cada ejecución (no solo al configurar) | SEC-CON-07 |
| D4 | `CONNECTOR_TIMEOUT_SECONDS` 10 (1–120) y menor que el tiempo del intento; caché 60 s (0–300); los fallos no se guardan en caché | SEC-CON-08, ADR-005 |
| D5 | `VAULTWARDEN_*` no se registran todavía: las agrega FNC-068 cuando el código las lea | Sin variables sin uso |
| D6 | `noop` solo se registra con `APP_ENV=development` o `TESTING`; una configuración `noop` en otro entorno da `conector_no_disponible` | Contrato (`noop` solo en dev y pruebas) |
| D7 | `consultar` es opcional por tipo: sin ella, permanente `consulta_no_disponible` | Ficha (`check` opcional) |
| D8 | `ON DELETE CASCADE` desde `platforms`; el ejecutor no escribe `credential_status` (lo hará la prueba de FNC-061) | Configuración sin plataforma no sirve; sin escrituras laterales en el ejecutor |
| D9 | Validación por campo aquí; la lista blanca de campos del cuerpo, el `409 plataforma_sin_conector` y la auditoría `conector_configurado` son del endpoint (FNC-061) | Alcance de la ficha |

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest tests/connectors -q` antes de implementar | salida 4 (`ModuleNotFoundError: app.modules.connectors`): las pruebas nuevas fallaban |
| `venv/bin/python -m pytest tests/connectors tests/test_migraciones.py -q` | 79 + migraciones en verde (tras corregir `AuditLog.detail` y cambiar IPv4 literales por IPv6 de documentación y formas abreviadas, como exige el control) |
| `venv/bin/python -m pytest -q` (suite completa) | **1630 passed, 15 xfailed, salida 0** (747 s, tras el último ajuste de pruebas) |
| `venv/bin/python -m pytest -q` tras traer develop (`bcd02a3`) | **1684 passed, 15 xfailed, salida 0** (889 s) |
| Regresiones B1–B3 antes de corregir | 7 fallidas + `test_validacion_conector.py` sin importar (`MENSAJE_PARAMS_PROFUNDOS`), salida 2 |
| `venv/bin/pytest tests/connectors` tras corregir | **93 passed, salida 0** |
| `venv/bin/pytest tests` (suite completa) tras corregir | **1698 passed, 15 xfailed, salida 0** (988 s) |

No verificado: MySQL real (las migraciones se prueban en SQLite); Vaultwarden real (FNC-068); tipos concretos (FNC-051 a FNC-053). No se lanzaron `revisor`, `tester` ni `auditor-seguridad` (indicación del orquestador; el auditor es obligatorio antes de cerrar).

## Correcciones de auditor-seguridad (veredicto Aprobado, hallazgos bajos)
| # | Hallazgo | Corrección | Regresión (fallaba antes) |
|---|---|---|---|
| B1 | `Destino` recibía el host crudo de la BD | `provider.py`: `normalizar_host(configuracion.host)` | `test_b1_el_destino_lleva_el_host_normalizado` |
| B2 | `_claves_sensibles` no revisaba listas y un anidado profundo daba `RecursionError` | Recorre objetos y listas hasta `PROFUNDIDAD_MAXIMA_PARAMS` (8); más profundo → `params`: «Los parámetros tienen demasiados niveles.» | `test_b2_secretos_dentro_de_listas`, `test_b2_profundidad_excesiva_es_invalida_sin_recursionerror` |
| B3 | Referencias con `__` o distintas con la misma variable de dev | `referencia_valida` (sin `__` ni `_` en los extremos de la variable) y `referencias_en_conflicto`; validación con `referencias_en_uso`, entorno (`ReferenciaInvalida`) y proveedor (contra las demás plataformas) → permanente `credencial_no_encontrada` | `test_b3_*` en `test_credenciales.py`, `test_validacion_conector.py` y `test_proveedor_conector.py` |
| B4 | La caché puede servir una credencial vieja tras cambiar la configuración o rotarla | Anotado en las fichas de FNC-061 (`limpiar_cache()` al guardar o borrar) y FNC-068 (al rotar) | — (lo implementan esas tareas) |

Recomendaciones anotadas: FNC-051, FNC-052 y FNC-053 (resolver el DNS y rechazar IPs privadas o de loopback; no seguir redirecciones a otros hosts, SEC-CON-06); FNC-061 (solo superadmin, SEC-CON-11; usar `validar_configuracion`).

## Impacto en elementos compartidos
Salida de `python3 ~/.claude/agentes/herramientas/impacto.py` tras traer develop (`bcd02a3`), con los archivos nuevos ya en commit:

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 26 elemento(s) usados en otras secciones: app, app/modules, app/utils, frontend, frontend/src, frontend/tests, migrations, migrations/versions, scratch, scripts/lineamientos, tests, tests/access, tests/access_requests, tests/areas, tests/audit, tests/authz, tests/directory, tests/home, tests/notifications, tests/platforms, tests/provisioning, tests/users, utils, utils/migrations. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Conector` | clase | `app/modules/connectors/base.py` | `app/modules/access/area_admin_sync.py`, `frontend/src/components/platforms/platform-integration-fields.tsx`, `frontend/src/lib/access/connectors.ts` | app/modules, frontend/src | ☐ |
| `Credencial` | clase | `app/modules/connectors/credenciales.py` | `migrations/versions/0004_vaciar_credencial_ldap.py`, `tests/directory/test_api.py` | migrations/versions, tests/directory | ☐ |
| `_Fallo` | clase | `app/modules/connectors/provider.py` | `app/modules/provisioning/ldap_provider.py` | app/modules | ☐ |
| `__init__` | función | `app/modules/connectors/base.py`, `app/modules/connectors/credenciales.py`, `app/modules/connectors/provider.py`, `tests/connectors/test_credenciales.py` | `app/modules/access/errores.py`, `app/modules/audit/parametros.py`, `app/modules/directory/ldap_client.py`, `app/modules/directory/writer.py`, `app/modules/notifications/services.py`, `app/modules/platforms/api.py`, `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py` (+11) | app/modules, app/utils, tests, tests/areas, tests/directory, tests/provisioning | ☐ |
| `_ejecutar` | función | `app/modules/connectors/provider.py` | `app/modules/directory/writer.py` | app/modules | ☐ |
| `_entero` | función | `app/modules/connectors/configuracion.py` | `app/modules/provisioning/configuracion.py` | app/modules | ☐ |
| `_leer` | función | `app/modules/connectors/configuracion.py` | `app/modules/directory/configuracion.py`, `app/modules/provisioning/configuracion.py` | app/modules | ☐ |
| `_preparar` | función | `app/modules/connectors/provider.py` | `app/modules/provisioning/ldap_provider.py` | app/modules | ☐ |
| `_solicitud` | función | `app/modules/connectors/provider.py` | `tests/home/test_resumen.py` | tests/home | ☐ |
| `cargar_configuracion` | función | `app/modules/connectors/configuracion.py` | `app/modules/directory/configuracion.py`, `app/modules/directory/ldap_client.py`, `app/modules/directory/resumen.py`, `app/modules/platforms/grupos.py`, `app/modules/provisioning/cli.py`, `app/modules/provisioning/configuracion.py`, `app/modules/provisioning/ejecucion.py`, `app/modules/provisioning/ldap_provider.py` (+15) | app/modules, tests, tests/access, tests/directory, tests/platforms, tests/provisioning | ☐ |
| `consultar` | función | `app/modules/connectors/base.py`, `app/modules/connectors/noop.py`, `app/modules/connectors/provider.py` | `app/authz.py`, `app/modules/directory/ldap_client.py`, `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/use-polling.ts`, `tests/provisioning/conftest.py`, `tests/provisioning/test_ldap_provider.py` | app, app/modules, frontend/src, tests/provisioning | ☐ |
| `datos` | función | `tests/connectors/test_validacion_conector.py` | `app/authz.py`, `app/modules/access/api.py`, `app/modules/access/serializacion.py`, `app/modules/access_requests/api.py`, `app/modules/api/admin.py`, `app/modules/api/helpers.py`, `app/modules/api/routes.py`, `app/modules/areas/api.py` (+73) | app, app/modules, app/utils, frontend, frontend/src, frontend/tests, migrations/versions, scratch, scripts/lineamientos, tests, tests/access, tests/areas, tests/audit, tests/authz, tests/directory, tests/home, tests/notifications, tests/platforms, tests/provisioning, tests/users, utils, utils/migrations | ☐ |
| `downgrade` | función | `migrations/versions/0009_conectores.py` | `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `migrations/versions/0007_accesos_otorgados.py`, `migrations/versions/0008_solicitudes.py` (+4) | migrations/versions, tests, tests/notifications, tests/platforms | ☐ |
| `encolar` | función | `tests/connectors/test_proveedor_conector.py` | `app/modules/access/services.py`, `app/modules/provisioning/consultas.py`, `app/modules/provisioning/queue.py`, `app/modules/provisioning/tipos.py`, `tests/access/test_area_admin_sync.py`, `tests/provisioning/conftest.py`, `tests/provisioning/test_encolado.py`, `tests/provisioning/test_ldap_provider.py` | app/modules, tests/access, tests/provisioning | ☐ |
| `obtener` | función | `app/modules/connectors/credenciales.py`, `tests/connectors/test_credenciales.py`, `tests/connectors/test_proveedor_conector.py` | `app/utils/redis_client.py`, `frontend/tests/utils/tokens-css.ts` | app/utils, frontend/tests | ☐ |
| `operacion` | función | `tests/connectors/test_proveedor_conector.py` | `app/modules/access/services.py`, `app/modules/access_requests/api.py`, `app/modules/directory/ldap_client.py`, `app/modules/directory/writer.py`, `app/modules/notifications/access_notifications.py`, `app/modules/provisioning/ejecucion.py`, `app/modules/provisioning/ldap_provider.py`, `app/modules/provisioning/providers.py` (+11) | app/modules, migrations/versions, tests/audit, tests/directory, tests/provisioning | ☐ |
| `otorgar` | función | `app/modules/connectors/base.py`, `app/modules/connectors/noop.py`, `app/modules/connectors/provider.py`, `tests/connectors/test_proveedor_conector.py` | `app/modules/access/__init__.py`, `app/modules/access/area_admin_sync.py`, `app/modules/access/rules.py`, `app/modules/access/services.py`, `app/modules/access_requests/approvals.py`, `app/modules/access_requests/catalogo.py`, `app/modules/notifications/access_notifications.py`, `app/modules/provisioning/ejecucion.py` (+21) | app/modules, frontend/src, tests, tests/access, tests/access_requests, tests/notifications, tests/provisioning | ☐ |
| `registrar` | función | `app/modules/connectors/__init__.py` | `app/modules/access/manejadores.py`, `app/modules/auth/services.py`, `migrations/env.py`, `tests/access/conftest.py` | app/modules, migrations, tests/access | ☐ |
| `resolver` | función | `app/modules/connectors/credenciales.py` | `frontend/tests/accesibilidad/medir.ts`, `frontend/tests/lib/use-polling.test.ts`, `frontend/tests/utils/tokens-css.ts` | frontend/tests | ☐ |
| `revocar` | función | `app/modules/connectors/base.py`, `app/modules/connectors/noop.py`, `app/modules/connectors/provider.py`, `tests/connectors/test_proveedor_conector.py` | `app/modules/access/__init__.py`, `app/modules/access/api.py`, `app/modules/access/area_admin_sync.py`, `app/modules/access/errores.py`, `app/modules/access/rules.py`, `app/modules/access/services.py`, `app/modules/notifications/access_notifications.py`, `app/modules/provisioning/ejecucion.py` (+19) | app/modules, frontend/src, frontend/tests, tests, tests/access, tests/provisioning | ☐ |
| `test_valores_invalidos_fallan` | función | `tests/connectors/test_configuracion_conectores.py` | `tests/provisioning/test_configuracion.py` | tests/provisioning | ☐ |
| `tiene_conector` | función | `app/modules/platforms/estado.py` | `app/modules/access_requests/catalogo.py`, `app/modules/core/models.py` | app/modules | ☐ |
| `to_dict` | función | `app/modules/connectors/models.py` | `app/modules/api/admin.py`, `app/modules/api/routes.py`, `app/modules/areas/api.py`, `app/modules/audit/api.py`, `app/modules/audit/models.py`, `app/modules/auth/models.py`, `app/modules/core/models.py`, `app/modules/notifications/models.py` (+6) | app/modules, tests/access, tests/access_requests, tests/audit, tests/users | ☐ |
| `trabajo` | función | `tests/connectors/test_proveedor_conector.py` | `app/modules/access/api.py`, `app/modules/access/area_admin_sync.py`, `app/modules/access/manejadores.py`, `app/modules/access/services.py`, `app/modules/access_requests/approvals.py`, `app/modules/provisioning/api.py`, `app/modules/provisioning/configuracion.py`, `app/modules/provisioning/consultas.py` (+20) | app/modules, migrations/versions, tests, tests/access, tests/access_requests, tests/provisioning | ☐ |
| `upgrade` | función | `migrations/versions/0009_conectores.py` | `migrations/env.py`, `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `migrations/versions/0006_ejecuciones_aprovisionamiento.py`, `migrations/versions/0007_accesos_otorgados.py` (+5) | migrations, migrations/versions, tests, tests/notifications, tests/platforms | ☐ |
| `validar_al_arrancar` | función | `app/modules/connectors/configuracion.py` | `app/modules/directory/configuracion.py`, `app/modules/platforms/grupos.py`, `app/modules/provisioning/configuracion.py`, `tests/directory/test_config.py` | app/modules, tests/directory | ☐ |

Lectura: de los 26, solo `tiene_conector` es un elemento compartido **modificado**. Los otros 25 son definiciones **nuevas** del módulo `connectors/`, de la migración 0009 o de las pruebas cuyo nombre coincide con funciones ajenas (`otorgar`, `revocar`, `to_dict`, `upgrade`, `cargar_configuracion`, `validar_al_arrancar`, etc.). No cambian el código que los usa.

Además (no los detecta la herramienta): `create_app()` valida `CONNECTOR_*` y registra el proveedor (toda la app y el worker); `saneo.MENSAJES` crece de forma aditiva (bitácora de ejecuciones, FNC-062); `tests/conftest.py` quita `CONNECTOR_*` del entorno heredado (todas las pruebas). Validar: `has_connector` en `GET /platforms` y niveles solicitables del catálogo para plataformas `conector`.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo por el orquestador; En curso en `fnc/FNC-050-conectores-base` (worktree `pokemon-wt-060`) |
| 2026-10-20 | Implementada; 79 pruebas nuevas (fallaban antes); suite 1630 passed, 15 xfailed, salida 0. En revisión; pendiente `revisor` y `auditor-seguridad` |
| 2026-10-20 | Rama actualizada con develop (FNC-062, FNC-067: `9499592`; DIS-013: `6c9eaa7`), con conflictos solo en documentación, resueltos uniendo ambas versiones. 0009 sigue sobre 0008. Impacto recalculado |
| 2026-10-20 | auditor-seguridad: Aprobado. Corregidos B1, B2 y B3 con regresión (fallaban antes); B4 y las recomendaciones anotadas en FNC-051/052/053/061/068. Suite: 1698 passed, 15 xfailed, salida 0 |
