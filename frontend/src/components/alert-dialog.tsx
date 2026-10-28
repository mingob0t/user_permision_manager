'use client';

/**
 * Diálogo de alerta y confirmación accesible estilo SweetAlert propio (DIS-074).
 *
 * - Diseñado sobre tokens y los 2 temas, sin librerías externas ni estilos en línea.
 * - `role="alertdialog"`, `aria-labelledby`, `aria-describedby` y `aria-modal="true"`.
 * - Foco inicial en el botón seguro (Cancelar) y retorno de foco al disparador (`useFocusTrap`).
 * - Bloqueo de desplazamiento con `useScrollLock` y canal estable.
 * - Icono destacado según tipo ('exito' | 'error' | 'aviso' | 'info' | 'pregunta').
 * - Botón de confirmación con estado `busy` y `aria-disabled`.
 */

import React, { useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Button } from './button';
import { Icono, type NombreIcono } from './icono';
import { useFocusTrap } from '@/lib/use-focus-trap';
import { useScrollLock } from '@/lib/use-scroll-lock';

export type AlertDialogType = 'exito' | 'error' | 'aviso' | 'info' | 'pregunta';

export interface AlertDialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  message?: string;
  type?: AlertDialogType;
  role?: 'alertdialog' | 'dialog';
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: 'primary' | 'danger' | 'secondary';
  onConfirm?: () => void;
  busy?: boolean;
  children?: React.ReactNode;
  devolverA?: React.RefObject<HTMLElement | null>;
}

const TYPE_CONFIG: Record<
  AlertDialogType,
  { icono: NombreIcono; contenedorColor: string; iconoColor: string; defaultVariant: 'primary' | 'danger' }
> = {
  exito: {
    icono: 'exito',
    contenedorColor: 'bg-success/15 border-success/30',
    iconoColor: 'text-success-text',
    defaultVariant: 'primary',
  },
  error: {
    icono: 'error',
    contenedorColor: 'bg-error/15 border-error/30',
    iconoColor: 'text-error-text',
    defaultVariant: 'danger',
  },
  aviso: {
    icono: 'aviso',
    contenedorColor: 'bg-warning/15 border-warning/30',
    iconoColor: 'text-warning-text',
    defaultVariant: 'danger',
  },
  info: {
    icono: 'info',
    contenedorColor: 'bg-primary/15 border-primary/30',
    iconoColor: 'text-primary-text',
    defaultVariant: 'primary',
  },
  pregunta: {
    icono: 'pregunta',
    contenedorColor: 'bg-warning/15 border-warning/30',
    iconoColor: 'text-warning-text',
    defaultVariant: 'danger',
  },
};

export function AlertDialog({
  open,
  onClose,
  title,
  message,
  type = 'pregunta',
  role = 'alertdialog',
  confirmLabel = 'Aceptar',
  cancelLabel = 'Cancelar',
  confirmVariant,
  onConfirm,
  busy = false,
  children,
  devolverA,
}: AlertDialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);

  const titleId = useId();
  const descId = useId();

  useScrollLock(open);
  useFocusTrap(panelRef, {
    activo: open,
    alEscape: onClose,
    devolverA,
    focoInicial: () => {
      // Foco seguro en Cancelar; si no existe botón cancelar, foco en Confirmar
      return [cancelButtonRef.current ?? confirmButtonRef.current].filter(
        Boolean,
      ) as HTMLElement[];
    },
  });

  if (!open) return null;

  const config = TYPE_CONFIG[type];
  const botonVariante = confirmVariant ?? config.defaultVariant;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-overlay backdrop-blur-xs p-4"
      onClick={(e) => {
        // Clic en el fondo no confirma; si no está ocupado permite cerrar
        if (e.target === e.currentTarget && !busy) {
          onClose();
        }
      }}
    >
      <div
        ref={panelRef}
        role={role}
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={message ? descId : undefined}
        tabIndex={-1}
        className="nx-modal-glass relative w-full max-w-dialogo rounded-2xl p-6 text-center shadow-2xl outline-none"
      >
        {/* Ícono grande circular centrado */}
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full border">
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-full border ${config.contenedorColor} ${config.iconoColor}`}
          >
            <Icono nombre={config.icono} tamano="lg" ariaHidden={true} />
          </div>
        </div>

        {/* Título de la alerta */}
        <h2 id={titleId} className="text-lg font-bold text-body-text">
          {title}
        </h2>

        {/* Mensaje descriptivo */}
        {message ? (
          <p id={descId} className="mt-2 text-sm text-label">
            {message}
          </p>
        ) : null}

        {/* Contenido / formulario opcional */}
        {children ? <div className="mt-4 text-left">{children}</div> : null}

        {/* Botones de acción */}
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          {cancelLabel ? (
            <Button
              ref={cancelButtonRef}
              variant="secondary"
              disabled={busy}
              onClick={onClose}
              className="min-h-12 min-w-28"
            >
              {cancelLabel}
            </Button>
          ) : null}
          <Button
            ref={confirmButtonRef}
            variant={botonVariante}
            busy={busy}
            onClick={() => {
              if (onConfirm) onConfirm();
              else onClose();
            }}
            className="min-h-12 min-w-28"
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
