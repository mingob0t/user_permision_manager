'use client';

/**
 * Menú de navegación para pantallas menores a `md` (DIS-025): botón en la
 * cabecera y panel lateral con el contenido que pasa `AppShell`.
 *
 * - Se cierra con Escape, al elegir una opción (`close` que recibe el
 *   contenido) y al hacer clic fuera del panel.
 * - Al abrir, el foco va al primer enlace; al cerrar, vuelve al botón; con el
 *   panel abierto, Tab y Mayús+Tab no salen de él. Trampa compartida con
 *   `Modal`: `useFocusTrap` (DIS-031).
 * - Con el panel abierto: velo `bg-overlay` detrás y desplazamiento del fondo
 *   bloqueado (`useScrollLock`, DIS-038).
 * - El velo y el panel se pintan en un portal en `document.body` (fuera de la
 *   raíz, que queda `inert` con el menú abierto); el portal se crea al montar
 *   en el cliente, nunca en el servidor.
 */

import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { enfocables, useFocusTrap } from '@/lib/use-focus-trap';
import { useScrollLock } from '@/lib/use-scroll-lock';

/** Desde `md` (768 px, breakpoint de Tailwind) el menú móvil no se muestra: se cierra. */
const CONSULTA_MD = '(min-width: 768px)';

export function MobileMenu({
  children,
}: {
  children: (close: () => void) => React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const [montado, setMontado] = useState(false);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => setMontado(true), []);

  // Primero el bloqueo: al cerrar, la raíz deja de ser `inert` antes de devolver el foco.
  useScrollLock(open);
  // Foco al primer enlace al abrir, atrapado con Tab, Escape cierra y el foco vuelve al botón.
  useFocusTrap(panel, {
    activo: open,
    alEscape: close,
    devolverA: button,
    focoInicial: (contenedor) => enfocables(contenedor).filter((el) => el.matches('a[href]')),
  });

  // Clic fuera y cruce de `md`, solo con el panel abierto.
  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      const target = event.target as Node | null;
      if (!target) return;
      // El botón alterna por su cuenta; el panel no cuenta como "fuera".
      if (panel.current?.contains(target) || button.current?.contains(target)) return;
      setOpen(false);
    }

    // Si la ventana cruza `md` con el menú abierto, el panel se oculta por CSS
    // y el foco quedaría atrapado: se cierra.
    const md = typeof window.matchMedia === 'function' ? window.matchMedia(CONSULTA_MD) : null;
    function onMedia(event: MediaQueryListEvent) {
      if (event.matches) setOpen(false);
    }
    if (md?.matches) {
      setOpen(false);
      return;
    }

    document.addEventListener('pointerdown', onPointerDown);
    md?.addEventListener('change', onMedia);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      md?.removeEventListener('change', onMedia);
    };
  }, [open]);

  return (
    <>
      <button
        ref={button}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className="inline-flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded-lg border border-panel-border px-3 text-sm text-label outline-none hover:text-body-text focus-visible:ring-2 focus-visible:ring-primary md:hidden"
      >
        Menú
      </button>

      {montado
        ? createPortal(
          <div id={panelId} hidden={!open} className="md:hidden">
            {/* Velo (DIS-038): el clic en él cierra por el oyente de clic fuera. */}
            <div aria-hidden="true" className="fixed inset-0 z-40 bg-overlay" />
            <div
              ref={panel}
              role="dialog"
              aria-modal="true"
              aria-label="Menú"
              tabIndex={-1}
              className="fixed inset-y-0 left-0 z-50 w-72 max-w-full overflow-y-auto border-r-2 border-primary bg-panel-fill p-4 shadow-2xl"
            >
              <div className="flex items-center justify-between gap-2 pb-4">
                <p className="px-3 text-lg font-semibold">Nexus</p>
                <button
                  type="button"
                  onClick={close}
                  className="inline-flex min-h-12 min-w-12 items-center justify-center rounded-lg border border-panel-border px-3 text-sm text-label outline-none hover:text-body-text focus-visible:ring-2 focus-visible:ring-primary"
                >
                  Cerrar
                </button>
              </div>
              {children(close)}
            </div>
          </div>,
          document.body,
        )
        : null}
    </>
  );
}
