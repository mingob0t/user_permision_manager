# FNC-058 — Accesos: consulta por usuario, mis accesos y revocación manual

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
| **Rama** | `fnc/FNC-058-accesos-consulta-revocacion-manual` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- F-ACC-02 pide revocar manualmente desde el portal (sacar del grupo o ejecutar el conector), y la pantalla "Usuarios y accesos" necesita ver los accesos de un usuario; el usuario ve los suyos en el Inicio y en Mis solicitudes
- Requerimientos: F-ACC-02, RF-03, pantallas "Usuarios y accesos" e "Inicio"

## Objetivo
- Exponer los accesos con alcance por rol y la revocación con motivo según P7

## Alcance
- **Incluye:**
  - `GET /me/access`: accesos propios
  - `GET /users/<id>/access`: superadmin todos; admin solo los de plataformas de sus áreas
  - `POST /access/<id>/revoke` (motivo según P7): superadmin o admin del área de la plataforma; un admin no revoca accesos de otras áreas
  - Blueprint en `app/modules/access/api.py`
- **No incluye:**
  - Otorgar manualmente sin solicitud (no pedido)
  - Baja masiva de un usuario (fuera de la v1)
  - Pantallas (DIS-014, DIS-018)

## Archivos previstos
- `app/modules/access/api.py`
- `app/__init__.py` (registro del blueprint)
- `tests/access/test_api.py`

## Reutilización
- Servicio de FNC-054
- `any_admin_required`, `can_manage_platform`, `scoped_users`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `app/__init__.py` | Arranque | Toda la app (una línea de registro) | Pendiente |

## Criterios de aceptación
- [ ] Matriz 401/403/200 por endpoint y rol (pruebas)
- [ ] Un admin no revoca accesos de un área ajena (prueba)
- [ ] Revocar deja el acceso en `revocando` y encola el trabajo (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-014, DIS-018
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-038
- Contrato → docs/contratos/accesos.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
