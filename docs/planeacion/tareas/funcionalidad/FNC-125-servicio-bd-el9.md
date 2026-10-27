# FNC-125 — Despliegue en RHEL 9: unidades systemd con el servicio real de la base de datos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 6 |
| **Módulo / Área** | deploy |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Rama** | `fnc/FNC-125-servicio-bd-el9` |
| **Creada** | 2026-10-27 |

## Contexto
- Servidor destino: familia RHEL 9 (el9), Python 3.12, Node 24 en `/usr/bin/node`, Redis 6.2.
- `backend.service.tmpl` y `worker.service.tmpl` fijaban `mysql.service` en `After=`/`Wants=`; en el9 es `mysqld.service` (MySQL) o `mariadb.service` (MariaDB): el orden de arranque no se aplicaba.
- Textos y comentarios decían «Rocky Linux 8» aunque los scripts aceptan 9.
- Autorizada por el dueño.
- Ampliación (pedido del orquestador, misma rama): `install.sh` hacía `rsync -a --delete` de `$SRC/` a `$PREFIX/` sin excluir `.env`; con el `.env` solo en el prefijo, lo borraba (y con `.env` en el origen, lo pisaba) y terminaba con «.env no existe».

## Criterios de aceptación
- [x] Plantillas con marcador `@DB_SERVICE@`
- [x] `install.sh` detecta `mysqld.service` → `mariadb.service` → `mysql.service`; sin ninguno, la dependencia se quita de `After=`/`Wants=` sin marcador ni línea vacía
- [x] `--db-service <nombre>` lo fuerza, validado con patrón de nombre de unidad
- [x] `redis.service` sin cambio
- [x] `preflight.sh` informa el servicio detectado
- [x] Textos «Rocky/RHEL 8 o 9»; nota de el9 en `deploy/README.md`
- [x] Pruebas en `tests/deploy/` escritas primero y en rojo
- [x] La copia al prefijo no borra ni pisa el `.env` ni los datos locales; el `.env` del origen se copia una vez si falta; regla en `deploy/README.md`

## Impacto cruzado
- Ninguno (solo `deploy/`, `tests/deploy/` y documentación de operación).

## Cambios
| Archivo | Cambio |
|---|---|
| `deploy/servicio_bd.sh` (nuevo) | `SERVICIOS_BD`, `detectar_servicio_bd` (`systemctl list-unit-files`, sin alias), `servicio_bd_valido`, `aplicar_servicio_bd` (filtro sed) |
| `deploy/copia_proyecto.sh` (nuevo) | `copiar_proyecto` extraída de `install.sh` con `EXCLUIDOS_COPIA` y copia única del `.env` (600) |
| `deploy/backend.service.tmpl`, `deploy/worker.service.tmpl` | `mysql.service` → `@DB_SERVICE@`; comentario de systemd el8/el9 |
| `deploy/install.sh` | `--db-service`/`DB_SERVICE` validado (salida 2), detección antes de renderizar, `render` pasa por `aplicar_servicio_bd`, copia con `copiar_proyecto`; textos Rocky/RHEL 8 o 9 |
| `deploy/preflight.sh` | informa el servicio de BD detectado; el9 pasa de AVISO a OK; sugerencia de Python para el9 |
| `tests/deploy/test_servicio_bd_sh.py` (nuevo) | 37 casos: detección con `systemctl` falso, validación, `install.sh --db-service`, reemplazo en plantillas |
| `tests/deploy/test_copia_proyecto_sh.py` (nuevo) | 6 casos: `.env` del prefijo intacto (con y sin `.env` en origen), locales intactos, sincronía (incl. `docs/logs/`), copia única 600, sin `.env` no crea uno |
| `deploy/README.md` | `.env` en el prefijo, servicio de BD, notas el9, tabla del worker, instalación manual |
| `README.md`, `docs/REQUERIMIENTOS.md`, `docs/operacion/ENTORNOS.md` | Rocky/RHEL 8 o 9; servicio de BD y copia |
| `docs/configuracion/VARIABLES.md`, `HISTORIAL.md` | `DB_SERVICE`, `SERVICIOS_BD`, `EXCLUIDOS_COPIA` |

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- **Funciones en archivos aparte** (`servicio_bd.sh`, `copia_proyecto.sh`), como `secretos.sh`: `install.sh` no se puede cargar sin ejecutarse entero y así se prueban.
- **Alias ignorados.** MariaDB declara `mysqld.service`/`mysql.service` como alias; se usa el nombre real. En systemd 239 (el8) los alias no salen como `alias`: se elegiría `mysqld.service`, que igual resuelve a MariaDB.
- **Sin BD local**: se borra `Wants=` si queda vacía (un `Wants=` vacío vacía la lista en systemd).
- **`--db-service`** acepta el nombre con o sin `.service`; patrón `^[A-Za-z0-9][A-Za-z0-9:_.@-]{0,120}\.service$` (sin `\`, `|`, `/`, `&`, espacios ni saltos). También `DB_SERVICE` por entorno, como `CREATE_USER`.
- **preflight en el9: OK, no AVISO.** Es el destino previsto; la nota de repos se mantiene como texto.
- **Copia**: además de `.env` se protegen `/.env.*` (salvo `.env.example`), `/instance/`, `/backups/`, `/uploads/`, `/storage/`, `/logs/` (los locales de `.gitignore`); anclados para no excluir `docs/logs/`.
- Sin cambios: `redis.service`, `docs/operacion/SECRETOS.md` (systemd 239), ADR-001 y DIAGNOSTICO-INICIAL (fotos históricas).

## Verificación
| Comando | Resultado |
|---|---|
| Pruebas nuevas antes de implementar (`test_servicio_bd_sh.py`) | 24 fallan, 14 pasan (los rechazos de nombres pasan sin script; la parada por root ya existía); salida 1 |
| `test_copia_proyecto_sh.py` contra la copia anterior extraída tal cual | 4 fallan por la causa real (`.env` borrado o pisado, `.env.respaldo` borrado, sin 600), 2 pasan; salida 1 |
| `venv/bin/python -m pytest -p no:cacheprovider --rootdir <wt> <wt>/tests/deploy` | 57 passed; salida 0 |
| `bash -n` de `install.sh`, `preflight.sh`, `servicio_bd.sh`, `copia_proyecto.sh`, `secretos.sh` | salida 0 en los cinco |
| Render de punta a punta (sed de `install.sh` + marcador) con `mariadb.service` y vacío | `After=`/`Wants=` correctos; 0 marcadores `@...@` |
| `validar_proyecto.py` | 0 errores, 1 aviso previo (sin carpeta `logs/`); salida 0 |
| pre-commit | al hacer el commit |

**No verificado:** `install.sh`/`preflight.sh` en un servidor el9 real; `systemd-analyze verify` de las unidades (rutas inexistentes en local); `systemctl list-unit-files` real de el8/el9 con MariaDB y MySQL; shellcheck (no instalado).

**Observaciones fuera de alcance (sin tarea):** el respaldo de Python de `install.sh` usa `dnf module ... python311`, que no existe en el9 (allí es el paquete `python3.11`/`python3.12`); no afecta al destino (trae 3.12). `mariadb-devel` + `mysql` en el9 sin comprobar.

## Impacto en elementos compartidos
`impacto.py`: **ninguno detectado** (contra `develop`; 16 archivos). Configuración compartida por naturaleza:
- Plantillas `backend`/`worker.service.tmpl` e `install.sh`: staging y producción; el orden de arranque cambia de `mysql.service` fijo al servicio real.
- Copia al prefijo: ya no borra lo local del prefijo; un archivo de esas rutas que antes se copiaba del origen (p. ej. `instance/` de desarrollo) deja de copiarse.
- `preflight.sh`: una línea nueva y el9 en OK (un aviso menos).

## Bitácora
- 2026-10-27 — devops: ficha creada; En curso.
- 2026-10-27 — devops: ampliación de la copia al prefijo (`.env`); implementación y verificación; En revisión.
