# DIS-018 — Usuarios y accesos: accesos de un usuario y revocación

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Alta |
| **Estatus** | En curso |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local |
| **Rama** | `dis/DIS-018-accesos-usuario-revocacion` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- En `/users` (`users-list.tsx`, 581 líneas) se asignan plataformas a mano; no se ven accesos con nivel ni se puede revocar (F-ACC-02)
- Requerimientos: F-ACC-02, RF-03

## Objetivo
- Panel de accesos de un usuario (plataforma, nivel, origen, desde, quién aprobó, estado, última ejecución) con revocación confirmada (motivo según P7), dentro del alcance del admin

## Alcance
- **Incluye:**
  - Componente `user-access-panel.tsx` abierto desde la fila del usuario
  - Revocar con diálogo de confirmación
  - Estado del aprovisionamiento y error saneado
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Alta en directorio y elevación (DIS-019)
  - Dividir `users-list.tsx` (DIS-011)

## Archivos previstos
- `frontend/src/components/users/user-access-panel.tsx`
- `frontend/src/components/users-list.tsx` (acción que abre el panel; retiro de la asignación directa si FNC-065 se aprueba)

## Reutilización
- `Modal`, `ConfirmDialog`, `access-status-badge.tsx`, `usePolling`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `users-list.tsx` | Pantalla | `/users` | Pendiente |

## Criterios de aceptación
- [ ] Un admin no ve botones de revocar en accesos de áreas ajenas
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-071, FNC-058, DIS-013
- Contrato → docs/contratos/accesos.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada por el orquestador (modo autónomo) y En curso en el worktree `pokemon-wt-d023` |
