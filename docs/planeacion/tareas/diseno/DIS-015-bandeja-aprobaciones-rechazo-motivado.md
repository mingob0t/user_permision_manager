# DIS-015 — Bandeja de aprobaciones con rechazo motivado

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | aprobaciones |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-015-bandeja-aprobaciones` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- F-SOL-03 pide una bandeja por área para aprobar o rechazar con motivo obligatorio (RF-06)
- Requerimientos: F-SOL-03, RF-03, RF-06

## Objetivo
- Pantalla `/approvals`: pendientes de las áreas del admin (todas para el superadmin) con solicitante, plataforma, nivel, justificación y fecha; aprobar con confirmación y rechazar con motivo obligatorio

## Alcance
- **Incluye:**
  - Filtros por estado y área
  - Detalle de la justificación (texto escapado)
  - Diálogo de rechazo con motivo obligatorio y validación visible
  - Confirmación de aprobación
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Aprobación en lote
  - Historial de la solicitud (DIS-020)

## Archivos previstos
- `frontend/src/components/access/approvals-inbox.tsx`
- `frontend/src/components/access/reject-dialog.tsx`
- `frontend/src/app/approvals/page.tsx`

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `frontend/src/app/approvals/page.tsx` | Monta `ApprovalsInbox` dentro de `RequireRole any_admin` (antes ruta reservada de FNC-070) |
| `frontend/src/components/access/approvals-inbox.tsx` | Nuevo: `GET /access-requests/inbox` con `usePolling`; filtros por estado (`pendiente` por defecto) y área; `ResponsiveList` de 5 columnas + justificación y motivo a ancho completo; acciones Aprobar/Rechazar; fila actualizada con la respuesta; aviso `status` con foco |
| `frontend/src/components/access/approve-dialog.tsx` | Nuevo: confirmación de aprobar (`Modal`, botón primario), efecto explicado (nivel y reemplazo), errores en el diálogo |
| `frontend/src/components/access/reject-dialog.tsx` | Nuevo: motivo obligatorio 10–500 (recortado) con pista/contador ligada al campo y al botón; envío deshabilitado sin motivo válido; 422 con foco al campo |
| `frontend/src/components/access/request-errors.ts` | Agrega `MOTIVO_MIN`, `MOTIVO_MAX`, `MENSAJE_MOTIVO`, `MENSAJES_DECISION`, `describeDecisionError`; lo existente sin cambios |
| `frontend/tests/components/access/approvals-inbox.test.tsx` | Nuevo: 16 pruebas |
| `frontend/tests/accesibilidad/pares-contraste.ts` | Pares `body-text/panel` y `btn-secondary-text/btn-secondary-bg` (pasan en los 7 temas) |

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Tras decidir, la fila se actualiza en su lugar con la respuesta del servidor (estado, motivo, sin acciones) y sale de "Pendientes" en el siguiente refresco de `usePolling` | Pedido del orquestador ("actualiza la fila sin recargar"); quitarla al instante deja el foco sin destino |
| 2 | El foco va al aviso (`role="status"`, `tabIndex=-1`) tras decidir; "Cerrar aviso" lo lleva al filtro de estado | Mismo patrón que el catálogo (DIS-013) |
| 3 | Aprobar usa `Modal` con botón primario, no `ConfirmDialog` | `ConfirmDialog` es de eliminar (botón `danger`, "Eliminando…"); aprobar no es destructivo |
| 4 | "Rechazar" del diálogo es primario, no `danger` | Blanco sobre `--color-error` (239 68 68, igual en todos los temas) = 3,76:1, falla AA; lo corrige DIS-004 |
| 5 | Sin motivo válido (recortado < 10 o > 500) el botón queda deshabilitado; la pista "Obligatorio. Escribe al menos N caracteres más (n/500)" está ligada al campo y al botón | Criterio "no habilita el envío y lo explica"; el servidor recorta el motivo (`approvals.py`) |
| 6 | Filtro de estado sin "Todas": Pendientes (por defecto), Aprobadas, Rechazadas | El contrato solo acepta esos tres valores y por defecto `pendiente` |
| 7 | Filtro de área: admin → `session.managed_areas` (sin llamada); superadmin → `GET /areas` | El backend ya acota; evita una llamada para el admin |
| 8 | La solicitud propia (requester = sesión) no muestra acciones y lo explica; el `403 solicitud_propia` igual se traduce | El backend no la lista para el admin; defensa en la interfaz |
| 9 | `404` y `409 solicitud_ya_decidida` recargan la lista y el diálogo queda abierto con el mensaje | La fila ya no refleja el servidor |
| 10 | Sin pestañas (no hay dos vistas): no se reutiliza `destinoPorTecla` | Los filtros cubren estado y área |
| 11 | La justificación se muestra en cada fila ("Sin justificación." si no hay), como texto con `whitespace-pre-line` | Detalle pedido por la ficha; React escapa el texto |

## Reutilización
- Pedido en la ficha: `ConfirmDialog`, `Modal`, `TextArea` de `form.tsx`; `usePolling`
- Reutilizados: `ResponsiveList`/`ResponsiveRow`/`ETIQUETA_CELDA`, `ListPager`, `RequestStatusBadge`/`ESTADOS_SOLICITUD`, `AccessStatusBadge`/`NIVELES`, `formatearFecha`, `listLoadError` (DIS-013/014); `Modal`, `Field`, `TextArea`, `Select`, `Button`; `FieldHint`, `FieldErrorNote`, `describedBy`; `Card`, `Spinner`, `ErrorNote`, `EmptyNote`; patrón de diálogo de `RequestFormModal` y aviso de `RequestCatalog`; `usePolling`, `useAsync`, `api.areas`
- `ConfirmDialog` no se usa (decisión 3)
- Nuevos al catálogo: `ApproveDialog`, `RejectDialog`, `describeDecisionError`, `MOTIVO_MIN`/`MOTIVO_MAX`

## Impacto en elementos compartidos
Salida de `python3 ~/.claude/agentes/herramientas/impacto.py`:

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Page` | función | `frontend/src/app/approvals/page.tsx` | las demás `page.tsx` | frontend/src | ☐ (falso positivo: nombre de convención de Next.js) |
| `listLoadError` | función | `frontend/src/components/access/request-errors.ts` | `my-access.tsx`, `my-requests.tsx` | frontend/src | ☐ (sin cambio: solo se agregaron funciones al final) |
| `message` | función/componente | `frontend/src/components/access/request-errors.ts` | `app/…` (+70) | app, frontend, tests… | ☐ (falso positivo: nombre de propiedad) |
| `tinte` | función | `frontend/tests/accesibilidad/pares-contraste.ts` | `styles/tokens.css` | frontend/src | ☐ (sin cambio: se agregaron dos pares) |

- Ningún elemento compartido modificado en su comportamiento; solo adiciones a `request-errors.ts` y `pares-contraste.ts`

## Criterios de aceptación
- [x] Rechazar sin motivo no habilita el envío y lo explica (pista ligada al campo y al botón)
- [x] Tras decidir, la fila sale de pendientes: estado actualizado al instante y fuera de la lista en el siguiente refresco (decisión 1)
- [x] Criterios comunes de diseño (FNC-037): componentes, clases y tokens existentes, sin estilos inline; carga, vacío, error y sin permiso (`RequireRole`); textos en español. Temas y móvil **no verificados en navegador**

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0, sin avisos |
| `npx eslint tests/components/access/approvals-inbox.test.tsx tests/accesibilidad/pares-contraste.ts` | salida 0 |
| `npx vitest run` | salida 0: 17 archivos, 608 passed + 25 expected fail (antes 575 + 25; las 25 conocidas sin cambio) |
| `npx vitest run tests/accesibilidad` | 415 passed + 25 expected fail; pares nuevos pasan en los 7 temas |
| `grep` de `style=`, `<style`, `.style.`, `#hex`, `rgb(`, IPs en los archivos nuevos y modificados | sin coincidencias |

- **No verificado en navegador:** temas claro y oscuro, móvil y escritorio. Sin backend ni sesión en el worktree; contraste medido con la fórmula sobre los tokens
- Sin revisor, tester ni auditores (por instrucción del orquestador)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-071, FNC-057
- Contrato → docs/contratos/solicitudes.md 1.1
- Relacionada → DIS-004 (contraste del botón `danger`, decisión 4)

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo por el orquestador; En curso en el worktree `pokemon-wt-d023` |
| 2026-10-20 | Implementada; En revisión. Sin tareas nuevas |
