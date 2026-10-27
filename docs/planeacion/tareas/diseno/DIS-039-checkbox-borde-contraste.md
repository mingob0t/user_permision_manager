# DIS-039 — `Checkbox`: borde de la casilla sin marcar con contraste 3:1

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |

## Contexto
- `.nexus-checkbox` (`components.css`) dibuja el borde con `--color-panel-border`; el fondo con el que linda es el panel (`--color-panel-fill`, también en `.nx-modal-glass`)
- Medido por auditor-accesibilidad en DIS-019: 1,42–2,02:1 según el tema, falla 3:1 (WCAG 1.4.11) en los 7 temas
- No se agregó el par a `pares-contraste.ts` para no subir las fallas conocidas (25)

## Objetivo
- Borde de la casilla con un token de rol (p. ej. `--color-control-border`) que cumpla 3:1 en cada tema
- Agregar el par `checkbox-borde/panel` (`--color-panel-border` sobre `--color-panel-fill`) a la prueba de contraste

## Impacto en elementos compartidos
| Elemento | Usado en |
|---|---|
| `.nexus-checkbox`, `Checkbox` (`form.tsx`), `tokens.css` | `/users`, `/areas`, `/admin/platforms`, `/settings`, `/login` |

## Impacto cruzado
- Origen ← DIS-019

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-019 |
| 2026-10-21 | Valor medido real (1,42–2,02:1) y fondo correcto (`--color-panel-fill`) según auditor-accesibilidad |
| 2026-10-26 | DIS-006 sube `--color-panel-border` a 3:1 contra panel y fondo en los 7 temas (par `panel-border/panel`: 3,06–3,39) y agrega `.nexus-checkbox:focus-visible`. Se propone cerrar esta tarea como resuelta por DIS-006 tras la validación del dueño |
