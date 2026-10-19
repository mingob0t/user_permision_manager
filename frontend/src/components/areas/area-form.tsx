'use client';

/**
 * Alta y edición de un área (DIS-016). Extraído de `areas-list.tsx` sin
 * cambiar sus campos; agrega los errores por campo (`422 fields`) y los
 * mensajes de los `409` del contrato `areas-y-roles.md`.
 *
 * En un alta el color no se envía hasta que se elige: el servidor aplica su
 * color por omisión (el mismo que antes fijaba aquí la pantalla), y así no
 * hay un color literal en el componente.
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import type { Area, AreaInput } from '@/lib/types';
import { Button, Checkbox, Field, Modal, TextArea, TextInput } from '../form';
import { ErrorNote } from '../ui';
import { erroresDeCampo, mensajeDeError } from './area-errors';

/** Mensaje de un campo rechazado por el servidor, ligado al control con `aria-describedby`. */
function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return (
    <span id={id} className="mt-1.5 block text-xs font-bold text-error">
      {message}
    </span>
  );
}

/** Atributos de accesibilidad de un control con posible error. */
function invalido(id: string, message?: string) {
  return message ? { 'aria-invalid': true, 'aria-describedby': id } : {};
}

export function AreaForm({
  area,
  onClose,
  onSaved,
}: {
  area: Area | null;
  onClose: () => void;
  /** Recibe el área que devolvió el servidor. */
  onSaved: (saved: Area) => void;
}) {
  const [form, setForm] = useState<AreaInput>(
    area
      ? {
          name: area.name,
          description: area.description ?? '',
          color: area.color,
          status: area.status,
        }
      : { name: '', description: '', status: 'Activo' },
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});

  async function save() {
    if (!form.name?.trim()) {
      setFields({});
      setError('El nombre es obligatorio.');
      return;
    }
    setSaving(true);
    setError(null);
    setFields({});
    try {
      const result = area ? await api.updateArea(area.id, form) : await api.createArea(form);
      onSaved(result.area);
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo guardar'));
      setFields(erroresDeCampo(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      title={area ? `Editar ${area.name}` : 'Nueva área'}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={save} disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar'}
          </Button>
        </>
      }
    >
      {error ? <ErrorNote message={error} /> : null}

      <div>
        <Field label="Nombre">
          <TextInput
            value={form.name ?? ''}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            {...invalido('area-name-error', fields.name)}
          />
        </Field>
        <FieldError id="area-name-error" message={fields.name} />
      </div>

      <div>
        <Field label="Descripción">
          <TextArea
            rows={2}
            value={form.description ?? ''}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            {...invalido('area-description-error', fields.description)}
          />
        </Field>
        <FieldError id="area-description-error" message={fields.description} />
      </div>

      <div>
        <Field
          label="Color"
          hint={form.color ? undefined : 'Si no eliges uno, se usa el color por omisión.'}
        >
          <TextInput
            type="color" className="h-10 p-1"
            value={form.color ?? ''}
            onChange={(e) => setForm({ ...form, color: e.target.value })}
            {...invalido('area-color-error', fields.color)}
          />
        </Field>
        <FieldError id="area-color-error" message={fields.color} />
      </div>

      <div>
        <Checkbox
          label="Activa"
          checked={form.status === 'Activo'}
          onChange={(e) => setForm({ ...form, status: e.target.checked ? 'Activo' : 'Inactivo' })}
          {...invalido('area-status-error', fields.status)}
        />
        <FieldError id="area-status-error" message={fields.status} />
      </div>
    </Modal>
  );
}
