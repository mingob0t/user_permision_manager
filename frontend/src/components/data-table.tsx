/**
 * Tabla de datos común (DIS-010, D-10): región desplazable con nombre y foco
 * visible, `<table>` con encabezados `th scope="col"` y los estados de carga,
 * error y vacío de `ui.tsx` (carga y error ocultan la tabla). Solo tokens.
 *
 * Para listas que en móvil pasan a tarjetas se sigue usando `ResponsiveList`
 * (DIS-014); `DataTable` es la tabla con desplazamiento horizontal.
 */

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

export function DataTable<T>({
  label,
  columns,
  rows,
  rowKey,
  loading,
  error,
  emptyMessage,
  tableClassName = ANCHO_MINIMO,
}: {
  /** Nombre accesible de la región. */
  label: string;
  columns: DataColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  loading?: boolean;
  error?: string | null;
  /** Texto cuando no hay filas. */
  emptyMessage: string;
  tableClassName?: string;
}) {
  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if (rows.length === 0) return <EmptyNote message={emptyMessage} />;

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
            {rows.map((row) => (
              <tr key={rowKey(row)}>
                {columns.map((col) => (
                  <td key={col.key} className={col.cellClassName ?? CELDA}>
                    {col.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
