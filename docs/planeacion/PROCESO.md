# Proceso

Método completo: `~/.claude/agentes/LINEAMIENTOS.md`. Resumen:
- Solo se implementan tareas **aprobadas** del [tablero](TABLERO.md). Lo nuevo entra como `Propuesta`.
- Carriles `FNC` (funcionalidad) y `DIS` (diseño); una **plataforma** y un **módulo** por tarea.
- Ramas: tarea `fnc/FNC-###-titulo` o `dis/DIS-###-titulo` desde `develop` → merge aprobado a `develop` → `staging` → `main`.
- Antes de cerrar: `python3 ~/.claude/agentes/herramientas/impacto.py` y su tabla en la ficha (elementos compartidos y áreas a validar).
