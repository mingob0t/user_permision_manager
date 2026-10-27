# FNC-118 — Web: retirar el rewrite de `/auth/:path*` en `next.config.ts`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | frontend |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-26 |
| **Requiere auditor-seguridad** | No |

## Contexto
`frontend/next.config.ts:18` reenvía `/auth/:path*` al backend en desarrollo. Desde FNC-027 el backend no tiene rutas `/auth` (responderían 404). Ninguna llamada del frontend las usa: todo va a `/api/v1/auth/*`.

## Alcance
- **Incluye:** quitar el `rewrite` y actualizar su comentario.
- **No incluye:** nada más del frontend.

## Impacto cruzado
- Origen ← FNC-027

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-26 | Creada como Propuesta desde FNC-027 |
