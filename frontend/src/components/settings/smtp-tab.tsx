'use client';

/** Ajustes › Correo: servidor saliente y correo de prueba. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import { Button, Checkbox, Field, Select, TextInput } from '../form';
import { Card, ErrorNote, Spinner, SuccessNote } from '../ui';

export function SmtpTab() {
  const { data, loading, error, reload } = useAsync(() => api.smtp(), []);
  const [form, setForm] = useState<Record<string, unknown> | null>(null);
  const [password, setPassword] = useState('');
  const [target, setTarget] = useState('');
  const [state, setState] = useState<{ saving: boolean; saved: boolean; error: string | null; tested: string | null }>(
    { saving: false, saved: false, error: null, tested: null },
  );

  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if (!data) return null;

  // Con SMTP_FORCE_ENV el servidor ignora lo que se guarde aquí, así que los
  // campos se muestran en solo lectura en lugar de fingir que se pueden editar.
  const locked = data.editable === false;

  const value = form ?? {
    server: data.server ?? '',
    port: data.port ?? 587,
    encryption: data.encryption ?? 'starttls',
    username: data.username ?? '',
    sender_name: data.sender_name ?? '',
    auth_enabled: data.auth_enabled ?? true,
  };

  async function save() {
    setState({ ...state, saving: true, saved: false, error: null });
    try {
      // Una contraseña vacía deja la guardada intacta.
      await api.saveSmtp({ ...value, ...(password ? { password } : {}) });
      setPassword('');
      setState({ saving: false, saved: true, error: null, tested: null });
      reload();
    } catch (err) {
      setState({
        saving: false, saved: false, tested: null,
        error: err instanceof Error ? err.message : 'No se pudo guardar',
      });
    }
  }

  async function test() {
    setState({ ...state, tested: null, error: null });
    try {
      await api.testSmtp(target);
      setState({ ...state, tested: `Correo enviado a ${target}.`, error: null });
    } catch (err) {
      setState({
        ...state, tested: null,
        error: err instanceof Error ? err.message : 'No se pudo enviar',
      });
    }
  }

  return (
    <Card className="space-y-4">
      {state.error ? <ErrorNote message={state.error} /> : null}
      {data.warning ? <ErrorNote message={data.warning} /> : null}

      {locked ? (
        <div className="rounded-xl border border-primary/40 bg-primary/10 p-3 text-sm">
          Estos valores vienen del <code>.env</code> del servidor
          (<code>SMTP_FORCE_ENV</code>) y no se pueden cambiar desde aquí. Para
          modificarlos, edita el archivo y reinicia el servicio.
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Servidor">
          <TextInput
            disabled={locked}
            value={String(value.server)}
            onChange={(e) => setForm({ ...value, server: e.target.value })}
          />
        </Field>
        <Field label="Puerto">
          <TextInput
            type="number"
            disabled={locked}
            value={String(value.port)}
            onChange={(e) => setForm({ ...value, port: Number(e.target.value) })}
          />
        </Field>
      </div>

      <Field label="Cifrado">
        <Select
          disabled={locked}
          value={String(value.encryption)}
          onChange={(e) => setForm({ ...value, encryption: e.target.value })}
        >
          <option value="starttls">STARTTLS</option>
          <option value="ssl">SSL/TLS</option>
          <option value="none">Ninguno</option>
        </Select>
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Usuario">
          <TextInput
            disabled={locked}
            value={String(value.username ?? '')}
            onChange={(e) => setForm({ ...value, username: e.target.value })}
          />
        </Field>
        <Field label="Contraseña" hint="Vacío conserva la actual.">
          <TextInput
            type="password" value={password} autoComplete="new-password"
            disabled={locked}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
      </div>

      <Field label="Nombre del remitente">
        <TextInput
          disabled={locked}
          value={String(value.sender_name ?? '')}
          onChange={(e) => setForm({ ...value, sender_name: e.target.value })}
        />
      </Field>

      <Checkbox
        label="Requiere autenticación"
        disabled={locked}
        checked={Boolean(value.auth_enabled)}
        onChange={(e) => setForm({ ...value, auth_enabled: e.target.checked })}
      />

      {!locked ? (
        <div className="flex items-center gap-3">
          <Button onClick={save} disabled={state.saving}>
            {state.saving ? 'Guardando…' : 'Guardar'}
          </Button>
          {state.saved ? <SuccessNote>Guardado.</SuccessNote> : null}
        </div>
      ) : null}

      <div className="border-t border-panel-border pt-4">
        <Field label="Enviar correo de prueba">
          <div className="flex gap-2">
            <TextInput
              type="email" placeholder="destino@ejemplo.com" value={target}
              onChange={(e) => setTarget(e.target.value)}
            />
            <Button variant="secondary" onClick={test} disabled={!target}>
              Enviar
            </Button>
          </div>
        </Field>
        {state.tested ? (
          <div className="mt-2">
            <SuccessNote>{state.tested}</SuccessNote>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
