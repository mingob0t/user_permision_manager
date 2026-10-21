/**
 * Piezas de interfaz.
 *
 * El marcado y las clases se toman de las plantillas del portal original, para
 * que el resultado sea el mismo: paneles `bg-panel-fill border border-panel-border
 * rounded-xl shadow-*`, botones `.nexus-btn`, y los colores vía los tokens.
 * No se define aquí ningún estilo propio.
 */

export function Card({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  // index.html: bg-panel-fill border border-panel-border rounded-xl p-6 shadow-sm
  return (
    <div
      className={`bg-panel-fill border border-panel-border rounded-xl p-6 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

/** Cabecera de panel, como la de los paneles de index.html. */
export function PanelHeader({
  title,
  children,
}: {
  title: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <div className="shrink-0 p-6 border-b border-panel-border bg-surface-container/20 flex items-center justify-between">
      <h2 className="text-xs font-black uppercase tracking-[0.15em] text-label">
        {title}
      </h2>
      {children}
    </div>
  );
}

export function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card>
      <p className="text-xs font-black uppercase tracking-[0.15em] text-label">
        {label}
      </p>
      <p className="mt-2 text-3xl font-black tabular-nums text-bi-main">{value}</p>
      {hint ? <p className="mt-1 text-xs text-bi-muted">{hint}</p> : null}
    </Card>
  );
}

export function Spinner({ label = 'Cargando…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 p-6 text-label" role="status">
      <span
        className="h-4 w-4 animate-spin rounded-full border-2 border-panel-border border-t-primary"
        aria-hidden
      />
      <span className="text-sm font-bold">{label}</span>
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-xl border border-error/30 bg-error/10 p-4 text-sm font-bold text-error-text"
    >
      {message}
    </div>
  );
}

export function EmptyNote({ message }: { message: string }) {
  return (
    <Card className="text-center">
      <p className="text-sm font-bold text-label/85">{message}</p>
    </Card>
  );
}

/** Insignia. Usa las clases .nx-badge del portal. */
export function Badge({
  children,
  tone = 'slate',
}: {
  children: React.ReactNode;
  tone?: 'primary' | 'success' | 'error' | 'warning' | 'violet' | 'sky' | 'slate' | 'cyan';
}) {
  return <span className={`nx-badge nx-badge-${tone}`}>{children}</span>;
}
