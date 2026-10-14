# FNC-065 — Retirar la asignación directa de plataformas (`user_platforms`) y migrarla a accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-065-retirar-user-platforms-migrar-accesos` |
| **Requiere migración BD** | Sí (datos de `user_platforms` a `platform_access_grants`) |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- `PUT /platforms/<id>/users` y `PUT /users/<id>/platforms` (`crud.py:212`, `:352`) asignan plataformas sin solicitud, sin nivel y sin escribir en LDAP, lo que contradice que otorgar sea agregar al grupo (RF-02). **Tarea condicionada a la respuesta P4.**
- Requerimientos: RF-02, F-ACC-01

## Objetivo
- Si P4 lo aprueba: migrar cada fila de `user_platforms` a un acceso de origen `heredado` (nivel según P4, sin escribir en LDAP), retirar los dos endpoints y marcar la tabla como obsoleta

## Alcance
- **Incluye:**
  - Migración de datos idempotente
  - Retiro de los dos endpoints y de `user_ids` en `Platform.to_dict`
  - Documentación de la tabla obsoleta
- **No incluye:**
  - Borrar la tabla (otra tarea, tras un periodo)
  - Pantallas (las asignaciones desaparecen de DIS-017/DIS-018)

## Archivos previstos
- Migración (ADR-002)
- `app/modules/api/crud.py` (retiro de dos rutas)
- `app/modules/core/models.py` (`to_dict`)
- `tests/access/`

## Reutilización
- Modelo de FNC-054

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `PUT /platforms/<id>/users`, `PUT /users/<id>/platforms` | Endpoints retirados | `platform-admin.tsx`, `users-list.tsx`, `lib/api.ts` | Pendiente |
| `Platform.to_dict` | Serialización | Catálogo, favoritos, administración | Pendiente |

## Criterios de aceptación
- [ ] Conteo de filas migradas igual al de `user_platforms` (prueba de migración)
- [ ] Los endpoints retirados responden 404 o 410 (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-063, Respuesta a P4

## Riesgos y reversión
- El frontend aún llama a los endpoints retirados hasta DIS-017/DIS-018: integrar en el mismo bloque.
- Reversión: bajar la migración de datos.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
