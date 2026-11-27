/**
 * Piezas de interfaz.
 *
 * El marcado y las clases se toman de las plantillas del portal original, para
 * que el resultado sea el mismo: paneles `bg-panel-fill border border-panel-border
 * rounded-xl shadow-*`, botones `.nexus-btn`, y los colores vía los tokens.
 * No se define aquí ningún estilo propio.
 */

import { Icono, type NombreIcono, type TamanoIcono } from './icono';

export type CardVariant = 'default' | 'link' | 'selectable';

export interface CardProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  className?: string;
  variant?: CardVariant;
  as?: 'div' | 'article' | 'section' | 'label' | 'fieldset';
}

const CARD_VARIANTS: Record<CardVariant, string> = {
  default: '',
  link: 'transition-colors transition-all hover:border-primary/60 hover:shadow-2',
  selectable: 'cursor-pointer has-[:checked]:border-primary has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary',
};

export function Card({
  children,
  className = '',
  variant = 'default',
  as: Component = 'div',
  ...props
}: CardProps) {
  // index.html: bg-panel-fill border border-panel-border rounded-xl p-6 shadow-1
  return (
    <Component
      {...props}
      className={`bg-panel-fill border border-panel-border rounded-xl p-6 shadow-1 ${CARD_VARIANTS[variant]} ${className}`}
    >
      {children}
    </Component>
  );
}

export interface PanelHeaderProps {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  icon?: NombreIcono;
  titleId?: string;
  titleTag?: 'h2' | 'h3' | 'h4';
  actions?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

/** Cabecera unificada de panel / contenedor / tarjeta (UI_GUIDE §Encabezados de Contenedores y Tarjetas). */
export function PanelHeader({
  title,
  subtitle,
  icon,
  titleId,
  titleTag = 'h2',
  actions,
  children,
  className = '',
}: PanelHeaderProps) {
  const TitleTag = titleTag;

  return (
    <div
      className={`flex min-h-16 shrink-0 items-center justify-between gap-4 border-b border-primary/20 bg-gradient-to-r from-primary/10 via-brand/10 to-accent/10 px-4 py-2 ${className}`}
    >
      <div className="flex items-center gap-3 min-w-0">
        {icon ? (
          <span
            className="flex size-8 shrink-0 items-center justify-center rounded-xl border border-primary/20 bg-superficie text-primary-text shadow-xs"
            aria-hidden="true"
          >
            <Icono nombre={icon} tamano="md" ariaHidden={true} />
          </span>
        ) : null}
        <div className="min-w-0">
          <TitleTag
            id={titleId}
            className="text-sm font-bold tracking-tight text-body-text truncate"
          >
            {title}
          </TitleTag>
          {subtitle ? (
            <p className="text-xs text-label truncate">{subtitle}</p>
          ) : null}
        </div>
      </div>
      {actions || children ? (
        <div className="flex shrink-0 items-center gap-2">
          {actions ?? children}
        </div>
      ) : null}
    </div>
  );
}

/** Tonos de las cajas de icono, avatares y círculos de actividad (`.nx-tono-*`, DIS-079). */
export type TonoCaja = 'activo' | 'success' | 'error' | 'warning' | 'neutro';

/** Clase de cada tono (literales, para que el CSS sin uso las encuentre). */
export const CLASE_TONO: Record<TonoCaja, string> = {
  activo: 'nx-tono-activo',
  success: 'nx-tono-success',
  error: 'nx-tono-error',
  warning: 'nx-tono-warning',
  neutro: 'nx-tono-neutro',
};

const CLASE_NOTA = { warning: 'nx-texto-warning', error: 'nx-texto-error' } as const;

/**
 * Indicador. Con `icon`, lo muestra decorativo en una caja del color del estado (`tone`) y
 * pone número y nota a su lado (DIS-079); sin `icon` conserva la tarjeta simple.
 */
export function StatTile({
  label,
  value,
  hint,
  icon,
  tone = 'activo',
  hintTone,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: NombreIcono;
  tone?: TonoCaja;
  /** Colorea la nota con el texto del estado (`warning` o `error`). */
  hintTone?: 'warning' | 'error';
}) {
  const claseNota = hintTone ? CLASE_NOTA[hintTone] : 'text-bi-muted';
  const cuerpo = (
    <div className="min-w-0">
      <p className="text-xs font-black uppercase tracking-[0.15em] text-label">
        {label}
      </p>
      <p className="mt-2 text-3xl font-black tabular-nums tracking-tight text-bi-main">{value}</p>
      {hint ? <p className={`mt-1 text-xs ${claseNota}`}>{hint}</p> : null}
    </div>
  );
  if (!icon) return <Card className="transition-colors hover:border-primary/40 shadow-xs">{cuerpo}</Card>;
  return (
    <Card className="transition-colors hover:border-primary/40 shadow-xs">
      <div className="flex items-start gap-4">
        <span
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-superficie/20 shadow-xs ${CLASE_TONO[tone]}`}
          aria-hidden="true"
        >
          <Icono nombre={icon} tamano="xl" />
        </span>
        {cuerpo}
      </div>
    </Card>
  );
}

export function Spinner({
  label = 'Cargando…',
  size = 'md',
  subtexto,
  className = '',
}: {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  subtexto?: string;
  className?: string;
}) {
  if (size === 'sm') {
    return (
      <div className={`inline-flex items-center gap-2 text-label ${className}`} role="status">
        <span className="relative flex size-4 shrink-0" aria-hidden="true">
          <span className="absolute inset-0 rounded-full border-2 border-primary/20" />
          <span className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary animate-spin" />
        </span>
        {label ? <span className="text-xs font-bold">{label}</span> : null}
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 p-6 text-center select-none ${className}`}
      role="status"
    >
      <div className="relative flex items-center justify-center size-10 shrink-0" aria-hidden="true">
        <span className="absolute inset-0 rounded-full border-2 border-primary/15" />
        <span className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary border-r-brand animate-spin" />
        <span className="size-2 rounded-full bg-primary/80 animate-pulse" />
      </div>
      <div className="flex flex-col items-center gap-0.5">
        <span className="text-sm font-bold tracking-tight text-body-text">{label}</span>
        {subtexto ? <span className="text-xs text-label font-medium">{subtexto}</span> : null}
      </div>
    </div>
  );
}

export { PantallaCarga, type PantallaCargaProps } from './pantalla-carga';

export { Note, ErrorNote, EmptyNote } from './note';
export type { NoteProps, NoteTone } from './note';
export { PremiumEmptyState, type PremiumEmptyStateProps } from './premium-message';

/** Mensaje de éxito en línea (texto `success-text`, AA en los dos temas; DIS-002, DIS-010). */
export function SuccessNote({ children }: { children: React.ReactNode }) {
  return <p className="text-sm font-bold text-success-text">{children}</p>;
}

/**
 * Tonos de estado (DIS-010): los de las insignias `.nx-badge-<tono>`, por token.
 * `ErrorNote` y `SuccessNote` usan los de peligro y éxito; nada de colores de Tailwind.
 */
export type Tone = 'primary' | 'success' | 'error' | 'warning' | 'violet' | 'sky' | 'slate' | 'cyan';

/** Insignia con texto o icono semántico (DIS-079). */
export function Badge({
  children,
  tone = 'slate',
  icon,
  dot = false,
  className = '',
  title,
  iconTamano = 'sm',
}: {
  children?: React.ReactNode;
  tone?: Tone;
  icon?: NombreIcono;
  dot?: boolean;
  className?: string;
  title?: string;
  iconTamano?: TamanoIcono;
}) {
  return (
    <span
      className={`nx-badge nx-badge-${tone} shadow-xs ${className}`}
      title={title}
    >
      {dot ? (
        <span
          className="size-1.5 shrink-0 rounded-full bg-current opacity-80"
          aria-hidden="true"
        />
      ) : null}
      {icon ? <Icono nombre={icon} tamano={iconTamano} ariaHidden={true} /> : null}
      {children}
    </span>
  );
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
/** Clases base del esqueleto: las reutilizan los esqueletos con forma propia (DIS-155). */
export const CLASES_ESQUELETO = 'animate-pulse rounded-lg bg-surface-container/60 motion-reduce:animate-none';

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
  const baseClasses = CLASES_ESQUELETO;
  const variantClasses = {
    fila: 'min-h-12 w-full',
    tarjeta: 'min-h-36 w-full rounded-xl border border-panel-border',
    contador: 'min-h-24 w-full rounded-xl border border-panel-border',
    texto: 'h-4 w-3/4',
    rect: 'h-full w-full',
  };

  if (count <= 1) {
    return (
      <div
        role="status"
        aria-label={ariaLabel}
        className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      >
        <span className="sr-only">{ariaLabel}</span>
      </div>
    );
  }

  return (
    <div role="status" aria-label={ariaLabel} className="space-y-3 w-full">
      <span className="sr-only">{ariaLabel}</span>
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          aria-hidden="true"
          className={`${baseClasses} ${variantClasses[variant]} ${className}`}
        />
      ))}
    </div>
  );
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
