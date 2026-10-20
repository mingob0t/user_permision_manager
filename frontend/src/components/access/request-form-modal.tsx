'use client';

/**
 * Formulario de solicitud de acceso (DIS-013, `POST /access-requests`,
 * contrato `solicitudes.md` 1.1): nivel entre los solicitables y
 * justificación opcional de hasta 500 caracteres.
 *
 * Errores: los del contrato con mensaje propio (`request-errors.ts`); el error
 * del campo va ligado con `aria-describedby` y recibe el foco.
 */

import { useState } from 'react';
import { requestsApi } from '@/lib/access/requests';
import type { AccessLevel, AccessRequest, CatalogItem } from '@/lib/access/types';
import { Button, Field, Modal, TextArea } from '../form';
import { FieldErrorNote, FieldHint, describedBy } from '../platforms/field-notes';
import { ErrorNote } from '../ui';
import { NIVELES } from './access-status-badge';
import {
  JUSTIFICACION_MAX, MENSAJE_JUSTIFICACION_LARGA, MENSAJES_SOLICITUD, describeRequestError,
} from './request-errors';

const FORM_ID = 'solicitud-acceso';
const JUSTIFICACION_ID = 'solicitud-justificacion';
const CONTADOR_ID = 'solicitud-justificacion-contador';
const JUSTIFICACION_ERROR_ID = 'solicitud-justificacion-error';
const NIVEL_ERROR_ID = 'solicitud-nivel-error';

const DESCRIPCION_NIVEL: Record<AccessLevel, string> = {
  usuario: 'Uso habitual de la plataforma.',
  admin: 'Administración de la plataforma.',
};

export function RequestFormModal({
  item,
  onClose,
  onCreated,
}: {
  item: CatalogItem;
  onClose: () => void;
  /** Recibe la solicitud que devolvió el servidor. */
  onCreated: (request: AccessRequest) => void;
}) {
  const niveles = item.requestable_levels;
  const [level, setLevel] = useState<AccessLevel | null>(niveles[0] ?? null);
  const [justification, setJustification] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});

  // El servidor recorta la justificación: se cuenta y valida igual.
  const texto = justification.trim();
  const excede = texto.length > JUSTIFICACION_MAX;
  const errorJustificacion = fields.justification ?? (excede ? MENSAJE_JUSTIFICACION_LARGA : undefined);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (sending) return;
    if (!level || excede) {
      setError(MENSAJES_SOLICITUD.validacion);
      setFields(level ? {} : { level: 'Elige un nivel.' });
      if (excede) document.getElementById(JUSTIFICACION_ID)?.focus();
      return;
    }
    setSending(true);
    setError(null);
    setFields({});
    try {
      const result = await requestsApi.create({
        platform_id: item.platform.id,
        level,
        ...(texto ? { justification: texto } : {}),
      });
      onCreated(result.request);
    } catch (err) {
      const view = describeRequestError(err);
      setError(view.message);
      setFields(view.fields);
      if (view.fields.justification) document.getElementById(JUSTIFICACION_ID)?.focus();
      setSending(false);
    }
  }

  return (
    <Modal
      title={`Solicitar acceso a ${item.platform.name}`}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form={FORM_ID} disabled={sending || niveles.length === 0}>
            {sending ? 'Enviando…' : 'Enviar solicitud'}
          </Button>
        </>
      }
    >
      <form id={FORM_ID} onSubmit={submit} noValidate aria-busy={sending} className="space-y-5">
        <p className="text-sm text-label">
          {item.area.name}
          {item.my_level
            ? ` · Nivel actual: ${NIVELES[item.my_level]}. Si se aprueba, el nuevo nivel lo reemplaza.`
            : null}
        </p>

        <fieldset {...describedBy([NIVEL_ERROR_ID, fields.level])}>
          <legend className="mb-2 block text-xs font-black uppercase tracking-[0.1em] text-label">
            Nivel
          </legend>
          <div className="grid gap-3 sm:grid-cols-2">
            {niveles.map((nivel) => (
              <label
                key={nivel}
                className="flex cursor-pointer items-start gap-3 rounded-xl border border-panel-border p-3 has-[:checked]:border-primary has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary"
              >
                <input
                  type="radio"
                  name="nivel"
                  value={nivel}
                  checked={level === nivel}
                  onChange={() => setLevel(nivel)}
                  className="mt-0.5 accent-primary"
                />
                <span className="min-w-0">
                  <span className="block text-sm font-bold text-body-text">{NIVELES[nivel]}</span>
                  <span className="block text-xs text-label">{DESCRIPCION_NIVEL[nivel]}</span>
                </span>
              </label>
            ))}
          </div>
          <FieldErrorNote id={NIVEL_ERROR_ID} message={fields.level} />
        </fieldset>

        <div>
          <Field label="Justificación (opcional)">
            <TextArea
              id={JUSTIFICACION_ID}
              rows={4}
              value={justification}
              onChange={(event) => setJustification(event.target.value)}
              placeholder="Para qué necesitas el acceso"
              {...describedBy([JUSTIFICACION_ERROR_ID, errorJustificacion], [CONTADOR_ID, true])}
            />
          </Field>
          <FieldHint id={CONTADOR_ID}>
            {`${texto.length}/${JUSTIFICACION_MAX} caracteres`}
          </FieldHint>
          <div role="alert">
            <FieldErrorNote id={JUSTIFICACION_ERROR_ID} message={errorJustificacion} />
          </div>
        </div>

        {error ? <ErrorNote message={error} /> : null}
      </form>
    </Modal>
  );
}
