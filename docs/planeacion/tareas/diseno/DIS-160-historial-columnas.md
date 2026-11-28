# DIS-160 — Historial de solicitudes: columnas Nivel, Justificación y Fecha

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Depende de** | FNC-216 (`motivos` en `GET /auth/context`) |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (pedido del dueño) |

## Cambios
- `access/approvals-inbox-columns.tsx`: sin columna Nivel; Estado solo con insignias; columna Fecha nueva (`Dos`: «Enviada: …» y, si aplica, «Decidida: … por …»).
- `access/approvals-inbox.tsx`: Justificación visible solo si `motivos.solicitud` ≠ `oculto` (`SOLICITUD_MOTIVO`); mientras carga, sin `motivos` o con error, oculta (mismo valor por omisión que el backend). Se retira la constante `MOSTRAR_JUSTIFICACION`.
- `lib/types.ts`: `AuthContext.motivos`.
- Orden: Solicitante, Plataforma, Estado, Fecha, [Justificación], [Motivo del rechazo], Acciones.

## Decisiones
- La columna Motivo del rechazo no cambia (no se pidió): sigue apareciendo si hay rechazadas con motivo.
- El valor se lee del backend (`/auth/context`); la web nunca lee `.env`.

## Impacto en elementos compartidos
- `AuthContext` (tipo): campo opcional nuevo; `login-form.tsx` no cambia.
- `columnasBandeja`: solo la usa el Historial.
