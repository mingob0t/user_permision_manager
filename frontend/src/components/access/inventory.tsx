'use client';

/**
 * Inventario de permisos (DIS-021, F-AUD-02, F-AUD-04; `GET /access/inventory`,
 * contrato `accesos.md` 1.1).
 *
 * - Admin de área: sus áreas; superadmin: todo (lo decide el backend).
 * - Filtros: área (las administradas; el superadmin, `GET /areas`), plataforma,
 *   nivel, origen, estado (`vigente` por defecto) y nombre o correo.
 *   Cualquier cambio de filtro vuelve a la página 1.
 * - Sin refresco periódico (contrato, "Refresco"): botón "Recargar".
 */

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { inventoryApi } from '@/lib/access/inventory';
import type { InventoryParams } from '@/lib/access/types';
import { useAsync } from '@/lib/use-async';
import { rutaHistorialPlataforma } from '../audit/audit-routes';
import { Button } from '../form';
import { valorPermitido } from './filtro-url';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import {
  FILTROS_INICIALES,
  type FiltrosInventario,
  InventoryFilters,
  hayFiltros,
} from './inventory-filters';
import { InventoryTable } from './inventory-table';
import { ListPager } from './list-pager';
import { listLoadError } from './request-errors';
import { FILTROS } from './my-access';
import { useOpcionesAlcance } from './scope-filters';

const NOMBRE_LISTA = 'los accesos del inventario';

export const VACIO_SIN_FILTROS = 'No hay accesos vigentes en tu alcance.';
export const VACIO_CON_FILTROS = 'Ningún acceso coincide con los filtros.';

/** Filtros de la pantalla → parámetros del contrato (sin los vacíos). */
export function aParametros(filtros: FiltrosInventario, page: number): InventoryParams {
  return {
    status: filtros.status,
    area_id: filtros.areaId ?? undefined,
    platform_id: filtros.platformId ?? undefined,
    level: filtros.level ?? undefined,
    origin: filtros.origin ?? undefined,
    q: filtros.q || undefined,
    page,
  };
}

export function Inventory() {
  // Estado que llega por la URL (DIS-036); lo inválido se ignora.
  const params = useSearchParams();
  const [filtros, setFiltros] = useState<FiltrosInventario>(() => ({
    ...FILTROS_INICIALES,
    status: valorPermitido(params?.get('status'), FILTROS.map((f) => f.valor)) ?? FILTROS_INICIALES.status,
  }));
  const [page, setPage] = useState(1);

  const parametros = aParametros(filtros, page);
  const clave = JSON.stringify(parametros);
  const lista = useAsync(
    () => inventoryApi.list(parametros).catch((err: unknown) => {
      throw listLoadError(err, NOMBRE_LISTA);
    }),
    [clave],
  );

  // Áreas y plataformas del filtro, según el rol (DIS-020: compartido con Auditoría).
  const opciones = useOpcionesAlcance();
  const plataformaElegida = opciones.plataformas.find((p) => p.id === filtros.platformId);

  function cambiar(cambio: Partial<FiltrosInventario>) {
    setFiltros((prev) => ({ ...prev, ...cambio }));
    setPage(1);
  }

  const data = lista.data;
  const recargando = lista.loading && data !== null;

  /** Mientras carga se ignora el clic. */
  function recargar() {
    if (!lista.loading) lista.reload();
  }

  return (
    <div className="space-y-4">
      <InventoryFilters filtros={filtros} opciones={opciones} onChange={cambiar} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-label" aria-live="polite">
          {recargando
            ? 'Recargando…'
            : data ? `${data.total} ${data.total === 1 ? 'acceso' : 'accesos'}` : ''}
        </p>
        <div className="flex flex-wrap gap-3">
          {/* DIS-020: con una plataforma elegida, su historial en Auditoría. */}
          {plataformaElegida ? (
            <Link
              href={rutaHistorialPlataforma(plataformaElegida.id)}
              className="nexus-btn nexus-btn-secondary"
              aria-label={`Historial de ${plataformaElegida.name} en Auditoría`}
            >
              Historial
            </Link>
          ) : null}
          {/* `aria-disabled` mientras carga: el foco se queda en el botón (con `disabled` caería en `body`). */}
          <Button
            variant="secondary"
            onClick={recargar}
            aria-disabled={lista.loading || undefined}
            className="aria-disabled:opacity-40"
          >
            Recargar
          </Button>
        </div>
      </div>

      {lista.loading && !data ? <Spinner label="Cargando el inventario…" /> : null}

      {lista.error ? (
        <div className="space-y-3">
          <ErrorNote message={lista.error} />
          <Button variant="secondary" onClick={lista.reload}>Reintentar</Button>
        </div>
      ) : null}

      {data ? (
        data.items.length === 0 ? (
          // Anunciado: el vacío suele llegar tras cambiar un filtro.
          <div role="status">
            <EmptyNote message={hayFiltros(filtros) ? VACIO_CON_FILTROS : VACIO_SIN_FILTROS} />
          </div>
        ) : (
          <>
            <InventoryTable items={data.items} />
            <ListPager
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              label="Páginas del inventario"
              onChange={setPage}
            />
          </>
        )
      ) : null}
    </div>
  );
}
