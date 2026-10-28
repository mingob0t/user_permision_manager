'use client';

/**
 * Confirmación de eliminar el conector de una plataforma (DIS-022, DIS-075,
 * `DELETE /platforms/<id>/connector`, contrato `conectores-y-ejecuciones.md` 1.1).
 * Migrado a `AlertDialog` (DIS-075).
 */

import { useId, useState } from 'react';
import { connectorsApi } from '@/lib/access/connectors';
import type { Platform } from '@/lib/types';
import { AlertDialog } from '../alert-dialog';
import { ErrorNote } from '../ui';
import { describeConnectorDeleteError } from './connector-errors';

export function ConnectorDeleteDialog({
  platform,
  onClose,
  onDeleted,
  onStale,
}: {
  platform: Platform;
  onClose: () => void;
  onDeleted: () => void;
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
      await connectorsApi.remove(platform.id);
      onDeleted();
    } catch (err) {
      const view = describeConnectorDeleteError(err);
      setError(view.message);
      setSending(false);
      if (view.stale) onStale();
    }
  }

  return (
    <AlertDialog
      open={true}
      title="Eliminar conector"
      onClose={onClose}
      onConfirm={confirmar}
      type="aviso"
      confirmVariant="danger"
      confirmLabel={sending ? 'Eliminando…' : 'Eliminar'}
      cancelLabel="Cancelar"
      busy={sending}
      describedBy={`${efectoId} ${detalleId}`}
    >
      <div aria-busy={sending} className="space-y-3">
        <p id={efectoId} className="text-sm text-body-text">
          Se borrará la configuración del conector de {platform.name}.
        </p>
        <p id={detalleId} className="text-sm text-label">
          Hasta configurarlo de nuevo, los accesos que se aprueben en esta plataforma no podrán
          aplicarse. No se borra el ítem del gestor de secretos. Si hay accesos vigentes, no se
          puede eliminar.
        </p>
        {error ? <ErrorNote message={error} /> : null}
      </div>
    </AlertDialog>
  );
}
