# FNC-219 — Pendientes por plataforma en el resumen de Solicitudes

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Finalizada** | 2026-11-28 |
| **Rama** | `fnc/FNC-219-pendientes-por-plataforma` |

## Contexto
- Pedido del dueño: Gestión > área > plataformas muestra «Solicitudes pendientes» por plataforma. Vinculada: DIS-161 (web).

## Cambios
- `access_requests/resumen.py`: `_por_plataforma` (extraído de `by_platform`, que conserva su forma) y campo `pending_by_platform` `{platform_id, platform, area_id, area, count}`, solo `pendiente`, `count > 0`, mismo orden y alcance de `approvals.bandeja`.
- Contrato `solicitudes.md` 1.6 (coordinar con FNC-218: quien integre segundo toma 1.7).

## Pruebas
- Suite completa: 3739 passed, salida 0.
- `tests/access_requests/test_resumen.py`: 3 nuevas (solo pendientes y orden, alcance del admin de área, superadmin todas) y la de vacío con la clave nueva; fallaban sin el cambio.
- Nota: dos `GET inbox/stats` con distintos usuarios en una misma prueba devuelven el resultado del primero. Causa (orquestador, 2026-11-28): la fixture `app` deja un `app_context` abierto; Flask 3.0 lo reutiliza en cada petición y Flask-Login guarda el usuario en `g`. Solo pasa en pruebas: en producción cada petición abre su propio contexto. No es fuga entre usuarios.

## Impacto en elementos compartidos
- `impacto.py` marca `resumen` (resumen.py); los «usos» son coincidencias por nombre con otras funciones `resumen`. Real: solo se agrega un campo a `inbox/stats` (consumidores: Solicitudes y, con DIS-161, Gestión).
