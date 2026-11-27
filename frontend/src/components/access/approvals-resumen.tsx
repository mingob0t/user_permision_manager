'use client';

/**
 * Resumen de Solicitudes (DIS-131, rehecho en DIS-141 y DIS-144; tabla a la izquierda y barras horizontales a la derecha en DIS-147): fila de KPI (cuatro `DonaKpi`:
 * estado, área pendiente, conectores y usuarios por rol; DIS-146), panel de pendientes por aprobar (3/5,
 * `SolicitudesPanel`) y gráficas de barras horizontales por área y por plataforma (2/5). Datos de
 * `GET /access-requests/inbox/stats` y `GET /stats` con `usePolling` y el intervalo de
 * preferencia. El historial con filtros es `ApprovalsInbox` (otra sección de la URL).
 */

import type { InboxStats } from '@/lib/access/types';
import { requestsApi } from '@/lib/access/requests';
import { usePolling } from '@/lib/use-polling';
import { GraficaBarras } from '../dashboard/grafica-barras';
import { api } from '@/lib/api';
import type { Stats } from '@/lib/types';
import { Button } from '../form';
import { useSession } from '../session-provider';
import { CLASES_ESQUELETO, ErrorNote } from '../ui';
import { DonaAreas } from './dona-areas';
import { DonaConectores } from './dona-conectores';
import { DonaEstados } from './dona-estados';
import { DonaUsuarios } from './dona-usuarios';
import { SolicitudesPanel } from './solicitudes-panel';
import { listLoadError } from './request-errors';

const NOMBRE_RESUMEN = 'el resumen de solicitudes';
/** Máximo de barras por gráfica (el backend no limita; la web recorta). */
export const MAX_BARRAS = 10;
export const RUTA_SOLICITUDES = '/approvals';

/**
 * DIS-141: fila de KPI = dona por estado, conectores (solo superadmin: `connectors` de
 * `GET /stats`) y usuarios por rol (`desglose.users_by_role`). Sin `panel` (o si su consulta
 * falla) solo queda la dona.
 */
function Contenido({ stats, panel }: { stats: InboxStats; panel: Stats | null }) {
  const porArea = stats.by_area.slice(0, MAX_BARRAS).map((fila) => (
    { id: fila.area_id, etiqueta: fila.area, cantidad: fila.count }));
  const porPlataforma = stats.by_platform.slice(0, MAX_BARRAS).map((fila) => (
    { id: fila.platform_id, etiqueta: fila.platform, cantidad: fila.count }));

  return (
    <section aria-label="Resumen de solicitudes" className="flex flex-1 min-h-0 flex-col gap-4">
      <h2 className="sr-only">Resumen de solicitudes</h2>
      <div className="grid w-full grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <DonaEstados stats={stats} />
        <DonaAreas stats={stats} />
        {/* DIS-150: Usuarios antes que Conectores (pedido del dueño). */}
        {panel?.users !== undefined ? (
          <DonaUsuarios valor={panel.users} desglose={panel.desglose?.users_by_role} />
        ) : null}
        {panel?.connectors !== undefined ? (
          <DonaConectores valor={panel.connectors} desglose={panel.desglose?.connectors} />
        ) : null}
      </div>

      <div className="grid w-full flex-1 min-h-0 grid-cols-1 gap-4 lg:grid-cols-5">
        {/* DIS-141: en lugar de la dona por estado, las pendientes con aprobar/rechazar. */}
        <div className="flex min-h-0 lg:col-span-3">
          <SolicitudesPanel />
        </div>
        <div className="flex min-h-0 flex-col gap-4 lg:col-span-2">
          <GraficaBarras
            titulo="Áreas"
            etiqueta="Solicitudes por área"
            subtitulo={`Las ${MAX_BARRAS} con más solicitudes`}
            icono="areas"
            serie="Solicitudes"
            columna="Área"
            filas={porArea}
            vacioTitulo="Sin solicitudes por área"
            vacioMensaje="Aún no hay solicitudes en las áreas de tu alcance."
          />
          <GraficaBarras
            titulo="Plataformas"
            etiqueta="Solicitudes por plataforma"
            subtitulo={`Las ${MAX_BARRAS} con más solicitudes`}
            icono="plataformas"
            serie="Solicitudes"
            columna="Plataforma"
            filas={porPlataforma}
            vacioTitulo="Sin solicitudes por plataforma"
            vacioMensaje="Aún no hay solicitudes para las plataformas de tu alcance."
            alterna
          />
        </div>
      </div>
    </section>
  );
}

const CAJA_ESQUELETO = `${CLASES_ESQUELETO} rounded-xl border border-panel-border`;
export const MENSAJE_CARGA_RESUMEN = 'Cargando el resumen de solicitudes…';

/**
 * DIS-155: esqueleto con la misma rejilla que `Contenido` (4 KPI; tabla 3/5 y dos gráficas 2/5)
 * para que la pantalla no salte al llegar los datos. Un solo `status` para el lector de pantalla.
 */
function EsqueletoResumen() {
  return (
    <div role="status" aria-label={MENSAJE_CARGA_RESUMEN} className="flex flex-1 min-h-0 flex-col gap-4">
      <span className="sr-only">{MENSAJE_CARGA_RESUMEN}</span>
      <div className="grid w-full grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4" aria-hidden="true">
        {Array.from({ length: 4 }, (_, i) => <div key={i} data-esqueleto="kpi" className={`${CAJA_ESQUELETO} min-h-52`} />)}
      </div>
      <div className="grid w-full flex-1 min-h-0 grid-cols-1 gap-4 lg:grid-cols-5" aria-hidden="true">
        <div data-esqueleto="tabla" className={`${CAJA_ESQUELETO} min-h-96 lg:col-span-3`} />
        <div className="flex min-h-0 flex-col gap-4 lg:col-span-2">
          <div data-esqueleto="grafica" className={`${CAJA_ESQUELETO} min-h-64 flex-1`} />
          <div data-esqueleto="grafica" className={`${CAJA_ESQUELETO} min-h-64 flex-1`} />
        </div>
      </div>
    </div>
  );
}

export function ApprovalsResumen() {
  const { session } = useSession();
  const resumen = usePolling(
    () => requestsApi.inboxStats().catch((err: unknown) => {
      throw listLoadError(err, NOMBRE_RESUMEN);
    }),
    { intervalSeconds: session?.preferences.refresh_interval },
  );
  // DIS-141: conectores y usuarios salen de `GET /stats` (FNC-214); si falla, solo no se muestran.
  const panel = usePolling(() => api.stats(), { intervalSeconds: session?.preferences.refresh_interval });

  if (resumen.data) return <Contenido stats={resumen.data} panel={panel.data ?? null} />;
  if (resumen.error) {
    return (
      <div className="space-y-3">
        <ErrorNote message={resumen.error} />
        <Button variant="secondary" onClick={resumen.refresh}>Reintentar</Button>
      </div>
    );
  }
  return <EsqueletoResumen />;
}
