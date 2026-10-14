# FNC-057 — Aprobaciones: bandeja por área, aprobar y rechazar con motivo obligatorio

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-057-aprobaciones-bandeja-aprobar-rechazar` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización de otorgamiento) |

## Contexto
- F-SOL-03 pide una bandeja de aprobación por área con rechazo motivado (RF-06)
- Un admin no aprueba solicitudes de áreas que no gestiona (RF-03)
- Requerimientos: F-SOL-03, RF-03, RF-06, F-NOT-01

## Objetivo
- Exponer la bandeja y las decisiones: aprobar crea el acceso (FNC-054) y encola el aprovisionamiento; rechazar exige motivo

## Alcance
- **Incluye:**
  - `GET /access-requests/inbox`: superadmin todas; admin las de plataformas de sus áreas; filtros por estado y área; paginado
  - `POST /access-requests/<id>/approve` y `POST /access-requests/<id>/reject` (motivo obligatorio, longitud mínima)
  - Solo se decide una solicitud `pendiente` (bloqueo para evitar doble decisión)
  - Regla de auto-aprobación según P12 (recomendado: nadie decide su propia solicitud)
  - Avisos `solicitud_aprobada` / `solicitud_rechazada` y auditoría
- **No incluye:**
  - Aprobación en lote (no pedido)
  - Suplentes y escalamiento (fuera de la v1)
  - Pantalla (DIS-015)

## Archivos previstos
- `app/modules/access_requests/approvals.py`
- `app/modules/access_requests/api.py` (rutas de la bandeja)
- `tests/access_requests/test_approvals.py`

## Reutilización
- `grant()` de FNC-054
- Avisos de FNC-048
- `managed_area_ids`, `can_manage_platform`

## Variables y configuración
- `ACCESS_REQUEST_REJECTION_MIN_LENGTH` (constante registrada).

## Criterios de aceptación
- [ ] Un admin de otra área recibe 403 al aprobar (prueba)
- [ ] Rechazo sin motivo responde 400 (prueba)
- [ ] Dos aprobaciones simultáneas producen un solo acceso (prueba)
- [ ] Aprobar crea el acceso `en_proceso` y el trabajo (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-015
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-056, FNC-054, FNC-048, Respuesta a P12
- Contrato → docs/contratos/solicitudes.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
