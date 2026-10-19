# DIS-016 — Áreas: alta por el admin y asignación de admins por el superadmin

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | areas |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-016-pantalla-areas` (worktree `pokemon-wt-d016`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- En `/areas` (`areas-list.tsx`) solo el superadmin crea áreas; no hay forma explícita de asignar admins (F-AREA-01/02)
- Requerimientos: F-AREA-01, F-AREA-02, RF-04

## Objetivo
- Permitir al admin crear sus áreas y al superadmin asignar o quitar admins de un área

## Alcance
- **Incluye:**
  - Botón y formulario de alta visibles para `admin_area`
  - Panel "Administradores del área" solo para el superadmin, con búsqueda de usuarios
  - Lo nuevo en archivos propios; `areas-list.tsx` solo los importa
- **No incluye:**
  - Rediseño de la lista de áreas
  - Estilos inline existentes de `areas-list.tsx` (DIS-012)

## Archivos previstos
- `frontend/src/components/areas/area-admins-panel.tsx`
- `frontend/src/components/areas/area-form.tsx` (si se extrae el existente)
- `frontend/src/components/areas-list.tsx` (importaciones y permiso del botón)

## Archivos modificados
| Archivo | Cambio |
|---|---|
| `frontend/src/components/areas/area-form.tsx` (nuevo) | `AreaForm` extraído; errores por campo (`fields`, `aria-invalid`/`aria-describedby`) y mensajes 409; el alta no envía color si no se elige |
| `frontend/src/components/areas/area-admins-panel.tsx` (nuevo) | Panel "Administradores de <área>": cuentas `admin_area`, búsqueda, casillas, `usersApi.setManagedAreas`; quitar se confirma; carga, vacío, error y "Cambios guardados" |
| `frontend/src/components/areas/area-errors.ts` (nuevo) | `MENSAJES_AREAS` (tabla de errores del contrato), `mensajeDeError`, `erroresDeCampo` |
| `frontend/src/components/areas-list.tsx` | Importa lo anterior; `RequireRole any_admin`; "Nueva área" para admin de área; "Eliminar" en las áreas propias; "Administradores" solo superadmin; áreas creadas en la visita quedan gestionables; error de baja con mensaje del contrato |
| `frontend/tests/components/areas-list.test.tsx` (nuevo) | 15 pruebas: por rol, panel, 422, 409 y estados |
| `frontend/tests/accesibilidad/colores-literales.excepciones.ts` | Tope de `areas-list.tsx`: `hex` 2 → 0 (se quitó el literal) |

## Reutilización
- `Modal`, `Field`, `Select`, `Button`, `ConfirmDialog`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `areas-list.tsx` (`AreasList`) | Pantalla | `/areas` (`app/areas/page.tsx`) | Pruebas Vitest; visual pendiente |
| `colores-literales.excepciones.ts` | Datos de prueba | `colores-literales.test.ts` | `npm test` en verde |

Componentes compartidos (`form.tsx`, `ui.tsx`, `require-role.tsx`, `lib/`) reutilizados sin modificar.

Salida real de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `AreasList` | función | `frontend/src/components/areas-list.tsx` | `frontend/src/app/areas/page.tsx` | frontend/src | ☑ pruebas |
| `TopeLiterales` | tipo | `frontend/tests/accesibilidad/colores-literales.excepciones.ts` | `frontend/tests/accesibilidad/colores-literales.test.ts` | frontend/tests | ☑ |
| `remove` | función | `frontend/src/components/areas-list.tsx` | `app/modules/api/routes.py`, `platform-admin.tsx`, `users-list.tsx`, `lib/access/connectors.ts`, … | app/modules, frontend/src, frontend/tests, tests, tests/audit | Homónimo |
| `save` | función | `frontend/src/components/areas-list.tsx` | `app/modules/auth/routes.py`, `platform-admin.tsx`, `settings-panel.tsx`, … (+3) | app/modules, frontend/src, frontend/tests, tests | Homónimo |

- `remove` y `save`: homónimos; son funciones locales no exportadas (`remove` dentro de `AreasScreen`; `save` se movió a `AreaForm`); las coincidencias son otras funciones con el mismo nombre
- `TopeLiterales`: el tipo no cambió; solo bajó el tope de `areas-list.tsx`
- `AreasList`: misma exportación; cambia el comportamiento de `/areas` (validar por rol)

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- "Nueva área" por rol (`any_admin`), no por `can_manage_areas` (en `/me` sigue siendo `is_admin()`, FNC-045); backend sin tocar
- Admin de área ve "Eliminar" en sus áreas (contrato: `DELETE` 200 en las suyas; `409 area_con_otros_admins` lo explica)
- Asignación por área: panel con las cuentas `admin_area`; cada cambio llama a `managed-areas` con la lista completa del usuario (agrega o quita solo esta área)
- Quitar admins se confirma (`ConfirmDialog`, "Quitar"); tras un error se recarga el estado real (lo previo al error queda aplicado)
- El panel queda abierto tras guardar con "Cambios guardados" (no hay componente de éxito estándar)
- Alta sin color elegido: no se envía y el servidor aplica su color por omisión (mismo valor que fijaba la pantalla); evita el literal hex
- Áreas creadas en la visita se tratan como propias sin pedir `/me` otra vez
- `/areas` con `RequireRole any_admin` dentro del componente (estado "sin permiso"; sin tocar `app/`)
- Error de campo con `<span class="text-error">` local (`FieldError`); `Field` compartido sin cambios

## Propuestas
- Estándar de error por campo (`Field` con `error`, `aria-invalid`) y de mensaje de éxito: sugerir tarea DIS para `docs/estandarizacion/`
- `can_manage_areas` de `/me` para `admin_area`: tarea FNC si se quiere permiso explícito

## Criterios de aceptación
- [x] Un admin de área no ve el panel de asignación (prueba)
- [ ] Criterios comunes de diseño (FNC-037): pendiente la verificación visual

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm ci` | exit 0 |
| `npm test` | exit 0; 11 archivos, 273 pasan, 88 fallas esperadas (`it.fails` de contraste ya conocidas) |
| `npx vitest run tests/components/areas-list.test.tsx` | 15/15 pasan |
| `npm run lint` | exit 0; sin avisos ni errores |
| `npx eslint tests vitest.config.ts` | exit 0 |
| `npm run typecheck` | exit 0 |
| `npm run build` | exit 0; `/areas` 4.82 kB |
| `grep` estilos inline, `#hex`, `rgb(`, IPs en lo nuevo | Sin coincidencias; queda el `style={{}}` previo de `areas-list.tsx` (DIS-012, fuera de alcance) |

- No verificado: tema claro/oscuro, móvil/escritorio y contraste en pantalla (sin backend levantado en el worktree). Solo se usan componentes y clases existentes (`Modal`, `ConfirmDialog`, `Field`, `TextInput`, `Checkbox`, `Button`, `Badge`, `EmptyNote`, `ErrorNote`, `Spinner`, `text-error`, `text-label`, `text-primary`)
- Prueba de contraste y de colores literales siguen en verde; sin fallas nuevas
- Sin integración con el backend real; sin revisores (por instrucción del orquestador)

## Commits / PR
- Commit local `[DIS-016]` en `dis/DIS-016-pantalla-areas`; sin push, merge ni PR

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-044, FNC-045
- Contrato → docs/contratos/areas-y-roles.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada; En revisión |
