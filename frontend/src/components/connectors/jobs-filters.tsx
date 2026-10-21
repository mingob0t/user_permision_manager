'use client';

/**
 * Filtros de la bitácora de ejecuciones (DIS-022, `GET /provisioning/jobs`,
 * contrato 1.1): estado, operación, proveedor, área y plataforma. Aplican al
 * cambiar; la lista vuelve a la página 1.
 */

import type { Job, JobOperation, JobParams, JobStatus } from '@/lib/access/types';
import { Field, Select } from '../form';
import { type OpcionesAlcance, ScopeSelects } from '../access/scope-filters';
import { ESTADOS_EJECUCION, OPERACIONES, PROVEEDORES } from './job-catalog';

export interface FiltrosEjecuciones {
  status: JobStatus | null;
  operation: JobOperation | null;
  provider: Job['provider'] | null;
  areaId: number | null;
  platformId: number | null;
}

export const FILTROS_EJECUCIONES_INICIALES: FiltrosEjecuciones = {
  status: null, operation: null, provider: null, areaId: null, platformId: null,
};

export const FILTRO_ESTADO_ID = 'ejecuciones-filtro-estado';

export function hayFiltrosEjecuciones(filtros: FiltrosEjecuciones): boolean {
  return (Object.keys(FILTROS_EJECUCIONES_INICIALES) as (keyof FiltrosEjecuciones)[])
    .some((clave) => filtros[clave] !== FILTROS_EJECUCIONES_INICIALES[clave]);
}

/** Filtros → parámetros del contrato (sin los vacíos). */
export function parametrosEjecuciones(filtros: FiltrosEjecuciones, page: number): JobParams {
  return {
    status: filtros.status ?? undefined,
    operation: filtros.operation ?? undefined,
    provider: filtros.provider ?? undefined,
    area_id: filtros.areaId ?? undefined,
    platform_id: filtros.platformId ?? undefined,
    page,
  };
}

function opciones<K extends string>(mapa: Record<K, string>) {
  return (Object.keys(mapa) as K[]).map((valor) => (
    <option key={valor} value={valor}>{mapa[valor]}</option>
  ));
}

const TEXTO_ESTADOS = Object.fromEntries(
  Object.entries(ESTADOS_EJECUCION).map(([estado, { texto }]) => [estado, texto]),
) as Record<JobStatus, string>;

export function JobsFilters({
  filtros,
  alcance,
  onChange,
}: {
  filtros: FiltrosEjecuciones;
  alcance: OpcionesAlcance;
  onChange: (cambio: Partial<FiltrosEjecuciones>) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <Field label="Estado">
        <Select
          id={FILTRO_ESTADO_ID}
          value={filtros.status ?? ''}
          onChange={(event) => onChange({ status: (event.target.value || null) as JobStatus | null })}
        >
          <option value="">Todos los estados</option>
          {opciones(TEXTO_ESTADOS)}
        </Select>
      </Field>
      <Field label="Operación">
        <Select
          value={filtros.operation ?? ''}
          onChange={(event) => onChange({ operation: (event.target.value || null) as JobOperation | null })}
        >
          <option value="">Todas las operaciones</option>
          {opciones(OPERACIONES)}
        </Select>
      </Field>
      <Field label="Proveedor">
        <Select
          value={filtros.provider ?? ''}
          onChange={(event) => onChange({ provider: (event.target.value || null) as Job['provider'] | null })}
        >
          <option value="">Todos los proveedores</option>
          {opciones(PROVEEDORES)}
        </Select>
      </Field>
      <ScopeSelects
        areaId={filtros.areaId}
        platformId={filtros.platformId}
        opciones={alcance}
        onChange={onChange}
      />
    </div>
  );
}
