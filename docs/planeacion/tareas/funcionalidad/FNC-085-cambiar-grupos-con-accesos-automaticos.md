# FNC-085 — Cambiar grupos o tipo de una plataforma con accesos automáticos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- Desde FNC-055 toda plataforma de un área con admins tiene accesos `admin_de_area` vigentes, así que cambiar sus grupos o su tipo responde siempre `409 plataforma_con_accesos`.
- No se puede resincronizar como con el área: el trabajo de revocación usa los grupos actuales de la plataforma y quitaría a la persona del grupo nuevo, no del anterior.
- Origen: FNC-055.

## Criterios de aceptación
- [ ] Definir el flujo (p. ej. revocar los automáticos, esperar `revocado`, cambiar y resincronizar; o guardar el grupo en el trabajo)
- [ ] Sin dejar miembros en el grupo anterior
- [ ] Pruebas

## Impacto cruzado
- Origen ← FNC-055
- Relacionadas → FNC-046, FNC-049

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (FNC-055) |
