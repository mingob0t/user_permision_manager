# FNC-124 — Hallazgos de `validar_proyecto.py`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 6 |
| **Módulo / Área** | operacion |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Rama** | `fnc/FNC-124-hallazgos-validar-proyecto` |
| **Creada** | 2026-10-27 |

## Contexto
Salida de `~/.claude/agentes/herramientas/validar_proyecto.py` durante FNC-035 (ya existían en `develop`):

| Tipo | Hallazgo |
|---|---|
| Error | `.gitignore` no ignora `logs/` |
| Aviso | `NODE_ENV` y `TZ` se usan en el código y no están en `.env.example` ni en `VARIABLES.md` |
| Aviso | `deploy/install.sh`: dirección de loopback literal en la lista `no_proxy` por defecto (usar nombre de host) |

## Criterios de aceptación
- [ ] `validar_proyecto.py` sin errores ni esos avisos
- [ ] Variables registradas en `VARIABLES.md` y `.env.example`

## Impacto cruzado
- Origen ← FNC-035
