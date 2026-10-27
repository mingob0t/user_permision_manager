'use client';

/**
 * Controles de formulario y modal.
 *
 * Las clases replican el marcado de las plantillas del portal: inputs
 * `h-12 bg-surface-container/30 border border-panel-border rounded-xl`, botones
 * `.nexus-btn`, casillas `.nexus-checkbox` y modales `.nx-modal-glass`.
 */

import { useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import { CAMPOS, esVisible, useFocusTrap } from '@/lib/use-focus-trap';
import { useScrollLock } from '@/lib/use-scroll-lock';

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-black uppercase tracking-[0.1em] text-label">
        {label}
      </span>
      {children}
      {hint ? (
        <span className="mt-1.5 block text-xs text-label/85">{hint}</span>
      ) : null}
    </label>
  );
}

// users.html: el input estándar del portal.
const INPUT =
  'w-full h-12 bg-surface-container/30 border border-panel-border rounded-xl px-4 ' +
  'text-sm font-bold text-body-text placeholder:text-label/85 ' +
  'focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all ' +
  'disabled:opacity-50';

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`${INPUT} ${props.className ?? ''}`} />;
}

export function TextArea(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement>,
) {
  return (
    <textarea
      {...props}
      className={`${INPUT} h-auto py-3 ${props.className ?? ''}`}
    />
  );
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`${INPUT} ${props.className ?? ''}`} />;
}

export function Checkbox({
  label,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex items-center gap-3 text-sm font-bold text-body-text">
      <input type="checkbox" {...props} className="nexus-checkbox" />
      {label}
    </label>
  );
}

export function Button({
  variant = 'primary',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger';
}) {
  // .nexus-btn y sus variantes vienen de components.css.
  const variants = {
    primary: 'nexus-btn-primary',
    secondary: 'nexus-btn-secondary',
    // El portal aplica el color con un override sobre la variante primaria.
    // DIS-004: relleno y texto de peligro por token (antes blanco sobre `error`, 3,76:1).
    danger: 'nexus-btn-primary !bg-error-solid !text-on-error shadow-error/20',
  };
  return (
    <button
      type="button"
      {...props}
      className={`nexus-btn ${variants[variant]} disabled:opacity-40 disabled:pointer-events-none ${props.className ?? ''}`}
    />
  );
}

/**
 * Diálogo modal, con el cristal del portal (.nx-modal-glass).
 *
 * - DIS-031: foco inicial en el primer campo del cuerpo (o en el panel si no
 *   hay campos), atrapado con Tab y devuelto al cerrar (`useFocusTrap`); el
 *   panel se enfoca solo al abrir, aunque `onClose` cambie en cada render.
 * - `describedBy`: id (o ids separados por espacio) del texto que explica la
 *   acción; va a `aria-describedby` del `role="dialog"`.
 * - DIS-038: velo `bg-overlay` (token `--color-overlay`) y bloqueo del
 *   desplazamiento del fondo (`useScrollLock`).
 * - Se pinta en un portal en `document.body`, fuera de la raíz de la app, que
 *   queda `inert` mientras está abierto (H2). Nombre del diálogo con
 *   `aria-labelledby` al título (H6). Solo se monta tras una acción del
 *   usuario: en el servidor no se pinta.
 */
export function Modal({
  title,
  onClose,
  children,
  footer,
  describedBy,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
  describedBy?: string;
}) {
  const panel = useRef<HTMLDivElement>(null);
  const cuerpo = useRef<HTMLDivElement>(null);
  const tituloId = useId();

  // Primero el bloqueo: al cerrar, la raíz deja de ser `inert` antes de devolver el foco.
  useScrollLock();
  useFocusTrap(panel, {
    alEscape: onClose,
    focoInicial: () =>
      Array.from(cuerpo.current?.querySelectorAll<HTMLElement>(CAMPOS) ?? []).filter(esVisible),
  });

  if (typeof document === 'undefined') return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-overlay backdrop-blur-sm p-4 sm:items-center"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={tituloId}
        aria-describedby={describedBy}
        tabIndex={-1}
        className="nx-modal-glass w-full max-w-lg rounded-2xl shadow-2xl outline-none"
      >
        <div className="flex items-center justify-between border-b border-panel-border px-6 py-4">
          <h2 id={tituloId} className="text-sm font-black uppercase tracking-[0.15em] text-panel-header-text">
            {title}
          </h2>
          {/* DIS-031: área táctil de 48 px (antes 36). */}
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="min-w-12 min-h-12 flex items-center justify-center rounded-base text-label hover:bg-surface-container transition-colors"
          >
            ✕
          </button>
        </div>
        <div ref={cuerpo} className="space-y-5 px-6 py-5">{children}</div>
        {footer ? (
          <div className="flex justify-end gap-3 border-t border-panel-border px-6 py-4">
            {footer}
          </div>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Eliminar',
  onConfirm,
  onCancel,
  busy,
}: {
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
}) {
  const mensajeId = useId();
  return (
    <Modal
      title={title}
      onClose={onCancel}
      describedBy={mensajeId}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
          {/* H3: `aria-disabled` mientras se envía (con `disabled` el foco caería en `body`);
              el clic se ignora. */}
          <Button
            variant="danger"
            onClick={() => {
              if (!busy) onConfirm();
            }}
            aria-disabled={busy || undefined}
            className="aria-disabled:opacity-40"
          >
            {busy ? 'Eliminando…' : confirmLabel}
          </Button>
        </>
      }
    >
      <p id={mensajeId} className="text-sm font-bold text-label">{message}</p>
    </Modal>
  );
}
