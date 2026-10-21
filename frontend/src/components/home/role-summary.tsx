'use client';

/**
 * Resumen de inicio por rol (DIS-024, `GET /home/summary`, contrato `inicio.md`).
 *
 * - Usuario (`propio`): mis solicitudes y mis accesos.
 * - Admin de área (`areas`): pendientes y resumen de sus áreas, más lo propio.
 * - Superadmin (`global`): pendientes y resumen global.
 * - Cada contador es un enlace (`StatTile` dentro de `Link`) a su pantalla.
 * - Refresco con `usePolling` y el intervalo de la preferencia del usuario.
 */

import Link from 'next/link';
import { homeApi } from '@/lib/access/home';
import type { HomeSummary } from '@/lib/access/types';
import { usePolling } from '@/lib/use-polling';
import { RUTA_AUDITORIA } from '../audit/audit-routes';
import { formatearFecha } from '../access/fecha';
import { listLoadError } from '../access/request-errors';
import { Button } from '../form';
import { useSession } from '../session-provider';
import { EmptyNote, ErrorNote, Spinner, StatTile } from '../ui';

/** Pantallas a las que lleva cada contador. */
export const RUTAS_INICIO = {
  solicitudes: '/requests',
  aprobaciones: '/approvals',
  inventario: '/inventory',
  areas: '/areas',
  plataformas: '/admin/platforms',
  catalogo: '/platforms',
} as const;

const NOMBRE_RESUMEN = 'los datos del resumen';
const TITULO_ID = 'resumen-inicio-titulo';

export const TITULOS: Record<HomeSummary['scope'], string> = {
  propio: 'Tu resumen',
  areas: 'Resumen de tus áreas',
  global: 'Resumen global',
};

export const MENSAJES_VACIO: Record<HomeSummary['scope'], string> = {
  propio: 'Todavía no tienes solicitudes ni accesos. Puedes pedir uno desde el catálogo.',
  areas: 'Todavía no hay solicitudes, accesos ni plataformas en tus áreas.',
  global: 'Todavía no hay áreas, plataformas ni solicitudes en el sistema.',
};

export interface Contador {
  etiqueta: string;
  valor: number;
  ruta: string;
  /** Nombre de la pantalla destino, para el nombre accesible del enlace. */
  destino: string;
}

export interface GrupoResumen {
  id: string;
  titulo: string;
  contadores: Contador[];
}

/** Grupos de contadores según los campos que el contrato envía al rol. */
export function gruposDelResumen(resumen: HomeSummary): GrupoResumen[] {
  const grupos: GrupoResumen[] = [];
  if (resumen.pending_approvals !== undefined || resumen.failed_access !== undefined) {
    grupos.push({
      id: 'pendientes',
      titulo: 'Pendientes',
      contadores: [
        { etiqueta: 'Por aprobar', valor: resumen.pending_approvals ?? 0, ruta: RUTAS_INICIO.aprobaciones, destino: 'Aprobaciones' },
        { etiqueta: 'Accesos con falla', valor: resumen.failed_access ?? 0, ruta: RUTAS_INICIO.inventario, destino: 'Inventario' },
      ],
    });
  }
  if (resumen.totals) {
    grupos.push({
      id: 'totales',
      titulo: resumen.scope === 'global' ? 'Todo el sistema' : 'Tus áreas',
      contadores: [
        { etiqueta: 'Áreas', valor: resumen.totals.areas, ruta: RUTAS_INICIO.areas, destino: 'Áreas' },
        { etiqueta: 'Plataformas', valor: resumen.totals.platforms, ruta: RUTAS_INICIO.plataformas, destino: 'Administrar plataformas' },
        { etiqueta: 'Accesos activos', valor: resumen.totals.active_access, ruta: RUTAS_INICIO.inventario, destino: 'Inventario' },
      ],
    });
  }
  if (resumen.my_requests) {
    grupos.push({
      id: 'mis-solicitudes',
      titulo: 'Mis solicitudes',
      contadores: [
        { etiqueta: 'Pendientes', valor: resumen.my_requests.pendiente, ruta: RUTAS_INICIO.solicitudes, destino: 'Mis solicitudes' },
        { etiqueta: 'Aprobadas', valor: resumen.my_requests.aprobada, ruta: RUTAS_INICIO.solicitudes, destino: 'Mis solicitudes' },
        { etiqueta: 'Rechazadas', valor: resumen.my_requests.rechazada, ruta: RUTAS_INICIO.solicitudes, destino: 'Mis solicitudes' },
      ],
    });
  }
  if (resumen.my_access) {
    grupos.push({
      id: 'mis-accesos',
      titulo: 'Mis accesos',
      contadores: [
        { etiqueta: 'Con acceso', valor: resumen.my_access.activo, ruta: RUTAS_INICIO.solicitudes, destino: 'Mis accesos' },
        { etiqueta: 'En proceso', valor: resumen.my_access.en_proceso, ruta: RUTAS_INICIO.solicitudes, destino: 'Mis accesos' },
        { etiqueta: 'Fallidos', valor: resumen.my_access.fallido, ruta: RUTAS_INICIO.solicitudes, destino: 'Mis accesos' },
      ],
    });
  }
  return grupos;
}

/** Sin ningún contador mayor que cero. */
export function resumenVacio(grupos: GrupoResumen[]): boolean {
  return grupos.every((grupo) => grupo.contadores.every((c) => c.valor === 0));
}

function ContadorEnlace({ contador }: { contador: Contador }) {
  return (
    <Link
      href={contador.ruta}
      aria-label={`${contador.etiqueta}: ${contador.valor}. Ir a ${contador.destino}`}
      className="block rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary [&:hover>div]:border-primary"
    >
      <StatTile label={contador.etiqueta} value={contador.valor} />
    </Link>
  );
}

function Grupo({ grupo }: { grupo: GrupoResumen }) {
  const tituloId = `resumen-${grupo.id}`;
  return (
    <section aria-labelledby={tituloId} className="space-y-3">
      <h3 id={tituloId} className="text-sm font-semibold">{grupo.titulo}</h3>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {grupo.contadores.map((contador) => (
          <li key={contador.etiqueta}>
            <ContadorEnlace contador={contador} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function Contenido({ resumen }: { resumen: HomeSummary }) {
  const grupos = gruposDelResumen(resumen);

  if (resumenVacio(grupos)) {
    return (
      <div role="status" className="space-y-3">
        <EmptyNote message={MENSAJES_VACIO[resumen.scope]} />
        {resumen.scope === 'propio' ? (
          <Link href={RUTAS_INICIO.catalogo} className="nexus-btn nexus-btn-primary">
            Ir al catálogo
          </Link>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {resumen.oldest_pending_at ? (
        <p className="text-sm text-label">
          La solicitud pendiente más antigua es del {formatearFecha(resumen.oldest_pending_at)}.
        </p>
      ) : null}
      {grupos.map((grupo) => (
        <Grupo key={grupo.id} grupo={grupo} />
      ))}
    </div>
  );
}

export function RoleSummary() {
  const { session } = useSession();
  const resumen = usePolling(
    () => homeApi.summary().catch((err: unknown) => {
      throw listLoadError(err, NOMBRE_RESUMEN);
    }),
    { intervalSeconds: session?.preferences.refresh_interval },
  );
  const data = resumen.data;

  return (
    <section aria-labelledby={TITULO_ID} className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id={TITULO_ID} className="text-lg font-semibold">
          {data ? TITULOS[data.scope] : 'Resumen'}
        </h2>
        <Link href={RUTA_AUDITORIA} className="nexus-btn nexus-btn-secondary">
          Ver auditoría
        </Link>
      </div>

      {resumen.loading && !data ? <Spinner label="Cargando el resumen…" /> : null}

      {resumen.error ? (
        <div className="space-y-3">
          <ErrorNote message={resumen.error} />
          <Button variant="secondary" onClick={resumen.refresh}>Reintentar</Button>
        </div>
      ) : null}

      {data ? <Contenido resumen={data} /> : null}
    </section>
  );
}
