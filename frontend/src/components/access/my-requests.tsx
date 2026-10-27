'use client';

/**
 * Mis solicitudes (DIS-014, F-SOL-02, `GET /access-requests/mine`): estado,
 * nivel, fechas, motivo de rechazo y estado del acceso tras aprobarse.
 *
 * - Paginada en el servidor; el filtro por estado vuelve a la página 1.
 * - Refresco con `usePolling` y el intervalo de la preferencia del usuario, solo
 *   con una solicitud `pendiente` o un acceso transitorio en la página (DIS-033).
 * - Anuncia a lectores de pantalla solo los cambios de estado entre respuestas (DIS-050).
 * - Tabla en escritorio y lista en móvil con el mismo marcado (`dl` por fila).
 */

import { useState } from 'react';
import { requestsApi } from '@/lib/access/requests';
import type { AccessRequest, RequestStatus } from '@/lib/access/types';
import { useCambiosDeEstado } from '@/lib/use-cambios-de-estado';
import { usePolling } from '@/lib/use-polling';
import { Button, Select } from '../form';
import { RegionDeAnuncios } from '../region-de-anuncios';
import { useSession } from '../session-provider';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import { AccessStatusBadge, ESTADOS as ESTADOS_ACCESO, NIVELES } from './access-status-badge';
import { formatearFecha } from './fecha';
import { ListPager } from './list-pager';
import { listLoadError } from './request-errors';
import { ETIQUETA_CELDA, ResponsiveList, ResponsiveRow } from './responsive-list';
import { ESTADOS_SOLICITUD, RequestStatusBadge, hayTransitoriosEnSolicitudes } from './request-status-badge';

const NOMBRE_LISTA = 'tus solicitudes';

/** Columnas en escritorio: plataforma, nivel, estado, fechas. */
const COLUMNAS = 'md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1.5fr)_minmax(0,2fr)]';

export const ESTADOS = Object.keys(ESTADOS_SOLICITUD) as RequestStatus[];

function Fila({ request }: { request: AccessRequest }) {
  const rechazo = request.status === 'rechazada' ? request.rejection_reason : null;
  return (
    <ResponsiveRow columns={COLUMNAS} label={`Solicitud de ${request.platform.name}`}>
      <div>
        <dt className={ETIQUETA_CELDA}>Plataforma</dt>
        <dd className="font-semibold text-body-text">{request.platform.name}</dd>
        <dd className="text-sm text-label">{request.area.name}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Nivel</dt>
        <dd className="text-sm text-body-text">{NIVELES[request.level]}</dd>
        {request.current_level ? (
          <dd className="text-sm text-label">Al pedirla tenías {NIVELES[request.current_level]}</dd>
        ) : null}
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Estado</dt>
        <dd className="flex flex-wrap gap-2">
          <RequestStatusBadge status={request.status} />
          {request.access ? <AccessStatusBadge status={request.access.status} /> : null}
        </dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Fechas</dt>
        <dd className="text-sm text-body-text">Enviada: {formatearFecha(request.created_at)}</dd>
        {request.decided_at ? (
          <dd className="text-sm text-label">
            Decidida: {formatearFecha(request.decided_at)}
            {request.decided_by ? ` por ${request.decided_by.name}` : ''}
          </dd>
        ) : null}
      </div>
      {rechazo ? (
        <div className="md:col-span-4">
          <dt className="text-xs font-medium uppercase tracking-wide text-error-text">
            Motivo del rechazo
          </dt>
          <dd className="text-sm text-body-text">{rechazo}</dd>
        </div>
      ) : null}
      {request.justification ? (
        <div className="md:col-span-4">
          <dt className="text-xs font-medium uppercase tracking-wide text-label">
            Tu justificación
          </dt>
          <dd className="text-sm text-label">{request.justification}</dd>
        </div>
      ) : null}
    </ResponsiveRow>
  );
}

/** `estadoInicial`: filtro que llegó por la URL (DIS-036). */
export function MyRequests({ estadoInicial }: { estadoInicial?: RequestStatus }) {
  const { session } = useSession();
  const [status, setStatus] = useState<RequestStatus | ''>(estadoInicial ?? '');
  const [page, setPage] = useState(1);

  const [transitorios, setTransitorios] = useState(true);

  const lista = usePolling(
    () => requestsApi.mine({ status: status || undefined, page })
      .then((r) => {
        setTransitorios(hayTransitoriosEnSolicitudes(r.items));
        return r;
      })
      .catch((err: unknown) => {
        throw listLoadError(err, NOMBRE_LISTA);
      }),
    { intervalSeconds: session?.preferences.refresh_interval, deps: [status, page], activo: transitorios },
  );

  const data = lista.data;

  const anuncio = useCambiosDeEstado(data?.items, `${status}:${page}`, (r) => [
    { clave: r.status, texto: `Solicitud de ${r.platform.name}: ${ESTADOS_SOLICITUD[r.status].texto}` },
    {
      clave: r.access?.status ?? '',
      texto: `Acceso a ${r.platform.name}: ${r.access ? ESTADOS_ACCESO[r.access.status].texto : ''}`,
    },
  ]);

  return (
    <div className="space-y-4">
      <RegionDeAnuncios mensaje={anuncio} />
      <Select
        value={status}
        onChange={(event) => {
          setStatus(event.target.value as RequestStatus | '');
          setPage(1);
        }}
        aria-label="Filtrar mis solicitudes por estado"
        className="sm:w-64"
      >
        <option value="">Todas las solicitudes</option>
        {ESTADOS.map((estado) => (
          <option key={estado} value={estado}>{ESTADOS_SOLICITUD[estado].texto}</option>
        ))}
      </Select>

      {lista.loading && !data ? <Spinner label="Cargando tus solicitudes…" /> : null}

      {lista.error ? (
        <div className="space-y-3">
          <ErrorNote message={lista.error} />
          <Button variant="secondary" onClick={lista.refresh}>Reintentar</Button>
        </div>
      ) : null}

      {data ? (
        data.items.length === 0 ? (
          <EmptyNote
            message={status
              ? 'No tienes solicitudes con ese estado.'
              : 'Aún no has solicitado accesos. Pídelos desde el catálogo.'}
          />
        ) : (
          <>
            <ResponsiveList
              columns={COLUMNAS}
              headers={['Plataforma', 'Nivel', 'Estado', 'Fechas']}
              label="Mis solicitudes"
            >
              {data.items.map((request) => <Fila key={request.id} request={request} />)}
            </ResponsiveList>
            <ListPager
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              label="Páginas de mis solicitudes"
              onChange={setPage}
            />
          </>
        )
      ) : null}
    </div>
  );
}
