'use client';

/**
 * Confirmación de eliminar el conector de una plataforma (DIS-022,
 * `DELETE /platforms/<id>/connector`, contrato `conectores-y-ejecuciones.md` 1.1).
 *
 * - Explica el efecto antes de confirmar. El servidor lo impide con accesos
 *   vigentes (`409 plataforma_con_accesos`).
 * - Patrón de `RevokeAccessDialog` (DIS-018): botón de confirmar primario (el
 *   blanco sobre `--color-error` falla AA hasta DIS-004) y `aria-disabled`
 *   durante el envío.
 */

import { useState } from 'react';
import { connectorsApi } from '@/lib/access/connectors';
import type { Platform } from '@/lib/types';
import { Button, Modal } from '../form';
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
    <Modal
      title="Eliminar conector"
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button
            onClick={confirmar}
            aria-disabled={sending || undefined}
            className="aria-disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary"
          >
            {sending ? 'Eliminando…' : 'Eliminar'}
          </Button>
        </>
      }
    >
      <div aria-busy={sending} className="space-y-3">
        <p className="text-sm text-body-text">
          Se borrará la configuración del conector de {platform.name}.
        </p>
        <p className="text-sm text-label">
          Hasta configurarlo de nuevo, los accesos que se aprueben en esta plataforma no podrán
          aplicarse. No se borra el ítem del gestor de secretos. Si hay accesos vigentes, no se
          puede eliminar.
        </p>
        {error ? <ErrorNote message={error} /> : null}
      </div>
    </Modal>
  );
}
