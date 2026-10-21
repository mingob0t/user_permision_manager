'use client';

/**
 * Menú de navegación para pantallas menores a `md` (DIS-025): botón en la
 * cabecera y panel lateral con el contenido que pasa `AppShell`.
 *
 * - Se cierra con Escape, al elegir una opción (`close` que recibe el
 *   contenido) y al hacer clic fuera del panel.
 * - Al abrir, el foco va al primer enlace; al cerrar, vuelve al botón; con el
 *   panel abierto, Tab y Mayús+Tab no salen de él.
 * - La trampa de foco es mínima y local: el patrón compartido para `Modal` es
 *   DIS-031; cuando exista, este menú debería reutilizarlo.
 */

import { useCallback, useEffect, useId, useRef, useState } from 'react';

const ENFOCABLES = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function MobileMenu({
  children,
}: {
  children: (close: () => void) => React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const wasOpen = useRef(false);
  const panelId = useId();

  const close = useCallback(() => setOpen(false), []);

  // Foco al abrir (primer enlace) y al cerrar (el botón).
  useEffect(() => {
    if (open) {
      wasOpen.current = true;
      panel.current?.querySelector<HTMLElement>('a[href]')?.focus();
    } else if (wasOpen.current) {
      wasOpen.current = false;
      button.current?.focus();
    }
  }, [open]);

  // Escape, trampa de foco y clic fuera, solo con el panel abierto.
  useEffect(() => {
    if (!open) return;

    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault();
        setOpen(false);
        return;
      }
      if (event.key !== 'Tab' || !panel.current) return;
      const items = Array.from(panel.current.querySelectorAll<HTMLElement>(ENFOCABLES));
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement;
      const outside = !panel.current.contains(active);
      if (event.shiftKey && (active === first || outside)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (active === last || outside)) {
        event.preventDefault();
        first.focus();
      }
    }

    function onPointerDown(event: PointerEvent) {
      const target = event.target as Node | null;
      if (!target) return;
      // El botón alterna por su cuenta; el panel no cuenta como "fuera".
      if (panel.current?.contains(target) || button.current?.contains(target)) return;
      setOpen(false);
    }

    document.addEventListener('keydown', onKey);
    document.addEventListener('pointerdown', onPointerDown);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('pointerdown', onPointerDown);
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
        className="inline-flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded-lg border border-panel-border px-3 text-sm text-label hover:text-body-text md:hidden"
      >
        Menú
      </button>

      <div id={panelId} hidden={!open} className="md:hidden">
        <div
          ref={panel}
          role="dialog"
          aria-modal="true"
          aria-label="Menú"
          className="fixed inset-y-0 left-0 z-50 w-72 max-w-full overflow-y-auto border-r border-panel-border bg-panel-fill p-4 shadow-2xl"
        >
          <div className="flex items-center justify-between gap-2 pb-4">
            <p className="px-3 text-lg font-semibold">Nexus</p>
            <button
              type="button"
              onClick={close}
              className="inline-flex min-h-12 min-w-12 items-center justify-center rounded-lg border border-panel-border px-3 text-sm text-label hover:text-body-text"
            >
              Cerrar
            </button>
          </div>
          {children(close)}
        </div>
      </div>
    </>
  );
}
