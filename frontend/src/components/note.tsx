import React from 'react';
import { Card } from './ui';
import { Icono, NombreIcono } from './icono';

export type NoteTone = 'error' | 'success' | 'warning' | 'info';

export interface NoteProps {
  tone?: NoteTone;
  title?: string;
  children?: React.ReactNode;
  message?: string;
  action?: React.ReactNode;
  className?: string;
  role?: string;
  id?: string;
}

const TONE_MAP: Record<NoteTone, { container: string; title: string; text: string; icon: NombreIcono }> = {
  error: {
    container: 'border-error/30 bg-error/10 text-error-text',
    title: 'text-error-text',
    text: 'text-error-text',
    icon: 'error',
  },
  success: {
    container: 'border-success/30 bg-success/10 text-success-text',
    title: 'text-success-text',
    text: 'text-success-text',
    icon: 'exito',
  },
  warning: {
    container: 'border-warning/40 bg-warning/10 text-warning-text',
    title: 'text-warning-text',
    text: 'text-warning-text',
    icon: 'aviso',
  },
  info: {
    container: 'border-primary/30 bg-primary/10 text-primary-text',
    title: 'text-primary-text',
    text: 'text-primary-text',
    icon: 'info',
  },
};

/**
 * Nota o aviso contextual por tono (DIS-062).
 * Accesible por defecto: error anuncia role="alert", los demás role="status".
 * El icono es puramente gráfico (SVG aria-hidden) sin ensuciar textContent.
 */
export function Note({
  tone = 'info',
  title,
  children,
  message,
  action,
  className = '',
  role,
  id,
}: NoteProps) {
  const styles = TONE_MAP[tone];
  const effectiveRole = role ?? (tone === 'error' ? 'alert' : 'status');
  const content = children ?? message;

  return (
    <div
      id={id}
      role={effectiveRole}
      className={`rounded-xl border p-4 text-sm font-bold ${styles.container} ${className}`}
    >
      <div className="flex items-start gap-3">
        <Icono
          nombre={styles.icon}
          tamano="md"
          className={`shrink-0 ${styles.text}`}
          ariaHidden={true}
        />
        <div className="min-w-0 flex-1 space-y-1">
          {title ? (
            <p className={`font-black tracking-wide ${styles.title}`}>{title}</p>
          ) : null}
          {content ? (
            <div className={`font-medium ${styles.text}`}>{content}</div>
          ) : null}
          {action ? <div className="pt-2">{action}</div> : null}
        </div>
      </div>
    </div>
  );
}

/** Atajo para avisos de error estándar (DIS-062). */
export function ErrorNote({
  message,
  title,
  children,
  className = '',
  action,
}: {
  message?: string;
  title?: string;
  children?: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}) {
  return (
    <Note tone="error" title={title} message={message} action={action} className={className}>
      {children}
    </Note>
  );
}

/** Estado vacío con soporte para acción opcional (DIS-062). */
export function EmptyNote({
  message,
  action,
  className = '',
}: {
  message: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={`text-center space-y-3 ${className}`}>
      <p className="text-sm font-bold text-label/85">{message}</p>
      {action ? <div className="flex justify-center">{action}</div> : null}
    </Card>
  );
}
