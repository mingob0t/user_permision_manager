'use client';

/**
 * KPI «Por estado» (DIS-131, DIS-141; título corto en DIS-151): dona de pendientes, aprobadas y rechazadas
 * con los colores semánticos de aviso, éxito y peligro (tokens). Usa `DonaKpi` (DIS-144).
 */

import type { InboxStats, RequestStatus } from '@/lib/access/types';
import { DonaKpi } from '../dashboard/dona-kpi';

const PALETA_ESTADOS: Record<RequestStatus, string> = {
  pendiente: '--color-indicador-pendientes',
  aprobada: '--color-indicador-aprobadas',
  rechazada: '--color-indicador-rechazadas',
};

/** Clases literales (el CSS sin uso las busca por nombre completo). */
export const ESTADOS_DONA: { estado: RequestStatus; nombre: string; punto: string }[] = [
  { estado: 'pendiente', nombre: 'Pendientes', punto: 'nx-dona__punto--pendiente' },
  { estado: 'aprobada', nombre: 'Aprobadas', punto: 'nx-dona__punto--aprobada' },
  { estado: 'rechazada', nombre: 'Rechazadas', punto: 'nx-dona__punto--rechazada' },
];

export function DonaEstados({ stats }: { stats: InboxStats }) {
  return (
    <DonaKpi
      titulo="Por estado"
      etiqueta="Solicitudes por estado"
      icono="solicitudes"
      paleta={PALETA_ESTADOS}
      filas={ESTADOS_DONA.map(({ estado, nombre, punto }) => (
        { clave: estado, nombre, cantidad: stats.by_status[estado] ?? 0, color: estado, punto }))}
      vacioTitulo="Sin solicitudes"
      vacioMensaje="Cuando lleguen solicitudes a tus áreas, verás aquí el reparto por estado."
    />
  );
}
