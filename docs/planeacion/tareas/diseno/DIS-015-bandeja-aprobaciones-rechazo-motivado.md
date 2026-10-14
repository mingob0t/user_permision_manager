# DIS-015 — Bandeja de aprobaciones con rechazo motivado

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | aprobaciones |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-015-bandeja-aprobaciones-rechazo-motivado` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- F-SOL-03 pide una bandeja por área para aprobar o rechazar con motivo obligatorio (RF-06)
- Requerimientos: F-SOL-03, RF-03, RF-06

## Objetivo
- Pantalla `/approvals`: pendientes de las áreas del admin (todas para el superadmin) con solicitante, plataforma, nivel, justificación y fecha; aprobar con confirmación y rechazar con motivo obligatorio

## Alcance
- **Incluye:**
  - Filtros por estado y área
  - Detalle de la justificación (texto escapado)
  - Diálogo de rechazo con motivo obligatorio y validación visible
  - Confirmación de aprobación
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Aprobación en lote
  - Historial de la solicitud (DIS-020)

## Archivos previstos
- `frontend/src/components/access/approvals-inbox.tsx`
- `frontend/src/components/access/reject-dialog.tsx`
- `frontend/src/app/approvals/page.tsx`

## Reutilización
- `ConfirmDialog`, `Modal`, `TextArea` de `form.tsx`
- `usePolling`

## Criterios de aceptación
- [ ] Rechazar sin motivo no habilita el envío y lo explica
- [ ] Tras decidir, la fila sale de pendientes
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-071, FNC-057
- Contrato → docs/contratos/solicitudes.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
