'use client';

/** Ajustes › Mis preferencias: disponibles para cualquier usuario. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { Button, Checkbox, Field, TextInput } from '../form';
import { useSession } from '../session-provider';
import { Card, ErrorNote, SuccessNote } from '../ui';

export function PreferencesTab() {
  const { session } = useSession();
  const [prefs, setPrefs] = useState(session?.preferences ?? null);
  const [state, setState] = useState<{ saving: boolean; saved: boolean; error: string | null }>(
    { saving: false, saved: false, error: null },
  );

  if (!prefs) return null;

  async function save() {
    setState({ saving: true, saved: false, error: null });
    try {
      // FNC-123: el tema lo guarda solo el selector; aquí se omite para no pisarlo con el de la sesión.
      const sinTema = { ...prefs! };
      delete sinTema.theme;
      const result = await api.savePreferences(sinTema);
      setPrefs(result.preferences);
      setState({ saving: false, saved: true, error: null });
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

      <Checkbox
        label="Recibir notificaciones en la aplicación"
        checked={prefs.notifications}
        onChange={(e) => setPrefs({ ...prefs, notifications: e.target.checked })}
      />
      <Checkbox
        label="Recibir notificaciones por correo"
        checked={prefs.email_notifications}
        onChange={(e) => setPrefs({ ...prefs, email_notifications: e.target.checked })}
      />
      <Checkbox
        label="Mostrar los tours de ayuda"
        checked={prefs.tour_enabled}
        onChange={(e) => setPrefs({ ...prefs, tour_enabled: e.target.checked })}
      />

      <Field label="Intervalo de refresco (segundos)" hint="Entre 15 y 3600.">
        <TextInput
          type="number" min={15} max={3600}
          value={String(prefs.refresh_interval)}
          onChange={(e) =>
            setPrefs({ ...prefs, refresh_interval: Number(e.target.value) })
          }
        />
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
