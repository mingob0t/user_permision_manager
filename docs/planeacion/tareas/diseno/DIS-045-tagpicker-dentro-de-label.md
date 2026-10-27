# DIS-045 — Usuarios: chips de `TagPicker` dentro del `<label>` de `Field`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |

## Contexto
- En `users-list.tsx` (`UserForm`), "Áreas a las que pertenece" y "Plataformas asignadas" son `Field` (un `<label>`) que envuelve los botones de `TagPicker`
- El `<label>` nombra al primer control etiquetable que contiene: el primer chip ("Finanzas" en la prueba) se anuncia como "Áreas a las que pertenece", no con su nombre
- Comprobado con Testing Library (jsdom) en DIS-008; no verificado con lector de pantalla

## Objetivo
- Grupo con `fieldset`/`legend` visible (patrón de `AreaChecklist`) o `role="group"` con `aria-labelledby`, sin `<label>` alrededor de botones

## Impacto cruzado
- Origen ← DIS-008
