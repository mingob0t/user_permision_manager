'use client';

/**
 * Detalle de una ejecución con sus intentos (DIS-022, `GET /provisioning/jobs/<id>`,
 * contrato 1.1). Se refresca con `usePolling` solo mientras la ejecución está
 * en un estado transitorio (contrato, "Refresco").
 *
 * - `attempts[].error` llega saneado y truncado por el servidor (SEC-CON-10);
 *   se pinta como texto (React lo escapa), nunca como HTML.
 * - Sin acciones dentro: el reintento se confirma desde la fila para no anidar
 *   diálogos. Cerrar devuelve el foco al botón que lo abrió (`JobsLog`).
 */

import { useEffect, useState } from 'react';
import { provisioningApi } from '@/lib/access/provisioning';
import type { Job } from '@/lib/access/types';
import { usePolling } from '@/lib/use-polling';
import { formatearFecha } from '../access/fecha';
import { DataList, DataListItem, Dato } from '../data-table';
import { Modal } from '../form';
import { useSession } from '../session-provider';
import { Badge, EmptyNote, ErrorNote, Spinner } from '../ui';
import { ESTADOS_EJECUCION, OPERACIONES, PROVEEDORES, RESULTADOS_INTENTO, esTransitorio } from './job-catalog';
import { jobLoadError } from './job-errors';

export function JobDetailModal({ job, onClose }: { job: Job; onClose: () => void }) {
  const { session } = useSession();
  // Se refresca mientras el último estado conocido sea transitorio.
  const [transitorio, setTransitorio] = useState(() => esTransitorio(job.status));
  const detalle = usePolling(
    () => provisioningApi.job(job.id).catch((err: unknown) => { throw jobLoadError(err); }),
    {
      intervalSeconds: session?.preferences.refresh_interval,
      deps: [job.id],
      activo: transitorio,
    },
  );
  const data = detalle.data;
  const actual = data ?? job;
  useEffect(() => {
    if (data) setTransitorio(esTransitorio(data.status));
  }, [data]);
  const estado = ESTADOS_EJECUCION[actual.status];
  const intentos = data ? [...data.attempts].sort((a, b) => b.n - a.n) : [];

  return (
    <Modal title={`Ejecución n.º ${job.id}`} onClose={onClose}>
      <dl className="grid gap-3 sm:grid-cols-2">
        <Dato etiqueta="Estado" valor={<Badge tone={estado.tono}>{estado.texto}</Badge>} />
        <Dato etiqueta="Operación" valor={`${OPERACIONES[actual.operation]} · ${PROVEEDORES[actual.provider]}`} />
        <Dato etiqueta="Usuario" valor={actual.user.name} />
        <Dato etiqueta="Plataforma" valor={`${actual.platform.name} · ${actual.area.name}`} />
        <Dato etiqueta="Intentos" valor={`${actual.attempts_count} de ${actual.max_attempts}`} />
        <Dato etiqueta="Próximo intento" valor={formatearFecha(actual.next_attempt_at)} />
        <Dato etiqueta="Creada" valor={formatearFecha(actual.created_at)} />
        <Dato etiqueta="Terminó" valor={formatearFecha(actual.finished_at)} />
      </dl>

      <section aria-labelledby="ejecucion-detalle-intentos" className="space-y-3">
        <h3 id="ejecucion-detalle-intentos" className="text-sm font-semibold text-body-text">Intentos</h3>
        {detalle.loading && !data ? <Spinner label="Cargando los intentos…" /> : null}
        {detalle.error ? <ErrorNote message={detalle.error} /> : null}
        {data ? (
          intentos.length === 0 ? (
            <EmptyNote message="Todavía no hay intentos." />
          ) : (
            <DataList>
              {intentos.map((intento) => {
                const resultado = RESULTADOS_INTENTO[intento.result];
                return (
                  <DataListItem key={intento.n}>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-body-text">Intento {intento.n}</span>
                      <Badge tone={resultado.tono}>{resultado.texto}</Badge>
                    </div>
                    <p className="text-sm text-label">
                      Inicio: {formatearFecha(intento.started_at)} · Fin: {formatearFecha(intento.finished_at)}
                    </p>
                    {intento.error ? (
                      <p className="break-words text-sm text-body-text">Error: {intento.error}</p>
                    ) : null}
                  </DataListItem>
                );
              })}
            </DataList>
          )
        ) : null}
      </section>
    </Modal>
  );
}
