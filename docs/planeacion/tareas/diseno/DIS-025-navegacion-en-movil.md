# DIS-025 — Navegación en móvil

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | navegacion |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-19 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-025-navegacion-en-movil` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El menú lateral de `app-shell.tsx` está oculto bajo `md` (`hidden md:block`) sin alternativa (deuda 8 del frontend)
- Con FNC-070 el menú tiene 13 entradas por rol; en móvil no hay forma de navegar

## Objetivo
- Menú accesible en móvil que reutilice `NAV` y `meetsRequirement` (mismas entradas por rol)

## Alcance
- **Incluye:** botón de menú en la cabecera bajo `md` con panel de navegación, foco y cierre con teclado
- **No incluye:** cambiar entradas ni permisos del menú

## Archivos previstos
- `frontend/src/components/app-shell.tsx`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `AppShell` | Layout | Todas las páginas autenticadas | Pendiente |

## Criterios de aceptación
- [ ] Bajo `md` se navega a todas las entradas del rol
- [ ] Criterios comunes web (FNC-037)

## Impacto cruzado
- Origen ← FNC-070 (revisión)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-19 | Creada como Propuesta desde la revisión de FNC-070 |
| 2026-10-19 | DIS-001 (captura de `/platforms` a 390 px con Chrome sin interfaz): el contenido se corta a la derecha (buscador y tarjetas); no viene de los tokens, sin investigar la causa |
