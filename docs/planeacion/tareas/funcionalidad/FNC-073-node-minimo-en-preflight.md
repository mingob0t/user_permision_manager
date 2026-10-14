# FNC-073 — Alinear la versión mínima de Node en el despliegue

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 6 |
| **Módulo / Área** | deploy |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |

## Contexto
- `deploy/preflight.sh:19,128` acepta Node 18 o mayor.
- Desde FNC-025, vitest 4 y jsdom 29 piden Node 20.19+ o 22.13+; con versiones menores `npm ci` avisa `EBADENGINE`.

## Criterios de aceptación
- [ ] `preflight.sh` y la documentación de entornos exigen la misma versión mínima que `package.json`
