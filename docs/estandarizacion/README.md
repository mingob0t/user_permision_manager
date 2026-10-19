# Estandarización

Estándares visuales, de comportamiento y catálogo de reutilización de este proyecto. Especifican los lineamientos
generales (`~/.claude/agentes/LINEAMIENTOS.md`): tokens, breakpoints, componentes y patrones concretos.

| Documento | Contenido |
|---|---|
| 01-visual.md | Tokens (claro/oscuro), tipografía, breakpoints, componentes |
| 02-comportamiento.md | Interacción de la interfaz y contrato de la API |
| 03-reutilizacion.md | Catálogo de componentes y utilidades compartidas |

## Regla: color de marca como texto (DIS-001)
- `--color-primary`, `brand`, `accent`, `accent-sky`, `accent-peach`: solo rellenos, bordes y tintes.
- Texto: `--color-<rol>-text` (`text-primary-text`…), definido en los 7 contextos de `tokens.css` a >= 4.5:1.
- Texto sobre relleno de marca: `--color-on-primary` sobre `--color-primary-solid`.
- Token nuevo: un valor en cada contexto y su par en `frontend/tests/accesibilidad/pares-contraste.ts`.
