# DIS-022 — Configuración de conectores y bitácora de ejecuciones

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-conectores |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local, sin push |
| **Rama** | `dis/DIS-022-conectores-ejecuciones` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El superadmin configura los conectores (tabla de pantallas, "Configuración"); no existe pantalla, y las ejecuciones fallidas no se ven
- Requerimientos: F-CON-01

## Objetivo
- Pantalla `/admin/connectors`: lista de plataformas `conector` con su configuración (tipo, host, parámetros, referencia de credencial — nunca el valor), probar conexión, y bitácora de ejecuciones con intentos y reintento manual

## Alcance
- **Incluye:**
  - Formulario dinámico por tipo de conector
  - Botón "Probar conexión" con resultado genérico
  - Bitácora filtrable y detalle de intentos
  - Reintentar según P10
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Editar ítems de Vaultwarden
  - Pestañas de Ajustes existentes

## Archivos previstos
- `frontend/src/components/connectors/connector-list.tsx`
- `frontend/src/components/connectors/connector-form.tsx`
- `frontend/src/components/connectors/jobs-log.tsx`
- `frontend/src/app/admin/connectors/page.tsx`

## Reutilización
- `Modal`, `Field`, `Select`, `Button`, `usePolling`

## Criterios de aceptación
- [x] Ningún campo pide ni muestra contraseñas (prueba: sin `input[type=password]`; credencial = referencia)
- [ ] Criterios comunes de diseño (FNC-037): cumplidos en código y pruebas; falta verificación en navegador y auditor-accesibilidad

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-071, FNC-061, FNC-062
- Contrato → docs/contratos/conectores-y-ejecuciones.md
- Genera → DIS-041 (bitácora para admin de área), DIS-042 (parámetros de SSH y BD)

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Implementación (2026-10-21)
| Archivo | Qué |
|---|---|
| `frontend/src/app/admin/connectors/page.tsx` | Monta `ConnectorsAdmin` (guarda `admin` sin cambios) |
| `components/connectors/connectors-admin.tsx` | Pantalla: plataformas `conector` (`GET /platforms`, `has_connector`), sección del conector y bitácora |
| `components/connectors/connector-list.tsx` | Filas en `ResponsiveList`: plataforma y área, configurado o no, accesos vigentes, "Configurar" |
| `components/connectors/connector-panel.tsx` | Sección (no `Modal`): lectura (`404` = sin configurar), resumen, probar, eliminar, aviso `status` con foco |
| `components/connectors/connector-form.tsx` | Tipo, host, puerto, parámetros del tipo, referencia de credencial y activo; `required`/`aria-required`, `aria-describedby`, foco al primer error, `aria-disabled` |
| `components/connectors/connector-delete-dialog.tsx` | Confirmación con el efecto explicado; botón primario |
| `components/connectors/connector-catalog.ts`, `connector-errors.ts` | Tipos, parámetros por tipo, estados de credencial, validación espejo, cuerpo del contrato y mensajes propios |
| `components/connectors/jobs-log.tsx`, `jobs-filters.tsx`, `jobs-table.tsx` | Bitácora: filtros a la página 1, `ListPager`, "Recargar", `usePolling` solo con transitorios, reintento |
| `components/connectors/job-detail-modal.tsx`, `job-retry-dialog.tsx` | Detalle con intentos (texto escapado) y confirmación del reintento con su efecto |
| `components/connectors/job-catalog.ts`, `job-errors.ts` | Estados, operaciones, proveedores, resultados y mensajes propios |
| `lib/access/types.ts` | `JobStatus` con `cancelado` (pendiente desde FNC-049) |
| `lib/access/query.ts`, `connectors.ts` | `jsonBody('DELETE')`: `remove` envía `{}` (contrato 1.1; sin él, `415`) |
| `lib/use-polling.ts` | Opción `activo` (por defecto `true`): sin consultas periódicas cuando es `false` |
| `components/audit/audit-detail-modal.tsx` | `Dato` exportado (sin cambio de marcado) |

- Reutilizado: `ResponsiveList`, `ListPager`, `formatearFecha`, `Field`/`Select`/`TextInput`/`Checkbox`/`Button`/`Modal`, `FieldErrorNote`/`FieldHint`/`describedBy`/`focusFirstError`, `useOpcionesAlcance`/`ScopeSelects`, `listLoadError`, `usePolling`, `useAsync`, `Badge`/`Card`/`Spinner`/`ErrorNote`/`EmptyNote`, `Dato`
- Sin tokens, clases CSS ni dependencias nuevas; sin estilos inline ni colores literales

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Configuración en una sección bajo la lista, no en `Modal` | La confirmación de eliminar no queda anidada (patrón DIS-018) |
| 2 | La lista usa `has_connector` de `GET /platforms`; la configuración se lee al abrir | Sin una petición por fila |
| 3 | Parámetros por tipo: solo `api.base_path` (único del contrato); `ssh` y `bd` sin editor; los guardados sin editor se conservan y solo se muestran sus nombres; cambiar de tipo los descarta | No inventar esquemas (P9) → DIS-042 |
| 4 | `noop` no se ofrece; si ya está guardado, se conserva como opción | Solo dev y pruebas (contrato) |
| 5 | "Probar conexión" prueba lo guardado; texto propio de éxito o fallo, nunca `message` del servidor | Sin texto del servidor; detalle solo al log |
| 6 | Confirmaciones (eliminar, reintentar) con botón primario, no `danger` | Blanco sobre `--color-error` falla AA hasta DIS-004 |
| 7 | Bitácora en la misma ruta, solo superadmin (guarda `admin` de FNC-070) | No cambiar permisos de ruta; el admin de área → DIS-041 |
| 8 | Filtros: estado, operación, proveedor, área y plataforma; sin `from`/`to` ni `user_id`/`access_id` | Alcance mínimo; agregarlos es aditivo |
| 9 | `usePolling` con opción nueva `activo` (por defecto `true`) | El contrato pide refresco solo con estados transitorios; sin cambio para los demás usos |
| 10 | Reintento desde la fila, no desde el detalle | Sin diálogos anidados |
| 11 | `connectorsApi.remove` envía `{}` | El contrato 1.1 lo exige (`415` sin JSON); era un defecto del cliente de FNC-069 |
| 12 | `attempts[].error` se muestra como texto | Es dato de la bitácora, saneado y truncado por el servidor (SEC-CON-10), no un mensaje de error de la petición |

## Verificación (2026-10-21, en `frontend/`)
| Comando | Salida |
|---|---|
| `npm run typecheck` | 0 |
| `npm run lint` | 0 (sin avisos) |
| `npx eslint tests vitest.config.ts` | 0 |
| `npx vitest run` | 0: 983 passed + 25 expected fail (las 25 conocidas; ninguna nueva) |
| `npm run build` | 0 (`/admin/connectors` 9.23 kB) |
| `grep` de `style=`, `<style`, `.style.`, `#hex`, `rgb(`, paleta fija, IPs y `password` en `components/connectors` y la página | Sin resultados |

- Pruebas nuevas: `tests/components/connectors/connectors-admin.test.tsx` (13), `jobs-log.test.tsx` (11), `tests/lib/use-polling.test.ts` (`activo`), `peticiones.test.ts` (DELETE con `{}`)
- Pares de contraste nuevos: `badge-ejecucion-*`, `badge-intento-*`, `badge-credencial-*` (pasan en los 7 temas)
- **No verificado en navegador** (tema claro y oscuro, móvil y escritorio): no se levantó la app con backend ni hubo captura. Las clases son las mismas de pantallas ya revisadas
- Sin revisor ni auditores (instrucción del orquestador); pendientes revisor y auditor-accesibilidad antes de cerrar

## Correcciones del auditor-accesibilidad (2026-10-21; veredicto: aprobado con 3 observaciones)
| # | Observación | Corrección | Prueba |
|---|---|---|---|
| 1 | Con solo `fields.params` el foco no se movía | `ORDEN` incluye `params` → `fieldset` `conector-params` (`tabIndex=-1`, anillo de foco) | `connectors-admin.test.tsx`: "422 solo en params" |
| 2 | "Recargando…" se anunciaba en cada refresco automático | Solo tras pulsar "Recargar" (`recargaManual`) | `jobs-log.test.tsx`: "anuncio de recarga" |
| 3 | El fallo de "Probar conexión" iba en `role="status"` | Regiones fijas: éxito en `status`, fallo en `alert` | `connectors-admin.test.tsx`: "probar conexión" |

- typecheck 0, lint 0 (y `eslint tests` 0), `next build` 0
- Vitest: la primera corrida salió 1 por la prueba intermitente conocida `areas-list.test.tsx` "409 rol_no_admin" (DIS-040, fuera de alcance); la segunda salió 0: 985 passed + 25 expected fail (las 25 conocidas)
- No comprobé que las pruebas nuevas fallen sin las correcciones. Sigue sin verificarse en el navegador

## Impacto en elementos compartidos (`impacto.py`, contra `develop`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Page` | función | `frontend/src/app/admin/connectors/page.tsx` | Las demás `page.tsx` (+8) | frontend/src | Falso positivo: mismo nombre, archivos distintos |
| `jsonBody` | función | `frontend/src/lib/access/query.ts` | `directory.ts`, `grants.ts`, `provisioning.ts`, `requests.ts`, `users.ts` | frontend/src | Solo se amplía el tipo del método (`DELETE`); `peticiones.test.ts` en verde |
| `tinte` | función | `frontend/tests/accesibilidad/pares-contraste.ts` | `tokens.css` | frontend/src | Falso positivo: no cambió; se agregaron pares |
| `usePolling` | función | `frontend/src/lib/use-polling.ts` | `approvals-inbox.tsx`, `my-access.tsx`, `my-requests.tsx`, `request-errors.ts`, `role-summary.tsx`, `user-access-panel.tsx` | frontend/src | Opción nueva con valor por defecto igual al anterior; sus pruebas y las de esas pantallas en verde |

- Además (no los detecta la herramienta): `Dato` exportado de `audit-detail-modal.tsx` (Auditoría, sin cambio de marcado); `JobStatus` con `cancelado` (solo lo usan `lib/access/` y `connectors/`); `connectorsApi.remove` (solo DIS-022)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-21 | Aprobada y En curso (modo autónomo autorizado por el dueño) |
| 2026-10-21 | Implementada; En revisión. Genera DIS-041 y DIS-042 |
| 2026-10-21 | auditor-accesibilidad aprobado; corregidas sus 3 observaciones (foco en parámetros, anuncio de recarga, alerta en prueba fallida) |
