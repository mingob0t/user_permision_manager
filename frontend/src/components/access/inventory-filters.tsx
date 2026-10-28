'use client';

/**
 * Filtros del inventario de permisos (DIS-021, `GET /access/inventory`,
 * contrato `accesos.md` 1.1): área, plataforma, nivel, origen, estado y
 * búsqueda por nombre o correo del usuario.
 *
 * - Los selectores aplican al cambiar; la búsqueda, al enviar (Enter o "Buscar").
 * - El texto se limpia antes de enviarlo: sin caracteres de control (el
 *   servidor responde 400) y como máximo `BUSQUEDA_MAX` caracteres.
 */

import { useState } from 'react';
import type { AccessLevel, AccessOrigin, InventoryParams } from '@/lib/access/types';
import { FilterBar, FilterBarGrid, FilterBarSearch } from '../filter-bar';
import { Field, Select, TextInput } from '../form';
import { NIVELES } from './access-status-badge';
import { FILTROS } from './my-access';
import { type OpcionesAlcance, ScopeSelects } from './scope-filters';

export type { PlataformaFiltro } from './scope-filters';

export type FiltroEstado = NonNullable<InventoryParams['status']>;

export interface FiltrosInventario {
  areaId: number | null;
  platformId: number | null;
  level: AccessLevel | null;
  origin: AccessOrigin | null;
  status: FiltroEstado;
  q: string;
}

export const FILTROS_INICIALES: FiltrosInventario = {
  areaId: null,
  platformId: null,
  level: null,
  origin: null,
  status: 'vigente',
  q: '',
};

/** Máximo de `q` (contrato `accesos.md`: texto ≤ 100). */
export const BUSQUEDA_MAX = 100;

/** Origen del acceso, visto por quien administra. */
export const ORIGENES_INVENTARIO: Record<AccessOrigin, string> = {
  solicitud: 'Por solicitud',
  admin_de_area: 'Automático (admin del área)',
};

export const FILTRO_AREA_ID = 'inventario-filtro-area';

// Caracteres de control (categoría Unicode Cc: C0, DEL y C1): el servidor
// rechaza `q` con ellos (400, SEG-FNC059-01).
const CONTROL = /[\u0000-\u001f\u007f-\u009f]/g;

/** Texto de búsqueda listo para enviar. */
export function limpiarBusqueda(texto: string): string {
  return texto.replace(CONTROL, '').trim().slice(0, BUSQUEDA_MAX);
}

/** ¿Hay algún filtro distinto del inicial? */
export function hayFiltros(filtros: FiltrosInventario): boolean {
  return (Object.keys(FILTROS_INICIALES) as (keyof FiltrosInventario)[])
    .some((clave) => filtros[clave] !== FILTROS_INICIALES[clave]);
}

export function InventoryFilters({
  filtros,
  opciones,
  onChange,
}: {
  filtros: FiltrosInventario;
  /** Áreas y plataformas del alcance (`useOpcionesAlcance`). */
  opciones: OpcionesAlcance;
  onChange: (cambio: Partial<FiltrosInventario>) => void;
}) {
  const [borrador, setBorrador] = useState(filtros.q);

  function buscar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = limpiarBusqueda(borrador);
    setBorrador(q);
    onChange({ q });
  }

  return (
    <FilterBar label="Filtros del inventario" layout="stack">
      <FilterBarSearch onSubmit={buscar}>
        <TextInput
          type="search"
          value={borrador}
          maxLength={BUSQUEDA_MAX}
          onChange={(event) => setBorrador(event.target.value)}
          placeholder="Nombre o correo del usuario…"
          aria-label="Buscar en el inventario por nombre o correo del usuario"
        />
      </FilterBarSearch>

      <FilterBarGrid>
        <ScopeSelects
          areaId={filtros.areaId}
          platformId={filtros.platformId}
          opciones={opciones}
          areaSelectId={FILTRO_AREA_ID}
          onChange={onChange}
        />
        <Field label="Estado">
          <Select
            value={filtros.status}
            onChange={(event) => onChange({ status: event.target.value as FiltroEstado })}
          >
            {FILTROS.map((filtro) => (
              <option key={filtro.valor} value={filtro.valor}>{filtro.texto}</option>
            ))}
          </Select>
        </Field>
        <Field label="Nivel">
          <Select
            value={filtros.level ?? ''}
            onChange={(event) =>
              onChange({ level: (event.target.value || null) as AccessLevel | null })}
          >
            <option value="">Todos los niveles</option>
            {(Object.keys(NIVELES) as AccessLevel[]).map((nivel) => (
              <option key={nivel} value={nivel}>{NIVELES[nivel]}</option>
            ))}
          </Select>
        </Field>
        <Field label="Origen">
          <Select
            value={filtros.origin ?? ''}
            onChange={(event) =>
              onChange({ origin: (event.target.value || null) as AccessOrigin | null })}
          >
            <option value="">Todos los orígenes</option>
            {(Object.keys(ORIGENES_INVENTARIO) as AccessOrigin[]).map((origen) => (
              <option key={origen} value={origen}>{ORIGENES_INVENTARIO[origen]}</option>
            ))}
          </Select>
        </Field>
      </FilterBarGrid>
    </FilterBar>
  );
}
