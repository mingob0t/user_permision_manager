'use client';

/**
 * Accesos de un usuario y revocación (DIS-018, F-ACC-02, RF-03;
 * `GET /users/<id>/access` y `POST /access/<id>/revoke`, contrato `accesos.md` 1.1).
 *
 * - Se abre desde la fila de Usuarios (`users-list.tsx`) como sección, no como
 *   `Modal`: así el diálogo de revocar no queda dentro de otro diálogo.
 * - Plataforma, nivel, origen, desde, quién aprobó, estado explicado y última
 *   ejecución. Por defecto `vigente`; el filtro vuelve a la página 1.
 * - El backend ya limita la lista a las áreas del admin. Revocar solo se ofrece
 *   cuando el contrato lo permite (activo, no propio y, para el admin de área,
 *   ni automático ni de otro admin del área); si no, se explica por qué.
 * - Tras revocar: la fila se actualiza con la respuesta y el aviso (`status`)
 *   recibe el foco, como en la bandeja (DIS-015).
 * - Refresco con `usePolling` y el intervalo de la preferencia del usuario.
 */

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { grantsApi } from '@/lib/access/grants';
import type { Access, AccessListParams, AccessOrigin, AccessStatus } from '@/lib/access/types';
import type { ManagedUser } from '@/lib/types';
import { usePolling } from '@/lib/use-polling';
import { Button, Select } from '../form';
import { useSession } from '../session-provider';
import { Card, EmptyNote, ErrorNote, Spinner } from '../ui';
import { AccessStatusBadge, NIVELES } from '../access/access-status-badge';
import { formatearFecha } from '../access/fecha';
import { ListPager } from '../access/list-pager';
import { FILTROS } from '../access/my-access';
import { listLoadError } from '../access/request-errors';
import { ETIQUETA_CELDA, ResponsiveList, ResponsiveRow } from '../access/responsive-list';
import { rutaHistorialUsuario } from '../audit/audit-routes';
import { RevokeAccessDialog } from './revoke-access-dialog';

type Filtro = NonNullable<AccessListParams['status']>;

const FILTRO_POR_DEFECTO: Filtro = 'vigente';

/** Columnas en escritorio: plataforma, nivel, otorgado, estado, acciones. */
const COLUMNAS =
  'md:grid-cols-[minmax(0,2fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_minmax(0,2.5fr)_minmax(0,1.5fr)]';

/** Qué significa cada estado, desde la vista del administrador. */
export const ESTADO_PARA_ADMIN: Record<AccessStatus, string> = {
  en_proceso: 'Se está aplicando en la plataforma.',
  activo: 'Confirmado en la plataforma.',
  fallido: 'No se pudo aplicar en la plataforma tras los reintentos.',
  revocando: 'Se está retirando de la plataforma.',
  revocado: 'Retirado de la plataforma.',
  fallo_revocacion: 'No se pudo retirar de la plataforma tras los reintentos.',
};

const ORIGENES: Record<AccessOrigin, string> = {
  solicitud: 'Por solicitud',
  admin_de_area: 'Automático: administra el área',
};

export const SIN_ACCION = {
  noActivo: 'Sin acciones',
  propio: 'Es tu acceso: lo revoca otro administrador.',
  automatico: 'Automático del área: solo lo revoca el superadmin.',
  adminDelArea: 'Administra esta área: solo lo revoca el superadmin.',
} as const;

/**
 * Por qué no se ofrece revocar (`null` = se puede). Refleja el contrato:
 * solo `activo` (409), nunca el propio (403) y, para el admin de área, ni el
 * automático ni el de otro admin del área (404; el superadmin sí).
 */
export function motivoSinRevocar(
  access: Access,
  user: ManagedUser,
  sesion: { id: number | undefined; esSuperadmin: boolean },
): string | null {
  if (access.status !== 'activo') return SIN_ACCION.noActivo;
  if (access.user.id === sesion.id) return SIN_ACCION.propio;
  if (sesion.esSuperadmin) return null;
  if (access.origin === 'admin_de_area') return SIN_ACCION.automatico;
  if (user.managed_areas.some((area) => area.id === access.area.id)) return SIN_ACCION.adminDelArea;
  return null;
}

/** Aviso tras revocar. */
export function avisoRevocacion(access: Access): string {
  return `Revocación en curso: ${access.user.name} en ${access.platform.name}. El acceso se retirará de la plataforma.`;
}

/** Estado vacío según el filtro. */
export function mensajeVacioAccesos(status: Filtro): string {
  return status === FILTRO_POR_DEFECTO
    ? 'No tiene accesos vigentes dentro de tu alcance.'
    : 'No tiene accesos con ese estado dentro de tu alcance.';
}

function Fila({
  access,
  sinRevocar,
  onRevocar,
}: {
  access: Access;
  sinRevocar: string | null;
  onRevocar: (access: Access, trigger: HTMLButtonElement) => void;
}) {
  return (
    <ResponsiveRow columns={COLUMNAS} label={`Acceso a ${access.platform.name}`}>
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Plataforma</dt>
        <dd className="break-words font-semibold text-body-text">{access.platform.name}</dd>
        <dd className="text-sm text-label">{access.area.name}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Nivel</dt>
        <dd className="text-sm text-body-text">{NIVELES[access.level]}</dd>
        <dd className="text-sm text-label">{ORIGENES[access.origin]}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Otorgado</dt>
        <dd className="text-sm text-body-text">{formatearFecha(access.granted_at)}</dd>
        <dd className="text-sm text-label">
          {access.granted_by ? `Aprobó ${access.granted_by.name}` : 'Por el sistema'}
        </dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Estado</dt>
        <dd><AccessStatusBadge status={access.status} /></dd>
        <dd className="mt-1 text-sm text-label">{ESTADO_PARA_ADMIN[access.status]}</dd>
        {access.last_job_id ? (
          <dd className="text-sm text-label">Última ejecución: n.º {access.last_job_id}</dd>
        ) : null}
        {access.revoked_at ? (
          <dd className="text-sm text-label">
            Retirado: {formatearFecha(access.revoked_at)}
            {access.revoked_by ? ` por ${access.revoked_by.name}` : ''}
          </dd>
        ) : null}
        {access.revoke_reason ? (
          // Texto de otro usuario: React lo escapa; nunca HTML.
          <dd className="mt-1 break-words text-sm text-body-text">Motivo: {access.revoke_reason}</dd>
        ) : null}
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Acciones</dt>
        {sinRevocar ? (
          <dd className="text-sm text-label">{sinRevocar}</dd>
        ) : (
          <dd>
            <Button
              variant="secondary"
              aria-label={`Revocar el acceso de ${access.user.name} a ${access.platform.name}`}
              onClick={(event) => onRevocar(access, event.currentTarget)}
            >
              Revocar
            </Button>
          </dd>
        )}
      </div>
    </ResponsiveRow>
  );
}

/** Lista con filtro, paginación y revocación (no se monta para el superadmin). */
function AccessList({ user }: { user: ManagedUser }) {
  const { session } = useSession();
  const esSuperadmin = session?.permissions.is_admin ?? false;
  const filtroId = `accesos-usuario-${user.id}-filtro`;
  const nombreLista = `los accesos de ${user.name}`;

  const [status, setStatus] = useState<Filtro>(FILTRO_POR_DEFECTO);
  const [page, setPage] = useState(1);
  /** Accesos revocados aquí, con la respuesta del servidor (por `id`). */
  const [revocados, setRevocados] = useState<Record<number, Access>>({});
  const [revocando, setRevocando] = useState<Access | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const disparador = useRef<HTMLElement | null>(null);
  const avisoRef = useRef<HTMLDivElement>(null);

  const lista = usePolling(
    () => grantsApi.ofUser(user.id, { status, page }).catch((err: unknown) => {
      throw listLoadError(err, nombreLista);
    }),
    { intervalSeconds: session?.preferences.refresh_interval, deps: [user.id, status, page] },
  );

  const items = useMemo(
    () => (lista.data?.items ?? []).map((item) => revocados[item.id] ?? item),
    [lista.data, revocados],
  );

  function abrir(access: Access, trigger: HTMLButtonElement) {
    disparador.current = trigger;
    setAviso(null);
    setRevocando(access);
  }

  // Estable: `Modal` reinstala su efecto (y el foco) si cambia `onClose`.
  const cerrar = useCallback(() => {
    setRevocando(null);
    // Si la fila cambió (refresco), el botón ya no existe: el foco va al filtro.
    const boton = disparador.current;
    if (boton?.isConnected) boton.focus();
    else document.getElementById(filtroId)?.focus();
  }, [filtroId]);

  function revocado(access: Access) {
    setRevocados((prev) => ({ ...prev, [access.id]: access }));
    setAviso(avisoRevocacion(access));
    setRevocando(null);
    // El botón de la fila desaparece: el foco va al aviso.
    requestAnimationFrame(() => avisoRef.current?.focus());
  }

  /** Al quitar el aviso, el foco va al filtro (no cae en `body`). */
  function cerrarAviso() {
    setAviso(null);
    document.getElementById(filtroId)?.focus();
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

      <Select
        id={filtroId}
        value={status}
        onChange={(event) => {
          setStatus(event.target.value as Filtro);
          setPage(1);
        }}
        aria-label={`Filtrar los accesos de ${user.name} por estado`}
        className="sm:w-64"
      >
        {FILTROS.map((filtro) => (
          <option key={filtro.valor} value={filtro.valor}>{filtro.texto}</option>
        ))}
      </Select>

      {lista.loading && !data ? <Spinner label="Cargando los accesos…" /> : null}

      {lista.error ? (
        <div className="space-y-3">
          <ErrorNote message={lista.error} />
          <Button variant="secondary" onClick={lista.refresh}>Reintentar</Button>
        </div>
      ) : null}

      {data ? (
        items.length === 0 ? (
          <EmptyNote message={mensajeVacioAccesos(status)} />
        ) : (
          <>
            <ResponsiveList
              columns={COLUMNAS}
              headers={['Plataforma', 'Nivel', 'Otorgado', 'Estado', 'Acciones']}
              label={`Accesos de ${user.name}`}
            >
              {items.map((access) => (
                <Fila
                  key={access.id}
                  access={access}
                  sinRevocar={motivoSinRevocar(access, user, { id: session?.id, esSuperadmin })}
                  onRevocar={abrir}
                />
              ))}
            </ResponsiveList>
            <ListPager
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              label={`Páginas de los accesos de ${user.name}`}
              onChange={setPage}
            />
          </>
        )
      ) : null}

      {revocando ? (
        <RevokeAccessDialog
          access={revocando}
          onClose={cerrar}
          onRevoked={revocado}
          onStale={lista.refresh}
        />
      ) : null}
    </div>
  );
}

export const MENSAJE_SUPERADMIN =
  'Es superadmin: tiene acceso a todas las plataformas desde el portal y no tiene accesos registrados.';

export function UserAccessPanel({ user, onClose }: { user: ManagedUser; onClose: () => void }) {
  const titleId = `accesos-usuario-${user.id}-titulo`;
  const titulo = useRef<HTMLHeadingElement>(null);

  // Al abrir, el foco va al título del panel (y la página se desplaza a él).
  useEffect(() => {
    titulo.current?.focus();
  }, [user.id]);

  return (
    <section aria-labelledby={titleId} className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2
            id={titleId}
            ref={titulo}
            tabIndex={-1}
            className="rounded text-lg font-semibold outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Accesos de {user.name}
          </h2>
          <p className="break-words text-sm text-label">{user.email}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          {/* DIS-020: historial del usuario en Auditoría. */}
          <Link
            href={rutaHistorialUsuario(user.id)}
            className="nexus-btn nexus-btn-secondary"
            aria-label={`Historial de ${user.name} en Auditoría`}
          >
            Historial
          </Link>
          <Button variant="secondary" onClick={onClose}>Cerrar accesos</Button>
        </div>
      </div>

      {user.role === 'administrador' ? (
        <EmptyNote message={MENSAJE_SUPERADMIN} />
      ) : (
        <AccessList user={user} />
      )}
    </section>
  );
}
