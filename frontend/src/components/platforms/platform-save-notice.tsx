'use client';

/**
 * Resultado de guardar una plataforma (DIS-017): confirma el guardado y lista
 * los avisos no bloqueantes (`warnings`) de `POST/PUT /platforms`.
 */

import type { PlatformWarning } from '@/lib/types';
import { Button } from '../form';
import { Badge, Card } from '../ui';

export interface SaveNotice {
  name: string;
  warnings: PlatformWarning[];
}

export function PlatformSaveNotice({
  notice,
  onDismiss,
}: {
  notice: SaveNotice;
  onDismiss: () => void;
}) {
  const conAvisos = notice.warnings.length > 0;
  return (
    <Card>
      <div role="status" className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <p className="text-sm font-bold">
            <Badge tone={conAvisos ? 'warning' : 'success'}>
              {conAvisos ? 'Guardada con avisos' : 'Guardada'}
            </Badge>{' '}
            Se guardó «{notice.name}».
          </p>
          {conAvisos ? (
            <ul className="list-disc space-y-1 pl-5 text-sm text-label">
              {notice.warnings.map((aviso) => (
                <li key={aviso.code + aviso.message}>{aviso.message}</li>
              ))}
            </ul>
          ) : null}
        </div>
        <Button variant="secondary" onClick={onDismiss}>
          Cerrar aviso
        </Button>
      </div>
    </Card>
  );
}
