# FNC-081 — Purgar hashes de contraseña heredados de cuentas locales no administrador y política mínima de la contraseña de emergencia

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | auth |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-19 |

## Contexto
- Tras FNC-077 solo la cuenta de emergencia usa el login local; las cuentas locales no `administrador` conservan `password_hash` heredados (p. ej. `nexus123`) que ya no sirven.
- La contraseña de emergencia no tiene política mínima (SEC-AUTH-12, §12 preguntas 4 y 5).
- Origen: revisión de FNC-077.

## Criterios de aceptación
- [ ] Migración o comando que pone `password_hash` en NULL a cuentas no `administrador`, con auditoría
- [ ] Longitud mínima de la contraseña de emergencia en `PUT /users/<id>` (valor por confirmar)
- [ ] Pruebas de regresión

## Impacto cruzado
- Origen ← FNC-077
- Relacionadas → FNC-003, FNC-010

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-19 | Creada como Propuesta (revisión de FNC-077) |
