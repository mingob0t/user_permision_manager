# FNC-034 — Semántica accesible: aria-label contextual, scope en th y texto del tipo de notificación

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | global |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-034-semantica-accesible` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
Botones Editar/Eliminar sin nombre de fila; `<th>` sin `scope`; tipo de notificación sin texto accesible.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-14

## Objetivo
Cerrar H-14: nombres accesibles contextuales, `scope` en `th` y texto accesible del tipo de notificación.

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** `components/connectors/` (DIS-042 lo cambia en otra rama; ya tiene `aria-label` contextual en Eliminar, sin tablas propias).

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [x] Prueba de regresión del tipo de notificación (falla sin el cambio: el texto era solo el título)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Revisión de la ficha contra el código (2026-10-27)
Decisión del orquestador (pendiente de validar en la prueba de concepto): implementar solo lo pendiente.

| Punto de H-14 | Estado | Resuelto por |
|---|---|---|
| Editar/Eliminar sin nombre de fila (Usuarios, Áreas, Plataformas) | Ya resuelto | DIS-008 / DIS-046 (`aria-label` con el nombre) |
| `th` sin `scope` | Ya resuelto | DIS-010 (`DataTable` con `scope="col"`; dashboard con `col`/`row`) |
| `th` vacío de acciones | Ya resuelto | DIS-008 (`headerSrOnly`, texto «Acciones») |
| Tipo de notificación sin texto accesible | **Implementado aquí** | FNC-034 |
| Pendiente en `components/connectors/` | Ninguno (ya con `aria-label`; no se tocó) | — |

## Impacto en elementos compartidos
Ninguno detectado (`impacto.py` contra `develop`). Se cambió solo `notifications-list.tsx` (pantalla `/notifications`, sin otros usos).

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `tsc --noEmit` | 0 |
| `next lint` | 0 |
| `vitest run` | 0 (1599 pruebas, 47 archivos; accesibilidad en 0) |
| `next build` | 0 |
No verificado en navegador ni con lector de pantalla.

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | Aprobada en modo autónomo; revisada contra develop: 3 de 4 puntos ya resueltos. Se agrega texto sr-only del tipo (`Éxito`/`Error`/`Advertencia`/`Información`) y `tests/components/semantica-accesible.test.tsx` |

- 2026-10-27: `auditor-accesibilidad` Aprobado; confirmó por grep y lectura los 3 puntos ya resueltos en develop. Hueco menor: la prueba nueva de nombres contextuales cubre Áreas; Usuarios y Plataformas dependen de sus pruebas previas. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
