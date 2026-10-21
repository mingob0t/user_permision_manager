# DIS-011 — Dividir settings-panel.tsx, users-list.tsx y platform-admin.tsx

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-011-dividir-settings-panel-tsx-users-list` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
`settings-panel.tsx` 745 líneas, `users-list.tsx` 581.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-06

## Objetivo
_Se completa al aprobar la tarea._

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** _se precisa al aprobar._

## Criterios de aceptación
- [ ] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [ ] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [ ] Cumple `docs/estandarizacion/` y no duplica código existente
- [ ] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → Después de DIS-010

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |

- 2026-10-21 (auditoría de seguridad DIS-019, Baja, previo): `users-list.tsx:137,233,308,322,457` muestran `err.message` del servidor (editar, buscar en directorio, purgar, eliminar). Al dividir el monolito, pasar a mensajes por código como `admin-role-errors.ts`.
