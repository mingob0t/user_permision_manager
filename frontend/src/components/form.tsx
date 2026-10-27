'use client';

/**
 * Controles de formulario y modal.
 *
 * Las clases replican el marcado de las plantillas del portal: inputs
 * `h-12 bg-surface-container/30 border border-panel-border rounded-xl`, botones
 * `.nexus-btn`, casillas `.nexus-checkbox` y modales `.nx-modal-glass`.
 */

import { useEffect, useRef } from 'react';

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

/** Diálogo modal, con el cristal del portal (.nx-modal-glass). */
export function Modal({
  title,
  onClose,
  children,
  footer,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    panel.current?.focus();
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 backdrop-blur-sm p-4 sm:items-center"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className="nx-modal-glass w-full max-w-lg rounded-2xl shadow-2xl outline-none"
      >
        <div className="flex items-center justify-between border-b border-panel-border px-6 py-4">
          <h2 className="text-sm font-black uppercase tracking-[0.15em] text-panel-header-text">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="w-9 h-9 flex items-center justify-center rounded-base text-label hover:bg-surface-container transition-colors"
          >
            ✕
          </button>
        </div>
        <div className="space-y-5 px-6 py-5">{children}</div>
        {footer ? (
          <div className="flex justify-end gap-3 border-t border-panel-border px-6 py-4">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
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
  return (
    <Modal
      title={title}
      onClose={onCancel}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={busy}>
            {busy ? 'Eliminando…' : confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-sm font-bold text-label">{message}</p>
    </Modal>
  );
}
