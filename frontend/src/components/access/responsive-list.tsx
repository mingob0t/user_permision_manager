/**
 * Tabla en escritorio y lista en móvil con el mismo marcado (DIS-014):
 * `Card` con una cabecera de columnas (solo en `md`) y una `ul` de filas;
 * cada fila es un `dl` cuyas etiquetas (`dt`) se ven en móvil y quedan para
 * lectores de pantalla en escritorio.
 */

import { Card } from '../ui';

/** Clase de la etiqueta (`dt`) de cada celda. */
export const ETIQUETA_CELDA = 'text-xs font-medium uppercase tracking-wide text-label md:sr-only';

export function ResponsiveList({
  columns,
  headers,
  label,
  children,
}: {
  /** Plantilla de columnas en `md`, la misma que usa cada fila (`md:grid-cols-[…]`). */
  columns: string;
  headers: string[];
  /** Nombre accesible de la lista. */
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="p-0">
      <div
        aria-hidden
        className={`hidden border-b border-panel-border px-6 py-3 text-xs font-medium uppercase tracking-wide text-label md:grid md:gap-4 ${columns}`}
      >
        {headers.map((header) => <span key={header}>{header}</span>)}
      </div>
      <ul className="divide-y divide-panel-border" aria-label={label}>
        {children}
      </ul>
    </Card>
  );
}

/** Fila: `li` con un `dl` en la cuadrícula de `columns`. */
export function ResponsiveRow({
  columns,
  label,
  children,
}: {
  columns: string;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <li className="p-4 md:px-6" aria-label={label}>
      <dl className={`grid gap-3 md:items-start md:gap-4 ${columns}`}>{children}</dl>
    </li>
  );
}
