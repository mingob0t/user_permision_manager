'use client';

/**
 * Confirmación de reintentar una ejecución fallida (DIS-022, DIS-075, P10,
 * `POST /provisioning/jobs/<id>/retry`, contrato 1.1; solo superadmin).
 * Migrado a `AlertDialog` (DIS-075).
 */

import { useId, useState } from 'react';
import { provisioningApi } from '@/lib/access/provisioning';
import type { Job, JobDetail } from '@/lib/access/types';
import { AlertDialog } from '../alert-dialog';
import { ErrorNote } from '../ui';
import { describeRetryError } from './job-errors';

/** Qué pasará al reintentar, según la operación. */
export function efectoReintento(job: Job): string {
  return job.operation === 'otorgar'
    ? `Se volverá a intentar dar acceso a ${job.user.name} en ${job.platform.name}. El acceso pasará a "en proceso" y el servidor revisa antes que siga siendo válido.`
    : `Se volverá a intentar retirar el acceso de ${job.user.name} en ${job.platform.name}. El acceso pasará a "revocando".`;
}

export function JobRetryDialog({
  job,
  onClose,
  onRetried,
  onStale,
}: {
  job: Job;
  onClose: () => void;
  onRetried: (job: JobDetail) => void;
  onStale: () => void;
}) {
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const efectoId = useId();
  const detalleId = useId();

  async function confirmar() {
    if (sending) return;
    setSending(true);
    setError(null);
    try {
      const result = await provisioningApi.retry(job.id);
      onRetried(result.job);
    } catch (err) {
      const view = describeRetryError(err);
      setError(view.message);
      setSending(false);
      if (view.stale) onStale();
    }
  }

  return (
    <AlertDialog
      open={true}
      title="Reintentar ejecución"
      onClose={onClose}
      onConfirm={confirmar}
      type="pregunta"
      confirmVariant="primary"
      confirmLabel={sending ? 'Reintentando…' : 'Reintentar'}
      cancelLabel="Cancelar"
      busy={sending}
      describedBy={`${efectoId} ${detalleId}`}
    >
      <div aria-busy={sending} className="space-y-3">
        <p id={efectoId} className="text-sm text-body-text">{efectoReintento(job)}</p>
        <p id={detalleId} className="text-sm text-label">
          La ejecución n.º {job.id} vuelve a pendiente con nuevos intentos y el reintento queda en la
          auditoría.
        </p>
        {error ? <ErrorNote message={error} /> : null}
      </div>
    </AlertDialog>
  );
}
