# FNC-129 — Instalador en sitio: sin copia y nombre por defecto desde la carpeta

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Fase** | 6 |
| **Módulo / Área** | deploy |
| **Prioridad** | Alta (urgente: el dueño está instalando) |
| **Estatus** | Hecha |
| **Rama** | `fnc/FNC-129-instalar-en-sitio` |
| **Creada** | 2026-10-27 |

## Origen (decisión del dueño, 2026-10-27)
- Clona el repo en `/opt/portal` y corre `./deploy/install.sh` ahí: el instalador solo instala dependencias y usa ese código, sin copiar.
- Incidente: sin `--name`, el defecto `nexus` (herencia de NEXUS) llevó a `/opt/nexus` y copió ahí el código y el `.env`.
- Ampliación (mismo día): `--force`/`--reinstall` para limpiar una instalación previa del mismo nombre a medias, con confirmación.

## Criterios
- [x] `PREFIX` = raíz del repo (`realpath` del padre de `deploy/`); sin `copiar_proyecto` ni rsync.
- [x] `--prefix` (y `--prefix=`) → salida 2: «…clona el repositorio donde quieras instalarlo».
- [x] Nombre por defecto = carpeta, con la regla de `--name`; inválido → salida 2 pidiendo `--name`. `nexus` ya no es defecto.
- [x] `.env`: `asegurar_env_prefijo` (sin enlaces, `O_NOFOLLOW`, 600), `chown -R -h`; si falta, se detiene pidiendo crearlo desde `.env.example`.
- [x] `copia_proyecto.sh` y sus pruebas de copia retirados; `asegurar_env_prefijo` y sus pruebas de enlace en `env_seguro.sh` / `test_env_seguro_sh.py`.
- [x] `preflight.sh`: nombre por defecto desde la carpeta (`APP_NAME` por entorno manda).
- [x] `--force`/`--reinstall`: lista + confirmación escribiendo el nombre en TTY; sin TTY o respuesta distinta, aborta sin tocar nada; sin `--force` no pregunta.
- [x] `--force` borra solo: unidades `<nombre>-*` (stop/disable, archivos, `daemon-reload`), `<nombre>.conf` de nginx, `venv/`, `frontend/node_modules/`, `frontend/.next/`, logdir. Nunca `.env`, código, `.git`, BD, Redis, cuenta, `instance/`, `backups/`, `uploads/`, `storage/`.
- [x] Documentación: `deploy/README.md`, `ENTORNOS.md`, VARIABLES/HISTORIAL.

## Decisiones (del orquestador, pendientes de validar en la prueba de concepto)
- Regla del nombre en `deploy/nombre_despliegue.sh` (`NOMBRE_DESPLIEGUE_REGEX`), compartida por install y preflight: antes estaba duplicada.
- Con `--force`, `--logdir` debe terminar en `/<nombre>` y no cruzarse con el prefijo; si no, aborta sin borrar.
- `--force` aborta si el prefijo o `frontend/` pasan por un enlace, o si el logdir es un enlace; un enlace dentro de lo borrado se quita sin seguirlo.
- La confirmación va antes de cualquier cambio (antes del proxy y los paquetes).
- `SYSTEMD_DIR` y `NGINX_CONF_DIR` como constantes con nombre (antes literales; mismo valor).
- Tras instalar, la carpeta es de la cuenta de servicio: `git pull` con esa cuenta (documentado). Relación con FNC-126 (prefijo de root), sin cambio aquí.

## Corrección de auditor-seguridad (Bloqueante en `6c0d70d`)
Decisión del orquestador; adelanta parte de FNC-126.
| Hallazgo | Corrección |
|---|---|
| SEG-1 (Alta) `chown -R` del prefijo: la cuenta de servicio editaba `install.sh`/plantillas y el siguiente `sudo install.sh` corría su código como root | Sin `chown` del prefijo; `codigo_protegido` (inline en `install.sh`, antes de cargar ningún `deploy/*.sh`) exige código y carpetas superiores de root sin escritura de grupo/otros, con mensaje `chown -R root:root` + `chmod -R go-w`; `umask 022`; `venv`/`npm ci`/`build` como root; `entregar_datos_a_servicio` (`deploy/propiedad.sh`) solo para `DATOS_SERVICIO` existentes y logdir; `.env` `root:<grupo>` 640 |
| SEG-2 (Baja) carrera entre validar `frontend` y el `rm` | `_borrar_validado`: revalida antes de cada `rm` (carpeta sin enlaces), `rm -rf --one-file-system` |
| SEG-3 (Baja) logdir arbitrario con `--force` | Debe estar bajo `LOGDIR_BASE` (`/var/log`) y terminar en `/<nombre>` |

- Next: las unidades ya tenían `ProtectSystem=strict` sin `ReadWritePaths` en el prefijo, así que en ejecución nunca escribió en `.next`; sin cambio.
- `.env` 640: `EnvironmentFile=` lo lee systemd (root); `load_dotenv()` de `app/__init__.py` lo lee como la cuenta, por el grupo.
- Clon del dueño (`sudo git clone` en `/opt/portal`): simulado con `git clone --no-local` y `umask 022` → la comprobación pasa (0 rutas con escritura de grupo/otros). Un clon local con enlaces duros puede heredar 664 en `.git/objects/info/packs`: el mensaje indica la corrección.

## Cambios
| Archivo | Cambio |
|---|---|
| `deploy/install.sh` | En sitio; `--prefix` rechazado; nombre desde la carpeta; `--force`/`--reinstall`; resumen sin `nexus` fijo |
| `deploy/preflight.sh` | `APP_NAME` por defecto desde la carpeta; prefijo mostrado = carpeta |
| `deploy/nombre_despliegue.sh` (nuevo) | `nombre_despliegue_valido`, `nombre_por_defecto` |
| `deploy/env_seguro.sh` (nuevo) | `asegurar_env_prefijo` movida de `copia_proyecto.sh`; mensaje de `.env` ausente pide `.env.example` |
| `deploy/reinstalar.sh` (nuevo) | `reinstalar_limpio` (validación, lista, confirmación TTY, limpieza); revalidación antes de cada `rm`; logdir bajo `LOGDIR_BASE` |
| `deploy/propiedad.sh` (nuevo, SEG-1) | `entregar_datos_a_servicio` |
| `deploy/worker.service.tmpl` | Comentario del `.env` (640) |
| `tests/deploy/test_propiedad_codigo.py` (nuevo, SEG-1) | Código de root, sin `chown` del prefijo, artefactos de root, datos y logdir de la cuenta |
| `deploy/copia_proyecto.sh` | Retirado |
| `tests/deploy/test_instalar_en_sitio.py` (nuevo) | Nombre, `--prefix`, sin copia, preflight |
| `tests/deploy/test_env_seguro_sh.py` (nuevo) | Pruebas de enlace movidas + `.env` ausente pide `.env.example` |
| `tests/deploy/test_reinstalar_sh.py` (nuevo) | `--force` con `systemctl` falso, raíz temporal y pty |
| `tests/deploy/test_copia_proyecto_sh.py` | Retirado (pruebas de copia; las de enlace se movieron) |
| `deploy/README.md`, `docs/operacion/ENTORNOS.md` | En sitio, `--force`, sin `/opt/nexus` ni `nexus-*` |
| `docs/configuracion/VARIABLES.md`, `HISTORIAL.md` | `APP_NAME`, baja `EXCLUIDOS_COPIA`/`--prefix`, alta de constantes |

## Verificación
| Comando | Resultado |
|---|---|
| Pruebas nuevas antes de implementar | 27 failed, 17 passed (las 17 pasaban por ausencia del script: validación negativa); salida 1 |
| `pytest tests/deploy` (venv de wt-054) | 136 passed; salida 0 |
| `bash -n` de `deploy/*.sh` y `tests/deploy/preflight_inyeccion.sh` | 0 en los 9 |
| `bash deploy/install.sh --prefix /opt/x` | mensaje esperado; salida 2 |
| `bash deploy/install.sh --force </dev/null` (sin root) | se detiene en root; salida 1 |
| `bash deploy/preflight.sh` (sección nombre) | `APP_NAME=pokemon-wt-d023`, prefijo = carpeta |
| `impacto.py` | ninguno detectado |
| Corrección SEG-1..3: pruebas nuevas antes de corregir | 21 failed, 135 passed; salida 1 |
| Corrección SEG-1..3: `pytest tests/deploy` | 156 passed; salida 0 |
| Corrección SEG-1..3: `bash -n` de `deploy/*.sh` y `preflight_inyeccion.sh` | 0 en los 10 |

**No verificado:** instalación real como root en RHEL (paquetes, systemd, nginx, `npm ci` como root, servicios leyendo el `.env` 640 por el grupo), `--force` sobre un servidor real, y `codigo_protegido` con uid 0 real (probado con el uid de la prueba); `shellcheck` no está instalado.

## Impacto en elementos compartidos
**Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 14 archivos cambiados).
- Tras la corrección SEG-1..3, `impacto.py` lista `_limpiar`, `_nombre`, `raiz`, `test_nombre_valido` y `test_nombre_invalido`: son funciones locales de las pruebas de `tests/deploy/` que coinciden **solo por nombre** con otras del proyecto; no se importan ni se comparten (falso positivo, nada que validar).
- Afecta el flujo de instalación de staging y producción (`install.sh`, `preflight.sh`). Quien instalaba con `--prefix` debe clonar en la carpeta destino.
- `tests/deploy/test_puertos_sh.py` ejecuta `install.sh` desde la carpeta del repo: si esa carpeta tiene un nombre inválido (mayúsculas, espacios), las pruebas que esperan pasar la validación saldrían con 2.

## Bitácora
- 2026-10-27: creada y aprobada por el dueño (urgente). Implementada en sitio + `--force` (ampliación del dueño el mismo día). Pendiente: `revisor` y `auditor-seguridad` (toca borrado de rutas y permisos del `.env`).
- 2026-10-27: `auditor-seguridad` Bloqueante en `6c0d70d` (SEG-1 Alta, SEG-2 y SEG-3 Bajas); corregidos en esta rama. Pendiente: nueva pasada de `auditor-seguridad`.

- 2026-10-27: `auditor-seguridad`: Bloqueante en `6c0d70d` (SEG-1 Alta: root ejecutaba código escribible por la cuenta de servicio; SEG-2 y SEG-3 Bajas) y Aprobado con observaciones en `32cf722` (código de root, datos y logdir de la cuenta, `.env` root:grupo 640, revalidación en `--force`, logdir bajo `/var/log`). Observaciones O-1 a O-3 registradas como FNC-130 (fase 5). Pendiente: instalación real en el servidor del dueño. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
