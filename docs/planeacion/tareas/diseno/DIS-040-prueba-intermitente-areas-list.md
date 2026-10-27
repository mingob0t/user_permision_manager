# DIS-040 — Prueba intermitente en `areas-list.test.tsx` (409 `rol_no_admin`)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | areas (pruebas) |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Creada** | 2026-10-21 |

## Contexto
- En DIS-019 la suite completa falló 1 vez de 3 en "Administradores del área (superadmin) > 409 rol_no_admin: muestra el mensaje del contrato y recarga"
- `expect(api.users).toHaveBeenCalledTimes(2)` se evalúa justo después de `findByText`, antes de que la recarga ocurra bajo carga
- Sola pasa siempre (3 de 3); en la suite completa, 2 de 3

## Objetivo
- Esperar la recarga con `waitFor` en esa prueba; sin cambios en `areas-list.tsx`

## Causa y solución
- Causa: aviso visible (`findByText`) y recarga `api.users` son asíncronos y no ordenados; `toHaveBeenCalledTimes(2)` inmediato falla bajo carga.
- Mismo patrón en 3 pruebas: `areas-list.test.tsx:187`, `users/directory-account-form.test.tsx:265`, `users/admin-role-dialog.test.tsx:243`.
- Solución: `await waitFor(() => expect(api.users).toHaveBeenCalledTimes(2))`; misma aserción, sin tocar componentes.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): corregir también las dos de `users/` (nota del 2026-10-27) y dejar otras aserciones inmediatas (`jobs-log`, `my-requests-view`, `inventory`, `audit-log`) sin cambios por no haber fallado.

## Verificación
- No se reprodujo la falla antes del cambio (3 corridas limpias); la causa es por análisis del código de las pruebas, no por reproducción.
- Después: 12 corridas completas seguidas con 6 procesos de CPU en paralelo (6 con `--sequence.shuffle`): todas exit 0, 1499/1499.
- typecheck 0, lint 0, vitest 0, build 0. Sin impacto en navegador (solo pruebas).

## Impacto en elementos compartidos
- Ninguno; solo 3 archivos de pruebas.

## Impacto cruzado
- Origen ← DIS-019 (hallazgo fuera de alcance)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-019 |

- 2026-10-27 (auditoría de DIS-033): también falló 1 de 4 corridas completas una prueba de `tests/components/users` (`api.users` esperado 2 veces); pasa sola (72/72). Revisar junto con esta.
| 2026-10-27 | Aprobada en modo autónomo; 3 pruebas con `waitFor`; En revisión |

- 2026-10-27: revisado por el orquestador (solo pruebas, 3 líneas con `waitFor`, misma aserción; 12 corridas seguidas en verde). Sin auditoría de accesibilidad: no hay cambio de interfaz. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
