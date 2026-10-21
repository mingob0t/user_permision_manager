# DIS-034 — Pestañas de Ajustes sin navegación con flechas

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | ajustes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- auditor-accesibilidad (revisión de DIS-014): las pestañas de `settings-panel.tsx` no tienen *roving tabindex* ni ←/→/Inicio/Fin, ni `aria-controls`/`tabpanel`, ni 48 px de alto
- DIS-014 ya lo resuelve en `access/my-requests-view.tsx` (`destinoPorTecla`)

## Objetivo
- Mismo comportamiento de pestañas que DIS-014 en Ajustes; idealmente un componente de pestañas compartido

## Impacto cruzado
- Origen ← DIS-014
