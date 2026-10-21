'use client';

/**
 * Bitácora de ejecuciones de aprovisionamiento (DIS-022, F-CON-01;
 * `GET /provisioning/jobs`, contrato `conectores-y-ejecuciones.md` 1.1).
 *
 * - Alcance: el superadmin ve todo y el admin sus áreas (lo decide el backend).
 * - Filtros a la página 1; paginación con `ListPager`.
 * - Refresco con `usePolling` (ADR-006) solo mientras la página tenga
 *   ejecuciones transitorias (contrato, "Refresco"); "Recargar" siempre.
 * - Reintentar: superadmin y ejecución fallida, con confirmación; la fila se
 *   actualiza con la respuesta y el aviso (`status`) recibe el foco.
 */

import { useCallback, useMemo, useRef, useState } from 'react';
import { provisioningApi } from '@/lib/access/provisioning';
import type { Job, JobDetail } from '@/lib/access/types';
import { usePolling } from '@/lib/use-polling';
import { ListPager } from '../access/list-pager';
import { listLoadError } from '../access/request-errors';
import { useOpcionesAlcance } from '../access/scope-filters';
import { Button } from '../form';
import { useSession } from '../session-provider';
import { Card, EmptyNote, ErrorNote, Spinner } from '../ui';
import { hayTransitorios } from './job-catalog';
import { JobDetailModal } from './job-detail-modal';
import { JobRetryDialog } from './job-retry-dialog';
import {
  FILTROS_EJECUCIONES_INICIALES, FILTRO_ESTADO_ID, type FiltrosEjecuciones, JobsFilters,
  hayFiltrosEjecuciones, parametrosEjecuciones,
} from './jobs-filters';
import { JobsTable, detalleId } from './jobs-table';

const NOMBRE_LISTA = 'las ejecuciones';
export const VACIO_EJECUCIONES = 'Todavía no hay ejecuciones en tu alcance.';
export const VACIO_EJECUCIONES_FILTROS = 'Ninguna ejecución coincide con los filtros.';

export function avisoReintento(job: Job): string {
  return `Reintento en curso: ejecución n.º ${job.id} de ${job.user.name} en ${job.platform.name}.`;
}

export function JobsLog() {
  const { session } = useSession();
  const esSuperadmin = session?.permissions.is_admin ?? false;
  const alcance = useOpcionesAlcance();

  const [filtros, setFiltros] = useState<FiltrosEjecuciones>(FILTROS_EJECUCIONES_INICIALES);
  const [page, setPage] = useState(1);
  const [transitorios, setTransitorios] = useState(true);
  /** Ejecuciones reintentadas aquí, con la respuesta del servidor (por `id`). */
  const [reintentadas, setReintentadas] = useState<Record<number, Job>>({});
  const [detalle, setDetalle] = useState<Job | null>(null);
  const [reintentando, setReintentando] = useState<Job | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const disparador = useRef<string | null>(null);
  const avisoRef = useRef<HTMLDivElement>(null);

  const parametros = parametrosEjecuciones(filtros, page);
  const clave = JSON.stringify(parametros);
  const lista = usePolling(
    () => provisioningApi.jobs(parametros)
      .then((r) => {
        setTransitorios(hayTransitorios(r.items));
        setReintentadas({});
        return r;
      })
      .catch((err: unknown) => { throw listLoadError(err, NOMBRE_LISTA); }),
    { intervalSeconds: session?.preferences.refresh_interval, deps: [clave], activo: transitorios },
  );

  const items = useMemo(
    () => (lista.data?.items ?? []).map((job) => reintentadas[job.id] ?? job),
    [lista.data, reintentadas],
  );

  function cambiar(cambio: Partial<FiltrosEjecuciones>) {
    setFiltros((prev) => ({ ...prev, ...cambio }));
    setPage(1);
  }

  /** Foco de vuelta al botón que abrió el diálogo; si ya no existe, al filtro. */
  const devolverFoco = useCallback(() => {
    const id = disparador.current;
    const boton = id ? document.getElementById(id) : null;
    (boton ?? document.getElementById(FILTRO_ESTADO_ID))?.focus();
  }, []);

  const cerrarDetalle = useCallback(() => {
    setDetalle(null);
    devolverFoco();
  }, [devolverFoco]);

  const cerrarReintento = useCallback(() => {
    setReintentando(null);
    devolverFoco();
  }, [devolverFoco]);

  function abrirDetalle(job: Job) {
    disparador.current = detalleId(job.id);
    setDetalle(job);
  }

  function abrirReintento(job: Job) {
    // El botón "Reintentar" desaparece al reintentar: el foco vuelve a "Detalle".
    disparador.current = detalleId(job.id);
    setAviso(null);
    setReintentando(job);
  }

  function reintentada(job: JobDetail) {
    setReintentadas((prev) => ({ ...prev, [job.id]: job }));
    setReintentando(null);
    setTransitorios(true);
    setAviso(avisoReintento(job));
    requestAnimationFrame(() => avisoRef.current?.focus());
  }

  function cerrarAviso() {
    setAviso(null);
    document.getElementById(FILTRO_ESTADO_ID)?.focus();
  }

  const data = lista.data;
  const recargando = lista.loading && data !== null;

  return (
    <section aria-labelledby="ejecuciones-titulo" className="space-y-4">
      <div>
        <h2 id="ejecuciones-titulo" className="text-lg font-semibold">Bitácora de ejecuciones</h2>
        <p className="text-sm text-label">
          Cada vez que el portal otorga o retira un acceso en una plataforma. Se actualiza sola
          mientras haya ejecuciones en curso.
        </p>
      </div>

      <div role="status" ref={avisoRef} tabIndex={-1} className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary">
        {aviso ? (
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-bold text-success-text">{aviso}</p>
              <Button variant="secondary" onClick={cerrarAviso}>Cerrar aviso</Button>
            </div>
          </Card>
        ) : null}
      </div>

      <JobsFilters filtros={filtros} alcance={alcance} onChange={cambiar} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-label" aria-live="polite">
          {recargando
            ? 'Recargando…'
            : data ? `${data.total} ${data.total === 1 ? 'ejecución' : 'ejecuciones'}` : ''}
        </p>
        <Button
          variant="secondary"
          onClick={() => { if (!lista.loading) lista.refresh(); }}
          aria-disabled={lista.loading || undefined}
          className="aria-disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary"
        >
          Recargar
        </Button>
      </div>

      {lista.loading && !data ? <Spinner label="Cargando las ejecuciones…" /> : null}

      {lista.error ? (
        <div className="space-y-3">
          <ErrorNote message={lista.error} />
          <Button variant="secondary" onClick={lista.refresh}>Reintentar</Button>
        </div>
      ) : null}

      {data ? (
        items.length === 0 ? (
          <div role="status">
            <EmptyNote message={hayFiltrosEjecuciones(filtros) ? VACIO_EJECUCIONES_FILTROS : VACIO_EJECUCIONES} />
          </div>
        ) : (
          <>
            <JobsTable
              items={items}
              esSuperadmin={esSuperadmin}
              onDetalle={abrirDetalle}
              onReintentar={abrirReintento}
            />
            <ListPager
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              label="Páginas de la bitácora de ejecuciones"
              onChange={setPage}
            />
          </>
        )
      ) : null}

      {detalle ? <JobDetailModal job={detalle} onClose={cerrarDetalle} /> : null}

      {reintentando ? (
        <JobRetryDialog
          job={reintentando}
          onClose={cerrarReintento}
          onRetried={reintentada}
          onStale={lista.refresh}
        />
      ) : null}
    </section>
  );
}
