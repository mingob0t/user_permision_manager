# FNC-105 — Validar el rango de los ids de ruta en la API v1 (OverflowError → 404)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | api |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |
| **Estatus Git** | — |
| **Rama** | — |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (entrada de rutas) |

## Contexto
- Un id de ruta como `2**70` pasa el convertidor `<int:...>` de Flask y desborda el entero de la BD (`OverflowError`): responde `500` en vez de `404`
- Reproducido en `/platforms/<id>/connector`, `/audit/platforms/<id>`, `DELETE /areas/<id>` y probablemente en otros endpoints con `<int:...>`
- Origen: auditoría de seguridad de FNC-061

## Objetivo
- Un id fuera del rango de la columna responde `404 no_encontrado`, igual que uno inexistente

## Alcance
- **Incluye:**
  - un convertidor de ruta común (p. ej. `id` con tope de 2**31 - 1) registrado en `create_app()` y usado en las rutas `/api/v1`
  - inventario de las rutas afectadas y prueba de regresión por cada una (la matriz puede recorrerlas con un id enorme)
- **No incluye:** cambiar el formato de los demás errores ni los ids de cuerpo o filtros (`leer_entero` ya los valida)

## Archivos previstos
- `app/modules/api/` (convertidor y registro), blueprints de `/api/v1`, `tests/test_guardia_rutas.py` o prueba nueva

## Reutilización
- `error_response(*NO_ENCONTRADO)`; `NO_ENCONTRADO` de `api/helpers.py`

## Criterios de aceptación
- [ ] Un id de 2**70 responde `404` con el formato estándar en todas las rutas con id (prueba que las recorre)
- [ ] Sin cambios en las respuestas de ids válidos

## Impacto cruzado
- Origen ← FNC-061
- Afecta a todos los blueprints de `/api/v1` (elemento compartido: el convertidor)

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta (auditoría de FNC-061) |
