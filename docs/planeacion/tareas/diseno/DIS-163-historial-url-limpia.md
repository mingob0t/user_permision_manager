# DIS-163 — Historial de solicitudes con URL limpia

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (pedido del dueño: «límpiame la URL») |

## Cambios
- `app/approvals/historial/page.tsx` (nuevo): ruta limpia del Historial.
- `access/filtros-historial.ts` (nuevo): filtros de entrada por URL (`?status`, `area_id`, `platform_id`, `q`) leídos una vez; después en `sessionStorage` de la pestaña (F5 los conserva); la URL se reemplaza por `/approvals/historial` sin entrada nueva en el historial. Sin almacenamiento: valores por defecto, sin error.
- `access/approvals-inbox.tsx`: usa `filtrosIniciales`/`guardarFiltrosHistorial` (antes escribía los filtros en la URL, DIS-036).
- `access/approvals-view.tsx`: Historial si la ruta es `/approvals/historial` o llega `?status=`.
- `marco/nav-principal.tsx`: el ítem activo se resuelve con `entradaDeRuta` (como las migas), así «Solicitudes» sigue activo en la subruta.

## Decisiones
- Los enlaces existentes con filtros (Resumen, Inicio, tarjeta de área) no cambian: se leen y la URL se limpia.
- Filtros por pestaña (`sessionStorage`), no por usuario: es comodidad, no estado que deba persistir.

## Impacto en elementos compartidos
- `NavPrincipal`: el ítem activo ahora incluye subrutas (prefijo más largo). Hoy solo afecta a `/approvals/historial`; ninguna otra ruta del menú tiene subrutas con página propia.
