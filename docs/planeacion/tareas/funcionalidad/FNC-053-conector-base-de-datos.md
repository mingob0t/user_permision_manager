# FNC-053 — Conector tipo base de datos

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
| **Estatus Git** | `fnc/FNC-053-conector-bd` (commit local, sin push) |
| **Rama** | `fnc/FNC-053-conector-bd` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (ejecución remota con credenciales) |

## Contexto
- Tipo de conector BD de F-CON-01
- Qué plataformas lo usan primero lo decide el dueño (pregunta P9); sin una plataforma piloto la tarea no se aprueba
- Requerimientos: F-CON-01

## Objetivo
- Implementar el tipo BD sobre la interfaz de FNC-050: Sentencias parametrizadas predefinidas por plataforma (sin SQL libre) para crear o desactivar la cuenta en la BD de la plataforma; motores admitidos según P9

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
- `app/modules/connectors/base_de_datos.py`, `bd_sentencias.py`, `bd_motores.py`, `bd_configuracion.py` (el repo no usa `types/`; la guía va en `docs/backend/README.md`)
- `tests/connectors/test_base_de_datos.py`

## Reutilización
- Interfaz, registro y credenciales de FNC-050

## Variables y configuración
- `CONNECTOR_DB_TIMEOUT_SECONDS` y `CONNECTOR_DB_CA_FILE`; controladores PyMySQL y psycopg2 (ya instalados). Registradas en VARIABLES, HISTORIAL y `.env.example` (sin valores secretos).

## Integración (lineamiento técnico 11)
- Llamadas salientes a la plataforma; no aplica webhook ni polling

## Criterios de aceptación
- [x] Otorgar y revocar contra el servidor simulado (pruebas; SQLite como doble)
- [x] Entrada maliciosa (comillas, `;`, saltos de línea) no altera la operación (prueba de inyección)
- [x] Verificación de TLS o de llave de host obligatoria (prueba con drivers simulados; sin servidor TLS real)
- [x] Declarado no verificado contra plataforma real: no hay plataforma piloto (P9) ni servidor MySQL/PostgreSQL de prueba
- [x] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-050, Respuesta del dueño a P9 (plataforma piloto)

## Riesgos y reversión
- Cada plataforma tiene su API o esquema: el tipo es genérico y lo específico va en parámetros.
- Reversión: desregistrar el tipo.

## Requisitos de seguridad heredados de FNC-050 (auditor-seguridad)
- Resolver el DNS del host antes de conectar y rechazar si resuelve a una IP privada, de loopback, *link-local* o no enrutable (DNS *rebinding*); conectar a la IP ya validada, no volver a resolver.
- No seguir redirecciones a otros hosts (SEC-CON-06 por analogía): sin *failover* ni réplicas que el servidor anuncie fuera de la lista blanca; TLS validado (SEC-CON-05).
- Usar el host de `Destino` (ya normalizado, B1 de FNC-050) y la lista blanca `CONNECTOR_ALLOWED_HOSTS`; nunca un host de `params`.

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- Motores: `mysql` (MySQL y MariaDB, PyMySQL 1.1.0 ya fijado) y `postgresql` (psycopg2-binary ya instalado; barato porque libpq conecta a `hostaddr` y verifica el nombre con `sslmode=verify-full`). Se fijó `psycopg2-binary==2.9.13` (la del venv). Sin otros motores
- Sin SQL libre: sentencias fijas en `params` con `%s`, una por operación, y marcas `correo`/`nivel`/`plataforma`; se rechaza `;`, comentarios, comillas, `\`, `$`, `?`, otro `%`, palabras de DDL/permisos/archivos/espera y `UPDATE`/`DELETE` sin `WHERE` (lo más seguro; el usuario de BD con permisos mínimos es la defensa de fondo)
- TLS obligatorio y verificado en **todos** los entornos (también dev), sin opción para apagarlo: más estricto que lo pedido («fuera de dev»); en dev ya se rechazan IP privadas, así que una BD local sin TLS tampoco era alcanzable
- Conexión a la IP validada con verificación del nombre: MySQL con socket propio + contexto TLS (`connect(sock)`, `host` = nombre); PostgreSQL con `hostaddr` + `host`, `verify-full` y `gssencmode=disable` (GSS no verifica el certificado)
- CA: variable del despliegue `CONNECTOR_DB_CA_FILE`, no por conector. Tiempo: `CONNECTOR_DB_TIMEOUT_SECONDS` (conectar y consultar; el doble < tiempo del intento)
- `max_filas` (1 por defecto, hasta 10): más filas afectadas se deshacen con `bd_filas_excesivas` (permanente); 0 filas → `sin_cambios`. Un duplicado no es `sin_cambios` automático: la sentencia debe ser idempotente (`ON DUPLICATE KEY UPDATE` / `ON CONFLICT DO NOTHING`)
- Errores del driver: solo un código en el detalle (`MySQL n`, `SQLSTATE xxxxx`); autenticación y certificado permanentes (no reintentar credenciales malas); bloqueos, interbloqueos, red y tiempo agotado transitorios; error de sentencia permanente; falla al confirmar transitoria
- Otra IP solo si falla la red antes de enviar (`ErrorConexion`); después no se reintenta
- Se reutilizan `_valores_seguros` y `_con_control` de `api_http.py` importándolos (sin tocar FNC-051); moverlos a un módulo común: FNC-115

## Correcciones de la auditoría de seguridad (aprobada con 1 hallazgo medio)
- Media: PyMySQL activa TLS solo si el servidor lo anuncia; si no, sigue sin cifrar y sin error. Ahora `MotorMysql.conectar` comprueba `conexion._secure` tras `connect` y, si no está cifrada, cierra y aborta como `tls_no_valido` (permanente) sin operar. Regresión: 2 pruebas fallaron antes (`test_mysql_servidor_que_no_anuncia_tls_se_aborta`, `test_conector_no_opera_si_el_servidor_no_ofrece_tls`); `_secure` es atributo interno del driver (versión fijada 1.1.0): revisar al actualizar PyMySQL. PostgreSQL ya falla con `verify-full` si el servidor no ofrece TLS
- Endurecimiento futuro (no hecho): la lista negra de `bd_sentencias.py` no cubre `WITH` (CTE) ni `SET` de sesión dentro de la sentencia; considerar una lista blanca de forma (p. ej. `INSERT INTO <tabla> (<columnas>) VALUES (%s…)`, `DELETE FROM <tabla> WHERE <col> = %s`, `SELECT … FROM <tabla> WHERE <col> = %s`) en lugar de palabras prohibidas. Mientras, la defensa de fondo es el usuario de BD con permisos mínimos

## Verificación
- `tests/connectors/test_base_de_datos.py`: 119 pruebas pasaron, sin red real (SQLite en memoria como doble con el marcador `%s`, DNS falso y drivers PyMySQL/psycopg2 simulados con sus excepciones reales)
- Cobertura: otorgar/revocar/consultar e idempotencia; inyección (comillas, `;`, `--`, `\`, `%s`, saltos de línea; la tabla sigue viva y el dato se guarda literal); validación de sentencias y de `params`; IP privada y DNS; reintento en otra IP; credencial incompleta; rollback y cierre; `max_filas`; clasificación MySQL y PostgreSQL; certificado en la cadena de causas; argumentos TLS de cada driver (`CERT_REQUIRED`, `check_hostname`, `verify-full`, `hostaddr`, IP en `create_connection`); configuración
- Controles rotos a propósito y detectados: sin `rollback` por exceso de filas, `sslmode=require`, `;` permitido, consulta que confirma
- `pytest` completo: 2123 passed, 15 xfailed, salida 0 antes de la corrección de la auditoría; tras ella 2126 passed, 15 xfailed, salida 0 (una corrida previa tuvo 1 fallo: `test_tipo_sin_implementar_o_desconocido` usaba `bd` como tipo sin implementar; ajustada a `ssh`, `otro`, `None`)
- No verificado: contra MySQL o PostgreSQL reales (handshake TLS real, `statement_timeout`, códigos de error reales); `crear_contexto` con CA propia contra un servidor de base de datos; plataforma piloto (P9)
- Sin revisor ni auditor-seguridad (requerido por la ficha: lo lanza el orquestador)

## Impacto en elementos compartidos (`impacto.py`, contra `develop`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas |
|---|---|---|---|---|
| `registrar` | función | `app/modules/connectors/__init__.py` | `app/__init__.py`, `app/modules/access/manejadores.py`, `app/modules/auth/services.py`, `app/modules/connectors/registry.py`, `app/modules/connectors/tipos.py`, `app/modules/provisioning/__init__.py`, `app/modules/secretos/vaultwarden.py`, `migrations/env.py` (+1) | app, app/modules, migrations, tests/access |
- Cambio real: `registrar` ahora también registra el tipo `bd` (siempre) y valida `CONNECTOR_DB_*` al arrancar; el resto de usos no cambia
- También compartidos, aditivos: `MENSAJES` y 4 motivos nuevos en `provisioning/saneo.py` (los lee `mensaje_de_error`, usado por `ejecucion.py` y la API de ejecuciones FNC-062); `requirements.txt` (versión fijada de `psycopg2-binary`)
- Conflictos probables con FNC-052 (`wt-060`): `connectors/__init__.py`, `saneo.py`, `.env.example`, `VARIABLES.md`, `HISTORIAL.md`, contrato, README y catálogo: todos aditivos
- Visible para quien valide: `PUT /platforms/<id>/connector` con `type: "bd"` ahora se acepta (antes `422`); contrato 1.3

## Tareas creadas
- FNC-115: mover `_valores_seguros` y `_con_control` a un módulo común de conectores (hoy en `api_http.py`; los usan `api` y `bd`, y `ssh` lo necesitará)
- FNC-116: probar el conector `bd` contra MySQL y PostgreSQL reales con TLS (servidor de pruebas o plataforma piloto, P9)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Recomendaciones de auditor-seguridad sobre FNC-050 agregadas (sección «Requisitos de seguridad heredados de FNC-050») |
| 2026-10-21 | Implementada: tipo `bd` (MySQL/MariaDB y PostgreSQL), sentencias parametrizadas, TLS verificado a la IP validada, 119 pruebas; contrato 1.3; En revisión |
| 2026-10-21 | Auditor-seguridad: aprobada con un hallazgo medio (MySQL sin TLS si el servidor no lo anuncia) corregido con regresión; endurecimiento de sentencias anotado |
