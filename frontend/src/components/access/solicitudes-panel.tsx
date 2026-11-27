'use client';

/**
 * Panel «Solicitudes» del resumen de Solicitudes (DIS-141): las pendientes de la bandeja
 * (`GET /access-requests/inbox?status=pendiente`, 8 por página) con el estilo de «Actividad
 * reciente»: usuario, área / plataforma, fecha y botones de aprobar y rechazar. Aprobar y
 * rechazar reutilizan los diálogos de la bandeja; la propia no se decide aquí.
 */

import Link from 'next/link';
import { useCallback, useRef, useState } from 'react';
import { requestsApi } from '@/lib/access/requests';
import type { AccessRequest } from '@/lib/access/types';
import { usePolling } from '@/lib/use-polling';
import { Button } from '../form';
import { Icono } from '../icono';
import { FilasFantasma, PanelTablaEncabezado, PanelTablaPie, claseFilaPanel } from '../panel-tabla';
import { useSession } from '../session-provider';
import { useToast } from '../toast';
import { Card, EmptyNote, ErrorNote, PanelHeader, Skeleton } from '../ui';
import { ApproveDialog } from './approve-dialog';
import { MENSAJE_PROPIA, avisoDecision } from './approvals-inbox';
import { formatearFechaCorta24h } from './fecha';
import { rutaConFiltro } from './filtro-url';
import { RejectDialog } from './reject-dialog';
import { listLoadError } from './request-errors';

/** Filas por página, como «Actividad reciente». */
export const SOLICITUDES_POR_PAGINA = 8;
const NOMBRE_LISTA = 'las solicitudes pendientes';
const TITULO_ID = 'panel-solicitudes-titulo';
const RUTA_PENDIENTES = rutaConFiltro('/approvals', { status: 'pendiente' });
const COLUMNAS = ['Usuario', 'Área / Plataforma', 'Fecha', 'Acciones'];
const GRID = 'sm:grid-cols-[minmax(0,1.6fr)_minmax(0,1.6fr)_minmax(0,1fr)_auto]';

type Decision = { tipo: 'aprobar' | 'rechazar'; request: AccessRequest };

/** Nombre accesible de cada botón: qué hace y sobre qué solicitud. */
export function nombreDecision(accion: 'Aprobar' | 'Rechazar', r: AccessRequest): string {
  return `${accion} la solicitud de ${r.requester.name} para ${r.platform.name}`;
}

function Fila({
  request,
  indice,
  propia,
  onDecidir,
}: {
  request: AccessRequest;
  indice: number;
  propia: boolean;
  onDecidir: (d: Decision, trigger: HTMLButtonElement) => void;
}) {
  const fecha = formatearFechaCorta24h(request.created_at);
  return (
    <li
      aria-label={`Solicitud de ${request.requester.name} para ${request.platform.name}`}
      className={`flex flex-1 min-h-11 sm:min-h-0 items-center justify-between gap-2 border-b border-panel-border/30 px-3 py-1.5 text-xs transition-colors hover:bg-primary/[0.04] sm:grid sm:gap-3 sm:px-4 sm:py-0 ${GRID} ${claseFilaPanel(indice)}`}
    >
      <div className="flex items-center gap-2.5 min-w-0">
        <span aria-hidden="true" className="flex size-7 shrink-0 items-center justify-center rounded-full shadow-xs nx-tono-warning">
          <Icono nombre="usuarios" tamano="sm" />
        </span>
        <div className="min-w-0 flex-1">
          <span className="block truncate font-semibold text-body-text" title={request.requester.name}>
            {request.requester.name}
          </span>
          <span className="block truncate text-xs text-label" title={request.requester.email}>
            {request.requester.email}
          </span>
          <span className="block truncate text-xs text-label sm:hidden">
            {request.area.name} · {request.platform.name} · {fecha}
          </span>
        </div>
      </div>
      <div className="hidden sm:block min-w-0">
        <span className="block truncate font-semibold text-body-text" title={request.platform.name}>
          {request.platform.name}
        </span>
        <span className="block truncate text-xs text-label" title={request.area.name}>
          {request.area.name}
        </span>
      </div>
      <div className="hidden sm:block tabular-nums font-medium text-label whitespace-nowrap">{fecha}</div>
      <div className="flex shrink-0 items-center justify-end gap-2">
        {propia ? (
          <span className="text-xs text-label" title={MENSAJE_PROPIA}>
            Tu solicitud<span className="sr-only">. {MENSAJE_PROPIA}</span>
          </span>
        ) : (
          <>
            <Button
              variant="fila-peligro"
              aria-label={nombreDecision('Rechazar', request)}
              title="Rechazar"
              onClick={(e) => onDecidir({ tipo: 'rechazar', request }, e.currentTarget)}
            >
              <Icono nombre="rechazar" />
            </Button>
            <Button
              variant="fila-primario"
              aria-label={nombreDecision('Aprobar', request)}
              title="Aprobar"
              onClick={(e) => onDecidir({ tipo: 'aprobar', request }, e.currentTarget)}
            >
              <Icono nombre="aprobar" />
            </Button>
          </>
        )}
      </div>
    </li>
  );
}

export function SolicitudesPanel() {
  const { session } = useSession();
  const { avisar } = useToast();
  const [pagina, setPagina] = useState(1);
  const [decision, setDecision] = useState<Decision | null>(null);
  const disparador = useRef<HTMLElement | null>(null);

  const lista = usePolling(
    () => requestsApi.inbox({ status: 'pendiente', page: pagina, per_page: SOLICITUDES_POR_PAGINA })
      .catch((err: unknown) => {
        throw listLoadError(err, NOMBRE_LISTA);
      }),
    { intervalSeconds: session?.preferences.refresh_interval, deps: [pagina] },
  );
  const refrescar = lista.refresh;

  const items = lista.data?.items ?? [];
  const total = lista.data?.total ?? items.length;
  const paginas = Math.max(1, Math.ceil(total / SOLICITUDES_POR_PAGINA));

  const abrir = (nueva: Decision, trigger: HTMLButtonElement) => {
    disparador.current = trigger;
    setDecision(nueva);
  };
  // Estable: `Modal` reinstala su efecto (y el foco) si cambia `onClose`.
  const cerrar = useCallback(() => {
    setDecision(null);
    if (disparador.current?.isConnected) disparador.current.focus();
  }, []);
  const decidida = (request: AccessRequest) => {
    avisar('success', avisoDecision(request), 'Solicitud decidida');
    cerrar();
    refrescar();
  };

  return (
    <section aria-labelledby={TITULO_ID} className="flex flex-1 min-h-0 flex-col h-full min-w-0">
      <Card className="!p-0 flex flex-1 min-h-0 flex-col overflow-hidden shadow-1 border border-panel-border/80">
        <PanelHeader
          title="Solicitudes"
          subtitle="Pendientes por aprobar"
          icon="solicitudes"
          titleId={TITULO_ID}
          // h3: dentro del resumen (h2 oculto), al nivel de la dona y las gráficas.
          titleTag="h3"
          actions={
            <Link
              href={RUTA_PENDIENTES}
              className="inline-flex min-h-12 items-center gap-1.5 whitespace-nowrap rounded-lg px-3 text-xs font-bold text-primary-text transition-colors hover:bg-surface-container outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <span>Ver todo</span>
              <Icono nombre="chevron-der" tamano="sm" ariaHidden={true} />
            </Link>
          }
        />

        <PanelTablaEncabezado columnas={COLUMNAS} claseGrid={GRID} />

        <div className="flex flex-1 min-h-0 flex-col overflow-x-auto overflow-y-hidden">
          {lista.loading && !lista.data ? (
            <div className="p-4 space-y-3">
              <Skeleton variant="fila" count={4} ariaLabel="Cargando las solicitudes pendientes…" />
            </div>
          ) : null}

          {lista.error ? (
            <div className="p-4 space-y-3">
              <ErrorNote message={lista.error} />
              <Button variant="secondary" onClick={refrescar}>Reintentar</Button>
            </div>
          ) : null}

          {lista.data && items.length === 0 ? (
            <div className="flex flex-1 min-h-0 flex-col h-full w-full">
              <EmptyNote variant="seamless" message="No hay solicitudes pendientes." className="h-full min-h-72" />
            </div>
          ) : null}

          {items.length > 0 ? (
            <ul role="list" aria-label="Solicitudes pendientes" className="flex flex-1 min-h-0 flex-col h-full justify-between">
              {items.map((request, indice) => (
                <Fila
                  key={request.id}
                  request={request}
                  indice={indice}
                  propia={request.requester.id === session?.id}
                  onDecidir={abrir}
                />
              ))}
              <FilasFantasma
                cantidad={Math.max(0, SOLICITUDES_POR_PAGINA - items.length)}
                desde={items.length}
                claseGrid={GRID}
              />
            </ul>
          ) : null}
        </div>

        <PanelTablaPie
          mostrados={items.length}
          total={total}
          pagina={pagina}
          paginas={paginas}
          onPagina={setPagina}
          etiqueta="de solicitudes"
        />
      </Card>

      {decision?.tipo === 'aprobar' ? (
        <ApproveDialog request={decision.request} onClose={cerrar} onDecided={decidida} onStale={refrescar} />
      ) : null}
      {decision?.tipo === 'rechazar' ? (
        <RejectDialog request={decision.request} onClose={cerrar} onDecided={decidida} onStale={refrescar} />
      ) : null}
    </section>
  );
}
