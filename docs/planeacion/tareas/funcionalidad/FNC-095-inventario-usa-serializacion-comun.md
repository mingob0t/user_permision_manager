# FNC-095 — Inventario: usar `accesos_publicos` de FNC-058 y retirar la serialización provisional

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Creada** | 2026-10-20 |

## Contexto
- FNC-059 se hizo en paralelo con FNC-058; `access/serializacion.py` (`accesos_publicos`) no estaba en develop.
- FNC-059 dejó la forma `Access` provisional en `access/inventario_serializacion.py` (duplica la de FNC-058).
- Origen: FNC-059.

## Criterios de aceptación
- [x] `access/inventario_api.py` usa `access.serializacion.accesos_publicos` (con `last_job_id`)
- [x] `access/inventario_serializacion.py` eliminado; formato de fecha único en ambos endpoints
- [x] `tests/access/test_inventario.py` en verde

## Impacto cruzado
- Origen ← FNC-059; depende de FNC-058 integrada en develop

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (FNC-059) |
| 2026-10-20 | Hecha: resuelta en FNC-059 |
