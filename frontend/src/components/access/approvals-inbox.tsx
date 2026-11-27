'use client';

/**
 * Bandeja de aprobaciones (DIS-015, F-SOL-03, RF-03, RF-06;
 * `GET /access-requests/inbox`, contrato `solicitudes.md` 1.1).
 *
 * - Admin de área: sus áreas; superadmin: todas (lo decide el backend).
 * - Historial (DIS-156): filtros Estado (Todas, Pendientes, Aprobadas, Rechazadas; `pendiente` por
 *   defecto), Área > Plataforma en cascada y búsqueda `q` (con retraso), reflejados en la URL.
 * - Aprobar con confirmación; rechazar con motivo obligatorio.
 * - Tras decidir: la fila se actualiza con la respuesta del servidor (sin
 *   recargar) y el resultado se avisa con toast (DIS-091); el foco va al filtro
 *   de estado. El siguiente refresco la saca de pendientes.
 * - Refresco con `usePolling` y el intervalo de la preferencia del usuario.
 * - DIS-156: mismo diseño que el detalle de un área en Plataformas: tarjeta de herramientas
 *   (Volver, buscador, selectores) y `DataTable` con filas de una línea. El buscador y los
 *   filtros los resuelve el backend (`q`, `area_id`, `platform_id`, `status=todas`; FNC-218).
 */

import { useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { requestsApi } from '@/lib/access/requests';
import type { AccessRequest, InboxStatus, RequestStatus } from '@/lib/access/types';
import type { AreaRef, Platform } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { useDebouncedValue } from '@/lib/use-debounced-value';
import { usePolling } from '@/lib/use-polling';
import { DataTable } from '../data-table';
import { Button } from '../form';
import { useSession } from '../session-provider';
import { useToast } from '../toast';
import { Card, ErrorNote, Skeleton } from '../ui';
import { NIVELES } from './access-status-badge';
import { ApproveDialog } from './approve-dialog';
import {
  ApprovalsInboxToolbar,
  FILTRO_AREA_ID,
  FILTRO_ESTADO_ID,
  BUSCADOR_ID,
} from './approvals-inbox-toolbar';
import { columnasBandeja, type TipoDecision } from './approvals-inbox-columns';
import { valorPermitido, idDeUrl } from './filtro-url';
import { RejectDialog } from './reject-dialog';
import { listLoadError } from './request-errors';
import { ESTADOS_SOLICITUD } from './request-status-badge';

export { MENSAJE_PROPIA } from './approvals-inbox-columns';

const NOMBRE_LISTA = 'las solicitudes de tu bandeja';
/** Filas por página: las que caben en la tabla (como Plataformas, 8 con filas fantasma). */
export const BANDEJA_POR_PAGINA = 8;
/** Columnas condicionables (FNC-217 las ocultará según la configuración). */
const MOSTRAR_JUSTIFICACION = true;
const MOSTRAR_MOTIVO = true;

/** Foco tras decidir: el filtro de estado (la fila decidida ya no tiene botones). */
function enfocarFiltro(): void {
  (document.getElementById(FILTRO_ESTADO_ID) ?? document.getElementById(FILTRO_AREA_ID))?.focus();
}

/** Estados del filtro (la URL admite `todas`). */
export const ESTADOS_BANDEJA: readonly InboxStatus[] = ['todas', ...(Object.keys(ESTADOS_SOLICITUD) as RequestStatus[])];
const RETRASO_BUSQUEDA_MS = 300;

/** Plural del estado para el filtro y el estado vacío. */
const ESTADO_PLURAL: Record<InboxStatus, string> = {
  todas: 'todas',
  pendiente: 'pendientes',
  aprobada: 'aprobadas',
  rechazada: 'rechazadas',
};

type Decision = { tipo: TipoDecision; request: AccessRequest };

/** Estado vacío según los filtros. */
export function mensajeVacio(status: InboxStatus, conFiltro: boolean): string {
  if (status === 'todas') return `No hay solicitudes${conFiltro ? ' con esos filtros' : ''}.`;
  return `No hay solicitudes ${ESTADO_PLURAL[status]}${conFiltro ? ' con esos filtros' : ''}.`;
}

/** Aviso tras decidir. */
export function avisoDecision(request: AccessRequest): string {
  const quien = `${request.requester.name} en ${request.platform.name}`;
  return request.status === 'rechazada'
    ? `Solicitud rechazada: ${quien}. El solicitante verá el motivo.`
    : `Solicitud aprobada: ${quien}, nivel ${NIVELES[request.level]}. El acceso queda en proceso.`;
}

/** Bandeja / historial de solicitudes; los filtros llegan y se reflejan en la URL (DIS-036, DIS-156). */
export function ApprovalsInbox({ volverHref }: { volverHref?: string } = {}) {
  const { session } = useSession();
  const esSuperadmin = session?.permissions.is_admin ?? false;

  // Estado que llega por la URL (DIS-036); lo inválido se ignora.
  const params = useSearchParams();
  const [status, setStatus] = useState<InboxStatus>(
    () => valorPermitido(params?.get('status'), ESTADOS_BANDEJA) ?? 'pendiente',
  );
  // Área que llega por la URL (DIS-137: «por aprobar» de la tarjeta de área).
  const [areaId, setAreaId] = useState<number | null>(() => idDeUrl(params?.get('area_id')));
  const [page, setPage] = useState(1);
  const [plataformaId, setPlataformaId] = useState<number | null>(() => idDeUrl(params?.get('platform_id')));
  const [busqueda, setBusqueda] = useState(() => params?.get('q') ?? '');
  const q = useDebouncedValue(busqueda.trim(), RETRASO_BUSQUEDA_MS);
  /** Solicitudes decididas aquí, con la respuesta del servidor (por `id`). */
  const [decididas, setDecididas] = useState<Record<number, AccessRequest>>({});
  const [decision, setDecision] = useState<Decision | null>(null);
  const disparador = useRef<HTMLElement | null>(null);
  const { avisar } = useToast();

  const lista = usePolling(
    () => requestsApi.inbox({
      status,
      area_id: areaId ?? undefined,
      ...(plataformaId !== null ? { platform_id: plataformaId } : {}),
      ...(q ? { q } : {}),
      page,
      per_page: BANDEJA_POR_PAGINA,
    })
      .catch((err: unknown) => {
        throw listLoadError(err, NOMBRE_LISTA);
      }),
    { intervalSeconds: session?.preferences.refresh_interval, deps: [status, areaId, plataformaId, q, page] },
  );

  // Áreas del filtro: las administradas; el superadmin, todas (`GET /areas`).
  const todas = useAsync<AreaRef[]>(
    () => (esSuperadmin ? api.areas() : Promise.resolve([])),
    [esSuperadmin],
  );
  const areas: AreaRef[] = esSuperadmin ? (todas.data ?? []) : (session?.managed_areas ?? []);

  // Plataformas del filtro: las del área elegida; sin área, las de todo el alcance (`GET /platforms`).
  const plataformas = useAsync<Platform[]>(
    () => api.platforms(areaId !== null ? { areaId } : {}),
    [areaId],
  );

  // Los filtros quedan en la URL (sin añadir entradas al historial): F5 y Volver los conservan.
  useEffect(() => {
    const consulta = new URLSearchParams({ status });
    if (areaId !== null) consulta.set('area_id', String(areaId));
    if (plataformaId !== null) consulta.set('platform_id', String(plataformaId));
    if (q) consulta.set('q', q);
    window.history.replaceState(window.history.state, '', `${window.location.pathname}?${consulta}`);
  }, [status, areaId, plataformaId, q]);

  const items = useMemo(
    () => (lista.data?.items ?? []).map((item) => decididas[item.id] ?? item),
    [lista.data, decididas],
  );

  const hayMotivos = items.some((item) => item.status === 'rechazada' && item.rejection_reason);

  const miId = session?.id;
  const columnas = useMemo(
    () => columnasBandeja({
      esPropia: (request) => request.requester.id === miId,
      onDecidir: (tipo, request, trigger) => {
        disparador.current = trigger;
        setDecision({ tipo, request });
      },
      mostrarJustificacion: MOSTRAR_JUSTIFICACION,
      mostrarMotivo: MOSTRAR_MOTIVO && hayMotivos,
    }),
    [miId, hayMotivos],
  );

  // Estable: `Modal` reinstala su efecto (y el foco) si cambia `onClose`.
  const cerrar = useCallback(() => {
    setDecision(null);
    // Si la fila cambió (refresco), el botón ya no existe: el foco va al filtro.
    const boton = disparador.current;
    if (boton?.isConnected) boton.focus();
    else enfocarFiltro();
  }, []);

  const refrescar = lista.refresh;

  function decidida(request: AccessRequest) {
    setDecididas((prev) => ({ ...prev, [request.id]: request }));
    avisar('success', avisoDecision(request), 'Solicitud decidida');
    setDecision(null);
    // Los botones de la fila desaparecen: el foco va al filtro (no cae en `body`).
    requestAnimationFrame(enfocarFiltro);
  }

  const data = lista.data;

  const limpiarBusqueda = () => {
    setBusqueda('');
    setPage(1);
    document.getElementById(BUSCADOR_ID)?.focus();
  };
  const hayBusqueda = busqueda.trim() !== '';
  const hayFiltros = hayBusqueda || areaId !== null || plataformaId !== null;
  const totalPaginas = data ? Math.max(1, Math.ceil(data.total / data.per_page)) : 1;

  return (
    <div className="flex h-full min-h-0 w-full flex-col gap-4">
      <ApprovalsInboxToolbar
        volverHref={volverHref}
        busqueda={busqueda}
        onBusqueda={(valor) => {
          setBusqueda(valor);
          setPage(1);
        }}
        estado={{
          valor: status,
          opciones: ESTADOS_BANDEJA.map((estado) => ({
            valor: estado,
            texto: ESTADO_PLURAL[estado].charAt(0).toUpperCase() + ESTADO_PLURAL[estado].slice(1),
          })),
          onChange: (valor) => {
            setStatus(valor);
            setPage(1);
          },
        }}
        areaId={areaId}
        areas={areas}
        etiquetaTodasAreas={esSuperadmin ? 'Todas las áreas' : 'Todas mis áreas'}
        onArea={(id) => {
          setAreaId(id);
          setPlataformaId(null);
          setPage(1);
        }}
        plataformaId={plataformaId}
        plataformas={plataformas.data ?? []}
        onPlataforma={(id) => {
          setPlataformaId(id);
          setPage(1);
        }}
      />

      <div className="flex min-h-0 w-full flex-1 flex-col">
        {lista.loading && !data ? (
          // Esqueleto con la forma de la tabla (misma tarjeta y filas de una línea).
          <Card className="!p-0 flex h-full min-h-0 w-full flex-1 flex-col overflow-hidden border border-panel-border/80 shadow-1">
            <div className="h-10 shrink-0 border-b-2 border-primary/40 bg-gradient-to-r from-primary/15 via-brand/10 to-accent/10" />
            <div className="min-h-0 flex-1 space-y-2 p-4">
              <Skeleton variant="fila" count={BANDEJA_POR_PAGINA} ariaLabel="Cargando la bandeja…" />
            </div>
          </Card>
        ) : null}

        {lista.error ? (
          <div className="space-y-3">
            <ErrorNote message={lista.error} />
            <Button variant="secondary" onClick={refrescar}>Reintentar</Button>
          </div>
        ) : null}

        {data ? (
          <DataTable
            label="Bandeja de aprobaciones"
            columns={columnas}
            rows={items}
            rowKey={(request) => request.id}
            emptyTitle={hayFiltros ? 'No se encontraron solicitudes' : undefined}
            emptyMessage={
              hayBusqueda
                ? `No hay solicitudes que coincidan con «${busqueda.trim()}» con los filtros elegidos.`
                : mensajeVacio(status, hayFiltros)
            }
            emptyIcon="solicitudes"
            emptyAction={hayBusqueda ? (
              <Button variant="fila" onClick={limpiarBusqueda} className="nx-btn-toolbar !w-auto !px-4">
                <span>Limpiar búsqueda</span>
              </Button>
            ) : null}
            page={data.page}
            totalPages={totalPaginas}
            totalRecords={data.total}
            onPageChange={setPage}
            targetRows={BANDEJA_POR_PAGINA}
          />
        ) : null}
      </div>

      {decision?.tipo === 'aprobar' ? (
        <ApproveDialog
          request={decision.request}
          onClose={cerrar}
          onDecided={decidida}
          onStale={refrescar}
        />
      ) : null}
      {decision?.tipo === 'rechazar' ? (
        <RejectDialog
          request={decision.request}
          onClose={cerrar}
          onDecided={decidida}
          onStale={refrescar}
        />
      ) : null}
    </div>
  );
}
