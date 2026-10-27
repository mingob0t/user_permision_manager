# DIS-049 — Toast: pausa al pasar el cursor o enfocar, y cierre accesible con diálogo abierto

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
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

## Implementación
- `toast.tsx`: `Tarjeta` pausa el temporizador con `mouseenter`/`focus` y lo reanuda completo (`TOAST_MS`) al salir cuando no queda cursor ni foco; el error no tiene temporizador y no se ve afectado.
- Verificado con prueba: con diálogo abierto, Tab NO llegaba al toast (la trampa solo cicla dentro del diálogo y el portal del aviso queda fuera). Corrección mínima: `use-focus-trap.ts` incluye en el ciclo las regiones con `data-fuera-de-trampa` (la del toast) y las recorre a mano.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): el cambio va en la trampa compartida (no en `Modal`), con un atributo de marca en lugar de acoplar el hook al toast.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): al reanudar corre `TOAST_MS` completo, no el resto.

## Impacto en elementos compartidos
- `src/lib/use-focus-trap.ts` (`useFocusTrap`): lo usan `Modal`/`ConfirmDialog` (`form.tsx`) y `mobile-menu.tsx`. Sin región marcada el comportamiento no cambia.
- `Modal`/`ConfirmDialog` no se modificaron; sus 18 archivos de uso: access/{approve,reject}-dialog, access/request-form-modal, areas/{area-form,area-admins-panel}, areas-list, audit/audit-detail-modal, connectors/{connector-delete-dialog,job-detail-modal,job-retry-dialog}, notifications-list, platform-admin, platforms/platform-form, users/{admin-role-dialog,directory-account-form,revoke-access-dialog}, users-list (más form.tsx). Con cualquiera abierto y un aviso visible, Tab incluye «Cerrar aviso» al final del ciclo.
- `toast.tsx`: lo usan `layout.tsx`, `platform-card.tsx` y consumidores de `useToast`.

## Verificación
- typecheck 0, lint 0, vitest 0 (41 archivos, 1515 pruebas, incluidas las de accesibilidad), build 0.
- 4 pruebas nuevas en `tests/components/componentes-comunes.test.tsx`: pausa con cursor, con foco, error sin temporizador, Tab con diálogo abierto y raíz `inert`.
- No verificado en navegador real (sin estilos nuevos, el tema no cambia).

## Correcciones de la auditoría de accesibilidad
- Decisión del orquestador (pendiente de validar en la prueba de concepto): foco al cerrar el aviso (medio): `useFocusTrap` observa el DOM (`MutationObserver`) y, si el foco venía de una región `data-fuera-de-trampa` y cae a `body`, lo devuelve al diálogo (no depende de `focusout`, que no se dispara al desmontar). Pruebas: cierre con clic y cierre programático.
- Escape con el foco en el aviso (bajo): ese foco cuenta como `libre` al desmontar la trampa; el foco vuelve al disparador. Prueba incluida.
- Toque (dudoso): `onPointerEnter`/`onPointerLeave` y pausa solo con `pointerType === 'mouse'`. Prueba con `touch`. Sigue pendiente de probar en un dispositivo táctil real.
- Verificación: tsc 0, lint 0, vitest 0 (1518), build 0.

- 2026-10-27: `auditor-accesibilidad` Aprobado tras corregir 2 hallazgos de foco y el de pausa táctil (`41d3045`). Mejora opcional pendiente: crear el `MutationObserver` solo cuando el foco entra a una región `data-fuera-de-trampa` (hoy cada trampa activa vigila `body` aunque no haya aviso; sin efecto de conducta). Pausa táctil sin probar en dispositivo real. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
