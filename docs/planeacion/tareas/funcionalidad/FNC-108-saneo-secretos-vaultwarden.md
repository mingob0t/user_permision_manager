# FNC-108 — Borrar los secretos de arranque de Vaultwarden del detalle de la bitácora

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | aprovisionamiento |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Creada** | 2026-10-21 |
| **Estatus Git** | resuelta en FNC-068 (`fnc/FNC-068-vaultwarden`, commit local, sin push) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí |

## Contexto
- FNC-068 agregó `VAULTWARDEN_CLIENT_SECRET` y `VAULTWARDEN_MASTER_PASSWORD` al entorno de staging/prod.
- `provisioning/saneo.py` borra del detalle de errores los valores de `VARIABLES_SECRETAS` (SEC-CON-10); hoy no incluye esas dos.
- El cliente de Vaultwarden nunca las pone en errores; esto es defensa en profundidad.
- No se hizo en FNC-068 porque FNC-051 está modificando `saneo.py` en paralelo.

## Alcance
- Agregar las dos variables a `VARIABLES_SECRETAS`, con prueba de regresión que falle primero.
- Actualizar VARIABLES.md (fila de `VARIABLES_SECRETAS`) y HISTORIAL.md.

## Impacto cruzado
- Origen ← FNC-068. Después de FNC-051.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta (FNC-068) |
| 2026-10-21 | Resuelta en FNC-068 (FNC-051 ya cerró): dos variables en `VARIABLES_SECRETAS`; regresión `tests/secretos/test_auditoria_fnc068.py::test_fnc108_*` (falló primero) |
