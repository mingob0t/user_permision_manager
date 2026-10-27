# DIS-049 — Toast: pausa al pasar el cursor o enfocar, y cierre accesible con diálogo abierto

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Rama** | `dis/DIS-049-toast-pausa-y-foco` |
| **Creada** | 2026-10-27 |

## Contexto
- Observaciones no bloqueantes del `auditor-accesibilidad` sobre DIS-010 (`src/components/toast.tsx`).
- El toast de éxito se cierra a los `TOAST_MS` (6 s) aunque el cursor o el foco estén sobre él (WCAG 2.2.1).
- El toast de error es persistente y vive en un portal fuera de la raíz: con un diálogo abierto, la trampa de foco podría impedir llegar a su botón «Cerrar aviso» (sin verificar).

## Objetivo
- Pausar el temporizador en `onMouseEnter`/`onFocus` y reanudar al salir.
- Verificar con teclado el cierre del toast de error con un diálogo abierto; corregir si no es alcanzable.
- Pruebas de componente de ambos casos.

## Impacto cruzado
- Origen ← DIS-010
