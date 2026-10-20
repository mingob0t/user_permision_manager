# FNC-084 — Revocar los accesos de una cuenta al desactivarla

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- FNC-055 revoca los accesos automáticos al quitar el área o el rol, pero `PUT /users/<id>` con `is_active=false` (`api/crud.py`, `update_user`) no revoca nada: la cuenta inactiva sigue en los grupos LDAP.
- Origen: FNC-055.

## Criterios de aceptación
- [ ] Desactivar una cuenta revoca sus accesos `activo` (automáticos y por solicitud) en la misma transacción, con auditoría `sistema`
- [ ] Los `en_proceso` se revocan al confirmarse (como `area_admin_sync.revocar_si_ya_no_administra`)
- [ ] Reactivar no devuelve accesos por solicitud; decidir si devuelve los automáticos
- [ ] Pruebas

## Impacto cruzado
- Origen ← FNC-055
- Relacionadas → FNC-008 (revocación de sesión al desactivar), FNC-054

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (FNC-055) |
