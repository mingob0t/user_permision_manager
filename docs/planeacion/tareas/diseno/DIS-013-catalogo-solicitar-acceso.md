# DIS-013 — Catálogo: solicitar acceso con nivel y justificación

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | catalogo |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-013-catalogo-solicitar` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El catálogo (`platform-catalog.tsx`, `platform-card.tsx`) solo abre enlaces y marca favoritos; no permite solicitar (F-SOL-01)
- El admin lo usa para áreas ajenas
- Requerimientos: F-SOL-01, F-SOL-02, RF-03

## Objetivo
- Mostrar el catálogo solicitable por área con el estado del usuario en cada plataforma (sin acceso, pendiente, con acceso y nivel) y un formulario modal para solicitar nivel `usuario` o `admin` con justificación

## Alcance
- **Incluye:**
  - Vista del catálogo solicitable con filtro por área y búsqueda
  - Indicador de estado por tarjeta (texto + insignia, no solo color)
  - Modal de solicitud: nivel (radio), justificación con contador y validación visible, envío y confirmación
  - Mensajes para 409 (duplicado o ya tiene acceso)
- **No incluye:**
  - Mis solicitudes (DIS-014)
  - Rediseñar la tarjeta existente fuera de lo necesario

## Archivos previstos
- `frontend/src/components/access/request-catalog.tsx`
- `frontend/src/components/access/request-form-modal.tsx`
- `frontend/src/components/access/access-status-badge.tsx` (reutilizable)
- `frontend/src/app/platforms/page.tsx` según P1

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `frontend/src/components/access/request-catalog.tsx` | Nuevo: pantalla, filtro por área y búsqueda en cliente, estados, aviso `status` |
| `frontend/src/components/access/request-catalog-card.tsx` | Nuevo: tarjeta con estado y acción |
| `frontend/src/components/access/request-form-modal.tsx` | Nuevo: modal con nivel (radio) y justificación opcional con contador |
| `frontend/src/components/access/access-status-badge.tsx` | Nuevo, reutilizable: `AccessStatusBadge`, `NIVELES` |
| `frontend/src/components/access/request-errors.ts` | Nuevo: mensajes de `POST /access-requests` y de la carga |
| `frontend/src/app/platforms/page.tsx` | Compone `RequestCatalog` y, debajo, `PlatformCatalog` |
| `frontend/src/components/platform-catalog.tsx` | Solo el encabezado: `h1` "Plataformas" → `h2` "Mis plataformas" |
| `frontend/src/lib/access/types.ts` | FNC-090: `justification` opcional |
| `frontend/tests/components/access/request-catalog.test.tsx` | Nuevo: 26 pruebas |
| `frontend/tests/lib/access/peticiones.test.ts` | Caso "crear solicitud sin justificación" (Content-Type JSON) |

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- `/platforms` muestra el catálogo solicitable arriba (`h1` "Catálogo") y "Mis plataformas" (el `PlatformCatalog` de siempre, con enlace y favorito) debajo: el catálogo del contrato no trae `direct_link`, así que reemplazarlo quitaría abrir las plataformas. Unificar ambas vistas: DIS-030.
- `PlatformCard` no se reutiliza ni se toca: `CatalogItem` no es una `Platform` y usa estilos inline heredados; la tarjeta nueva copia su caja con clases existentes.
- Filtro por área y búsqueda en el cliente con una sola carga (el catálogo no se pagina); el selector de área se arma con las áreas del propio catálogo.
- Tras enviar: la tarjeta pasa a "Solicitud pendiente" con el id devuelto, sin volver a pedir el catálogo; el aviso va en una región `role="status"` siempre montada que recibe el foco (el botón de la tarjeta desaparece).
- Justificación vacía → no se envía el campo (el contrato la acepta ausente o `null`); se cuenta y valida recortada, como el backend; > 500 se marca en vivo (`aria-invalid` + `aria-describedby`) y al enviar se anuncia con `role="alert"` y foco en el campo.
- Sin `maxLength` en el campo, para que el exceso se vea y se anuncie en lugar de cortar el texto en silencio.
- Nivel por omisión: el primero de `requestable_levels`.
- Errores con mensaje propio por `code` (`request-errors.ts`); 401/403/404 sin código y 5xx con mensaje fijo, sin texto del servidor.
- Sin acción, la tarjeta explica el motivo: pendiente, superadmin, área que administra, ya tiene admin, o "No disponible para solicitar".
- Foco del diálogo: `Modal` enfoca el panel al abrir; al cerrar, la pantalla devuelve el foco al botón que lo abrió. `Modal` no atrapa el foco con Tab (compartido, no se toca): DIS-031.
- Radios nativos con `accent-primary` y caja `has-[:checked]:border-primary` (utilidades Tailwind sobre tokens existentes; no hay radio en el estándar).

## Reutilización
- `Modal`, `Field`, `TextArea`, `Button` de `form.tsx`; `Badge`, `Spinner`, `EmptyNote`, `ErrorNote` de `ui.tsx`; `PlatformCard` si admite la acción sin cambiar su uso en Favoritos

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `PlatformCard` | Componente | Catálogo y Favoritos (`favorites-list.tsx`) | No se modificó |
| `PlatformCatalog` (encabezado) | Componente | Solo `/platforms` | Pendiente (dueño) |
| `AccessRequest.justification`, `AccessRequestInput.justification` | Tipo | `lib/access/requests.ts`, `mocks.ts`; DIS-014, DIS-015 | Typecheck y pruebas en verde |
| `Page` de `/platforms` | Función | Falso positivo de `impacto.py` (mismo nombre en cada `page.tsx`) | N/A |

Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `AccessRequest` | tipo | `frontend/src/lib/access/types.ts` | `app/modules/access_requests/serializacion.py`, `frontend/src/lib/access/mocks.ts`, `frontend/src/lib/access/requests.ts` | app/modules, frontend/src | ☐ (el `.py` es coincidencia de nombre) |
| `AccessRequestInput` | tipo | `frontend/src/lib/access/types.ts` | `frontend/src/lib/access/requests.ts` | frontend/src | ☐ |
| `Page` | función | `frontend/src/app/platforms/page.tsx` | `frontend/src/app/*/page.tsx` (+6) | frontend/src | ☐ (falso positivo) |

Reutilizados sin modificar: `Modal`, `Field`, `TextArea`, `TextInput`, `Select`, `Button` (`form.tsx`); `Card`, `Badge`, `Spinner`, `EmptyNote`, `ErrorNote` (`ui.tsx`); `FieldErrorNote`, `FieldHint`, `describedBy` (`platforms/field-notes.tsx`); `useAsync`, `useSession`, `requestsApi`.

## Criterios de aceptación
- [x] La justificación inválida se anuncia al lector de pantalla (prueba "justificación de más de 500")
- [x] Tras enviar, el estado de la tarjeta cambia a "pendiente" sin recargar (prueba "sin justificación")
- [ ] Criterios comunes de diseño (FNC-037): tokens, sin inline, estados y teclado verificados; tema claro/oscuro y responsive no verificados visualmente

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm ci` | Salida 0 (los `node_modules` del worktree estaban incompletos) |
| `npx vitest run` antes del cambio | 472 passed, 25 expected fail; salida 0 |
| `npm run typecheck` | Salida 0 |
| `npm run lint` | "No ESLint warnings or errors"; salida 0 |
| `npx eslint tests/components/access tests/lib/access` | Salida 0 |
| `npx vitest run` | 15 archivos; 499 passed, 25 expected fail (las mismas de DIS-004/005/006), incluidas contraste y colores literales; salida 0 |
| `grep` de `style=`, `<style`, `.style.`, `#hex`, `rgb(`, paleta fija e IPs en los archivos tocados | Sin coincidencias |

- Pruebas nuevas: carga, vacío, error con reintento, 403 al cargar; insignias y acción por estado; filtro y búsqueda; superadmin y admin de área; envío sin y con justificación; > 500; Escape y foco; 409 (5 códigos), 403 `sin_permiso`, 422 con campo, 500 genérico; doble envío.
- `POST` con `Content-Type: application/json`: lo añade `apiRequest` cuando hay cuerpo y `jsonBody` siempre manda cuerpo; cubierto por `peticiones.test.ts` (también sin justificación).
- **No verificado:** tema claro y oscuro, móvil y escritorio en el navegador (la app exige sesión del backend y no se levantó); solo se usan clases y tokens existentes, medidos por `contraste.test.ts`. Sin revisor, tester, auditor-accesibilidad ni auditor-seguridad (no se lanzaron, por instrucción).

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-056
- Contrato → docs/contratos/solicitudes.md
- Absorbe → FNC-090 (resuelta en DIS-013)
- Genera → DIS-030, DIS-031

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | FNC-070: el menú ya dice "Catálogo" pero el título de la pantalla (`platform-catalog.tsx`) sigue diciendo "Plataformas"; alinearlo aquí |
| 2026-10-20 | Aprobada en modo autónomo y En curso; rama `dis/DIS-013-catalogo-solicitar` desde develop (c80f906) |
| 2026-10-20 | Implementada: catálogo solicitable, modal de solicitud, `AccessStatusBadge`; título "Catálogo"; absorbe FNC-090 (tipos). Propone DIS-030 y DIS-031. En revisión |
