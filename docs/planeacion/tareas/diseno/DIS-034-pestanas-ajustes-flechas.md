# DIS-034 — Pestañas de Ajustes sin navegación con flechas

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | ajustes |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Creada** | 2026-10-20 |

## Contexto
- auditor-accesibilidad (revisión de DIS-014): las pestañas de `settings-panel.tsx` no tienen *roving tabindex* ni ←/→/Inicio/Fin, ni `aria-controls`/`tabpanel`, ni 48 px de alto
- DIS-014 ya lo resuelve en `access/my-requests-view.tsx` (`destinoPorTecla`)

## Objetivo
- Mismo comportamiento de pestañas que DIS-014 en Ajustes; idealmente un componente de pestañas compartido

## Impacto cruzado
- Origen ← DIS-014

## Resolución
- Hecha junto con DIS-023 (rama `dis/DIS-023-ajustes-directorio`): `settings-panel.tsx` importa `destinoPorTecla`; pestañas con *roving tabindex*, ←/→/Inicio/Fin, `aria-controls`, `tabpanel` enfocable y `min-h-12`
- Sin componente de pestañas común (queda para DIS-011). Decisión del orquestador (pendiente de validar en la prueba de concepto)
- Verificación: prueba Vitest en `tests/components/settings/directory-tab.test.tsx`; visual no verificada

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (DIS-014) |
| 2026-10-26 | Aprobada (modo autónomo) e implementada dentro de DIS-023. En revisión |
