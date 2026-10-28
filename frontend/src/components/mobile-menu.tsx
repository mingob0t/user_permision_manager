'use client';

/**
 * Menú de navegación para pantallas menores a `md` (DIS-025): botón en la
 * cabecera y panel lateral Drawer con el contenido que pasa `AppShell` (DIS-061).
 *
 * - Se cierra con Escape, al elegir una opción (`close` que recibe el
 *   contenido) y al hacer clic fuera del panel.
 * - Atrapa foco y devuelve al botón con `Drawer` (`useFocusTrap`, DIS-031).
 * - Con el panel abierto: velo `bg-overlay` detrás y desplazamiento del fondo
 *   bloqueado (`useScrollLock`, DIS-038).
 */

import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { enfocables } from '@/lib/use-focus-trap';
import { Button } from './form';
import { Drawer } from './drawer';

/** Desde `md` (768 px, breakpoint de Tailwind) el menú móvil no se muestra: se cierra. */
const CONSULTA_MD = '(min-width: 768px)';

export function MobileMenu({
  children,
}: {
  children: (close: () => void) => React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  const close = useCallback(() => setOpen(false), []);

  // Cierra si la pantalla supera md
  useEffect(() => {
    if (!open) return;
    const md = typeof window.matchMedia === 'function' ? window.matchMedia(CONSULTA_MD) : null;
    function onMedia(event: MediaQueryListEvent) {
      if (event.matches) setOpen(false);
    }
    if (md?.matches) {
      setOpen(false);
      return;
    }
    md?.addEventListener('change', onMedia);
    return () => {
      md?.removeEventListener('change', onMedia);
    };
  }, [open]);

  return (
    <>
      <Button
        ref={button}
        variant="secondary"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className="min-h-12 min-w-12 shrink-0 md:hidden focus-visible:ring-2 focus-visible:ring-primary"
      >
        Menú
      </Button>

      <Drawer
        id={panelId}
        open={open}
        onClose={close}
        devolverA={button}
        focoInicial={(contenedor) => enfocables(contenedor).filter((el) => el.matches('a[href]'))}
        title="Nexus"
        ariaLabel="Menú"
        className="md:hidden"
      >
        {children(close)}
      </Drawer>
    </>
  );
}
