# FNC-055 — Acceso automático de los admins a las plataformas de sus áreas

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
| **Rama** | `fnc/FNC-055-acceso-automatico-admins-areas` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (otorgamiento sin solicitud) |

## Contexto
- El admin "da de alta sus áreas y plataformas y tiene acceso automático a ellas" (REQUERIMIENTOS §2)
- Hoy no existe ningún otorgamiento automático
- Requerimientos: F-AREA-01, RF-03

## Objetivo
- Otorgar con origen `admin_de_area` el nivel que defina P6 (recomendado: `admin`) a cada admin de un área sobre cada plataforma `ldap` o `conector` de esa área: al crear la plataforma, al asignar el admin al área, y revocarlo según P6 al quitarlo

## Alcance
- **Incluye:**
  - Servicio `sync_area_admin_grants(area)` en el módulo de accesos, idempotente
  - Llamado desde el alta de plataforma (FNC-046), la asignación de admins (FNC-044) y el alta de área (FNC-045) mediante una función pública, sin lógica en esos módulos
  - Comportamiento al quitar un admin o mover una plataforma según P6
- **No incluye:**
  - Accesos de áreas ajenas (se solicitan, RF-03)
  - Endpoints o pantallas

## Archivos previstos
- `app/modules/access/area_admin_sync.py`
- Una llamada en los servicios de FNC-044, FNC-045 y FNC-046
- `tests/access/test_area_admin_sync.py`

## Reutilización
- `grant()`/`revoke()` de FNC-054

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `create_platform`, asignación de `area_admins`, `create_area` | Endpoints de otros módulos (una llamada) | Pantallas `/admin/platforms`, `/areas`, `/users` | Pendiente |

## Criterios de aceptación
- [ ] Crear una plataforma en un área con dos admins genera dos accesos `admin_de_area` (prueba)
- [ ] Asignar un admin a un área con tres plataformas genera tres accesos (prueba)
- [ ] Repetir la sincronización no duplica (prueba)
- [ ] El superadmin no recibe accesos automáticos salvo que P6 lo indique
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-044, FNC-045, FNC-046, Respuesta a P6

## Riesgos y reversión
- Muchos trabajos al asignar un admin a un área grande: se encolan por lotes.
- Reversión: revertir la rama; los accesos creados quedan auditados.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |

## Decisiones del dueño (2026-10-14)
- Nivel del acceso automático: `usuario`.
- Lo reciben todos los admins del área, también en plataformas nuevas.
- Al quitarle el área a un admin se revocan sus accesos `admin_de_area` de esa área.
- El superadmin no entra a los grupos LDAP.
