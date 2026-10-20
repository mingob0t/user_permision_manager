# DIS-032 — Texto de 10–11 px en `.nx-badge` y `.nexus-btn`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | estilos |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- auditor-accesibilidad (revisión de DIS-013): `.nx-badge` y `.nexus-btn` de `frontend/src/styles/components.css` usan texto de 10–11 px, por debajo del mínimo de 12 px
- Clases compartidas: insignias y botones de todas las pantallas

## Objetivo
- Llevar el texto a >= 12 px con un token de tamaño, sin romper la simetría de botones e insignias

## Impacto cruzado
- Origen ← DIS-013
- Relacionada con DIS-007
