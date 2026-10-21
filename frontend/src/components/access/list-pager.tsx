/**
 * Paginación de una lista paginada del contrato (`Paginated`, DIS-014):
 * "Anterior" y "Siguiente" con la página actual anunciada. Sin otra página,
 * no se muestra.
 */

import { Button } from '../form';

export function totalPaginas(total: number, perPage: number): number {
  return perPage > 0 ? Math.max(1, Math.ceil(total / perPage)) : 1;
}

export function ListPager({
  page,
  perPage,
  total,
  label,
  onChange,
}: {
  page: number;
  perPage: number;
  total: number;
  /** Nombre accesible de la navegación, p. ej. "Páginas de mis solicitudes". */
  label: string;
  onChange: (page: number) => void;
}) {
  const paginas = totalPaginas(total, perPage);
  if (paginas <= 1) return null;

  return (
    <nav aria-label={label} className="flex flex-wrap items-center justify-between gap-3">
      <Button variant="secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        Anterior
      </Button>
      <p className="text-sm text-label" aria-live="polite">
        Página {page} de {paginas} · {total} en total
      </p>
      <Button variant="secondary" disabled={page >= paginas} onClick={() => onChange(page + 1)}>
        Siguiente
      </Button>
    </nav>
  );
}
