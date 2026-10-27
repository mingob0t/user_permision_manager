# DIS-064 — Pantallas de usuario final: Inicio, Plataformas, Favoritos, Mis solicitudes y accesos, Notificaciones

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | pantallas-usuario |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-064-pantallas-usuario-final` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Pantallas: Inicio, Plataformas, Favoritos, Mis solicitudes, Notificaciones. Hoy componen encabezado, filtros, listas y estados a mano (plan §2.6-2.8).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Migrar cada pantalla a su plantilla y a los componentes comunes, sin cambiar funcionalidad, con CLS ≈ 0.

## Alcance
- **Incluye:**
  - Cada pantalla sobre `PantallaListado`/`Detalle`/`Formulario`/`Panel` y `PageHeader`
  - Carga con `Skeleton`, avisos en zona reservada
  - Retirar todas las excepciones de `patrones-unicos`, `escala-simetria` y `estados-con-token` de estos archivos
  - Revisión visual por pantalla (claro/oscuro, 360/1280 px, carga/vacío/error) y CLS medido; resultado en la ficha
- **No incluye:**
  - Funcionalidad, textos, datos, rutas o permisos
  - Componentes comunes (si falta algo, se registra como tarea)

## Archivos previstos
- `dashboard.tsx`, `home/role-summary.tsx`, `app/platforms/page.tsx`, `platforms-view.tsx`, `access/request-catalog*.tsx`, `access/catalog-*.tsx`, `favorites-list.tsx`, `platform-card.tsx`, `access/my-requests*.tsx`, `access/my-access.tsx`, `notifications-list.tsx`

## Reutilización
Plantillas (DIS-070) y componentes de C1–C5.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Pantallas listadas | vistas | solo estas pantallas | No |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [ ] Pruebas de cada pantalla en verde sin cambiar su comportamiento
- [ ] CLS < 0,01 en las pantallas principales del grupo (medido)
- [ ] Sin excepciones restantes en estos archivos, o con motivo
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §7
- Depende de → DIS-070, DIS-075

## Riesgos y reversión
Cambio visible amplio: verificación por pantalla; reversión por commit de pantalla.

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
