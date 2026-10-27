# DIS-052 — Dividir el monolito `RequestCatalog`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | catalogo |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |

## Contexto
- `access/request-catalog.tsx` pasó de unas 50 a unas 175 líneas en `RequestCatalog` (carga, cruce, filtro, aviso, modal y lista en una función)
- Observación del revisor de DIS-030; no se refactoriza de paso

## Objetivo
- Separar filtro, lista, aviso de solicitud y estado de carga en unidades con una responsabilidad, sin cambiar el comportamiento
- Las pruebas existentes deben pasar sin cambios

## Impacto cruzado
- Origen ← DIS-030
