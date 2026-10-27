# FNC-127 — Instalador: puertos de backend y frontend configurables

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 6 |
| **Módulo / Área** | deploy |
| **Prioridad** | Alta (urgente) |
| **Estatus** | En revisión |
| **Rama** | `fnc/FNC-127-puerto-web-configurable` |
| **Creada** | 2026-10-27 |

## Contexto
- El servidor del dueño tiene Grafana en el 3000; las plantillas fijaban 3000 (frontend) y 5001 (backend).
- Autorizada por el dueño. Ajuste del dueño (vía orquestador): los puertos también en `<prefijo>/.env`.

## Criterios de aceptación
- [x] Plantillas con `@WEB_PORT@`/`@API_PORT@`; bind siempre en `127.0.0.1`
- [x] `install.sh --web-port`/`--api-port`, también `WEB_PORT`/`API_PORT` por entorno y en `<prefijo>/.env`; por defecto 3000/5001
- [x] Precedencia: opción > entorno > `.env` > defecto
- [x] Enteros 1024-65535 y distintos; opción/entorno validados antes de root (salida 2), `.env` al leerlo (después de `asegurar_env_prefijo`)
- [x] `.env` sin `source`: solo `grep -E '^CLAVE='`; no imprime nada más
- [x] `preflight.sh` toma los puertos del entorno o del `.env`
- [x] Mensajes finales con los puertos reales
- [x] README, `.env.example`, VARIABLES, HISTORIAL; `PORT_APP` aclarada (solo desarrollo)
- [x] Pruebas en `tests/deploy/` escritas primero y en rojo

## Impacto cruzado
- Ninguno fuera de `deploy/`, `tests/deploy/`, `.env.example` y documentación.

## Cambios
| Archivo | Cambio |
|---|---|
| `deploy/puertos.sh` (nuevo) | Defectos, `puerto_servicio_valido`, `puerto_de_env` (grep, sin enlaces), `resolver_puerto`, `aplicar_puertos` |
| `deploy/frontend.service.tmpl` | `PORT=@WEB_PORT@`; `BACKEND_URL=http://localhost:@API_PORT@` |
| `deploy/backend.service.tmpl` | `--bind 127.0.0.1:@API_PORT@` |
| `deploy/nginx.conf.tmpl` | upstreams con `@API_PORT@`/`@WEB_PORT@` |
| `deploy/install.sh` | opciones, validación temprana, lectura del `.env` tras `asegurar_env_prefijo`, `render` con `aplicar_puertos`, resumen, ayuda |
| `deploy/preflight.sh` | entorno > `.env` > defecto; valida rango e igualdad |
| `deploy/README.md` | sección «Puertos del backend y del frontend» (caso Grafana) |
| `.env.example` | `WEB_PORT`/`API_PORT` comentadas; nota de `PORT_APP` |
| `docs/configuracion/VARIABLES.md`, `HISTORIAL.md` | `WEB_PORT`, `API_PORT`; `PORT_APP` solo desarrollo |
| `tests/deploy/test_puertos_sh.py` (nuevo) | 33 casos: render real sin marcadores, mismo puerto en nginx y unidades, rechazos, `.env`, precedencia, enlace |

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- **Funciones en `deploy/puertos.sh`**, como `servicio_bd.sh`: se prueban sin ejecutar `install.sh`; preflight usa la misma lógica.
- **Mínimo 1024**: los servicios no corren como root; un puerto privilegiado no arrancaría.
- **`BACKEND_URL` en la unidad del frontend**: el SSR de Next llama a Flask con `BACKEND_URL` (por defecto `localhost:5001`); sin él, con otro `--api-port` el SSR fallaría. Mismo host (`localhost`) que el defecto previo, sin cambio de comportamiento con 5001.
- **`.env` enlace**: `puerto_de_env` no lo lee (preflight); en install ya lo rechaza `asegurar_env_prefijo`.
- **Valor del `.env` inválido**: install se detiene (`die`); preflight lo marca FALTA.
- Sin cambio: `run.py` (desarrollo) ni `BACKEND_URL_POR_DEFECTO` del frontend.

## Verificación
| Comando | Resultado |
|---|---|
| `pytest tests/deploy/test_puertos_sh.py` antes de implementar | 12 fallan, 21 pasan (rechazos pasan sin script; parada por root ya existía); salida 1 |
| `pytest tests/deploy` (venv de wt-054) | 105 passed; salida 0 |
| `bash -n deploy/*.sh` | 0 en los seis |
| `preflight.sh` con `.env` sintético (`WEB_PORT=3100`, `API_PORT=5101`; luego `WEB_PORT=3200` por entorno; luego `WEB_PORT=80`) | usa 3100/5101; el entorno gana (3200); 80 → FALTA |
| `validar_proyecto.py` | 0 errores, 2 avisos previos (`logs/`, `PATH`) |
| `impacto.py` | ninguno detectado |

**No verificado:** instalación real en el servidor (systemd, nginx, SSR con otro `API_PORT`); `shellcheck` no está instalado.

## Impacto en elementos compartidos
**Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 11 archivos cambiados).

Configuración de despliegue (compartida por definición): afecta a staging y producción; con los valores por defecto el resultado es el mismo que antes.

## Bitácora
- 2026-10-27: creada y aprobada (dueño, urgente). Implementada; ajuste del `.env` incorporado. En revisión.
