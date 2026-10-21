/**
 * Filas de la bitácora de ejecuciones (DIS-022): ejecución, usuario y
 * plataforma, estado con intentos, fechas y acciones ("Ver detalle" y, para el
 * superadmin con una ejecución fallida, "Reintentar").
 *
 * Tabla en escritorio y tarjeta en móvil con `ResponsiveList` (DIS-014).
 */

import type { Job } from '@/lib/access/types';
import { formatearFecha } from '../access/fecha';
import { ETIQUETA_CELDA, ResponsiveList, ResponsiveRow } from '../access/responsive-list';
import { Button } from '../form';
import { Badge } from '../ui';
import { ESTADOS_EJECUCION, OPERACIONES, PROVEEDORES, sePuedeReintentar } from './job-catalog';

const COLUMNAS =
  'md:grid-cols-[minmax(0,1.5fr)_minmax(0,2fr)_minmax(0,2fr)_minmax(0,2fr)_minmax(0,1.5fr)]';

export const ENCABEZADOS_EJECUCIONES = ['Ejecución', 'Usuario y plataforma', 'Estado', 'Fechas', 'Acciones'];

export function detalleId(jobId: number): string {
  return `ejecucion-${jobId}-detalle`;
}

export function reintentarId(jobId: number): string {
  return `ejecucion-${jobId}-reintentar`;
}

const FOCO = 'focus-visible:ring-2 focus-visible:ring-primary';

function Fila({
  job,
  esSuperadmin,
  onDetalle,
  onReintentar,
}: {
  job: Job;
  esSuperadmin: boolean;
  onDetalle: (job: Job) => void;
  onReintentar: (job: Job) => void;
}) {
  const estado = ESTADOS_EJECUCION[job.status];
  return (
    <ResponsiveRow columns={COLUMNAS} label={`Ejecución n.º ${job.id}`}>
      <div>
        <dt className={ETIQUETA_CELDA}>Ejecución</dt>
        <dd className="font-semibold text-body-text">n.º {job.id}</dd>
        <dd className="text-sm text-label">{OPERACIONES[job.operation]} · {PROVEEDORES[job.provider]}</dd>
      </div>
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Usuario</dt>
        <dd className="break-words text-sm font-semibold text-body-text">{job.user.name}</dd>
        <dt className="sr-only">Plataforma y área</dt>
        <dd className="break-words text-sm text-label">{job.platform.name} · {job.area.name}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Estado</dt>
        <dd><Badge tone={estado.tono}>{estado.texto}</Badge></dd>
        <dd className="mt-1 text-sm text-label">Intentos: {job.attempts_count} de {job.max_attempts}</dd>
        {job.next_attempt_at ? (
          <dd className="text-sm text-label">Próximo: {formatearFecha(job.next_attempt_at)}</dd>
        ) : null}
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Fechas</dt>
        <dd className="text-sm text-body-text">Creada: {formatearFecha(job.created_at)}</dd>
        <dd className="text-sm text-label">Terminó: {formatearFecha(job.finished_at)}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Acciones</dt>
        <dd className="flex flex-wrap gap-2">
          <Button
            id={detalleId(job.id)}
            variant="secondary"
            aria-label={`Ver el detalle de la ejecución n.º ${job.id}`}
            onClick={() => onDetalle(job)}
            className={FOCO}
          >
            Detalle
          </Button>
          {sePuedeReintentar(job, esSuperadmin) ? (
            <Button
              id={reintentarId(job.id)}
              variant="secondary"
              aria-label={`Reintentar la ejecución n.º ${job.id}`}
              onClick={() => onReintentar(job)}
              className={FOCO}
            >
              Reintentar
            </Button>
          ) : null}
        </dd>
      </div>
    </ResponsiveRow>
  );
}

export function JobsTable({
  items,
  esSuperadmin,
  onDetalle,
  onReintentar,
}: {
  items: Job[];
  esSuperadmin: boolean;
  onDetalle: (job: Job) => void;
  onReintentar: (job: Job) => void;
}) {
  return (
    <ResponsiveList columns={COLUMNAS} headers={ENCABEZADOS_EJECUCIONES} label="Bitácora de ejecuciones">
      {items.map((job) => (
        <Fila key={job.id} job={job} esSuperadmin={esSuperadmin} onDetalle={onDetalle} onReintentar={onReintentar} />
      ))}
    </ResponsiveList>
  );
}
