# DIS-011 — Dividir settings-panel.tsx, users-list.tsx y platform-admin.tsx

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-011-dividir-monolitos-frontend` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
`settings-panel.tsx` 745 líneas, `users-list.tsx` 581.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-06

## Objetivo
Dividir `settings-panel.tsx`, `users-list.tsx` y `platform-admin.tsx` en archivos de una responsabilidad, sin cambio visible ni de comportamiento (decisión del orquestador, pendiente de validar en la prueba de concepto).

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** cambiar mensajes de error (`err.message` → por código), convertir las tarjetas de usuarios o áreas a `DataTable`, dividir `areas-list.tsx`.

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados (H-06)
- [x] Prueba de regresión: no aplica (refactor); las existentes pasan sin cambios
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → Después de DIS-010

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | Bloqueo del hook resuelto con FNC-121 (sin respaldos literales) |
| 2026-10-27 | Aprobada en modo autónomo, implementada y pasada a En revisión |

- 2026-10-21 (auditoría de seguridad DIS-019, Baja, previo): `users-list.tsx:137,233,308,322,457` muestran `err.message` del servidor (editar, buscar en directorio, purgar, eliminar). Al dividir el monolito, pasar a mensajes por código como `admin-role-errors.ts`.

## Resultado (2026-10-27)
| Archivo | Antes | Después |
|---|---|---|
| `settings-panel.tsx` | 634 | 98 (pestañas en `settings/portal-tab`, `smtp-tab`, `templates-tab`, `backup-tab`, `preferences-tab`, `settings-tabs.ts`) |
| `users-list.tsx` | 724 | 239 (`users/user-form`, `directory-picker`, `purge-panel`, `user-card`, `tag-picker`, `grupo-chips`) |
| `platform-admin.tsx` | 275 | 188 (`platforms/platform-columns`, `missing-link-note`) |

## Decisiones (del orquestador, pendientes de validar en la prueba de concepto)
- Los tres archivos conservan su nombre y export: las páginas y pruebas no cambian.
- Avisos de `settings-panel` ("Guardado.", "Respaldo descargado", correo de prueba) pasan a `SuccessNote`: cambia solo el peso de la fuente (negrita, como el estándar de DIS-010).
- `useToast` no se aplicó: los avisos de Ajustes son en línea junto al botón; migrarlos cambia el comportamiento.
- Bloqueo del hook por los 2 hex de respaldo del `<input type="color">` resuelto con FNC-121: `GET /settings` ya entrega siempre `portal_name`, `portal_identity_type`, `bg_color` y `text_color`; se quitaron los respaldos y la excepción de `colores-literales.excepciones.ts` (tope 0). Sin cambio en `.claude/lineamientos-ignorar`.
- Tarjetas de usuarios: solo se extrajo `UserCard`; no se pasaron a `DataTable` (cambiaría el aspecto).

## Impacto en elementos compartidos
- Ninguno modificado: `SuccessNote`, `Card`, `Button`, `Modal`, `DataTable` y `ACCION_FILA*` solo se usan.
- Páginas que montan los componentes (sin cambio de API): `/settings`, `/users`, `/admin/platforms`.
- Efecto visible: peso de fuente de los avisos de éxito de Ajustes (4 puntos).
- `tests/accesibilidad/colores-literales.excepciones.ts` (excepción eliminada).

## Verificación
- `typecheck` 0, `lint` 0, `vitest` 0 (40 archivos, 1520 pruebas; accesibilidad 9 archivos, 1089), `build` 0.
- No verificado en navegador (tema claro/oscuro, móvil): sin captura.

## Propuestas (sin ID: se abrirán en el tablero al validar)
- Mensajes por código en vez de `err.message` en `user-form`, `directory-picker`, `purge-panel` y borrado (hallazgo DIS-019, Baja); cambia textos y pide `auditor-seguridad`.
- Listas de tarjetas de usuarios y áreas sobre un componente común (`DataTable` o `ResponsiveList`).

- 2026-10-27: actualizada con develop; typecheck, lint, vitest (1596) y build en 0 (verificado por el orquestador). `auditor-accesibilidad` Aprobado sin hallazgos (pestañas, etiquetas, ids, foco y estados conservados). Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto). Sin verificar en navegador.
