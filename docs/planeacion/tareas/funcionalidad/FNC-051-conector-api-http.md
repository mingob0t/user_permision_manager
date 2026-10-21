# FNC-051 — Conector tipo API HTTP

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Local, sin push |
| **Rama** | `fnc/FNC-051-conector-api` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (ejecución remota con credenciales) |

## Contexto
- Tipo de conector API HTTP de F-CON-01
- Qué plataformas lo usan primero lo decide el dueño (pregunta P9); sin una plataforma piloto la tarea no se aprueba
- Requerimientos: F-CON-01

## Objetivo
- Implementar el tipo API HTTP sobre la interfaz de FNC-050: Llamadas HTTPS configurables (método, ruta, cuerpo con plantilla de campos permitidos) para crear y quitar la cuenta; autenticación por token o básica tomada de la credencial; códigos de estado mapeados a éxito, transitorio o permanente

## Alcance
- **Incluye:**
  - Implementación del tipo y su esquema de parámetros
  - Clasificación de errores en transitorios y permanentes
  - Pruebas con servidor simulado
  - Guía de configuración para la plataforma piloto en `docs/backend/conectores.md`
- **No incluye:**
  - Plataformas distintas de la piloto aprobada
  - Sincronizar o conciliar cuentas existentes (fuera de la v1)
  - Pantalla (DIS-022)

## Archivos previstos
- `app/modules/connectors/api_http.py` (estructura plana como `noop.py`), `destino_seguro.py`, `http_transporte.py`
- `tests/connectors/`
- `docs/backend/README.md` (la guía va en la sección de conectores; no existe `conectores.md`)

## Reutilización
- Interfaz, registro y credenciales de FNC-050

## Variables y configuración
- Se reutiliza `CONNECTOR_TIMEOUT_SECONDS` (no hay variable propia de tiempo de espera) y la verificación TLS es obligatoria
- `CONNECTOR_HTTP_CA_FILE` (nueva, opcional): CA del despliegue; registrada en VARIABLES, HISTORIAL y `.env.example`

## Integración (lineamiento técnico 11)
- Llamadas salientes a la plataforma; no aplica webhook ni polling

## Criterios de aceptación
- [x] Otorgar y revocar contra el servidor simulado (pruebas)
- [x] Entrada maliciosa (comillas, `;`, saltos de línea) no altera la operación (prueba de inyección)
- [x] Verificación de TLS o de llave de host obligatoria (prueba)
- [x] Probado contra la plataforma piloto en dev, con evidencia, o declarado no verificado con motivo: **no verificado** contra una plataforma real (P9 sin respuesta; sin red en las pruebas). Solo servidor simulado y un servidor TLS local en loopback
- [x] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-050, Respuesta del dueño a P9 (plataforma piloto)

## Riesgos y reversión
- Cada plataforma tiene su API o esquema: el tipo es genérico y lo específico va en parámetros.
- Reversión: desregistrar el tipo.

## Requisitos de seguridad heredados de FNC-050 (auditor-seguridad)
- Resolver el DNS del host antes de conectar y rechazar si resuelve a una IP privada, de loopback, *link-local* o no enrutable (DNS *rebinding*); conectar a la IP ya validada, no volver a resolver.
- No seguir redirecciones a otros hosts (SEC-CON-06): `allow_redirects=False` o solo al mismo host y esquema `https`; TLS validado, sin `verify=False`.
- Usar el host de `Destino` (ya normalizado, B1 de FNC-050) y la lista blanca `CONNECTOR_ALLOWED_HOSTS`; nunca un host de `params`.

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- Solo biblioteca estándar (`http.client` + `ssl`): el venv no tiene `requests` ni `httpx`; así se conecta a la IP validada con SNI y verificación del nombre sin adaptadores ni dependencias nuevas
- Un host que resuelva a **alguna** IP no pública se rechaza (permanente `destino_no_permitido`); sin lista de redes internas permitidas (propuesta FNC-106)
- Esquema de `params` cerrado y plantillas con tres marcas fijas; sin `eval` ni `format`; los `params` se revalidan al ejecutar
- Al otorgar, 409 es permanente salvo que `params` declare `sin_cambios: [409]`; al revocar, 404 y 410 son `sin_cambios` (lo más seguro: no dar por otorgado lo que no se sabe)
- Transitorios: 408, 425, 429, 500, 502, 503, 504; 3xx permanente (nunca se sigue); el detalle es solo `HTTP <estado>` (no se guarda el cuerpo de la respuesta)
- CA: una variable del despliegue (`CONNECTOR_HTTP_CA_FILE`), no por conector (evita rutas de archivo en la BD)
- Se prueban hasta 3 IP validadas si una no conecta (doble pila)
- Autenticación: `bearer`, `basic` (requiere usuario en la credencial) o cabecera propia (nombre no reservado)

## Verificación
- Pruebas nuevas (`tests/connectors/test_destino_seguro.py`, `test_api_http.py`, `test_api_http_proveedor.py`, `test_api_http_tls.py`): 149 pasaron, sin red real (DNS y transporte falsos; el TLS contra un servidor local en loopback con certificado propio)
- Fallaron primero (ImportError) y luego pasaron; además, cada control se rompió a propósito y la prueba lo detectó: IP no públicas permitidas, valor sin codificar en la ruta, `CERT_NONE` y sin `check_hostname`, redirecciones sin bloquear
- Ajustadas 2 pruebas existentes que usaban `api` como tipo sin implementar: ahora `ssh`
- `pytest` completo: 1906 passed, 15 xfailed, salida 0
- No verificado: plataforma real, servidor TLS con CA del sistema, comportamiento de Vaultwarden (FNC-068)
- Sin revisor ni auditor-seguridad (requerido por la ficha: lo lanza el orquestador)

## Impacto en elementos compartidos (`impacto.py`, contra `develop`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas |
|---|---|---|---|---|
| `registrar` | función | `app/modules/connectors/__init__.py` | `app/__init__.py`, `app/modules/access/manejadores.py`, `app/modules/auth/services.py`, `app/modules/connectors/registry.py`, `app/modules/connectors/tipos.py`, `app/modules/provisioning/__init__.py`, `migrations/env.py`, `tests/access/conftest.py` | app, app/modules, migrations, tests/access |
- Cambio real: `registrar` ahora también registra el tipo `api` (siempre); el resto de usos no cambia
- También compartidos, aditivos: `MENSAJES` y 7 motivos nuevos en `provisioning/saneo.py` (los lee `mensaje_de_error`, usado por `ejecucion.py` y la API de ejecuciones FNC-062)
- Visible para quien valide: `PUT /platforms/<id>/connector` con `type: "api"` ahora se acepta (antes `422`); contrato 1.2

## Tareas creadas
- FNC-106: redes internas autorizadas por despliegue (CIDR)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Recomendaciones de auditor-seguridad sobre FNC-050 agregadas (sección «Requisitos de seguridad heredados de FNC-050») |
| 2026-10-21 | Implementada: `api_http.py`, `destino_seguro.py`, `http_transporte.py`, variable `CONNECTOR_HTTP_CA_FILE`, contrato 1.2; En revisión (pendiente revisor y auditor-seguridad) |
