'use client';

/**
 * Filtros de alcance por área y plataforma (DIS-021, reutilizado en DIS-020):
 * las opciones según el rol y los dos selectores encadenados.
 *
 * - Áreas: las administradas; el superadmin, todas (`GET /areas`).
 * - Plataformas: las de las áreas del alcance; se acotan al área elegida.
 * - Cambiar de área quita la plataforma que no le pertenece.
 */

import { useMemo } from 'react';
import { api } from '@/lib/api';
import type { AreaRef } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { Field, Select } from '../form';
import { useSession } from '../session-provider';

/** Plataforma del filtro: solo lo que el filtro necesita de `Platform`. */
export interface PlataformaFiltro {
  id: number;
  name: string;
  area_id: number;
}

export interface OpcionesAlcance {
  esSuperadmin: boolean;
  areas: AreaRef[];
  plataformas: PlataformaFiltro[];
}

/**
 * Áreas y plataformas del alcance de quien administra. Con `activo` en
 * `false` no se pide nada (p. ej. un usuario sin rol de administrador).
 */
export function useOpcionesAlcance(activo = true): OpcionesAlcance {
  const { session } = useSession();
  const esSuperadmin = session?.permissions.is_admin ?? false;

  const todas = useAsync<AreaRef[]>(
    () => (activo && esSuperadmin ? api.areas() : Promise.resolve([])),
    [activo, esSuperadmin],
  );
  const areas = useMemo<AreaRef[]>(() => {
    if (!activo) return [];
    return esSuperadmin ? (todas.data ?? []) : (session?.managed_areas ?? []);
  }, [activo, esSuperadmin, todas.data, session]);

  const catalogo = useAsync(
    () => (activo ? api.platforms() : Promise.resolve([])),
    [activo],
  );
  const plataformas = useMemo<PlataformaFiltro[]>(() => {
    const ids = new Set(areas.map((a) => a.id));
    return (catalogo.data ?? [])
      .filter((p) => esSuperadmin || ids.has(p.area_id))
      .map(({ id, name, area_id }) => ({ id, name, area_id }));
  }, [catalogo.data, areas, esSuperadmin]);

  return { esSuperadmin, areas, plataformas };
}

export interface CambioAlcance {
  areaId?: number | null;
  platformId?: number | null;
}

/** Selectores de área y plataforma. */
export function ScopeSelects({
  areaId,
  platformId,
  opciones,
  areaSelectId,
  onChange,
}: {
  areaId: number | null;
  platformId: number | null;
  opciones: OpcionesAlcance;
  /** `id` del selector de área (para llevarle el foco desde fuera). */
  areaSelectId?: string;
  onChange: (cambio: CambioAlcance) => void;
}) {
  const { areas, plataformas, esSuperadmin } = opciones;
  const visibles = areaId === null
    ? plataformas
    : plataformas.filter((p) => p.area_id === areaId);

  return (
    <>
      <Field label="Área">
        <Select
          id={areaSelectId}
          value={areaId ?? ''}
          onChange={(event) => {
            const nueva = event.target.value ? Number(event.target.value) : null;
            const sigue = plataformas.some(
              (p) => p.id === platformId && (nueva === null || p.area_id === nueva));
            onChange({ areaId: nueva, platformId: sigue ? platformId : null });
          }}
        >
          <option value="">{esSuperadmin ? 'Todas las áreas' : 'Todas mis áreas'}</option>
          {areas.map((area) => (
            <option key={area.id} value={area.id}>{area.name}</option>
          ))}
        </Select>
      </Field>
      <Field label="Plataforma">
        <Select
          value={platformId ?? ''}
          onChange={(event) =>
            onChange({ platformId: event.target.value ? Number(event.target.value) : null })}
        >
          <option value="">Todas las plataformas</option>
          {visibles.map((plataforma) => (
            <option key={plataforma.id} value={plataforma.id}>{plataforma.name}</option>
          ))}
        </Select>
      </Field>
    </>
  );
}
