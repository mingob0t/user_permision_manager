/**
 * Nombres y tonos de las ejecuciones de aprovisionamiento (DIS-022,
 * `GET /provisioning/jobs`, contrato `conectores-y-ejecuciones.md` 1.1).
 * El estado siempre lleva texto; nunca solo color.
 */

import type { Job, JobAttempt, JobOperation, JobStatus } from '@/lib/access/types';
import type { Badge } from '../ui';

type Tono = React.ComponentProps<typeof Badge>['tone'];

export const ESTADOS_EJECUCION: Record<JobStatus, { texto: string; tono: Tono }> = {
  pendiente: { texto: 'Pendiente', tono: 'primary' },
  en_ejecucion: { texto: 'En ejecución', tono: 'sky' },
  reintentando: { texto: 'Reintentando', tono: 'warning' },
  exitoso: { texto: 'Exitosa', tono: 'success' },
  fallido: { texto: 'Fallida', tono: 'error' },
  cancelado: { texto: 'Cancelada', tono: 'slate' },
};

export const OPERACIONES: Record<JobOperation, string> = {
  otorgar: 'Otorgar',
  revocar: 'Revocar',
};

export const PROVEEDORES: Record<Job['provider'], string> = {
  ldap: 'Directorio',
  conector: 'Conector',
};

export const RESULTADOS_INTENTO: Record<JobAttempt['result'], { texto: string; tono: Tono }> = {
  exitoso: { texto: 'Exitoso', tono: 'success' },
  sin_cambios: { texto: 'Sin cambios', tono: 'slate' },
  error_transitorio: { texto: 'Error transitorio', tono: 'warning' },
  error_permanente: { texto: 'Error permanente', tono: 'error' },
};

/** Estados que todavía cambian: con ellos se refresca (contrato, "Refresco"). */
export const ESTADOS_TRANSITORIOS: readonly JobStatus[] = ['pendiente', 'en_ejecucion', 'reintentando'];

export function esTransitorio(status: JobStatus): boolean {
  return ESTADOS_TRANSITORIOS.includes(status);
}

export function hayTransitorios(jobs: Job[]): boolean {
  return jobs.some((job) => esTransitorio(job.status));
}

/** Solo una ejecución `fallida` se reintenta, y solo el superadmin (P10). */
export function sePuedeReintentar(job: Job, esSuperadmin: boolean): boolean {
  return esSuperadmin && job.status === 'fallido';
}
