# FNC-130 — Instalador: endurecimientos pendientes

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Fase** | 5 |
| **Módulo / Área** | despliegue |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |

## Contexto (observaciones de `auditor-seguridad` en FNC-129)
| Id | Observación | Corrección propuesta |
|---|---|---|
| O-1 | `pip install` y `npm ci`/`build` corren como root: un `postinstall` o `setup.py` malicioso de una dependencia correría como root | Compilar con un usuario de build sin privilegios y luego `chown` a root, o `npm ci --ignore-scripts` si el build lo permite |
| O-2 | El `chown -R -h` de datos y logdir depende de `fs.protected_hardlinks=1` | Comprobarlo en `preflight.sh` |
| O-3 | Sin `--force`, `--logdir` no se limita a `/var/log/` y recibe `chown -R` | Misma regla que con `--force` |

## Impacto cruzado
- Origen ← FNC-129
