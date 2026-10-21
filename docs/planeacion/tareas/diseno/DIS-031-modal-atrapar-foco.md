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
- Foco inicial en el primer campo del diálogo (hoy va al panel) (auditor-accesibilidad, DIS-013)
- `Modal` acepta `describedBy` (`aria-describedby` del `role="dialog"`), para ligar el texto que explica la acción, p. ej. la confirmación de aprobar (auditor-accesibilidad, DIS-015)
- `describedBy` también para los diálogos de rol de Usuarios (`AdminAreasDialog`, `RemoveAdminDialog`): ligar el texto del efecto (áreas, permisos, accesos automáticos) (auditor-accesibilidad, DIS-019)
- El efecto de `Modal` depende de `onClose` y re-enfoca el panel si cambia: enfocar solo al montar (DIS-019 lo evita con `useCallback` en `users-list.tsx`)

## Impacto en elementos compartidos
| Elemento | Usado en |
|---|---|
| `Modal`, `ConfirmDialog` | `areas-list`, `users-list`, `platform-admin`, `notifications-list`, `settings-panel`, `access/request-form-modal` |

## Impacto cruzado
- Origen ← DIS-013

## Bitácora
| Fecha | Nota |
|---|---|

| 2026-10-20 | DIS-015 (auditor-accesibilidad): agregar `describedBy` a `Modal` |
| 2026-10-21 | DIS-019 (auditor-accesibilidad): `describedBy` para los diálogos de rol y foco inicial solo al montar |
