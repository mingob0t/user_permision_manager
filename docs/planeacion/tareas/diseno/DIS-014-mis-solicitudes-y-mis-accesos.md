# DIS-014 — Mis solicitudes y mis accesos

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-014-mis-solicitudes-y-mis-accesos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- No hay pantalla para que el usuario vea sus solicitudes ni sus accesos (F-SOL-02, pantallas "Mis solicitudes" e "Inicio")
- Requerimientos: F-SOL-02, F-ACC-02 (vista del usuario)

## Objetivo
- Pantalla `/requests` con dos pestañas: solicitudes (estado, nivel, fecha, motivo de rechazo) y accesos (plataforma, nivel, desde, estado del aprovisionamiento)

## Alcance
- **Incluye:**
  - Lista paginada de solicitudes con estado y motivo de rechazo visible
  - Lista de accesos con estado `en_proceso`/`activo`/`fallido` explicado en lenguaje claro
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Cancelar solicitudes (no pedido)
  - Revocar desde el usuario (no pedido)

## Archivos previstos
- `frontend/src/components/access/my-requests.tsx`
- `frontend/src/components/access/my-access.tsx`
- `frontend/src/app/requests/page.tsx`

## Reutilización
- `access-status-badge.tsx` (DIS-013)
- `Card`, `Badge`, estados de `ui.tsx`
- `usePolling`

## Criterios de aceptación
- [ ] Tabla responsive (en móvil se presenta como lista)
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-071, FNC-056, FNC-058, DIS-013
- Contrato → docs/contratos/solicitudes.md y accesos.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
