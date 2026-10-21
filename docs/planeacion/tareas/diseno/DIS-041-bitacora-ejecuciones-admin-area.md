# DIS-041 — Bitácora de ejecuciones para el admin de área

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-conectores |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |

## Contexto
- El contrato `conectores-y-ejecuciones.md` 1.1 da `GET /provisioning/jobs` al admin de área (sus áreas, lectura)
- DIS-022 dejó la bitácora en `/admin/connectors`, con guarda `admin` (solo superadmin, FNC-070): el admin de área no la ve

## Objetivo
- Mostrar `JobsLog` (ya reutilizable; oculta "Reintentar" sin superadmin) al admin de área en una ruta o entrada propia, sin la configuración de conectores

## Impacto cruzado
- Origen ← DIS-022
- Menú `NAV` de `app-shell.tsx` (compartido) si se agrega una entrada

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-022 |
