# FNC-086 — Sincronización inicial de los accesos automáticos de plataformas existentes

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
- FNC-055 otorga los accesos automáticos solo ante un evento (alta de plataforma, área agregada a un admin, cambio de área o de grupos). Las plataformas y admins que ya existen al desplegar no los reciben.
- Origen: FNC-055.

## Criterios de aceptación
- [ ] Comando explícito (p. ej. `flask accesos sincronizar-admins [--area ID]`) que llama a `area_admin_sync.sincronizar_plataforma` por plataforma, con resumen y auditoría `sistema`
- [ ] Idempotente; respeta el tamaño de lote del ejecutor
- [ ] Documentado en `docs/operacion/`
- [ ] Pruebas

## Impacto cruzado
- Origen ← FNC-055
- Relacionadas → FNC-049, FNC-067

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (FNC-055) |
