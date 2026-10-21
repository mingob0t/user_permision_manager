# DIS-037 — Panel: retirar o reubicar los contadores heredados de `/stats` que duplican el resumen por rol

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | dashboard |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |

## Contexto
- Tras DIS-024, el admin y el superadmin ven "Áreas" y "Plataformas" dos veces: en el resumen (`/home/summary`) y en "Actividad del portal" (`/stats`)
- DIS-024 no quitó contenido existente (fuera de su alcance); la gráfica y "Más visitadas" no se duplican

## Objetivo
- Decidir con el dueño, en el rediseño visual, si se retiran los contadores duplicados y se deja de `/stats` solo visitas, gráfica y "Más visitadas"

## Impacto cruzado
- Origen ← DIS-024
- Relacionada → DIS-003 (gráfica con variables `--nx-*` inexistentes)
