# DIS-036 — Inicio: enlaces que abren la pantalla con el filtro del contador

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | dashboard |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |

## Contexto
- DIS-024 enlaza cada contador a su pantalla, pero ninguna lee parámetros de la URL
- "Mis accesos" abre `/requests` en la pestaña "Mis solicitudes"; "Accesos con falla" abre `/inventory` con el filtro `vigente`

## Objetivo
- `/requests?tab=accesos&status=...`, `/inventory?status=fallido`, `/approvals?status=pendiente`, leídos al montar (solo frontend, sin FNC)

## Impacto cruzado
- Origen ← DIS-024
