# DIS-075 — Migrar los confirmar y avisos actuales a `AlertDialog` o toast según la tabla de decisión

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-075-migrar-confirmar-y-avisos` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- 6 `ConfirmDialog`, 6 diálogos propios (`approve`, `reject`, `connector-delete`, `job-retry`, `admin-role`, `revoke-access`), `SuccessNote` en 11 archivos y 2 toasts (plan §2.9).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Cada confirmación y aviso usa el patrón de la tabla de decisión (plan §4.7).

## Alcance
- **Incluye:**
  - Los 6 diálogos propios sobre `AlertDialog` (con cuerpo de campos donde lo tienen)
  - Revisar los 6 `ConfirmDialog` (tipo, verbo del botón)
  - Clasificar los 11 `SuccessNote` y los 2 toasts: rutina → toast; resultado que hay que leer → `AlertDialog`; estado persistente → `Note`; lista en la ficha
  - Retirar sus excepciones
- **No incluye:**
  - Textos nuevos salvo el verbo del botón; flujos o llamadas a la API

## Archivos previstos
- `access/approve-dialog.tsx`, `access/reject-dialog.tsx`, `connectors/connector-delete-dialog.tsx`, `connectors/job-retry-dialog.tsx`, `users/admin-role-dialog.tsx`, `users/revoke-access-dialog.tsx`
- Los 6 usuarios de `ConfirmDialog` y los 11 de `SuccessNote` (plan §2.9)

## Reutilización
`AlertDialog`, `ConfirmDialog`, `useToast`, `Note`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Diálogos de confirmación | componentes | Aprobaciones, Usuarios, Conectores, Ejecuciones, Áreas, Notificaciones, Administrar plataformas, Ajustes | No |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [ ] Pruebas de cada diálogo y pantalla en verde (con el foco nuevo)
- [ ] Clasificación de cada aviso anotada en la ficha
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← DIS-074
- Depende de → DIS-074

## Riesgos y reversión
Toca archivos de pantallas que luego migran D1–D2: va antes que ellas.

## Verificación
Pendiente (tarea en Propuesta).

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | | |
| revisor | | |
| auditor-accesibilidad | | |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
