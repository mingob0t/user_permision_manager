# FNC-056 — Solicitudes: catálogo solicitable, crear solicitud y mis solicitudes

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-056-solicitudes-catalogo-crear-mis-solicitudes` |
| **Requiere migración BD** | Sí (tabla `platform_access_requests`) |
| **Requiere auditor-seguridad** | Sí (entrada de usuario, autorización) |

## Contexto
- El catálogo existe pero no permite solicitar (F-SOL-01) y el flujo de solicitudes se retiró (F-SOL-02; referencia de solo lectura `nexus_master/app/modules/requests/routes.py`)
- Un admin solicita accesos de áreas ajenas como usuario (RF-03)
- Requerimientos: F-SOL-01, F-SOL-02, RF-03

## Objetivo
- Crear `app/modules/access_requests/` con la solicitud (usuario, plataforma, nivel, justificación, estado, decisión) y los endpoints del solicitante

## Alcance
- **Incluye:**
  - Tabla `platform_access_requests` (nunca `access_requests`, ver FNC-039): estados `pendiente`, `aprobada`, `rechazada`; `decided_by`, `decided_at`, `rejection_reason`
  - `GET /access-requests/catalog`: plataformas activas solicitables según P1, con el estado del solicitante (sin acceso, pendiente, con acceso y nivel)
  - `POST /access-requests`: nivel `usuario` o `admin`, justificación obligatoria con longitud mínima y máxima; rechaza duplicado pendiente, acceso vigente del mismo nivel, plataforma inactiva o sin grupos, y solicitudes de un admin sobre sus propias áreas
  - `GET /access-requests/mine` paginado
  - Aviso `solicitud_nueva` (FNC-048) y auditoría
- **No incluye:**
  - Bandeja y decisión (FNC-057)
  - Cancelar una solicitud (no pedido; sugerencia)
  - Recordatorios y escalamiento (fuera de la v1)
  - Pantallas (DIS-013, DIS-014)

## Archivos previstos
- `app/modules/access_requests/models.py`
- `app/modules/access_requests/services.py`
- `app/modules/access_requests/api.py`
- Migración (ADR-002)
- `app/__init__.py` (registro)
- `tests/access_requests/`

## Reutilización
- Servicio de accesos de FNC-054 (consulta de vigentes)
- Avisos de FNC-048
- `sanitize_display_name` o equivalente para normalizar texto

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `app/__init__.py` | Arranque | Toda la app (registro del blueprint) | Pendiente |

## Variables y configuración
- `ACCESS_REQUEST_JUSTIFICATION_MIN_LENGTH`, `ACCESS_REQUEST_JUSTIFICATION_MAX_LENGTH` (constantes registradas).

## Criterios de aceptación
- [ ] Matriz 401/403/201/400/409 (pruebas)
- [ ] Duplicado pendiente responde 409 (prueba)
- [ ] Un admin no puede solicitar en un área que administra (prueba)
- [ ] Justificación vacía o demasiado larga responde 400 (prueba)
- [ ] Se notifica a los admins del área (prueba con SMTP simulado)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → FNC-057, DIS-013, DIS-014
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, FNC-046, FNC-047, FNC-048, FNC-054, FNC-038, Respuesta a P1
- Contrato → docs/contratos/solicitudes.md

## Riesgos y reversión
- Reversión: bajar la migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
