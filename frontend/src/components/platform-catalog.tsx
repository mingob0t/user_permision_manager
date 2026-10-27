'use client';

/** Catálogo de plataformas con filtro por área y búsqueda. */

import { useMemo, useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import { FILTRO_BUSQUEDA, FILTRO_SELECTOR, FilterBar } from './filter-bar';
import { Select, TextInput } from './form';
import { PlatformCard } from './platform-card';
import { EmptyNote, ErrorNote, Spinner } from './ui';

export function PlatformCatalog() {
  const [areaId, setAreaId] = useState<number | null>(null);
  const [term, setTerm] = useState('');

  const areas = useAsync(() => api.areas(), []);
  // El filtro por área va al servidor; la búsqueda se resuelve en cliente para
  // no pedir a cada tecla.
  const platforms = useAsync(
    () => api.platforms(areaId ? { areaId } : {}),
    [areaId],
  );

  const shown = useMemo(() => {
    const list = platforms.data ?? [];
    const needle = term.trim().toLowerCase();
    if (!needle) return list;
    return list.filter(
      (p) =>
        p.name.toLowerCase().includes(needle) ||
        (p.description ?? '').toLowerCase().includes(needle),
    );
  }, [platforms.data, term]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Mis plataformas</h2>
        <p className="mt-1 text-sm text-label">
          Abre los sistemas a los que ya tienes acceso.
        </p>
      </div>

      <FilterBar label="Filtros de plataformas">
        <TextInput
          type="search"
          value={term}
          onChange={(event) => setTerm(event.target.value)}
          placeholder="Buscar plataforma…"
          aria-label="Buscar plataforma"
          className={FILTRO_BUSQUEDA}
        />
        <Select
          value={areaId ?? ''}
          onChange={(event) =>
            setAreaId(event.target.value ? Number(event.target.value) : null)
          }
          aria-label="Filtrar por área"
          className={FILTRO_SELECTOR}
        >
          <option value="">Todas las áreas</option>
          {(areas.data ?? []).map((area) => (
            <option key={area.id} value={area.id}>
              {area.name}
            </option>
          ))}
        </Select>
      </FilterBar>

      {platforms.loading ? <Spinner /> : null}
      {platforms.error ? <ErrorNote message={platforms.error} /> : null}

      {!platforms.loading && !platforms.error ? (
        shown.length === 0 ? (
          <EmptyNote
            message={
              term || areaId
                ? 'Ninguna plataforma coincide con el filtro.'
                : 'No tienes plataformas asignadas.'
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {shown.map((platform) => (
              <PlatformCard key={platform.id} platform={platform} />
            ))}
          </div>
        )
      ) : null}
    </div>
  );
}
