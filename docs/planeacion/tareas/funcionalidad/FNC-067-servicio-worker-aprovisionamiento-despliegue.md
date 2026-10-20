# FNC-067 — Servicio del worker de aprovisionamiento en el despliegue

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 3 |
| **Módulo / Área** | deploy |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en la rama, sin push |
| **Rama** | `fnc/FNC-067-servicio-worker` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (proceso privilegiado) |

## Contexto
- El despliegue tiene dos unidades systemd (`deploy/backend.service.tmpl`, frontend)
- El worker de FNC-049 necesita su propia unidad y, si ADR-003 elige Redis, que Redis deje de ser opcional y tenga contraseña (SEG-29)
- Requerimientos: F-CON-01, RNF-03

## Objetivo
- Agregar la unidad `<nombre>-worker`, su instalación, arranque, reinicio y registros, y el ajuste de Redis según ADR-003

## Alcance
- **Incluye:**
  - `deploy/worker.service.tmpl` con usuario sin privilegios, `Restart=on-failure` y el mismo `EnvironmentFile`
  - Instalador y `preflight.sh` actualizados
  - Redis obligatorio con contraseña si ADR-003 lo elige
  - `docs/operacion/ENTORNOS.md` y `RELEASES.md` (orden: migrar, reiniciar backend y worker)
- **No incluye:**
  - TLS y cabeceras de nginx (FNC-004)
  - CI (FNC-026)

## Hallazgos de seguridad que absorbe
- **FNC-017** parcial: SEG-29 (contraseña de Redis), solo si ADR-003 elige Redis.

## Archivos previstos
- `deploy/worker.service.tmpl`
- `deploy/install.sh`
- `deploy/preflight.sh`
- `docs/operacion/ENTORNOS.md`
- `docs/operacion/RELEASES.md`

## Archivos modificados
| Archivo | Cambio |
|---|---|
| `deploy/worker.service.tmpl` | Nueva unidad `<nombre>-worker` |
| `deploy/install.sh` | `WORKER_UNIT`; render, chequeo de marcadores, `reset-failed`, `enable --now` y `is-active` del worker; resumen |
| `tests/deploy/preflight_inyeccion.sh` | Prueba de regresión de la inyección y de `REDIS_PASS` vacía |
| `deploy/preflight.sh` | Host y puerto con lista blanca y argumentos posicionales; Redis bloqueante, `REDIS_HOST` sin IP, `REDIS_PASS` con valor; unidad `-worker` en el nombre del despliegue |
| `README.md` | Terminal 3 (worker en dev con `REDIS_*`), sección systemd con el worker, Redis obligatorio |
| `deploy/README.md` | Tabla de servicios, preflight, sección del worker, migraciones con reinicio del worker |
| `docs/operacion/ENTORNOS.md`, `RELEASES.md` | Fila del worker, preflight, instalación y orden migrar → reiniciar backend y worker |
| `docs/configuracion/VARIABLES.md`, `HISTORIAL.md` | `REDIS_PASS` en preflight; parámetros de la unidad |

## Decisiones
Todas son **decisión del orquestador (pendiente de validar en la prueba de concepto)**, modo autónomo autorizado por el dueño, con el valor más seguro de `docs/seguridad/LINEAMIENTOS.md`.

| # | Decisión | Motivo |
|---|---|---|
| D1 | Misma cuenta de servicio (`@SVC_USER@`) que el backend, sin privilegios | El `.env` es 600 de esa cuenta; una cuenta aparte obligaría a abrir permisos de grupo sobre los secretos |
| D2 | `ExecStart=venv/bin/flask --app run:app provisioning worker` | No depende de que `FLASK_APP` esté en el `.env` |
| D3 | `Restart=on-failure`, `RestartSec=30`, `StartLimitIntervalSec=900`, `StartLimitBurst=10`; después `failed` | Backoff con freno compatible con systemd 239 (Rocky 8 no tiene `RestartSteps`/`RestartMaxDelaySec`); una configuración rota no reintenta sin fin. Los trabajos viven en la BD y el barrido los retoma |
| D4 | `KillSignal=SIGTERM`, `KillMode=mixed`, `TimeoutStopSec=630` | Nunca corta un intento: máximo admitido de `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS` (600) + `MARGEN_RESERVA_SEGUNDOS` (30) |
| D5 | Endurecimiento: `NoNewPrivileges`, `CapabilityBoundingSet=` vacío, `UMask=0077`, `PrivateTmp`, `PrivateDevices`, `ProtectSystem=strict`, `ProtectHome`, `ProtectKernelTunables`, `ProtectKernelModules`, `ProtectControlGroups`, `RestrictNamespaces`, `RestrictRealtime`, `LockPersonality`, `SystemCallArchitectures=native`, `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6` | Mínimo privilegio; solo directivas presentes en systemd 239. Sin `MemoryDenyWriteExecute` (puede romper cffi/cryptography). `systemd-analyze security`: 3.5 OK |
| D6 | Sin `ReadWritePaths`: registros a journald | El worker no escribe en disco |
| D7 | `After=`/`Wants=` `network-online.target`, `mysql.service`, `redis.service` | `Wants` de una unidad inexistente es inocuo si Redis o MySQL están en otro host |
| D8 | `install.sh` hace `reset-failed` del worker antes de `enable --now` y falla si no queda activo | Repetir la instalación recupera un worker que agotó reinicios; idempotente |
| D9 | `preflight.sh`: Redis sin respuesta, `REDIS_HOST` con IP o `REDIS_PASS` vacía → `FALTA` (bloqueante) | ADR-003 (Redis obligatorio) y SEG-29/SEC-CFG-08; `REDIS_PASS` solo se comprueba con `grep -q`, nunca se imprime |
| D11 | `preflight.sh`: host `^[A-Za-z0-9.-]+$` y puerto `^[0-9]{1,5}$` en 1–65535 (si no, `FALTA`), y sondeo con `bash -c '</dev/tcp/$1/$2' _ "$h" "$p"` | Hallazgo Media de auditor-seguridad: inyección de comandos como root por `DB_*`/`REDIS_*` interpolados en `bash -c`. `install.sh` no tiene el patrón (revisado: sin `bash -c`, `/dev/tcp` ni `eval`) |
| D12 | Redis en el mismo servidor, solo en loopback, `REDIS_HOST=localhost`; remoto solo como excepción con TLS y aprobación del dueño, hoy **no admitido** (la app no habla TLS con Redis) | SEC-CFG-08 (hallazgo Baja); una conexión en claro expondría `REDIS_PASS` y la cola |
| D13 | `REDIS_PASS=""` y `REDIS_PASS=''` cuentan como vacías | Hallazgo Baja de auditor-seguridad |
| D10 | `REDIS_PASS` sigue saliendo del `.env` del servidor (Vaultwarden `pokemon/<entorno>/REDIS_PASS`) | Sin secretos en la unidad ni en el repositorio |

## Reutilización
- `deploy/backend.service.tmpl` como base

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `deploy/install.sh`, `deploy/preflight.sh` | Scripts de despliegue | Instalación completa del portal (todos los entornos de servidor: staging y producción) | Pendiente (prueba en máquina de prueba) |

Salida de `impacto.py` (contra `develop`):

> **Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 10 archivos cambiados).

Afecta por definición (infra compartida): staging y producción; servicios `<nombre>-backend`, `<nombre>-frontend` (sin cambios en sus unidades) y el nuevo `<nombre>-worker`; flujo de instalación y de release (preflight ahora bloquea sin Redis).

## Variables y configuración
- Las del worker (FNC-049) en la plantilla de entorno del despliegue; `REDIS_PASS` obligatoria si aplica.

## Criterios de aceptación
- [ ] La unidad arranca, reinicia tras un fallo y se detiene ordenadamente en una máquina de prueba (evidencia)
- [x] `preflight.sh` detecta la falta de Redis o de variables del worker (`.env` sintéticos, ver Verificación)
- [ ] Criterios comunes infra (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-049, ADR-003

## Riesgos y reversión
- Reversión: `systemctl disable --now <nombre>-worker`; los trabajos quedan en la BD.
- `install.sh` comprueba `is-active` a los 3 s: con `Type=simple` un fallo posterior (p. ej. Redis rechaza la contraseña) no lo detecta; revisar `journalctl -u <nombre>-worker`.
- `install.sh` repetido no reinicia unidades ya activas (comportamiento previo, también del backend): tras actualizar hay que `systemctl restart` (documentado en RELEASES).
- **Pendiente:** `DEBUG_LDAP=true` escribe un log en el directorio de trabajo; con `ProtectSystem=strict` fallaría (igual que en el backend). Pendiente de decidir: `ReadWritePaths` al directorio de registros o log a journald.
- **Pendiente:** `SystemCallFilter=@system-service` (y `~@privileged @resources`) como endurecimiento adicional, a probar en Rocky 8 en la PoC.
- **Pendiente:** Redis remoto con TLS requiere una tarea de backend (soporte `ssl` en la conexión); se propondría desde FNC-110 si el dueño lo necesita.

## Verificación
| Comando | Resultado |
|---|---|
| `bash -n deploy/install.sh` / `bash -n deploy/preflight.sh` | OK (salida 0) |
| `shellcheck` | No instalado: no verificado |
| Render de `worker.service.tmpl` con los mismos `sed` de `install.sh` + `grep -c "@[A-Z_]*@"` | 0 marcadores sin sustituir |
| `systemd-analyze verify nexus-worker.service` (systemd 255 local) | Salida 0, sin avisos de la unidad (solo avisos de unidades ajenas del sistema) |
| `systemd-analyze security --offline=true` | Exposición 3.5 OK |
| `preflight.sh` con `.env` sintético: Redis en puerto cerrado y `REDIS_PASS` vacía | `FALTA Redis no responde…` y `FALTA REDIS_PASS sin definir…` |
| Ídem con `REDIS_HOST` IP | `FALTA REDIS_HOST debe ser un nombre de host…` |
| Ídem con Redis local accesible y `REDIS_PASS` con valor | `OK Redis accesible…`, `OK REDIS_PASS definida` |
| `bash tests/deploy/preflight_inyeccion.sh` (`.env` sintéticos en `mktemp -d`, nunca el real) | 12 PASA, `Fallos: 0`, salida 0: la carga `localhost/1;touch${IFS}<tmp>;#` en `DB_HOST`, `REDIS_HOST` y `DB_PORT` no crea el archivo y da `FALTA`; `REDIS_PORT=70000` → `FALTA`; `REDIS_PASS=""`/`''`/vacía → `FALTA`; `"sintetica"` → OK. El control confirma que la carga sí ejecuta con el patrón anterior |
| Misma prueba con el `preflight.sh` anterior (`git stash`) | 9 FALLA (la carga crea los archivos): la regresión primero falla |
| `bash -n` tras las correcciones | OK |
| `validar_proyecto.py` | 1 error y 9 avisos, **idénticos a `develop`** (`.gitignore` sin `logs/`, deuda previa); ninguno nuevo |

**No verificado** (entorno dev: sin `install.sh` ni `systemctl`):
- Arranque, reinicio tras fallo y parada ordenada de la unidad en una máquina de prueba (criterio 1).
- Compatibilidad de las directivas con systemd 239 de Rocky 8 (verificado con 255; las elegidas existen desde ≤ 235).
- `RestrictAddressFamilies` con la resolución DNS y el TLS de LDAP/SMTP reales.
- Que `install.sh` completo sea idempotente con el worker (solo revisión del código y `bash -n`).
- `auditor-seguridad`: aprobado (2026-10-20); hallazgos corregidos en esta tarea.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | En curso (modo autónomo, autorizado por el dueño) |
| 2026-10-20 | En revisión: unidad, instalador, preflight y documentación; pendiente prueba en máquina de prueba y auditor-seguridad |
| 2026-10-20 | auditor-seguridad aprobado; corregidos: Media (inyección en `preflight.sh`, D11, prueba `tests/deploy/preflight_inyeccion.sh`), Bajas (Redis en loopback D12, `REDIS_PASS` con comillas vacías D13); pendientes DEBUG_LDAP y `SystemCallFilter` |
