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
- `.nexus-checkbox` (`components.css`) dibuja el borde con `--color-panel-border` sobre `--color-input-bg`
- Medido en DIS-019 con la prueba de contraste: falla 3:1 (WCAG 1.4.11) en los 7 temas
- No se agregó el par a `pares-contraste.ts` para no subir las fallas conocidas (25)

## Objetivo
- Borde de la casilla con un token de rol (p. ej. `--color-control-border`) que cumpla 3:1 en cada tema
- Agregar el par `checkbox-borde/input-bg` a la prueba de contraste

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
