# FNC-067 — Servicio del worker de aprovisionamiento en el despliegue

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 3 |
| **Módulo / Área** | deploy |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-067-servicio-worker-aprovisionamiento-despliegue` |
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

## Reutilización
- `deploy/backend.service.tmpl` como base

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `deploy/install.sh`, `deploy/preflight.sh` | Scripts de despliegue | Instalación completa del portal | Pendiente |

## Variables y configuración
- Las del worker (FNC-049) en la plantilla de entorno del despliegue; `REDIS_PASS` obligatoria si aplica.

## Criterios de aceptación
- [ ] La unidad arranca, reinicia tras un fallo y se detiene ordenadamente en una máquina de prueba (evidencia)
- [ ] `preflight.sh` detecta la falta de Redis o de variables del worker
- [ ] Criterios comunes infra (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-049, ADR-003

## Riesgos y reversión
- Reversión: deshabilitar la unidad.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
