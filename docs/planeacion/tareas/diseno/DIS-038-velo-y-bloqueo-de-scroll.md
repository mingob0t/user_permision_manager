# DIS-038 — Menú móvil y `Modal`: token de velo y bloqueo de desplazamiento

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |

## Contexto
- `MobileMenu` (DIS-025) no tiene velo detrás del panel ni bloquea el desplazamiento del fondo
- El único velo existente es `bg-black/60` en `Modal` (color literal) y el bloqueo usa `document.body.style.overflow` (prohibido `el.style.*`)

## Objetivo
- Token de rol para el velo (p. ej. `--color-scrim`) con valor por tema, usado por `Modal` y `MobileMenu`
- Bloqueo de desplazamiento con clase o atributo en `body` (p. ej. `data-scroll-lock`), sin `el.style`

## Impacto en elementos compartidos
| Elemento | Usado en |
|---|---|
| `Modal`, `MobileMenu`, `tokens.css` | Pantallas con modal y todas las autenticadas |

## Impacto cruzado
- Origen ← DIS-025; relacionada con DIS-031

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-025 |
