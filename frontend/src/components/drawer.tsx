'use client';

/**
 * Drawer (panel lateral emergente / off-canvas) accesible (DIS-061).
 *
 * Base compartida de paneles laterales y navegación móvil:
 * - Atrapa foco con `useFocusTrap`, cierra con Escape y devuelve el foco al botón de apertura.
 * - Bloquea scroll del fondo con `useScrollLock` y velo accesible (`bg-overlay`).
 * - Se monta vía portal en `document.body` y expone `role="dialog"` con `aria-modal="true"`.
 */

import React, { useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Button } from './button';
import { useFocusTrap } from '@/lib/use-focus-trap';
import { useScrollLock } from '@/lib/use-scroll-lock';

export interface DrawerProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  ariaLabel?: string;
  position?: 'left' | 'right';
  width?: string;
  id?: string;
  className?: string;
  devolverA?: React.RefObject<HTMLElement | null>;
  focoInicial?: (contenedor: HTMLElement) => HTMLElement[];
}

export function Drawer({
  open,
  onClose,
  children,
  title,
  ariaLabel,
  position = 'left',
  width = 'w-72 max-w-full',
  id,
  className = '',
  devolverA,
  focoInicial,
}: DrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  useScrollLock(open);
  useFocusTrap(panelRef, {
    activo: open,
    alEscape: onClose,
    devolverA,
    focoInicial,
  });

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      const target = event.target as Node | null;
      if (!target) return;
      if (
        panelRef.current?.contains(target) ||
        (devolverA?.current && devolverA.current.contains(target))
      ) {
        return;
      }
      onClose();
    }

    document.addEventListener('pointerdown', onPointerDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
    };
  }, [open, onClose, devolverA]);

  if (typeof document === 'undefined') return null;

  const borderClass =
    position === 'right'
      ? 'right-0 border-l border-panel-border'
      : 'left-0 border-r-2 border-primary';

  return createPortal(
    <div id={id} hidden={!open} className={`relative z-50 ${className}`}>
      {open ? (
        <>
          {/* Velo de fondo accesible con clic para cerrar */}
          <div
            aria-hidden="true"
            data-testid="drawer-backdrop"
            onClick={onClose}
            className="fixed inset-0 z-40 bg-overlay backdrop-blur-xs transition-opacity motion-reduce:transition-none"
          />

          <div
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-label={ariaLabel ?? (title ? undefined : 'Panel lateral')}
            aria-labelledby={ariaLabel ? undefined : (title ? titleId : undefined)}
            tabIndex={-1}
            className={`fixed inset-y-0 ${borderClass} z-50 ${width} overflow-y-auto bg-panel-fill p-4 shadow-2xl outline-none transition-transform duration-200 motion-reduce:transition-none`}
          >
            <div className="flex items-center justify-between gap-2 pb-4">
              {title ? (
                <p id={titleId} className="px-3 text-lg font-semibold text-body-text">
                  {title}
                </p>
              ) : (
                <span />
              )}
              <Button
                variant="secondary"
                onClick={onClose}
                className="min-h-12 min-w-12 focus-visible:ring-2 focus-visible:ring-primary"
              >
                Cerrar
              </Button>
            </div>
            {children}
          </div>
        </>
      ) : null}
    </div>,
    document.body,
  );
}
