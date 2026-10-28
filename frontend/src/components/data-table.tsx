/**
 * Componente unificado de tablas y listas de datos (DIS-010, DIS-014, DIS-071, ADR-007).
 *
 * Responsabilidad:
 * - Tabla de datos con desplazamiento horizontal accesible (`DataTable`).
 * - Tabla oculta para lectores de pantalla como alternativa textual (`DataTable srOnly`).
 * - Lista adaptable a móvil y escritorio con matriz de estados (`ResponsiveList` / `ResponsiveRow`).
 * - Etiquetas y listas de datos estructurados (`DataLabel`, `DataList`, `DataListItem`).
 *
 * Estados de fila:
 * - Interactiva (hover / foco accesible).
 * - Seleccionada (`aria-selected="true"`, token de acento y borde de selección).
 * - Error (`border-l-error`, fondo sutil).
 *
 * Solo utiliza tokens de diseño; cumple estrictamente con el sistema 8pt.
 */

import React from 'react';
import { Card, EmptyNote, ErrorNote, Spinner } from './ui';

export type DataColumn<T> = {
  /** Identifica la columna (clave del `th`). */
  key: string;
  /** Texto del encabezado. */
  header: string;
  /** Solo para lectores de pantalla (p. ej. la columna de acciones). */
  headerSrOnly?: boolean;
  /** Contenido de la celda. */
  cell: (row: T) => React.ReactNode;
  /** Clases de la celda (relleno propio, alineación, ancho). */
  cellClassName?: string;
};

const CELDA = 'px-4 py-2.5';
const ANCHO_MINIMO = 'min-w-[44rem]';

export interface DataTableProps<T> {
  /** Nombre accesible de la región o tabla. */
  label: string;
  columns: DataColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  loading?: boolean;
  error?: string | null;
  /** Texto cuando no hay filas. */
  emptyMessage: string;
  tableClassName?: string;
  /** Tabla alternativa oculta para lectores de pantalla (p. ej. datos de gráficas). */
  srOnly?: boolean;
  /** Clave de la fila seleccionada para destacar visualmente y con aria-selected. */
  selectedKey?: string | number;
  /** Callback al hacer clic en una fila (habilita hover interactivo). */
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({
  label,
  columns,
  rows,
  rowKey,
  loading,
  error,
  emptyMessage,
  tableClassName = ANCHO_MINIMO,
  srOnly = false,
  selectedKey,
  onRowClick,
}: DataTableProps<T>) {
  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if (rows.length === 0) return <EmptyNote message={emptyMessage} />;

  if (srOnly) {
    return (
      <table className="sr-only">
        <caption>{label}</caption>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} scope="col">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((col, idx) =>
                idx === 0 ? (
                  <th key={col.key} scope="row">
                    {col.cell(row)}
                  </th>
                ) : (
                  <td key={col.key}>{col.cell(row)}</td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <Card className="p-0">
      {/* Región desplazable con nombre y foco visible para quien usa teclado (DIS-008). */}
      <div
        role="region"
        aria-label={label}
        tabIndex={0}
        className="overflow-x-auto rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <table className={`w-full text-sm ${tableClassName}`}>
          <thead className="border-b border-panel-border text-left text-xs uppercase tracking-wide text-label">
            <tr>
              {columns.map((col) => (
                <th key={col.key} scope="col" className="px-4 py-3 font-medium">
                  {col.headerSrOnly ? <span className="sr-only">{col.header}</span> : col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-panel-border">
            {rows.map((row) => {
              const clave = rowKey(row);
              const seleccionada = selectedKey !== undefined && selectedKey === clave;
              const interactiva = Boolean(onRowClick);

              const claseFila = seleccionada
                ? 'bg-primary/10 font-medium'
                : interactiva
                  ? 'hover:bg-surface-container/30 cursor-pointer transition-colors'
                  : '';

              return (
                <tr
                  key={clave}
                  aria-selected={seleccionada ? 'true' : undefined}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={claseFila}
                >
                  {columns.map((col) => (
                    <td key={col.key} className={col.cellClassName ?? CELDA}>
                      {col.cell(row)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** Clase de la etiqueta (`dt`) de cada celda en vista móvil. */
export const ETIQUETA_CELDA = 'text-xs font-medium uppercase tracking-wide text-label md:sr-only';

/**
 * Tabla en escritorio y lista en móvil con el mismo marcado (DIS-014, DIS-071):
 * `Card` con una cabecera de columnas (solo en `md`) y una `ul` de filas.
 */
export function ResponsiveList({
  columns,
  headers,
  label,
  children,
  className = '',
}: {
  /** Plantilla de columnas en `md` (p. ej. `md:grid-cols-[...]`). */
  columns: string;
  headers: string[];
  /** Nombre accesible de la lista. */
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={`p-0 ${className}`}>
      <div
        aria-hidden="true"
        className={`hidden border-b border-panel-border px-6 py-3 text-xs font-medium uppercase tracking-wide text-label md:grid md:gap-4 ${columns}`}
      >
        {headers.map((header) => (
          <span key={header}>{header}</span>
        ))}
      </div>
      <ul className="divide-y divide-panel-border" aria-label={label}>
        {children}
      </ul>
    </Card>
  );
}

/**
 * Fila adaptable (`li` con un `dl` en cuadrícula de columnas) con matriz de estados:
 * hover interactivo, selección visual y accesible, o estado de error.
 */
export function ResponsiveRow({
  columns,
  label,
  children,
  className = '',
  interactive = false,
  selected = false,
  error = false,
  onClick,
}: {
  columns: string;
  label: string;
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
  selected?: boolean;
  error?: boolean;
  onClick?: () => void;
}) {
  const estadoClass = selected
    ? 'bg-primary/10 border-l-4 border-l-primary'
    : error
      ? 'bg-error/5 border-l-4 border-l-error'
      : interactive
        ? 'hover:bg-surface-container/30 transition-colors cursor-pointer focus-within:ring-2 focus-within:ring-primary'
        : '';

  return (
    <li
      className={`p-4 md:px-6 ${estadoClass} ${className}`}
      aria-label={label}
      data-selected={selected ? 'true' : undefined}
      onClick={onClick}
    >
      <dl className={`grid gap-3 md:items-start md:gap-4 ${columns}`}>{children}</dl>
    </li>
  );
}

/**
 * Par etiqueta-valor accesible (`dt`, `dd`) para detalles, inspecciones y tarjetas.
 */
export function DataLabel({
  label,
  children,
  className = '',
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`min-w-0 ${className}`}>
      <dt className="text-xs font-medium uppercase tracking-wide text-label">{label}</dt>
      <dd className="break-words text-sm font-semibold text-body-text">{children}</dd>
    </div>
  );
}

/** Componente retrocompatible para pares etiqueta/valor en modales. */
export function Dato({
  etiqueta,
  valor,
  label,
  children,
  className = '',
}: {
  etiqueta?: string;
  valor?: React.ReactNode;
  label?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <DataLabel label={label ?? etiqueta ?? ''} className={className}>
      {children ?? valor}
    </DataLabel>
  );
}

/**
 * Lista de datos estructurada con borde y separación tokenizada para paneles de detalle.
 */
export function DataList({
  children,
  className = '',
  'aria-label': ariaLabel,
  'aria-labelledby': ariaLabelledBy,
}: {
  children: React.ReactNode;
  className?: string;
  'aria-label'?: string;
  'aria-labelledby'?: string;
}) {
  return (
    <ul
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledBy}
      className={`divide-y divide-panel-border rounded-xl border border-panel-border ${className}`}
    >
      {children}
    </ul>
  );
}

/**
 * Elemento de `DataList` con estados interactivo, seleccionado o error opcionales.
 */
export function DataListItem({
  children,
  className = '',
  interactive = false,
  selected = false,
  error = false,
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
  selected?: boolean;
  error?: boolean;
  onClick?: () => void;
}) {
  const estadoClass = selected
    ? 'bg-primary/10 border-l-4 border-l-primary'
    : error
      ? 'bg-error/5 border-l-4 border-l-error'
      : interactive
        ? 'hover:bg-surface-container/30 transition-colors cursor-pointer'
        : '';

  return (
    <li onClick={onClick} className={`space-y-1 p-3 ${estadoClass} ${className}`}>
      {children}
    </li>
  );
}
