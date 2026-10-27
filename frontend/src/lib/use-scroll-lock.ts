'use client';

/**
 * Bloqueo del fondo mientras hay un diálogo o el menú móvil abiertos
 * (DIS-038, DIS-044), sin `el.style`. Lo usan `Modal` y `MobileMenu`, que se
 * pintan en un portal en `document.body`, fuera de la raíz.
 *
 * - Pone la clase `scroll-bloqueado` en la raíz de la app (`#raiz-app`): la
 *   regla de `styles/global.css` quita el desplazamiento a la raíz y a los
 *   contenedores `[data-desplazable]` de dentro (el `<main>` de `AppShell`).
 * - Marca la raíz `inert`: lo de detrás no recibe foco, clics ni lectores de
 *   pantalla (H2 de auditor-accesibilidad).
 * - Cuenta los bloqueos activos: con dos diálogos, se libera al cerrar el último.
 * - El componente lo declara ANTES de `useFocusTrap`: al cerrar, React corre
 *   las limpiezas en orden y la raíz deja de ser `inert` antes de devolver el foco.
 */

import { useEffect } from 'react';
import { RAIZ_APP_ID } from './raiz-app';

export const CLASE_SCROLL_BLOQUEADO = 'scroll-bloqueado';

let bloqueos = 0;

function raiz(): HTMLElement | null {
  return document.getElementById(RAIZ_APP_ID);
}

export function useScrollLock(activo = true) {
  useEffect(() => {
    if (!activo) return;
    bloqueos += 1;
    raiz()?.classList.add(CLASE_SCROLL_BLOQUEADO);
    raiz()?.setAttribute('inert', '');
    return () => {
      bloqueos -= 1;
      if (bloqueos > 0) return;
      raiz()?.classList.remove(CLASE_SCROLL_BLOQUEADO);
      raiz()?.removeAttribute('inert');
    };
  }, [activo]);
}
