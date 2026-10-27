'use client';

/** Ajustes › Portal: identidad visual (nombre, colores y logo). */

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import { Button, Field, TextInput } from '../form';
import { Card, ErrorNote, Spinner, SuccessNote } from '../ui';

export function PortalTab() {
  const { data, loading, error, reload } = useAsync(() => api.settings(), []);
  const [form, setForm] = useState<Record<string, string> | null>(null);
  const [state, setState] = useState<{ saving: boolean; saved: boolean; error: string | null }>(
    { saving: false, saved: false, error: null },
  );

  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if (!data) return null;

  const value = form ?? {
    portal_name: data.portal_name,
    bg_color: data.bg_color,
    text_color: data.text_color,
    portal_identity_type: data.portal_identity_type,
    portal_icon: data.portal_icon ?? '',
  };

  /** Convierte la imagen elegida en data URI: el logo se guarda en la base de
   *  datos, no como archivo en el servidor. */
  function pickLogo(file: File) {
    if (file.size > 512 * 1024) {
      setState({ ...state, error: 'La imagen supera 512 KB.' });
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setForm({
        ...value,
        portal_identity_type: 'image',
        portal_icon: String(reader.result),
      });
    };
    reader.readAsDataURL(file);
  }

  async function save() {
    setState({ saving: true, saved: false, error: null });
    try {
      await api.saveSettings(value);
      setState({ saving: false, saved: true, error: null });
      reload();
    } catch (err) {
      setState({
        saving: false, saved: false,
        error: err instanceof Error ? err.message : 'No se pudo guardar',
      });
    }
  }

  return (
    <Card className="space-y-4">
      {state.error ? <ErrorNote message={state.error} /> : null}

      <Field label="Nombre del portal">
        <TextInput
          value={value.portal_name}
          onChange={(e) => setForm({ ...value, portal_name: e.target.value })}
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Color de fondo">
          <TextInput
            type="color" className="p-1"
            value={value.bg_color}
            onChange={(e) => setForm({ ...value, bg_color: e.target.value })}
          />
        </Field>
        <Field label="Color de texto">
          <TextInput
            type="color" className="p-1"
            value={value.text_color}
            onChange={(e) => setForm({ ...value, text_color: e.target.value })}
          />
        </Field>
      </div>

      <Field
        label="Logo del portal"
        hint="PNG, JPEG, GIF, WebP o SVG, hasta 512 KB. Se guarda en la base de datos."
      >
        <div className="flex flex-wrap items-center gap-3">
          {value.portal_identity_type === 'image' && value.portal_icon ? (
            // El logo es un data URI guardado en la BD: next/image no lo optimiza.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={value.portal_icon}
              alt="Logo actual"
              className="h-10 w-10 rounded border border-panel-border object-contain"
            />
          ) : null}
          <input
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) pickLogo(file);
            }}
            className="min-h-12 text-sm text-label"
          />
          {value.portal_identity_type === 'image' ? (
            <Button
              variant="secondary"
              onClick={() =>
                setForm({ ...value, portal_identity_type: 'icon', portal_icon: '' })
              }
            >
              Quitar
            </Button>
          ) : null}
        </div>
      </Field>

      <div className="flex items-center gap-3">
        <Button onClick={save} disabled={state.saving}>
          {state.saving ? 'Guardando…' : 'Guardar'}
        </Button>
        {state.saved ? <SuccessNote>Guardado.</SuccessNote> : null}
      </div>
    </Card>
  );
}
