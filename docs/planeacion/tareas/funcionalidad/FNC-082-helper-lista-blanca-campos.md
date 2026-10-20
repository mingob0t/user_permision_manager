# FNC-082 — Helper común de lista blanca de campos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | api |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-19 |

## Contexto
- La lista blanca (SEC-AUTHZ-09, `400 campo_no_permitido`) se resuelve en cada módulo con su propia función: `campos_no_permitidos` en `users/roles.py` y `users/directory_accounts.py`, y equivalentes en áreas y plataformas.
- Origen: revisión de FNC-064.

## Criterios de aceptación
- [ ] Un helper en `app/modules/api/helpers.py` (campos permitidos → campos rechazados) usado por roles, áreas, directorio y plataformas
- [ ] Sin cambio de comportamiento: las pruebas de lista blanca existentes siguen en verde

## Impacto cruzado
- Origen ← FNC-064
- Relacionadas → FNC-044, FNC-045, FNC-046

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-19 | Creada como Propuesta (revisión de FNC-064) |
