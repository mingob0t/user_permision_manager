# DIS-047 — Limpiar el CSS suelto de `tokens.css` (`.dt-*`, `table.dataTable`, `.animate-shake`)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | estilos |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Rama** | `dis/DIS-047-limpiar-css-suelto-de-tokens-css` |
| **Creada** | 2026-10-27 |

## Contexto
- `tokens.css` mezcla tokens con reglas de componente que nadie usa: `.dt-container`, `.dt-layout-row…`, `table.dataTable tbody tr`, `.animate-shake` y `@keyframes shake` (origen: DIS-009, que solo depuró `components.css` y `global.css`).
- `html, body { background; color }` también está ahí y puede pasar a `global.css`.

## Objetivo
- Borrar lo muerto y dejar `tokens.css` solo con variables; extender `css-sin-uso.test.ts` para cubrirlo.

## Impacto cruzado
- Origen ← DIS-009
