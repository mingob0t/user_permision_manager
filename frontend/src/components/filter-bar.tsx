/**
 * Barra de filtros común (DIS-010, D-09): fila que se parte en móvil y agrupa
 * los controles de `form.tsx` (`TextInput`, `Select`) con el mismo aspecto.
 * Cada control lleva su `aria-label`; la barra es una región de búsqueda con
 * nombre.
 */

/** Clases para que un `TextInput` de búsqueda ocupe el espacio libre de la barra. */
export const FILTRO_BUSQUEDA = 'min-w-56 flex-1';

/** Clases para que un `Select` de la barra no ocupe toda la fila desde `sm`. */
export const FILTRO_SELECTOR = 'sm:w-auto';

export function FilterBar({
  label,
  children,
}: {
  /** Nombre accesible de la barra (p. ej. "Filtros de plataformas"). */
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div role="search" aria-label={label} className="flex flex-wrap items-center gap-3">
      {children}
    </div>
  );
}
