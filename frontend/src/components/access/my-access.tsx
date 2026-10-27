'use client';

/**
 * Mis accesos (DIS-014, F-ACC-02, `GET /me/access`): plataforma, nivel,
 * desde cuándo, origen y estado del aprovisionamiento explicado en lenguaje
 * claro.
 *
 * - Por defecto `vigente` (contrato `accesos.md`); el filtro vuelve a la página 1.
 * - Refresco con `usePolling` y el intervalo de la preferencia del usuario, solo
 *   con accesos `en_proceso` o `revocando` en la página (DIS-033).
 * - Tabla en escritorio y lista en móvil con el mismo marcado (`dl` por fila).
 */

import { useState } from 'react';
import { grantsApi } from '@/lib/access/grants';
import type { Access, AccessListParams, AccessOrigin, AccessStatus } from '@/lib/access/types';
import { usePolling } from '@/lib/use-polling';
import { Button, Select } from '../form';
import { useSession } from '../session-provider';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import { AccessStatusBadge, NIVELES, hayAccesosTransitorios } from './access-status-badge';
import { formatearFecha } from './fecha';
import { ListPager } from './list-pager';
import { listLoadError } from './request-errors';
import { ETIQUETA_CELDA, ResponsiveList, ResponsiveRow } from './responsive-list';

type Filtro = NonNullable<AccessListParams['status']>;

const NOMBRE_LISTA = 'tus accesos';
const FILTRO_POR_DEFECTO: Filtro = 'vigente';

export const FILTROS: { valor: Filtro; texto: string }[] = [
  { valor: 'vigente', texto: 'Vigentes' },
  { valor: 'activo', texto: 'Con acceso' },
  { valor: 'en_proceso', texto: 'En proceso' },
  { valor: 'fallido', texto: 'Fallidos' },
  { valor: 'revocando', texto: 'Revocándose' },
  { valor: 'revocado', texto: 'Revocados' },
  { valor: 'fallo_revocacion', texto: 'Con fallo al revocar' },
];

/** Qué significa cada estado para quien tiene el acceso. */
export const EXPLICACION_ESTADO: Record<AccessStatus, string> = {
  en_proceso: 'Se está aplicando en la plataforma. Puede tardar unos minutos.',
  activo: 'Ya puedes entrar a la plataforma con este nivel.',
  fallido: 'No se pudo aplicar en la plataforma. El administrador del área puede reintentarlo.',
  revocando: 'Se está retirando de la plataforma.',
  revocado: 'Ya no tienes este acceso.',
  fallo_revocacion: 'No se pudo retirar de la plataforma. El administrador del área lo revisará.',
};

const ORIGENES: Record<AccessOrigin, string> = {
  solicitud: 'Por solicitud',
  admin_de_area: 'Automático: administras el área',
};

/** Columnas en escritorio: plataforma, nivel, desde, estado. */
const COLUMNAS = 'md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1.5fr)_minmax(0,2.5fr)]';

function Fila({ access }: { access: Access }) {
  return (
    <ResponsiveRow columns={COLUMNAS} label={`Acceso a ${access.platform.name}`}>
      <div>
        <dt className={ETIQUETA_CELDA}>Plataforma</dt>
        <dd className="font-semibold text-body-text">{access.platform.name}</dd>
        <dd className="text-sm text-label">{access.area.name}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Nivel</dt>
        <dd className="text-sm text-body-text">{NIVELES[access.level]}</dd>
        <dd className="text-sm text-label">{ORIGENES[access.origin]}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Desde</dt>
        <dd className="text-sm text-body-text">{formatearFecha(access.granted_at)}</dd>
        {access.revoked_at ? (
          <dd className="text-sm text-label">Retirado: {formatearFecha(access.revoked_at)}</dd>
        ) : null}
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Estado</dt>
        <dd><AccessStatusBadge status={access.status} /></dd>
        <dd className="mt-1 text-sm text-label">{EXPLICACION_ESTADO[access.status]}</dd>
        {access.revoke_reason ? (
          <dd className="mt-1 text-sm text-body-text">Motivo: {access.revoke_reason}</dd>
        ) : null}
      </div>
    </ResponsiveRow>
  );
}

export function MyAccess() {
  const { session } = useSession();
  const [status, setStatus] = useState<Filtro>(FILTRO_POR_DEFECTO);
  const [page, setPage] = useState(1);

  const [transitorios, setTransitorios] = useState(true);

  const lista = usePolling(
    () => grantsApi.mine({ status, page })
      .then((r) => {
        setTransitorios(hayAccesosTransitorios(r.items));
        return r;
      })
      .catch((err: unknown) => {
        throw listLoadError(err, NOMBRE_LISTA);
      }),
    { intervalSeconds: session?.preferences.refresh_interval, deps: [status, page], activo: transitorios },
  );

  const data = lista.data;

  return (
    <div className="space-y-4">
      <Select
        value={status}
        onChange={(event) => {
          setStatus(event.target.value as Filtro);
          setPage(1);
        }}
        aria-label="Filtrar mis accesos por estado"
        className="sm:w-64"
      >
        {FILTROS.map((filtro) => (
          <option key={filtro.valor} value={filtro.valor}>{filtro.texto}</option>
        ))}
      </Select>

      {lista.loading && !data ? <Spinner label="Cargando tus accesos…" /> : null}

      {lista.error ? (
        <div className="space-y-3">
          <ErrorNote message={lista.error} />
          <Button variant="secondary" onClick={lista.refresh}>Reintentar</Button>
        </div>
      ) : null}

      {data ? (
        data.items.length === 0 ? (
          <EmptyNote
            message={status === FILTRO_POR_DEFECTO
              ? 'Aún no tienes accesos. Solicítalos desde el catálogo.'
              : 'No tienes accesos con ese estado.'}
          />
        ) : (
          <>
            <ResponsiveList
              columns={COLUMNAS}
              headers={['Plataforma', 'Nivel', 'Desde', 'Estado']}
              label="Mis accesos"
            >
              {data.items.map((access) => <Fila key={access.id} access={access} />)}
            </ResponsiveList>
            <ListPager
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              label="Páginas de mis accesos"
              onChange={setPage}
            />
          </>
        )
      ) : null}
    </div>
  );
}
