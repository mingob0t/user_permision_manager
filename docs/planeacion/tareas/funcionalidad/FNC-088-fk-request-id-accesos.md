# FNC-088 — FK de `platform_access_grants.request_id` hacia `platform_access_requests`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- FNC-054 dejó `request_id` sin FK hasta que existiera la tabla de solicitudes; FNC-056 la crea (migración 0008) sin tocar `app/modules/access`.
- Origen: FNC-056.

## Criterios de aceptación
- [ ] Migración que agrega la FK (sin `ON DELETE`) y el modelo alineado (`test_migraciones` en verde)
- [ ] Prueba: un acceso por solicitud con `request_id` inexistente falla en la BD

## Impacto cruzado
- Origen ← FNC-056
