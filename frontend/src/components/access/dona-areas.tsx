'use client';

/**
 * KPI «Solicitudes pendientes por área» (DIS-144, DIS-145): dona con las áreas que más solicitudes
 * pendientes tienen (`inbox/stats.pending_by_area`, ya ordenado; v1.4) y el resto agrupado en
 * «Otras». Los colores son los tokens de los indicadores existentes, uno por serie.
 */

import type { InboxStats } from '@/lib/access/types';
import { DonaKpi, type FilaDona } from '../dashboard/dona-kpi';

/** Una serie por posición; la última se reserva a «Otras» si hay más áreas. */
const PALETA_AREAS: Record<string, string> = {
  serie1: '--color-indicador-areas',
  serie2: '--color-indicador-plataformas',
  serie3: '--color-indicador-visitas',
  serie4: '--color-indicador-usuarios',
  serie5: '--color-indicador-solicitudes',
};
/** Clases literales (el CSS sin uso las busca por nombre completo). */
export const SERIES_AREAS: { color: string; punto: string }[] = [
  { color: 'serie1', punto: 'nx-dona__punto--serie-1' },
  { color: 'serie2', punto: 'nx-dona__punto--serie-2' },
  { color: 'serie3', punto: 'nx-dona__punto--serie-3' },
  { color: 'serie4', punto: 'nx-dona__punto--serie-4' },
  { color: 'serie5', punto: 'nx-dona__punto--serie-5' },
];
export const NOMBRE_OTRAS = 'Otras';

/** Filas de la dona: hasta 5 áreas; con más, 4 áreas y «Otras» con la suma del resto. */
export function filasPorArea(stats: InboxStats): FilaDona[] {
  const areas = stats.pending_by_area ?? [];
  const caben = areas.length > SERIES_AREAS.length ? SERIES_AREAS.length - 1 : areas.length;
  const filas: FilaDona[] = areas.slice(0, caben).map((fila, i) => (
    { clave: `area-${fila.area_id}`, nombre: fila.area, cantidad: fila.count, ...SERIES_AREAS[i] }));
  if (areas.length > caben) {
    const resto = areas.slice(caben).reduce((suma, fila) => suma + fila.count, 0);
    filas.push({ clave: 'otras', nombre: NOMBRE_OTRAS, cantidad: resto, ...SERIES_AREAS[caben] });
  }
  return filas;
}

export function DonaAreas({ stats }: { stats: InboxStats }) {
  return (
    <DonaKpi
      titulo="Solicitudes pendientes por área"
      icono="areas"
      paleta={PALETA_AREAS}
      filas={filasPorArea(stats)}
      vacioTitulo="Sin solicitudes pendientes"
      vacioMensaje="No hay solicitudes pendientes en las áreas de tu alcance."
    />
  );
}
