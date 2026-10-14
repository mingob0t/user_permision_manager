# FNC-054 — Accesos otorgados: modelo con origen y estados, y servicio de otorgar y revocar

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-054-accesos-otorgados-modelo-servicio` |
| **Requiere migración BD** | Sí (tabla `platform_access_grants`) |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- No existe registro de quién tiene qué plataforma y nivel, desde cuándo ni por qué; `user_platforms` es una relación sin nivel ni origen que además no limita la visibilidad (deuda 13)
- Es la base del inventario (F-AUD-02) y de la revocación (F-ACC-02)
- Requerimientos: F-ACC-01, F-ACC-02, F-AUD-02, RF-02, RF-05

## Objetivo
- Crear `app/modules/access/` con el acceso otorgado (usuario, plataforma, nivel, origen, solicitud, quién aprobó, fechas, estado) y el servicio `grant()`/`revoke()` que valida reglas, encola el trabajo en FNC-049 y actualiza el estado con el resultado

## Alcance
- **Incluye:**
  - Tabla `platform_access_grants`: `user_id`, `platform_id`, `level` (`usuario`/`admin`), `origin` (`solicitud`/`admin_de_area`/`heredado`), `request_id`, `granted_by`, `granted_at`, `status`, `revoked_by`, `revoked_at`, `revoke_reason`; un acceso vigente por usuario, plataforma y nivel
  - Regla de niveles según P5 (recomendado: excluyentes; pasar de `usuario` a `admin` quita del grupo de usuario)
  - `grant()` y `revoke()` en una transacción con el trabajo de aprovisionamiento; manejadores de resultado registrados en FNC-049
  - Estados `en_proceso` → `activo`/`fallido` y `revocando` → `revocado`/`fallo_revocacion`
  - Auditoría con antes y después en cada cambio
- **No incluye:**
  - Endpoints (FNC-058, FNC-059)
  - Acceso automático de admins (FNC-055)
  - Aprobación de solicitudes (FNC-057)
  - Visibilidad del catálogo (FNC-063)
  - Retirar `user_platforms` (FNC-065)
  - Accesos temporales con vencimiento (fuera de la v1)

## Archivos previstos
- `app/modules/access/models.py`
- `app/modules/access/services.py`
- `app/modules/access/rules.py`
- Migración (ADR-002)
- `tests/access/`

## Reutilización
- `queue.enqueue` y manejadores de FNC-049
- `can_manage_platform` de `app/authz.py`
- `add_audit_log` ampliado

## Criterios de aceptación
- [ ] Otorgar crea el acceso `en_proceso` y un trabajo en la misma transacción (prueba)
- [ ] El resultado del worker lleva el acceso a `activo` o `fallido` (prueba)
- [ ] No se duplica un acceso vigente (prueba)
- [ ] Revocar un acceso ya revocado no encola nada (prueba)
- [ ] La regla de niveles de P5 tiene pruebas de permitido y denegado
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → FNC-055, FNC-056, FNC-057, FNC-058, FNC-059, FNC-063, FNC-065
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, FNC-046, FNC-047, FNC-049, Respuesta a P5

## Riesgos y reversión
- Desfase entre portal y LDAP si alguien cambia grupos a mano: aceptado por RF-05 (sin conciliación).
- Reversión: bajar la migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
