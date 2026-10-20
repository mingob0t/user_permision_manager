# FNC-096 — `GET /platforms`: campos de integración para quien administra

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de DN) |

## Contexto
- DIS-017 y `platform-form.tsx` esperan de FNC-063 `integration_type`, los DN y `active_grants` en `GET /platforms` para la edición; FNC-063 no lo incluía (alcance: visibilidad).
- Con FNC-063 un admin puede ver una plataforma de un área que no administra (acceso propio `activo`): la interfaz necesita saber si la administra.

## Alcance
- Agregar esos campos y un indicador `can_manage` solo para quien administra la plataforma (`can_manage_platform`); un usuario no recibe DN.
- Contrato `plataformas-integracion.md`: campo opcional (misma versión, nota en Historial).
- N+1 de `active_grants` en listas (nota de FNC-054): agrupar.

## Agregado por la auditoría de FNC-063 (Baja, previos)
- `scoped_platforms` no filtra por `status` de plataforma ni de área: con acceso activo se ve una plataforma o área inactiva con su `direct_link`. Filtrar por `Activo` como `catalogo.py`.
- `/stats` (`platforms_by_area`) y `/areas` (`platforms_count`, `users_count`) cuentan todo el área, no solo "mis plataformas": usar `platforms_q`.

## Impacto cruzado
- Origen ← FNC-063
- Relacionada → DIS-017

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (FNC-063) |
