# DIS-053 — Formularios de plataforma y portal: «Color de texto» ya no se usa en la interfaz

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Rama** | `dis/DIS-053-color-de-texto-sin-uso` |
| **Creada** | 2026-10-27 |

## Contexto
- Tras DIS-048 el ícono de plataforma calcula el texto (claro u oscuro) según `bg_color` e ignora `text_color`.
- `platform-form.tsx` (≈214-224) sigue pidiendo «Color de texto», y la pestaña Portal de Ajustes (`settings/portal-tab.tsx`) pide fondo y texto aunque ninguna vista los pinta.
- El usuario elige un valor que no tiene efecto visible.

## Objetivo (a decidir por el dueño)
- Opción A: retirar «Color de texto» de los formularios (el campo sigue en la API sin uso) o mostrar una nota «se calcula automáticamente».
- Opción B: decidir dónde se usan los colores del portal y aplicarlos con contraste garantizado.

## Impacto cruzado
- Origen ← FNC-033, DIS-048
- Si se retira el campo de la API: tarea FNC backend vinculada.
