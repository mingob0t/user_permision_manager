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

No verificado: MySQL real (las migraciones se prueban en SQLite); Vaultwarden real (FNC-068); tipos concretos (FNC-051 a FNC-053). No se lanzaron `revisor`, `tester` ni `auditor-seguridad` (indicación del orquestador; el auditor es obligatorio antes de cerrar).

## Impacto en elementos compartidos
Salida de `python3 ~/.claude/agentes/herramientas/impacto.py`:

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `tiene_conector` | función | `app/modules/platforms/estado.py` | `app/modules/access_requests/catalogo.py`, `app/modules/core/models.py` | app/modules | ☐ |

Además (no los detecta la herramienta): `create_app()` valida `CONNECTOR_*` y registra el proveedor (toda la app y el worker); `saneo.MENSAJES` crece de forma aditiva (bitácora de ejecuciones, FNC-062); `tests/conftest.py` quita `CONNECTOR_*` del entorno heredado (todas las pruebas). Validar: `has_connector` en `GET /platforms` y niveles solicitables del catálogo para plataformas `conector`.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo por el orquestador; En curso en `fnc/FNC-050-conectores-base` (worktree `pokemon-wt-060`) |
| 2026-10-20 | Implementada; 79 pruebas nuevas (fallaban antes); suite 1630 passed, 15 xfailed, salida 0. En revisión; pendiente `revisor` y `auditor-seguridad` |
