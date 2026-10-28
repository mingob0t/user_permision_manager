'use client';

/** Modal de búsqueda de cuentas en el directorio corporativo. */

import { useState } from 'react';
import { api } from '@/lib/api';
import type { DirectoryUser } from '@/lib/types';
import { Button, Modal, TextInput } from '../form';
import { Badge, EmptyNote, ErrorNote } from '../ui';

export function DirectoryPicker({
  onPick,
  onClose,
}: {
  onPick: (found: DirectoryUser) => void;
  onClose: () => void;
}) {
  const [term, setTerm] = useState('');
  const [results, setResults] = useState<DirectoryUser[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    setBusy(true);
    setError(null);
    try {
      const found = await api.searchDirectory(term);
      setResults(found.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo buscar');
      setResults(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      title="Buscar en el directorio"
      onClose={onClose}
      footer={<Button variant="secondary" onClick={onClose}>Cerrar</Button>}
    >
      {error ? <ErrorNote message={error} /> : null}

      <div className="flex gap-2">
        <TextInput
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') void search(); }}
          placeholder="Nombre, cuenta o correo"
          autoFocus
        />
        <Button onClick={search} disabled={busy || term.trim().length < 2}>
          {busy ? 'Buscando…' : 'Buscar'}
        </Button>
      </div>

      {results !== null ? (
        results.length === 0 ? (
          <EmptyNote message="Sin resultados." />
        ) : (
          <ul className="max-h-72 divide-y divide-panel-border overflow-y-auto">
            {results.map((found) => (
              <li
                key={found.account || found.email}
                className="flex items-center justify-between gap-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{found.name}</p>
                  <p className="truncate text-xs text-label">
                    {found.email || found.account}
                  </p>
                </div>
                {found.exists ? (
                  <Badge>Ya existe</Badge>
                ) : (
                  <Button variant="secondary" onClick={() => onPick(found)}>
                    Dar de alta
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )
      ) : null}
    </Modal>
  );
}
