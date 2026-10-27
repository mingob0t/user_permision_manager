'use client';

/**
 * Bloqueo del desplazamiento del fondo (DIS-038) con una clase en `<html>`,
 * sin `el.style` (lineamiento). Lo usan `Modal` y `MobileMenu`.
 *
 * Cuenta los bloqueos activos: con dos diálogos abiertos, la clase se quita
 * solo cuando se cierra el último. La regla vive en `styles/global.css`.
 */

import { useEffect } from 'react';

export const CLASE_SCROLL_BLOQUEADO = 'scroll-bloqueado';

let bloqueos = 0;

export function useScrollLock(activo = true) {
  useEffect(() => {
    if (!activo) return;
    bloqueos += 1;
    document.documentElement.classList.add(CLASE_SCROLL_BLOQUEADO);
    return () => {
      bloqueos -= 1;
      if (bloqueos === 0) document.documentElement.classList.remove(CLASE_SCROLL_BLOQUEADO);
    };
  }, [activo]);
}
