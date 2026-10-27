# FNC-120 — Backend: lista blanca estricta de campos en los endpoints de usuarios, preferencias, ajustes, SMTP y plantillas

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | api |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |

## Contexto
- FNC-119 dejó `leer_cuerpo(None)` en los endpoints heredados (solo exige objeto) porque la interfaz reenvía objetos completos (p. ej. `Partial<SmtpConfig>` con `source`, `editable`) y una lista blanca habría roto las pantallas.
- SEC-AUTHZ-09 pide lista blanca por endpoint.
- Origen: decisión de FNC-119.

## Criterios de aceptación
- [ ] Cada endpoint de `users/api.py`, `users/preferencias_api.py`, `users/higiene_api.py`, `settings/api.py`, `notifications/api.py` y `areas/api.py` (`PUT /areas/<id>/users`) usa `leer_cuerpo(<permitidos>)` con su lista, y un campo fuera de ella da `400 campo_no_permitido` (prueba que primero falla)
- [ ] Los formularios del frontend envían solo esos campos (tarea `web` vinculada si hace falta)

## Impacto cruzado
- Origen ← FNC-119
- Genera → tarea `web` para los formularios de Ajustes, Usuarios y preferencias (antes de activar la lista)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (decisión de FNC-119) |

- 2026-10-27: movida a la fase 5 (decisión del orquestador, pendiente de validar en la prueba de concepto). Es endurecimiento de seguridad (SEC-AUTHZ-09) y puede romper formularios; el dueño pausó la fase 5 para dejar primero el sistema funcional. Sin cambio de alcance.
