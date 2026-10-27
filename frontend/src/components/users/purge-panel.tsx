'use client';

/** Purga de cuentas inactivas: vista previa y confirmación. */

import { useState } from 'react';
import { api } from '@/lib/api';
import type { InactiveUser } from '@/lib/types';
import { Button, ConfirmDialog, Field, TextInput } from '../form';
import { Card, ErrorNote } from '../ui';

export function PurgePanel({ onDone }: { onDone: () => void }) {
  const [days, setDays] = useState(30);
  const [preview, setPreview] = useState<InactiveUser[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  async function load() {
    setBusy(true);
    setError(null);
    try {
      const result = await api.inactiveUsers(days);
      setPreview(result.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo consultar');
    } finally {
      setBusy(false);
    }
  }

  async function purge() {
    setBusy(true);
    try {
      await api.purgeInactiveUsers(days);
      setConfirming(false);
      setPreview(null);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo purgar');
      setConfirming(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="space-y-3">
      <div>
        <h2 className="text-sm font-medium">Purgar cuentas inactivas</h2>
        <p className="mt-1 text-sm text-label">
          Elimina las cuentas sin acceso en el periodo indicado, incluidas las
          que nunca han iniciado sesión. Nunca afecta a los administradores
          globales.
        </p>
      </div>

      {error ? <ErrorNote message={error} /> : null}

      <div className="flex flex-wrap items-end gap-2">
        <Field label="Días sin actividad">
          <TextInput
            type="number" min={7} className="w-28"
            value={String(days)}
            onChange={(e) => setDays(Number(e.target.value))}
          />
        </Field>
        <Button variant="secondary" onClick={load} disabled={busy}>
          {busy ? 'Consultando…' : 'Ver candidatas'}
        </Button>
      </div>

      {preview !== null ? (
        preview.length === 0 ? (
          <p className="text-sm text-label">
            Ninguna cuenta cumple ese criterio.
          </p>
        ) : (
          <div className="space-y-2">
            <p className="text-sm">
              <strong>{preview.length}</strong> cuenta(s) se eliminarían:
            </p>
            <ul className="max-h-48 space-y-1 overflow-y-auto text-sm text-label">
              {preview.map((user) => (
                <li key={user.id} className="truncate">
                  {user.email}
                  {' · '}
                  {user.last_login_at
                    ? `último acceso ${user.last_login_at.slice(0, 10)}`
                    : 'nunca ha entrado'}
                </li>
              ))}
            </ul>
            <Button variant="danger" onClick={() => setConfirming(true)}>
              Purgar {preview.length} cuenta(s)
            </Button>
          </div>
        )
      ) : null}

      {confirming ? (
        <ConfirmDialog
          title="Purgar cuentas inactivas"
          message={`Se eliminarán ${preview?.length ?? 0} cuenta(s) de forma permanente.`}
          confirmLabel="Purgar"
          onConfirm={purge}
          onCancel={() => setConfirming(false)}
          busy={busy}
        />
      ) : null}
    </Card>
  );
}
