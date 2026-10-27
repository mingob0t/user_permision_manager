# DIS-040 — Prueba intermitente en `areas-list.test.tsx` (409 `rol_no_admin`)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | areas (pruebas) |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |

## Contexto
- En DIS-019 la suite completa falló 1 vez de 3 en "Administradores del área (superadmin) > 409 rol_no_admin: muestra el mensaje del contrato y recarga"
- `expect(api.users).toHaveBeenCalledTimes(2)` se evalúa justo después de `findByText`, antes de que la recarga ocurra bajo carga
- Sola pasa siempre (3 de 3); en la suite completa, 2 de 3

## Objetivo
- Esperar la recarga con `waitFor` en esa prueba; sin cambios en `areas-list.tsx`

## Impacto cruzado
- Origen ← DIS-019 (hallazgo fuera de alcance)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-019 |

- 2026-10-27 (auditoría de DIS-033): también falló 1 de 4 corridas completas una prueba de `tests/components/users` (`api.users` esperado 2 veces); pasa sola (72/72). Revisar junto con esta.
