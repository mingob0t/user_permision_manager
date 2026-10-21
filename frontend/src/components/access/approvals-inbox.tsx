'use client';

/**
 * Bandeja de aprobaciones (DIS-015, F-SOL-03, RF-03, RF-06;
 * `GET /access-requests/inbox`, contrato `solicitudes.md` 1.1).
 *
 * - Admin de área: sus áreas; superadmin: todas (lo decide el backend).
 * - Filtros por estado (`pendiente` por defecto, como el contrato) y área.
 * - Aprobar con confirmación; rechazar con motivo obligatorio.
 * - Tras decidir: la fila se actualiza con la respuesta del servidor (sin
 *   recargar) y el resultado se anuncia en una región `status` con el foco,
 *   como el aviso del catálogo (DIS-013). El siguiente refresco la saca de
 *   pendientes.
 * - Refresco con `usePolling` y el intervalo de la preferencia del usuario.
 */

import { useCallback, useMemo, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { requestsApi } from '@/lib/access/requests';
import type { AccessRequest, RequestStatus } from '@/lib/access/types';
import type { AreaRef } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { usePolling } from '@/lib/use-polling';
import { Button, Select } from '../form';
import { useSession } from '../session-provider';
import { Card, EmptyNote, ErrorNote, Spinner } from '../ui';
import { AccessStatusBadge, NIVELES } from './access-status-badge';
import { ApproveDialog } from './approve-dialog';
import { formatearFecha } from './fecha';
import { ListPager } from './list-pager';
import { RejectDialog } from './reject-dialog';
import { listLoadError } from './request-errors';
import { ETIQUETA_CELDA, ResponsiveList, ResponsiveRow } from './responsive-list';
import { ESTADOS_SOLICITUD, RequestStatusBadge } from './request-status-badge';

const NOMBRE_LISTA = 'las solicitudes de tu bandeja';
const FILTRO_ESTADO_ID = 'bandeja-filtro-estado';

/** Columnas en escritorio: solicitante, plataforma, nivel, estado, acciones. */
const COLUMNAS =
  'md:grid-cols-[minmax(0,2fr)_minmax(0,2fr)_minmax(0,1fr)_minmax(0,1.5fr)_minmax(0,1.5fr)]';
const ANCHO_COMPLETO = 'md:col-span-5';

const ESTADOS = Object.keys(ESTADOS_SOLICITUD) as RequestStatus[];

/** Plural del estado para el filtro y el estado vacío. */
const ESTADO_PLURAL: Record<RequestStatus, string> = {
  pendiente: 'pendientes',
  aprobada: 'aprobadas',
  rechazada: 'rechazadas',
};

export const MENSAJE_PROPIA = 'Es tu solicitud: la decide otro administrador.';

type Decision = { tipo: 'aprobar' | 'rechazar'; request: AccessRequest };

/** Estado vacío según los filtros. */
export function mensajeVacio(status: RequestStatus, conArea: boolean): string {
  return `No hay solicitudes ${ESTADO_PLURAL[status]}${conArea ? ' en esa área' : ''}.`;
}

/** Aviso tras decidir. */
export function avisoDecision(request: AccessRequest): string {
  const quien = `${request.requester.name} en ${request.platform.name}`;
  return request.status === 'rechazada'
    ? `Solicitud rechazada: ${quien}. El solicitante verá el motivo.`
    : `Solicitud aprobada: ${quien}, nivel ${NIVELES[request.level]}. El acceso queda en proceso.`;
}

function Fila({
  request,
  propia,
  onDecidir,
}: {
  request: AccessRequest;
  propia: boolean;
  onDecidir: (decision: Decision, trigger: HTMLButtonElement) => void;
}) {
  const rechazo = request.status === 'rechazada' ? request.rejection_reason : null;
  const quien = `${request.requester.name} para ${request.platform.name}`;
  return (
    <ResponsiveRow columns={COLUMNAS} label={`Solicitud de ${quien}`}>
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Solicitante</dt>
        <dd className="font-semibold text-body-text">{request.requester.name}</dd>
        <dd className="break-words text-sm text-label">{request.requester.email}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Plataforma</dt>
        <dd className="text-sm font-semibold text-body-text">{request.platform.name}</dd>
        <dd className="text-sm text-label">{request.area.name}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Nivel</dt>
        <dd className="text-sm text-body-text">{NIVELES[request.level]}</dd>
        {request.current_level ? (
          <dd className="text-sm text-label">Tiene {NIVELES[request.current_level]}</dd>
        ) : null}
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Estado</dt>
        <dd className="flex flex-wrap gap-2">
          <RequestStatusBadge status={request.status} />
          {request.access ? <AccessStatusBadge status={request.access.status} /> : null}
        </dd>
        <dd className="text-sm text-label">Enviada: {formatearFecha(request.created_at)}</dd>
        {request.decided_at ? (
          <dd className="text-sm text-label">
            Decidida: {formatearFecha(request.decided_at)}
            {request.decided_by ? ` por ${request.decided_by.name}` : ''}
          </dd>
        ) : null}
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Acciones</dt>
        {request.status !== 'pendiente' ? (
          <dd className="text-sm text-label">Decidida</dd>
        ) : propia ? (
          <dd className="text-sm text-label">{MENSAJE_PROPIA}</dd>
        ) : (
          <dd className="flex flex-wrap gap-2">
            <Button
              aria-label={`Aprobar la solicitud de ${quien}`}
              onClick={(event) => onDecidir({ tipo: 'aprobar', request }, event.currentTarget)}
            >
              Aprobar
            </Button>
            <Button
              variant="secondary"
              aria-label={`Rechazar la solicitud de ${quien}`}
              onClick={(event) => onDecidir({ tipo: 'rechazar', request }, event.currentTarget)}
            >
              Rechazar
            </Button>
          </dd>
        )}
      </div>
      {rechazo ? (
        <div className={ANCHO_COMPLETO}>
          <dt className="text-xs font-medium uppercase tracking-wide text-error-text">
            Motivo del rechazo
          </dt>
          <dd className="break-words text-sm text-body-text">{rechazo}</dd>
        </div>
      ) : null}
      <div className={ANCHO_COMPLETO}>
        <dt className="text-xs font-medium uppercase tracking-wide text-label">Justificación</dt>
        {/* Texto del solicitante: React lo escapa; nunca HTML. */}
        <dd className="whitespace-pre-line break-words text-sm text-body-text">
          {request.justification || 'Sin justificación.'}
        </dd>
      </div>
    </ResponsiveRow>
  );
}

export function ApprovalsInbox() {
  const { session } = useSession();
  const esSuperadmin = session?.permissions.is_admin ?? false;

  const [status, setStatus] = useState<RequestStatus>('pendiente');
  const [areaId, setAreaId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  /** Solicitudes decididas aquí, con la respuesta del servidor (por `id`). */
  const [decididas, setDecididas] = useState<Record<number, AccessRequest>>({});
  const [decision, setDecision] = useState<Decision | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const disparador = useRef<HTMLElement | null>(null);
  const avisoRef = useRef<HTMLDivElement>(null);

  const lista = usePolling(
    () => requestsApi.inbox({ status, area_id: areaId ?? undefined, page })
      .catch((err: unknown) => {
        throw listLoadError(err, NOMBRE_LISTA);
      }),
    { intervalSeconds: session?.preferences.refresh_interval, deps: [status, areaId, page] },
  );

  // Áreas del filtro: las administradas; el superadmin, todas (`GET /areas`).
  const todas = useAsync<AreaRef[]>(
    () => (esSuperadmin ? api.areas() : Promise.resolve([])),
    [esSuperadmin],
  );
  const areas: AreaRef[] = esSuperadmin ? (todas.data ?? []) : (session?.managed_areas ?? []);

  const items = useMemo(
    () => (lista.data?.items ?? []).map((item) => decididas[item.id] ?? item),
    [lista.data, decididas],
  );

  function abrir(nueva: Decision, trigger: HTMLButtonElement) {
    disparador.current = trigger;
    setAviso(null);
    setDecision(nueva);
  }

  // Estable: `Modal` reinstala su efecto (y el foco) si cambia `onClose`.
  const cerrar = useCallback(() => {
    setDecision(null);
    disparador.current?.focus();
  }, []);

  const refrescar = lista.refresh;

  function decidida(request: AccessRequest) {
    setDecididas((prev) => ({ ...prev, [request.id]: request }));
    setAviso(avisoDecision(request));
    setDecision(null);
    // Los botones de la fila desaparecen: el foco va al aviso.
    requestAnimationFrame(() => avisoRef.current?.focus());
  }

  /** Al quitar el aviso, el foco va al filtro (no cae en `body`). */
  function cerrarAviso() {
    setAviso(null);
    document.getElementById(FILTRO_ESTADO_ID)?.focus();
  }

  const data = lista.data;

  return (
    <div className="space-y-4">
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

      <div className="grid gap-3 sm:grid-cols-2 lg:w-2/3">
        <Select
          id={FILTRO_ESTADO_ID}
          value={status}
          onChange={(event) => {
            setStatus(event.target.value as RequestStatus);
            setPage(1);
          }}
          aria-label="Filtrar la bandeja por estado"
        >
          {ESTADOS.map((estado) => (
            <option key={estado} value={estado}>
              {ESTADO_PLURAL[estado].charAt(0).toUpperCase() + ESTADO_PLURAL[estado].slice(1)}
            </option>
          ))}
        </Select>
        <Select
          value={areaId ?? ''}
          onChange={(event) => {
            setAreaId(event.target.value ? Number(event.target.value) : null);
            setPage(1);
          }}
          aria-label="Filtrar la bandeja por área"
        >
          <option value="">{esSuperadmin ? 'Todas las áreas' : 'Todas mis áreas'}</option>
          {areas.map((area) => (
            <option key={area.id} value={area.id}>{area.name}</option>
          ))}
        </Select>
      </div>

      {lista.loading && !data ? <Spinner label="Cargando la bandeja…" /> : null}

      {lista.error ? (
        <div className="space-y-3">
          <ErrorNote message={lista.error} />
          <Button variant="secondary" onClick={refrescar}>Reintentar</Button>
        </div>
      ) : null}

      {data ? (
        items.length === 0 ? (
          <EmptyNote message={mensajeVacio(status, areaId !== null)} />
        ) : (
          <>
            <ResponsiveList
              columns={COLUMNAS}
              headers={['Solicitante', 'Plataforma', 'Nivel', 'Estado', 'Acciones']}
              label="Bandeja de aprobaciones"
            >
              {items.map((request) => (
                <Fila
                  key={request.id}
                  request={request}
                  propia={request.requester.id === session?.id}
                  onDecidir={abrir}
                />
              ))}
            </ResponsiveList>
            <ListPager
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              label="Páginas de la bandeja"
              onChange={setPage}
            />
          </>
        )
      ) : null}

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
