'use client';

/** Ajustes › Respaldo: descarga y restauración de la configuración. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { Button, FileInput } from '../form';
import { Card, ErrorNote, SuccessNote } from '../ui';

export function BackupTab() {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function download() {
    setBusy(true);
    setError(null);
    setDone(null);
    try {
      const blob = await api.downloadBackup();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const stamp = new Date().toISOString().slice(0, 10);
      link.download = `nexus_backup_${stamp}.zip`;
      link.click();
      URL.revokeObjectURL(url);
      setDone('Respaldo descargado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo descargar');
    } finally {
      setBusy(false);
    }
  }

  async function restore(file: File) {
    setBusy(true);
    setError(null);
    setDone(null);
    try {
      const result = await api.uploadBackup(file);
      setDone(`Restaurado: ${result.restored.join(', ') || 'nada'}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo restaurar');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="space-y-5">
      {error ? <ErrorNote message={error} /> : null}
      {done ? <SuccessNote>{done}</SuccessNote> : null}

      <div>
        <h2 className="text-sm font-medium">Descargar respaldo</h2>
        <p className="mt-1 text-sm text-label">
          Incluye la identidad del portal, el directorio, el correo, las
          plantillas y las cuentas locales.
        </p>
        <Button onClick={download} disabled={busy} className="mt-3">
          {busy ? 'Preparando…' : 'Descargar ZIP'}
        </Button>
      </div>

      <div className="border-t border-panel-border pt-5">
        <h2 className="text-sm font-medium">Restaurar</h2>
        <p className="mt-1 text-sm text-label">
          Sobrescribe la configuración con la del paquete. Las cuentas que ya
          existan no se modifican.
        </p>
        <FileInput
          accept=".zip,application/zip"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) restore(file);
          }}
          className="mt-3 block"
        />
      </div>
    </Card>
  );
}
