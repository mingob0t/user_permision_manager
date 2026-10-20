# FNC-082 — 409 al borrar plataformas o cuentas con accesos otorgados

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-19 |

## Contexto
- FNC-054: `platform_access_grants.user_id`/`platform_id` sin `ON DELETE`; en MySQL, borrar una plataforma o cuenta con accesos falla por FK (500).
- Origen: FNC-054.

## Criterios de aceptación
- [ ] `DELETE /platforms/<id>` con accesos (vigentes o históricos) → `409` con código de contrato
- [ ] Baja de cuentas con accesos → `409` (o desactivación), según contrato
- [ ] Pruebas con `PRAGMA foreign_keys=ON`

## Impacto cruzado
- Origen ← FNC-054
- Relacionadas → FNC-046, FNC-044

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-19 | Creada como Propuesta (FNC-054) |
