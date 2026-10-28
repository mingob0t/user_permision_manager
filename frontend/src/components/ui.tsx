/**
 * Piezas de interfaz.
 *
 * El marcado y las clases se toman de las plantillas del portal original, para
 * que el resultado sea el mismo: paneles `bg-panel-fill border border-panel-border
 * rounded-xl shadow-*`, botones `.nexus-btn`, y los colores vía los tokens.
 * No se define aquí ningún estilo propio.
 */

export type CardVariant = 'default' | 'link' | 'selectable';

export interface CardProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  className?: string;
  variant?: CardVariant;
  as?: 'div' | 'article' | 'section' | 'label' | 'fieldset';
}

const CARD_VARIANTS: Record<CardVariant, string> = {
  default: '',
  link: 'transition-colors hover:border-primary/60',
  selectable: 'cursor-pointer has-[:checked]:border-primary has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary',
};

export function Card({
  children,
  className = '',
  variant = 'default',
  as: Component = 'div',
  ...props
}: CardProps) {
  // index.html: bg-panel-fill border border-panel-border rounded-xl p-6 shadow-sm
  return (
    <Component
      {...props}
      className={`bg-panel-fill border border-panel-border rounded-xl p-6 shadow-sm ${CARD_VARIANTS[variant]} ${className}`}
    >
      {children}
    </Component>
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

export function Spinner({
  label = 'Cargando…',
  size = 'md',
  className = '',
}: {
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}) {
  const containerClasses =
    size === 'sm' ? 'flex items-center gap-2 text-label' : 'flex items-center gap-3 p-6 text-label';
  return (
    <div className={`${containerClasses} ${className}`} role="status">
      <span
        className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-panel-border border-t-primary"
        aria-hidden="true"
      />
      <span className="text-sm font-bold">{label}</span>
    </div>
  );
}

export { Note, ErrorNote, EmptyNote } from './note';
export type { NoteProps, NoteTone } from './note';

/** Mensaje de éxito en línea (texto `success-text`, AA en los dos temas; DIS-002, DIS-010). */
export function SuccessNote({ children }: { children: React.ReactNode }) {
  return <p className="text-sm font-bold text-success-text">{children}</p>;
}

/**
 * Tonos de estado (DIS-010): los de las insignias `.nx-badge-<tono>`, por token.
 * `ErrorNote` y `SuccessNote` usan los de peligro y éxito; nada de colores de Tailwind.
 */
export type Tone = 'primary' | 'success' | 'error' | 'warning' | 'violet' | 'sky' | 'slate' | 'cyan';

/** Insignia. Usa las clases .nx-badge del portal. */
export function Badge({
  children,
  tone = 'slate',
}: {
  children: React.ReactNode;
  tone?: Tone;
}) {
  return <span className={`nx-badge nx-badge-${tone}`}>{children}</span>;
}

/**
 * Esqueleto de carga con dimensiones finales (DIS-073).
 *
 * Reserva el espacio exacto del elemento para evitar desplazamientos de diseño
 * acumulados (CLS < 0.01).
 *
 * Variantes:
 * - 'fila': simula una fila de tabla o lista (alto estándar min-h-12)
 * - 'tarjeta': simula un panel Card
 * - 'contador': simula un StatTile
 * - 'texto': línea de texto
 * - 'rect': bloque genérico
 */
export function Skeleton({
  variant = 'fila',
  className = '',
  count = 1,
  ariaLabel = 'Cargando contenido…',
}: {
  variant?: 'fila' | 'tarjeta' | 'contador' | 'texto' | 'rect';
  className?: string;
  count?: number;
  ariaLabel?: string;
}) {
  const baseClasses = 'animate-pulse rounded-lg bg-surface-container/60 motion-reduce:animate-none';
  const variantClasses = {
    fila: 'min-h-12 w-full',
    tarjeta: 'min-h-36 w-full rounded-xl border border-panel-border',
    contador: 'min-h-24 w-full rounded-xl border border-panel-border',
    texto: 'h-4 w-3/4',
    rect: 'h-full w-full',
  };

  const items = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      role="status"
      aria-label={ariaLabel}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
    >
      <span className="sr-only">{ariaLabel}</span>
    </div>
  ));

  return count === 1 ? items[0] : <div className="space-y-3 w-full">{items}</div>;
}

/**
 * Región con alto reservado para avisos y errores (DIS-073).
 *
 * Evita que la aparición de un mensaje de error o éxito empuje el resto de los
 * controles de la pantalla (CLS = 0).
 */
export function RegionDeAviso({
  children,
  className = '',
  minHeight = 'min-h-6',
}: {
  children?: React.ReactNode;
  className?: string;
  minHeight?: string;
}) {
  return (
    <div className={`transition-opacity duration-normal ${minHeight} ${className}`} aria-live="polite">
      {children}
    </div>
  );
}
