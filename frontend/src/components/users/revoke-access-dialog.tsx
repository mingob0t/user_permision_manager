'use client';

/**
 * Confirmación de revocar un acceso (DIS-018, F-ACC-02, `POST /access/<id>/revoke`,
 * contrato `accesos.md` 1.1): motivo opcional de hasta 500 caracteres (P7).
 *
 * - Mismo patrón que `access/reject-dialog.tsx` (DIS-015): contador ligado con
 *   `aria-describedby`, error del campo con el foco y `aria-disabled` durante
 *   el envío para que el foco no caiga en `body`.
 * - Botón de confirmar `danger` (DIS-043): revocar es destructivo y, desde
 *   DIS-004, el texto sobre `--color-error-solid` pasa AA (4,83:1).
 * - El efecto y la advertencia describen el diálogo (`describedBy`, DIS-031).
 */

import { useState } from 'react';
import { grantsApi } from '@/lib/access/grants';
import type { Access } from '@/lib/access/types';
import { Button, Field, Modal, TextArea } from '../form';
import { FieldErrorNote, FieldHint, describedBy } from '../platforms/field-notes';
import { ErrorNote } from '../ui';
import { NIVELES } from '../access/access-status-badge';
import {
  MENSAJE_MOTIVO_REVOCACION, REVOCACION_MOTIVO_MAX, describeRevokeError,
} from './revoke-errors';

const FORM_ID = 'revocacion-acceso';
const MOTIVO_ID = 'revocacion-motivo';
const PISTA_ID = 'revocacion-motivo-pista';
const MOTIVO_ERROR_ID = 'revocacion-motivo-error';
const EFECTO_ID = 'revocacion-efecto';
const AVISO_ID = 'revocacion-aviso';

/** Pista del motivo según su largo (recortado, como lo valida el servidor). */
export function pistaMotivoRevocacion(largo: number): string {
  return `Opcional. ${largo}/${REVOCACION_MOTIVO_MAX} caracteres`;
}

export function RevokeAccessDialog({
  access,
  onClose,
  onRevoked,
  onStale,
}: {
  access: Access;
  onClose: () => void;
  /** Recibe el acceso que devolvió el servidor (`revocando`). */
  onRevoked: (access: Access) => void;
  /** El acceso ya no se puede revocar (404 o 409): recargar la lista. */
  onStale: () => void;
}) {
  const [motivo, setMotivo] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});

  const texto = motivo.trim();
  const excede = texto.length > REVOCACION_MOTIVO_MAX;
  const errorMotivo = fields.reason ?? (excede ? MENSAJE_MOTIVO_REVOCACION : undefined);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (sending || excede) return;
    setSending(true);
    setError(null);
    setFields({});
    try {
      const result = await grantsApi.revoke(access.id, texto || null);
      onRevoked(result.access);
    } catch (err) {
      const view = describeRevokeError(err);
      setError(view.message);
      setFields(view.fields);
      if (view.stale) onStale();
      if (view.fields.reason) document.getElementById(MOTIVO_ID)?.focus();
      setSending(false);
    }
  }

  return (
    <Modal
      title="Revocar acceso"
      onClose={onClose}
      describedBy={`${EFECTO_ID} ${AVISO_ID}`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            type="submit"
            form={FORM_ID}
            disabled={excede}
            // Mientras se envía: `aria-disabled` para que el foco no caiga en `body`.
            aria-disabled={sending || undefined}
            className="aria-disabled:opacity-40"
            aria-describedby={PISTA_ID}
          >
            {sending ? 'Revocando…' : 'Revocar'}
          </Button>
        </>
      }
    >
      <form id={FORM_ID} onSubmit={submit} noValidate aria-busy={sending} className="space-y-5">
        <p id={EFECTO_ID} className="text-sm text-body-text">
          Se retirará el acceso de {access.user.name} a {access.platform.name} (nivel{' '}
          {NIVELES[access.level]}, área {access.area.name}).
        </p>
        <p id={AVISO_ID} className="text-sm text-label">
          La revocación se aplica en la plataforma y no se puede deshacer: para recuperarlo hará
          falta una nueva solicitud.
        </p>

        <div>
          <Field label="Motivo de la revocación">
            <TextArea
              id={MOTIVO_ID}
              rows={3}
              value={motivo}
              onChange={(event) => setMotivo(event.target.value)}
              placeholder="Opcional: explica por qué se retira"
              {...describedBy([MOTIVO_ERROR_ID, errorMotivo], [PISTA_ID, true])}
            />
          </Field>
          <FieldHint id={PISTA_ID}>{pistaMotivoRevocacion(texto.length)}</FieldHint>
          <FieldErrorNote id={MOTIVO_ERROR_ID} message={errorMotivo} />
        </div>

        <p className="text-sm text-label">La persona verá este motivo en Mis accesos.</p>

        {error ? <ErrorNote message={error} /> : null}
      </form>
    </Modal>
  );
}
