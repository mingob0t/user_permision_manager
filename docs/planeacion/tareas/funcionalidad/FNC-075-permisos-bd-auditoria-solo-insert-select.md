# FNC-075 — Permisos de BD solo INSERT/SELECT sobre audit_logs

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 3 |
| **Módulo / Área** | auditoria |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-14 |

## Contexto
- FNC-047 hace la auditoría inmutable desde el ORM; el SQL crudo no se intercepta (SEC-AUD-03).
- Pendiente de aprobación del dueño. Origen: revisión de FNC-047.

## Criterios de aceptación
- [ ] El usuario de BD de la app solo tiene INSERT y SELECT sobre `audit_logs` en staging y prod
- [ ] Las migraciones usan otra cuenta (SEC-CFG-09); verificar que `ON DELETE SET NULL` sigue funcionando con estos permisos
- [ ] Documentado en `docs/operacion/`
