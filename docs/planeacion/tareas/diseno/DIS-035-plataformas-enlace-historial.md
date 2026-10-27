# DIS-035 — Administrar plataformas: enlace al historial y acciones de fila de 48 px

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Aprobada** | 2026-10-27 (modo autónomo del orquestador) |
| **Inicio** | 2026-10-27 |
| **Rama** | `dis/DIS-008-035-areas-tactiles` (junto con DIS-008) |
| **Estatus Git** | Commit local, sin push |
| **Creada** | 2026-10-20 |

## Contexto
- DIS-020 creó `/audit/platforms/[id]` y lo enlaza desde Inventario y (por usuario) desde Usuarios
- La ficha de DIS-020 pedía enlazarlo también desde Plataformas; en `platform-admin.tsx` las acciones de fila ("Editar", "Eliminar") son botones de texto de ~28 px, sin el estándar de 48 px

## Objetivo
- Acción "Historial" por plataforma (`rutaHistorialPlataforma` de `components/audit/audit-routes.ts`) junto con Editar y Eliminar, todas con 48 px (`.nexus-btn` o un menú de fila)

## Impacto cruzado
- Origen ← DIS-020
- Relacionada → DIS-008 (área táctil de botones de fila), DIS-032

## Implementación
| Archivo | Cambio |
|---|---|
| `frontend/src/components/platform-admin.tsx` | Celda de acciones: `Link` "Historial" a `rutaHistorialPlataforma(id)` con `aria-label` "Historial de {nombre} en Auditoría"; Editar y Eliminar con `ACCION_FILA` / `ACCION_FILA_PELIGRO` (48 px, `min-w-12`, foco `ring-primary`); una línea (`whitespace-nowrap`, `flex gap-1`), celda `py-1` |
| `frontend/src/components/acciones-fila.ts` | Nuevo (compartido con DIS-008) |
| `frontend/tests/components/platform-admin.test.tsx` | Prueba: `href` `/audit/platforms/12`, nombre accesible y clases de 48 px y foco en las tres acciones |
| `docs/frontend/README.md` | `/admin/platforms` y `/audit/platforms/[id]` |

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
1. "Historial" usa `ACCION_FILA` y no `.nexus-btn-secondary` (como se pidió, siguiendo a Inventario): en la fila conviven tres acciones de texto y `.nexus-btn` mide al menos 140 px y va en mayúsculas; con la misma clase las tres se ven y se comportan igual. Si el dueño prefiere `.nexus-btn-secondary`, es cambiar una clase
2. "Historial" se muestra a todo el que ve la pantalla (`any_admin`, igual que `/audit/platforms/[id]`), no solo con `canManage`
3. Sin menú de fila: tres acciones caben en una línea (≈ 240 px) dentro de la tabla con `min-w-[44rem]` y desplazamiento horizontal

## Pantallas afectadas
- `/admin/platforms` (filas), `/audit/platforms/[id]` (nuevo punto de entrada)

## Verificación (2026-10-27)
- Typecheck, lint, vitest (1277) y build con código 0; detalle en la ficha de DIS-008
- No verificado en navegador (temas, móvil, alto de fila)

## Impacto en elementos compartidos
- `ACCION_FILA` / `ACCION_FILA_PELIGRO` (nuevo): Usuarios, Áreas, Administrar plataformas. Tabla completa de `impacto.py` en la ficha de DIS-008
- `rutaHistorialPlataforma`: solo se agrega un uso

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (origen DIS-020) |
| 2026-10-27 | Aprobada en modo autónomo, En curso e implementada con DIS-008; En revisión (sin revisor ni auditores; no verificada en navegador) |
