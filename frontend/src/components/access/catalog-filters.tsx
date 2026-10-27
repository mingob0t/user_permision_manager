'use client';

/**
 * Filtros del catálogo (DIS-052, extraídos de `RequestCatalog`): búsqueda por texto y
 * por área, resueltos en el cliente. `filtrarCatalogo` es la función pura del filtro.
 */

import type { CatalogItem } from '@/lib/access/types';
import { FILTRO_BUSQUEDA, FILTRO_SELECTOR, FilterBar } from '../filter-bar';
import { Select, TextInput } from '../form';

/** Id del buscador: el foco vuelve aquí al cerrar el aviso. */
export const BUSCADOR_ID = 'catalogo-buscar';

function coincide(item: CatalogItem, needle: string): boolean {
  return item.platform.name.toLowerCase().includes(needle)
    || (item.platform.description ?? '').toLowerCase().includes(needle);
}

export function filtrarCatalogo(
  items: CatalogItem[],
  areaId: number | null,
  term: string,
): CatalogItem[] {
  const needle = term.trim().toLowerCase();
  return items.filter((item) =>
    (areaId === null || item.area.id === areaId) && (!needle || coincide(item, needle)));
}

export function CatalogFilters({
  term,
  onTermChange,
  areaId,
  onAreaChange,
  areas,
}: {
  term: string;
  onTermChange: (term: string) => void;
  areaId: number | null;
  onAreaChange: (areaId: number | null) => void;
  areas: { id: number; name: string }[];
}) {
  return (
    <FilterBar label="Filtros del catálogo">
      <TextInput
        id={BUSCADOR_ID}
        type="search"
        value={term}
        onChange={(event) => onTermChange(event.target.value)}
        placeholder="Buscar plataforma…"
        aria-label="Buscar en el catálogo"
        className={FILTRO_BUSQUEDA}
      />
      <Select
        value={areaId ?? ''}
        onChange={(event) => onAreaChange(event.target.value ? Number(event.target.value) : null)}
        aria-label="Filtrar el catálogo por área"
        className={FILTRO_SELECTOR}
      >
        <option value="">Todas las áreas</option>
        {areas.map((area) => (
          <option key={area.id} value={area.id}>{area.name}</option>
        ))}
      </Select>
    </FilterBar>
  );
}
