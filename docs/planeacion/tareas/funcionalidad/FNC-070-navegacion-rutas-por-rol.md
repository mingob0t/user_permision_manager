# FNC-070 — Navegación y rutas por rol del gestor de accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | navegacion |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Estatus Git** | `fnc/FNC-070-navegacion-por-rol` (commit local, sin push) |
| **Rama** | `fnc/FNC-070-navegacion-por-rol` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El menú (`NAV` en `frontend/src/components/app-shell.tsx`) solo distingue `any_admin`; la fase agrega Mis solicitudes, Aprobaciones, Inventario y Conectores con visibilidad por rol (tabla de pantallas)
- La barra lateral se oculta en móvil sin alternativa (deuda 8 del frontend)
- Requerimientos: Tabla de pantallas por rol (REQUERIMIENTOS §4)

## Objetivo
- Agregar las entradas nuevas con su permiso, una guarda de ruta reutilizable que muestra el estado "sin permiso" y las rutas de página vacías que llenarán las tareas DIS

## Alcance
- **Incluye:**
  - Entradas: Mis solicitudes (todos), Aprobaciones (`any_admin`), Inventario (todos, alcance por rol), Conectores (`admin`); "Plataformas" pasa a mostrarse como Catálogo según DIS-013
  - Componente `RequireRole` en `components/require-role.tsx`
  - Rutas `/requests`, `/approvals`, `/inventory`, `/admin/connectors`
- **No incluye:**
  - Menú móvil (deuda 8: se registra como sugerencia o la toma DIS-011/fase 4)
  - Contenido de las pantallas

## Archivos previstos
- `frontend/src/components/app-shell.tsx` (solo `NAV`)
- `frontend/src/components/require-role.tsx`
- `frontend/src/app/{requests,approvals,inventory,admin/connectors}/page.tsx`

## Reutilización
- `useSession`, `ErrorNote`/`EmptyNote` de `ui.tsx`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `NAV` de `app-shell.tsx` (entradas nuevas, "Plataformas" → "Catálogo", filtro con `meetsRequirement`) | Navegación compartida | Todas las pantallas con `AppShell` (13 rutas autenticadas) | Pendiente |
| `RequireRole`, `meetsRequirement` (nuevos) | Componente / utilidad | `app-shell.tsx`, `/requests`, `/approvals`, `/admin/connectors` | Pendiente |

Salida real de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Page` | función | `frontend/src/app/admin/connectors/page.tsx`, `frontend/src/app/approvals/page.tsx`, `frontend/src/app/inventory/page.tsx`, `frontend/src/app/requests/page.tsx` | `frontend/src/app/admin/platforms/page.tsx`, `frontend/src/app/areas/page.tsx`, `frontend/src/app/audit/page.tsx`, `frontend/src/app/favorites/page.tsx`, `frontend/src/app/login/page.tsx`, `frontend/src/app/logout/page.tsx`, `frontend/src/app/notifications/page.tsx`, `frontend/src/app/page.tsx` (+3) | frontend/src | ☐ |
| `Pantalla` | función | `frontend/tests/components/navegacion-por-rol.test.tsx` | `frontend/src/components/login-form.tsx`, `frontend/src/components/session-provider.tsx` | frontend/src | ☐ |
| `Rol` | tipo | `frontend/tests/components/navegacion-por-rol.test.tsx` | `app/authz.py`, `frontend/src/components/users-list.tsx`, `frontend/tests/components/users-list.test.tsx`, `tests/fabricas.py`, `tests/test_proteccion_por_rol.py`, `tests/test_sso.py`, `utils/check_db.py` | app, frontend/src, frontend/tests, tests, utils | ☐ |
| `sesion` | función | `frontend/tests/components/navegacion-por-rol.test.tsx` | `tests/conftest.py` | tests | ☐ |

- Las 4 filas son **homónimos**: `Page` es el export obligatorio de cada página del App Router; `Pantalla`, `Rol` y `sesion` son locales de la prueba nueva; ninguno se modificó en otro archivo
- `impacto.py` no detecta `NAV` (constante); se reporta a mano arriba

## Criterios de aceptación
- [x] Cada rol ve exactamente las entradas de la tabla de pantallas (prueba de componente)
- [x] Una ruta sin permiso muestra el estado "sin permiso" y no llama a la API
- [ ] Criterios comunes web (FNC-037): pendiente `auditor-accesibilidad` y revisión visual (no lanzados por instrucción)

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- "Mis solicitudes" solo para `usuario` y `admin_area` (requisito `requester`): la ficha decía "todos", pero la tabla de pantallas y el Anexo A dan "—"/"Ver" al superadmin
- "Catálogo" (`/platforms`) sigue visible al superadmin: Anexo A le da "Ver"; la tabla dice "—"
- "Inventario" visible para todos sin guarda (Anexo A: el usuario ve "los propios"; el backend limita)
- Estado "sin permiso" con `ErrorNote` (rol `alert`) y el texto "No tienes permiso para ver esta sección."
- Rutas existentes (`/areas`, `/users`, `/admin/platforms`) sin `RequireRole`: fuera del alcance de la ficha
- Etiquetas existentes sin cambios salvo "Plataformas" → "Catálogo"; "Ajustes" sigue para todos (incluye "Mis preferencias")

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm ci` | código 0 |
| `npm test` | código 0; 9 archivos, 241 pasan, 88 fallas esperadas (`it.fails` conocidas); nueva `tests/components/navegacion-por-rol.test.tsx`: 12 pasan |
| `npm run lint` | código 0; sin avisos ni errores |
| `npx eslint tests/components/navegacion-por-rol.test.tsx` | código 0 |
| `npm run typecheck` | código 0 |
| `npm run build` | código 0; 18 páginas, incluye `/requests`, `/approvals`, `/inventory`, `/admin/connectors` |

- No verificado: vista en navegador (tema claro/oscuro, móvil/escritorio) ni `auditor-accesibilidad`; solo se usan clases ya existentes (`text-2xl font-semibold`, `text-label`, `EmptyNote`, `ErrorNote`)
- `auditor-accesibilidad` (modo cambio): Con observaciones. Estructura OK (un h1, aria-current, alert/status, sin inline ni literales); contraste falla en EmptyNote `text-label/60` (3.35 claro, 3.31 oscuro), ErrorNote `text-error` en claro (3.30) y entrada activa del menú `text-primary` sobre `bg-primary/15` (4.19 claro, 3.01 oscuro). Los tres son tokens/componentes preexistentes, no nuevos de FNC-070
- Prueba de colores literales en verde: sin literales nuevos

## Revisiones
- `auditor-accesibilidad`: Con observaciones heredadas (3 fallas de contraste de componentes previos, anotadas en DIS-005, DIS-002 y DIS-001)
- `revisor`: Requiere cambios, corregido:
  - prueba intermitente: el caso permitido espera con `findByText` y `waitFor`; `npm test` 10/10 en serie y 4/4 en paralelo, código 0
  - `NAV` ya no se exporta (nada lo importaba)
  - DIS-013: anotado que el título del catálogo dice "Plataformas" y el menú "Catálogo"
  - navegación en móvil registrada como DIS-025 (Propuesta)
- Tras las correcciones: `npm test` (241 pasan, 88 fallas esperadas), `lint`, `typecheck` y `build`: código 0

## Commits / PR
- `b608396` [FNC-070] implementación; segundo commit [FNC-070] con las correcciones de revisión; sin push ni PR

## Impacto cruzado
- Genera → DIS-013 a DIS-024
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada por el dueño (modo autónomo); implementada: `RequireRole`, `NAV` por rol y 4 rutas; pasa a En revisión |
| 2026-10-19 | Correcciones de revisión (prueba estable, `NAV` sin export, notas en DIS-001/002/005/013, DIS-025); sigue En revisión |
- Cierre (2026-10-19): revisor y auditor-accesibilidad atendidos (contrastes heredados en DIS-001/002/005; móvil en DIS-025); merge local a `develop` (modo autónomo).
