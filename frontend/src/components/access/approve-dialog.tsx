'use client';

/**
 * Confirmación de aprobar una solicitud (DIS-015, `POST /access-requests/<id>/approve`
 * con `{}`, contrato `solicitudes.md` 1.1). `Modal` con botón primario: aprobar
 * no es destructivo (`ConfirmDialog` es para eliminar).
 */

import { useState } from 'react';
import { requestsApi } from '@/lib/access/requests';
import type { AccessRequest } from '@/lib/access/types';
import { Button, Modal } from '../form';
import { ErrorNote } from '../ui';
import { NIVELES } from './access-status-badge';
import { describeDecisionError } from './request-errors';

/** Texto de lo que hará la aprobación (sube de nivel si ya tenía uno). */
export function efectoAprobacion(request: AccessRequest): string {
  const nivel = NIVELES[request.level];
  const base = `${request.requester.name} recibirá el nivel ${nivel} en ${request.platform.name}.`;
  return request.current_level
    ? `${base} Reemplaza su nivel ${NIVELES[request.current_level]}.`
    : base;
}

export function ApproveDialog({
  request,
  onClose,
  onDecided,
  onStale,
}: {
  request: AccessRequest;
  onClose: () => void;
  /** Recibe la solicitud aprobada que devolvió el servidor. */
  onDecided: (request: AccessRequest) => void;
  /** La solicitud ya no se puede decidir (404 o ya decidida): recargar la lista. */
  onStale: () => void;
}) {
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function aprobar() {
    if (sending) return;
    setSending(true);
    setError(null);
    try {
      const result = await requestsApi.approve(request.id);
      onDecided(result.request);
    } catch (err) {
      const view = describeDecisionError(err);
      setError(view.message);
      if (view.stale) onStale();
      setSending(false);
    }
  }

  return (
    <Modal
      title="Aprobar solicitud"
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={aprobar} disabled={sending}>
            {sending ? 'Aprobando…' : 'Aprobar'}
          </Button>
        </>
      }
    >
      <div aria-busy={sending} className="space-y-3">
        <p className="text-sm text-body-text">{efectoAprobacion(request)}</p>
        <p className="text-sm text-label">
          Área {request.area.name}. El acceso se aplicará en la plataforma y quedará en proceso hasta
          que termine.
        </p>
        {error ? <ErrorNote message={error} /> : null}
      </div>
    </Modal>
  );
}
