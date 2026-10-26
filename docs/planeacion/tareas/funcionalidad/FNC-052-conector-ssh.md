# FNC-052 — Conector tipo SSH

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
| **Estatus Git** | Rama local `fnc/FNC-052-conector-ssh` (sin push) |
| **Rama** | `fnc/FNC-052-conector-ssh` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (ejecución remota con credenciales) |

## Contexto
- Tipo de conector SSH de F-CON-01
- Qué plataformas lo usan primero lo decide el dueño (pregunta P9); sin una plataforma piloto la tarea no se aprueba
- Requerimientos: F-CON-01

## Objetivo
- Implementar el tipo SSH sobre la interfaz de FNC-050: Ejecución de comandos predefinidos por plataforma (lista cerrada, sin interpolar texto libre en el *shell*; argumentos escapados) con llave o contraseña tomada de la credencial y verificación obligatoria de la llave del host (`known_hosts` por conector)

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
- `app/modules/connectors/ssh.py` y `ssh_transporte.py` (el proyecto usa archivos planos como `api_http.py`, no `types/`)
- `tests/connectors/`
- `docs/backend/README.md` (la guía vive ahí; no existe `conectores.md`)

## Reutilización
- Interfaz, registro y credenciales de FNC-050; `destino_seguro.py`, motivos de saneo y reglas de valores del conector `api` (FNC-051). Catálogo: `03-reutilizacion.md`.

## Decisiones (modo autónomo: del orquestador, pendientes de validar en la prueba de concepto)
| Tema | Decisión | Motivo |
|---|---|---|
| Técnica contra la inyección | **Comando fijo** (lista de argumentos de la configuración, lista blanca `[A-Za-z0-9_./=:+-]`, ruta absoluta sin `..`, armado con `shlex.quote`) **sin datos de la solicitud**; los datos van por **stdin como una línea JSON** (`json.dumps`, ASCII). En el servidor se recomienda un comando forzado (`command=` + `restrict` en `authorized_keys`) | Es la más segura: no hay valor variable que un shell o analizador de argumentos pueda interpretar; `shlex.quote` con argumentos validados dejaba una superficie (el valor llega a un shell remoto) que aquí no existe. El comando forzado del lado remoto lo decide quien administra la plataforma; el cliente es seguro con o sin él |
| Llave del host | `params.huellas` (1–5 `SHA256:`) o `CONNECTOR_SSH_KNOWN_HOSTS_FILE`; sin ninguna, no conecta; se verifica **antes** de enviar la credencial; no hay confianza en el primer uso | SEC-CON-04; las huellas permiten rotar la llave (varias) sin tocar el despliegue |
| Librería | `paramiko==5.1.0`, con `Transport` (no `SSHClient`) | Sin `AutoAddPolicy`, `ssh_config`, `ProxyCommand` ni agente por construcción; `asyncssh` obliga a un bucle asíncrono que el ejecutor RQ no usa |
| Autenticación | Llave privada de la credencial (por defecto); contraseña solo si `params.auth.metodo = contrasena`. Llaves con frase de paso: no (FNC-110) | La llave se puede restringir en el servidor (`restrict`, comando forzado); la contraseña queda para plataformas que no admiten llave |
| Algoritmos | `ssh-rsa` (SHA-1) y `ssh-dss` desactivados (huella y autenticación) | Débiles; RSA con SHA-2 sigue permitido |
| Salida remota | Se cuenta y se descarta (≤ `CONNECTOR_SSH_MAX_OUTPUT_BYTES`); solo sale el código (`salida <n>`) | Nunca se guarda texto del servidor remoto |
| Códigos de salida | 0 éxito; `sin_cambios`/`ausente` y `transitorios` (por defecto `[75]`, EX_TEMPFAIL) declarados por operación; un cierre sin código es transitorio; el resto, permanente | No reintentar a ciegas un rechazo; sin código, lo más probable es corte de red |
| Reintento en otra IP | Solo si falla la conexión o el saludo (antes de autenticar), máximo 3 | Tras enviar la credencial o el comando no se duplica la escritura |
| Cambios fuera de la ficha | `saneo.py` (5 motivos, aditivo), `configuracion.py` (3 variables con valores por defecto; validación al arrancar) y 3 pruebas existentes que usaban `ssh` como «tipo sin implementar» (ahora `bd`) | Necesarios para el catálogo de motivos, la validación al arrancar y porque `ssh` ya está implementado. FNC-068 toca `saneo.py`: cambio aditivo en el bloque de motivos |

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `requirements.txt` (`paramiko==5.1.0`) | Dependencias | Backend completo (instalación) | Pendiente |
| `configuracion.cargar_configuracion` / `ConfiguracionConectores` | Utilidad | `provider.py`, `validacion.py`, `credenciales.py`, `api_http.py`; cambio aditivo (3 campos con valor por defecto) | Pendiente |
| `connectors.registrar` | Función | `create_app()`, migraciones, pruebas: ahora registra también el tipo `ssh` | Pendiente |
| `saneo.MENSAJES` | Catálogo | Bitácora de ejecuciones (todos los proveedores): 5 motivos nuevos, sin cambiar los existentes | Pendiente |

Salida de `~/.claude/agentes/herramientas/impacto.py` (comparado contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `cargar_configuracion` | función | `app/modules/connectors/configuracion.py` | `credenciales.py`, `provider.py`, `validacion.py`, `directory/*` (homónimo), `platforms/grupos.py`, `provisioning/cli.py` (+19) | app/modules, tests (access, connectors, directory, platforms, provisioning) | ☐ |
| `registrar` | función | `app/modules/connectors/__init__.py` | `app/__init__.py`, `access/manejadores.py`, `auth/services.py`, `provisioning/__init__.py`, `migrations/env.py`, `tests/access/conftest.py` | app, app/modules, migrations, tests/access | ☐ |

## Variables y configuración
- `CONNECTOR_SSH_TIMEOUT_SECONDS` (30), `CONNECTOR_SSH_MAX_OUTPUT_BYTES` (4096), `CONNECTOR_SSH_KNOWN_HOSTS_FILE` (vacía): registradas en `VARIABLES.md`, `HISTORIAL.md` y `.env.example` (sin valores secretos); se validan al arrancar.
- Dependencia: `paramiko==5.1.0` (`requirements.txt`).

## Integración (lineamiento técnico 11)
- Llamadas salientes a la plataforma; no aplica webhook ni polling

## Criterios de aceptación
- [x] Otorgar y revocar contra el servidor simulado (pruebas)
- [x] Entrada maliciosa (comillas, `;`, saltos de línea) no altera la operación (prueba de inyección)
- [x] Verificación de TLS o de llave de host obligatoria (prueba)
- [x] Probado contra la plataforma piloto en dev, con evidencia, o declarado no verificado con motivo: **no verificado**, P9 sin plataforma piloto; sí contra un servidor SSH real en loopback
- [x] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-050, Respuesta del dueño a P9 (plataforma piloto)

## Riesgos y reversión
- Cada plataforma tiene su API o esquema: el tipo es genérico y lo específico va en parámetros.
- Reversión: desregistrar el tipo.

## Requisitos de seguridad heredados de FNC-050 (auditor-seguridad)
- Resolver el DNS del host antes de conectar y rechazar si resuelve a una IP privada, de loopback, *link-local* o no enrutable (DNS *rebinding*); conectar a la IP ya validada, no volver a resolver.
- No seguir redirecciones ni saltos a otros hosts (SEC-CON-06 por analogía): sin `ProxyJump`/`ProxyCommand` ni reenvío de agente; `known_hosts` fijo (SEC-CON-04).
- Usar el host de `Destino` (ya normalizado, B1 de FNC-050) y la lista blanca `CONNECTOR_ALLOWED_HOSTS`; nunca un host de `params`.

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest tests/connectors/test_ssh.py tests/connectors/test_ssh_transporte.py -q` | 106 passed, salida 0 |
| Mutaciones (cada una rompió pruebas y se restauró): huella siempre válida (4 fallan), sin chequeo de caracteres de control (4), comando con dato añadido (13), huella como transitoria (2), salida excesiva como transitoria (1) | Detectadas |
| `venv/bin/python -m pytest -q` (completo) | 2019 passed, 15 xfailed, salida 0 (897 s) |
- Servidor de prueba: `tests/connectors/servidor_ssh_falso.py` (paramiko real en `127.0.0.1`, puerto efímero): huella correcta, distinta y por `known_hosts`; llave autorizada y no autorizada; contraseña; comando exacto y datos por stdin con entrada maliciosa; límite de salida; tiempo de ejecución; puerto cerrado.
- **No verificado:** contra una plataforma piloto real (P9); algoritmos de servidores antiguos que solo ofrezcan `ssh-rsa`; llaves con frase de paso (no soportadas, FNC-110); el comando forzado del lado remoto (lo configura quien administra la plataforma); `revisor` y `auditor-seguridad` (no lanzados por indicación del orquestador; la ficha exige `auditor-seguridad`).
- El destino con IP privada se rechaza (`destino_no_permitido`), como en `api`: plataformas internas dependen de FNC-106.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Recomendaciones de auditor-seguridad sobre FNC-050 agregadas (sección «Requisitos de seguridad heredados de FNC-050») |
| 2026-10-21 | En curso: tipo `ssh` (`ssh.py`, `ssh_transporte.py`), variables, motivos, contrato 1.3 y guía |
| 2026-10-21 | En revisión: pruebas verdes, impacto registrado; pendiente `auditor-seguridad` y validación del dueño. Propone FNC-110 (llave con frase de paso) |
