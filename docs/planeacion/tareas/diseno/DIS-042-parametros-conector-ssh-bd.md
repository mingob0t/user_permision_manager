# DIS-042 — Parámetros de los conectores SSH y base de datos en el formulario

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | configuracion-conectores |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Creada** | 2026-10-21 |

## Contexto
- El contrato 1.1 solo documenta `params.base_path` de `api`; los esquemas de `ssh` y `bd` llegan con FNC-052 y FNC-053 (P9, versión aditiva)
- DIS-022 dejó `PARAMETROS_POR_TIPO` vacío para `ssh` y `bd` y conserva sin editar los parámetros guardados

## Objetivo
- Agregar los campos de cada tipo a `PARAMETROS_POR_TIPO` (`connector-catalog.ts`) cuando el contrato publique sus esquemas; revisar también los de `api` con FNC-051

## Impacto cruzado
- Origen ← DIS-022
- Depende de → FNC-051, FNC-052, FNC-053

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-022 |
| 2026-10-27 | En curso. Aprobada en modo autónomo: decisión del orquestador (pendiente de validar en la prueba de concepto) |
| 2026-10-27 | Implementada: parámetros de `api`, `ssh` y `bd` en el formulario; error `params.<ruta>` en su campo. Revisor y auditor-accesibilidad pendientes |

## Cambios
- Nuevos: `connector-params.ts` (esquema por tipo, conversión, validación), `connector-param-fields.tsx` (campos agrupados), `tests/components/connectors/connector-params.test.tsx`
- Modificados: `connector-catalog.ts` (parámetros vía `connector-params`), `connector-errors.ts` (`paramFields`, `tipo`), `connector-form.tsx`, `connectors-admin.test.tsx` (fixture `api` completa y 422 por campo)
- Sin secretos: la credencial sigue siendo la referencia del gestor; sin IPs en textos ni ejemplos

## Impacto en elementos compartidos
| Elemento | Cambio | Usado por |
|---|---|---|
| `PARAMETROS_POR_TIPO`, `formularioDesde`, `cuerpoConector`, `parametrosConservados`, `CampoParametro` (`connector-catalog.ts`) | Parámetros anidados por tipo; `FormularioConector.params` con claves con puntos | `connector-form.tsx`; `connector-panel.tsx` (solo tipos) |
| `describeConnectorSaveError`, `ConnectorErrorView` (`connector-errors.ts`) | Segundo argumento opcional `tipo`; nuevo `paramFields` | `connector-form.tsx` |
| Un conector `api` guardado solo con `base_path` ya no pasa la validación del formulario (el servidor ya lo exige: `auth`, `otorgar` y `revocar` obligatorios) | Comportamiento | Pantalla `/admin/connectors` |

## Verificación
| Comprobación | Resultado |
|---|---|
| `tsc --noEmit` | 0 |
| `npm run lint` | 0 |
| `vitest run` | 0 (47 archivos, 1585 pruebas; accesibilidad 0 fallas) |
| `npm run build` | 0 |
| grep de `style=`, `<style`, `.style.`, colores literales e IPs | Sin coincidencias |
| Tema claro/oscuro, móvil y escritorio en navegador | No verificado (sin captura); solo tokens y clases ya usadas |
