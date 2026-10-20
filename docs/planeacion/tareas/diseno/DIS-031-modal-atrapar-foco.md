# DIS-031 — `Modal`: atrapar el foco con Tab y devolverlo al cerrar

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- `Modal` (`form.tsx`) enfoca el panel al abrir y cierra con Escape, pero Tab sale del diálogo y el foco no vuelve al disparador
- DIS-013 devuelve el foco desde la pantalla; las demás pantallas con modal (áreas, usuarios, plataformas, notificaciones) no

## Objetivo
- Ciclo de foco dentro del diálogo y foco de regreso al elemento que lo abrió, en el componente compartido

## Impacto en elementos compartidos
| Elemento | Usado en |
|---|---|
| `Modal`, `ConfirmDialog` | `areas-list`, `users-list`, `platform-admin`, `notifications-list`, `settings-panel`, `access/request-form-modal` |

## Impacto cruzado
- Origen ← DIS-013
