'use client';

/**
 * Lista de auditoría con filtros, paginación y detalle (DIS-020; F-AUD-01,
 * F-AUD-03, F-AUD-04; contrato `auditoria.md`). La usan la pantalla general
 * (`GET /audit`) y los historiales por usuario y por plataforma.
 *
 * - El backend decide el alcance (superadmin todo; admin sus áreas; usuario lo suyo).
 * - Cualquier cambio de filtro vuelve a la página 1.
 * - Sin refresco periódico (contrato, "Refresco"): botón "Recargar".
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '@/lib/api';
import type { AuditEntryV1, AuditParams, Paginated } from '@/lib/access/types';
import { useAsync } from '@/lib/use-async';
import { ListPager } from '../access/list-pager';
import { listLoadError } from '../access/request-errors';
import { useOpcionesAlcance } from '../access/scope-filters';
import { Button } from '../form';
import { useSession } from '../session-provider';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import { AuditDetailModal } from './audit-detail-modal';
import {
  AuditFilters,
  FILTROS_INICIALES,
  type FiltrosAuditoria,
  aParametros,
  hayFiltros,
} from './audit-filters';
import { AuditTable } from './audit-table';

const NOMBRE_LISTA = 'los registros de auditoría';

export const VACIO_SIN_FILTROS = 'No hay registros dentro de tu alcance.';
export const VACIO_CON_FILTROS = 'Ningún registro coincide con los filtros.';

/** `404` del historial: el usuario o la plataforma no existe o está fuera del alcance. */
export const MENSAJE_NO_ENCONTRADO = 'No existe o está fuera de tu alcance.';

/** Error de carga en español, sin detalles del servidor. */
export function errorDeCarga(err: unknown): Error {
  if (err instanceof ApiError && err.status === 404) {
    return new ApiError(404, MENSAJE_NO_ENCONTRADO);
  }
  return listLoadError(err, NOMBRE_LISTA);
}

export function AuditHistory({
  cargar,
  conAlcance = true,
  onDatos,
}: {
  /** Endpoint del contrato con los parámetros ya armados. */
  cargar: (params: AuditParams) => Promise<Paginated<AuditEntryV1>>;
  /**
   * Filtros de área y plataforma para quien administra. `false` en el
   * historial de una plataforma (ya está fijada).
   */
  conAlcance?: boolean;
  /** Cada página recibida (p. ej. para nombrar al usuario o la plataforma del historial). */
  onDatos?: (items: AuditEntryV1[]) => void;
}) {
  const { session } = useSession();
  const administra = Boolean(session?.permissions.is_admin || session?.permissions.is_area_admin);
  const mostrarAlcance = conAlcance && administra;

  const [filtros, setFiltros] = useState<FiltrosAuditoria>(FILTROS_INICIALES);
  const [page, setPage] = useState(1);
  const [detalle, setDetalle] = useState<AuditEntryV1 | null>(null);
  const origen = useRef<HTMLButtonElement | null>(null);

  const parametros = aParametros(filtros, page);
  const clave = JSON.stringify(parametros);
  const lista = useAsync(
    () => cargar(parametros).catch((err: unknown) => {
      throw errorDeCarga(err);
    }),
    [clave],
  );

  const opciones = useOpcionesAlcance(mostrarAlcance);

  function cambiar(cambio: Partial<FiltrosAuditoria>) {
    setFiltros((prev) => ({ ...prev, ...cambio }));
    setPage(1);
  }

  function abrir(entry: AuditEntryV1, boton: HTMLButtonElement) {
    origen.current = boton;
    setDetalle(entry);
  }

  // Al cerrar, el foco vuelve al botón "Ver detalle" de la fila.
  const cerrar = useCallback(() => {
    setDetalle(null);
    const boton = origen.current;
    origen.current = null;
    if (boton) requestAnimationFrame(() => boton.focus());
  }, []);

  const data = lista.data;
  useEffect(() => {
    if (data) onDatos?.(data.items);
  }, [data, onDatos]);
  const recargando = lista.loading && data !== null;

  /** Mientras carga se ignora el clic. */
  function recargar() {
    if (!lista.loading) lista.reload();
  }

  return (
    <div className="space-y-4">
      <AuditFilters
        filtros={filtros}
        opciones={opciones}
        conAlcance={mostrarAlcance}
        onChange={cambiar}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-label" aria-live="polite">
          {recargando
            ? 'Recargando…'
            : data ? `${data.total} ${data.total === 1 ? 'registro' : 'registros'}` : ''}
        </p>
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

      {lista.loading && !data ? <Spinner label="Cargando la auditoría…" /> : null}

      {lista.error ? (
        <div className="space-y-3">
          <ErrorNote message={lista.error} />
          <Button variant="secondary" onClick={lista.reload}>Reintentar</Button>
        </div>
      ) : null}

      {data && !lista.error ? (
        data.items.length === 0 ? (
          // Anunciado: el vacío suele llegar tras cambiar un filtro.
          <div role="status">
            <EmptyNote message={hayFiltros(filtros) ? VACIO_CON_FILTROS : VACIO_SIN_FILTROS} />
          </div>
        ) : (
          <>
            <AuditTable items={data.items} onDetalle={abrir} />
            <ListPager
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              label="Páginas de la auditoría"
              onChange={setPage}
            />
          </>
        )
      ) : null}

      {detalle ? <AuditDetailModal entry={detalle} onClose={cerrar} /> : null}
    </div>
  );
}
