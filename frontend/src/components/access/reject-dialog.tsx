'use client';

/**
 * Rechazo de una solicitud (DIS-015, DIS-075, RF-06, `POST /access-requests/<id>/reject`,
 * contrato `solicitudes.md` 1.1): motivo obligatorio de 10 a 500 caracteres.
 * Migrado a `AlertDialog` (DIS-075).
 */

import { useState } from 'react';
import { requestsApi } from '@/lib/access/requests';
import type { AccessRequest } from '@/lib/access/types';
import { AlertDialog } from '../alert-dialog';
import { Field, TextArea } from '../form';
import { FieldErrorNote, FieldHint, describedBy } from '../platforms/field-notes';
import { ErrorNote } from '../ui';
import { NIVELES } from './access-status-badge';
import { MENSAJE_MOTIVO, MOTIVO_MAX, MOTIVO_MIN, describeDecisionError } from './request-errors';

const FORM_ID = 'rechazo-solicitud';
const MOTIVO_ID = 'rechazo-motivo';
const PISTA_ID = 'rechazo-motivo-pista';
const MOTIVO_ERROR_ID = 'rechazo-motivo-error';
const RESUMEN_ID = 'rechazo-resumen';

/** Pista del motivo según su largo (recortado, como lo valida el servidor). */
export function pistaMotivo(largo: number): string {
  if (largo < MOTIVO_MIN) {
    const faltan = MOTIVO_MIN - largo;
    return `Obligatorio. Escribe al menos ${faltan} ${faltan === 1 ? 'carácter' : 'caracteres'} más (${largo}/${MOTIVO_MAX}).`;
  }
  return `${largo}/${MOTIVO_MAX} caracteres`;
}

export function RejectDialog({
  request,
  onClose,
  onDecided,
  onStale,
}: {
  request: AccessRequest;
  onClose: () => void;
  /** Recibe la solicitud rechazada que devolvió el servidor. */
  onDecided: (request: AccessRequest) => void;
  /** La solicitud ya no se puede decidir (404 o ya decidida): recargar la lista. */
  onStale: () => void;
}) {
  const [motivo, setMotivo] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});

  const texto = motivo.trim();
  const valido = texto.length >= MOTIVO_MIN && texto.length <= MOTIVO_MAX;
  const excede = texto.length > MOTIVO_MAX;
  const errorMotivo = fields.reason ?? (excede ? MENSAJE_MOTIVO : undefined);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (sending || !valido) return;
    setSending(true);
    setError(null);
    setFields({});
    try {
      const result = await requestsApi.reject(request.id, texto);
      onDecided(result.request);
    } catch (err) {
      const view = describeDecisionError(err);
      setError(view.message);
      setFields(view.fields);
      if (view.stale) onStale();
      if (view.fields.reason) document.getElementById(MOTIVO_ID)?.focus();
      setSending(false);
    }
  }

  return (
    <AlertDialog
      open={true}
      title="Rechazar solicitud"
      onClose={onClose}
      type="aviso"
      confirmVariant="danger"
      confirmLabel={sending ? 'Rechazando…' : 'Rechazar'}
      cancelLabel="Cancelar"
      confirmDisabled={!valido}
      confirmForm={FORM_ID}
      confirmType="submit"
      confirmAriaDescribedBy={PISTA_ID}
      describedBy={RESUMEN_ID}
      busy={sending}
    >
      <form id={FORM_ID} onSubmit={submit} noValidate aria-busy={sending} className="space-y-5">
        <p id={RESUMEN_ID} className="text-sm text-label">
          {request.requester.name} · {request.platform.name} ({request.area.name}) · Nivel{' '}
          {NIVELES[request.level]}
        </p>

        <div>
          <Field label="Motivo del rechazo">
            <TextArea
              id={MOTIVO_ID}
              rows={4}
              required
              value={motivo}
              onChange={(event) => setMotivo(event.target.value)}
              placeholder="Explica al solicitante por qué no se aprueba"
              {...describedBy([MOTIVO_ERROR_ID, errorMotivo], [PISTA_ID, true])}
            />
          </Field>
          <FieldHint id={PISTA_ID}>{pistaMotivo(texto.length)}</FieldHint>
          <FieldErrorNote id={MOTIVO_ERROR_ID} message={errorMotivo} />
        </div>

        <p className="text-sm text-label">El solicitante verá este motivo.</p>

        {error ? <ErrorNote message={error} /> : null}
      </form>
    </AlertDialog>
  );
}
