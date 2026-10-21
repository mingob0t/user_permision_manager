# DIS-042 — Parámetros de los conectores SSH y base de datos en el formulario

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-conectores |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |

## Contexto
- El contrato 1.1 solo documenta `params.base_path` de `api`; los esquemas de `ssh` y `bd` llegan con FNC-052 y FNC-053 (P9, versión aditiva)
- DIS-022 dejó `PARAMETROS_POR_TIPO` vacío para `ssh` y `bd` y conserva sin editar los parámetros guardados

## Objetivo
- Agregar los campos de cada tipo a `PARAMETROS_POR_TIPO` (`connector-catalog.ts`) cuando el contrato publique sus esquemas; revisar también los de `api` con FNC-051

## Impacto cruzado
- Origen ← DIS-022
- Depende de → FNC-051, FNC-052, FNC-053

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-022 |
