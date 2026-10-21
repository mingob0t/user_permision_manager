# FNC-078 — Lista blanca completa de campos en POST/PUT /users (SEC-AUTHZ-09) e is_active

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios-roles |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-15 |

## Contexto
- FNC-044 rechaza `managed_area_ids`, `auth_source` y `password_hash`, pero `POST/PUT /users` aún aceptan campos desconocidos sin error.
- `is_active` figura en la lista de rechazo del README de contratos, pero la pantalla lo usa en `PUT /users/<id>`: hay que decidir y versionar.
- Origen: revisión de FNC-044.

## Criterios de aceptación
- [ ] Campos desconocidos → `400 campo_no_permitido` en `POST/PUT /users`
- [ ] Regla de `is_active` decidida, en el contrato y con prueba
- [ ] Cliente web adaptado por tarea vinculada (FNC-069)

## Nota (auditoría de seguridad de FNC-051, 2026-10-21)
- La validación del formato del correo en `POST /users` (`crud.py:84-111`) es anterior a FNC-051 y no cubre todo (p. ej. `..` o valores sin `@` podían llegar a un conector); FNC-051 se protege en el conector (`valor_no_valido`)
- Al aplicar la lista blanca de `/users`, endurecer esa validación del correo aquí; no se crea otra tarea

## Impacto cruzado
- Origen ← FNC-044
- Relacionadas → FNC-069, FNC-077

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-15 | Creada como Propuesta (revisión de FNC-044) |
| 2026-10-21 | Nota de la auditoría de FNC-051 sobre la validación del correo en `POST /users` |
