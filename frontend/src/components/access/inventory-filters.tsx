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
import type { AreaRef } from '@/lib/types';
import { Button, Select, TextInput } from '../form';
import { NIVELES } from './access-status-badge';
import { FILTROS } from './my-access';

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

/** Plataforma del filtro: solo lo que el filtro necesita de `Platform`. */
export interface PlataformaFiltro {
  id: number;
  name: string;
  area_id: number;
}

// Caracteres de control C0 y DEL: el servidor rechaza `q` con ellos (400).
const CONTROL = /[\u0000-\u001f\u007f]/g;

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
  areas,
  plataformas,
  esSuperadmin,
  onChange,
}: {
  filtros: FiltrosInventario;
  areas: AreaRef[];
  /** Plataformas del alcance; se acotan al área elegida. */
  plataformas: PlataformaFiltro[];
  esSuperadmin: boolean;
  onChange: (cambio: Partial<FiltrosInventario>) => void;
}) {
  const [borrador, setBorrador] = useState(filtros.q);
  const visibles = filtros.areaId === null
    ? plataformas
    : plataformas.filter((p) => p.area_id === filtros.areaId);

  function buscar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = limpiarBusqueda(borrador);
    setBorrador(q);
    onChange({ q });
  }

  return (
    <div className="space-y-3">
      <form role="search" onSubmit={buscar} className="grid gap-3 sm:grid-cols-[1fr_auto]">
        <TextInput
          type="search"
          value={borrador}
          maxLength={BUSQUEDA_MAX}
          onChange={(event) => setBorrador(event.target.value)}
          placeholder="Nombre o correo del usuario…"
          aria-label="Buscar en el inventario por nombre o correo del usuario"
        />
        <Button type="submit" variant="secondary">Buscar</Button>
      </form>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Select
          id={FILTRO_AREA_ID}
          value={filtros.areaId ?? ''}
          onChange={(event) => {
            const areaId = event.target.value ? Number(event.target.value) : null;
            const sigue = plataformas.some(
              (p) => p.id === filtros.platformId && (areaId === null || p.area_id === areaId));
            onChange({ areaId, platformId: sigue ? filtros.platformId : null });
          }}
          aria-label="Filtrar el inventario por área"
        >
          <option value="">{esSuperadmin ? 'Todas las áreas' : 'Todas mis áreas'}</option>
          {areas.map((area) => (
            <option key={area.id} value={area.id}>{area.name}</option>
          ))}
        </Select>
        <Select
          value={filtros.platformId ?? ''}
          onChange={(event) =>
            onChange({ platformId: event.target.value ? Number(event.target.value) : null })}
          aria-label="Filtrar el inventario por plataforma"
        >
          <option value="">Todas las plataformas</option>
          {visibles.map((plataforma) => (
            <option key={plataforma.id} value={plataforma.id}>{plataforma.name}</option>
          ))}
        </Select>
        <Select
          value={filtros.status}
          onChange={(event) => onChange({ status: event.target.value as FiltroEstado })}
          aria-label="Filtrar el inventario por estado"
        >
          {FILTROS.map((filtro) => (
            <option key={filtro.valor} value={filtro.valor}>{filtro.texto}</option>
          ))}
        </Select>
        <Select
          value={filtros.level ?? ''}
          onChange={(event) =>
            onChange({ level: (event.target.value || null) as AccessLevel | null })}
          aria-label="Filtrar el inventario por nivel"
        >
          <option value="">Todos los niveles</option>
          {(Object.keys(NIVELES) as AccessLevel[]).map((nivel) => (
            <option key={nivel} value={nivel}>{NIVELES[nivel]}</option>
          ))}
        </Select>
        <Select
          value={filtros.origin ?? ''}
          onChange={(event) =>
            onChange({ origin: (event.target.value || null) as AccessOrigin | null })}
          aria-label="Filtrar el inventario por origen"
        >
          <option value="">Todos los orígenes</option>
          {(Object.keys(ORIGENES_INVENTARIO) as AccessOrigin[]).map((origen) => (
            <option key={origen} value={origen}>{ORIGENES_INVENTARIO[origen]}</option>
          ))}
        </Select>
      </div>
    </div>
  );
}
