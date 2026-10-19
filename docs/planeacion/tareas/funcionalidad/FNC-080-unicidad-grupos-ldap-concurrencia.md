# FNC-080 — Unicidad de los grupos LDAP de plataformas ante altas concurrentes

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | platforms |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-19 |

## Contexto
- `409 grupo_en_uso` (FNC-046) se comprueba en Python antes del commit (`app/modules/platforms/api.py:116-123`); no hay restricción única.
- Dos altas o ediciones simultáneas con el mismo DN pueden pasar la comprobación (re-auditoría de FNC-046, Baja).
- Datos previos: la migración 0005 no deduplica DN repetidos.

## Criterios de aceptación
- [ ] Tabla de grupos con el DN normalizado y restricción única, o bloqueo alrededor de comprobación y escritura
- [ ] `IntegrityError` → 409 `grupo_en_uso`
- [ ] Revisión de DN duplicados existentes
