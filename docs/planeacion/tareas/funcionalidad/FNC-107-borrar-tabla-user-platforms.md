# FNC-107 — Borrar la tabla obsoleta `user_platforms` y la relación `User.platforms`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-21 |
| **Estatus Git** | — |
| **Rama** | — |
| **Requiere migración BD** | Sí (borra `user_platforms`) |
| **Requiere auditor-seguridad** | No |

## Contexto
- FNC-065 retiró los endpoints y dejó la tabla obsoleta sin borrar ni migrar (P4: sus filas se descartan)
- Tras un periodo sin incidencias se borra (el downgrade no restaura filas: hay que respaldar antes)

## Objetivo
- Quitar la tabla, la relación `User.platforms` (`platform_users`) y su uso en fábricas y pruebas

## Alcance
- **Incluye:** migración con respaldo de las filas en el downgrade, modelos, `tests/fabricas.py`, documentación
- **No incluye:** migrar sus filas a accesos (P4)

## Impacto cruzado
- Origen ← FNC-065; depende de FNC-065 y de la validación del dueño en la prueba de concepto
- Compartido: `tests/fabricas.crear_usuario` (parámetro `plataformas`)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta (FNC-065) |
