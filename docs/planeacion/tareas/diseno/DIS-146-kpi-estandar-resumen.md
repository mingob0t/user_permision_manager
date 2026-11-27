# DIS-146 — Estandarizar las 4 KPI del Resumen de Solicitudes

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (aprobada por pedido directo del dueño) |

## Contexto
- Pedido inicial: mostrar «2 usuarios · 12 administradores» en la tarjeta Usuarios. Cambio de alcance del dueño: las 4 KPI del Resumen usan el diseño de «Solicitudes por estado» (`DonaKpi`).

## Cambios
- `access/dona-conectores.tsx` (nuevo): «Conectores», filas Asociados / Sin asociar (`desglose.connectors`).
- `access/dona-usuarios.tsx` (nuevo): «Usuarios», filas Usuarios / Administradores (`desglose.users_by_role`).
- `access/approvals-resumen.tsx`: reemplaza las dos `TarjetaIndicador` por estas donas; aparecen solo con `panel` y su desglose (conectores solo superadmin); quita `useDisenoTarjetas`.
- Colores: puntos `nx-dona__punto--serie-*` y tokens `--color-indicador-*` existentes; sin tokens ni CSS nuevos.
- Pruebas: `approvals-resumen.test.tsx` ajustada (leyendas, porcentajes, «N en total»).

## Decisiones
- `TarjetaIndicador` no se modifica (decisión del dueño): Dashboard y selector de diseño sin cambios.
- Misma altura y estructura: `DonaKpi` usa `h-full` en la rejilla.

## Impacto en elementos compartidos
- Ninguno modificado. `DonaKpi` y `TarjetaIndicador` solo se reutilizan/sin tocar; afecta solo la vista Resumen de Solicitudes (`/approvals`). La preferencia de diseño de tarjetas ya no influye en Conectores y Usuarios allí.

## Verificación
- tsc, lint y vitest: ver bitácora. Sin captura visual de ambos temas (no verificada).
