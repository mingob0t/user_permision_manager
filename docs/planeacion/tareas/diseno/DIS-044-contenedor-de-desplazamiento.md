# DIS-044 — Verificar qué contenedor se desplaza con `html, body { overflow: hidden }`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-26 |

## Contexto
- `global.css` (heredado) pone `overflow: hidden` en `html` y `body`; `AppShell` usa `min-h-screen` sin contenedor con `overflow-y-auto`
- DIS-038 bloquea el desplazamiento con la clase `html.scroll-bloqueado` (`html` y `body`), igual que antes hacía `Modal` con `body.style`; su efecto visible depende de qué elemento se desplaza

## Objetivo
- Comprobar en navegador (móvil y escritorio) si las páginas largas se desplazan y con qué elemento
- Si es otro contenedor, que `scroll-bloqueado` lo cubra; si no se desplaza nada, corregir el marco con el dueño

## Impacto cruzado
- Origen ← DIS-038

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-26 | Creada como Propuesta desde DIS-038 |
