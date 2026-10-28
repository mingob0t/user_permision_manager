'use client';

/**
 * Historial de una plataforma (`/audit/platforms/[id]`; DIS-020, F-AUD-04;
 * `GET /audit/platforms/<id>`). Solo admin (sus áreas; 404 fuera de ellas) y
 * superadmin: la ruta va dentro de `RequireRole any_admin` (el usuario recibe 403).
 */

import { ButtonLink } from '../form';
import { useCallback, useState } from 'react';
import { auditApi } from '@/lib/access/audit';
import type { AuditEntryV1, AuditParams } from '@/lib/access/types';
import { AuditHistory } from './audit-history';
import { RUTA_AUDITORIA } from './audit-routes';

/** Nombre de la plataforma según los registros. */
export function nombreDePlataforma(items: AuditEntryV1[], platformId: number): string | null {
  return items.find((entry) => entry.platform?.id === platformId)?.platform?.name ?? null;
}

export function PlatformAuditHistory({ platformId }: { platformId: number }) {
  const [nombre, setNombre] = useState<string | null>(null);

  const cargar = useCallback(
    (params: AuditParams) => auditApi.ofPlatform(platformId, params), [platformId]);
  const nombrar = useCallback((items: AuditEntryV1[]) => {
    setNombre((actual) => actual ?? nombreDePlataforma(items, platformId));
  }, [platformId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold">Historial de la plataforma</h1>
          <p className="mt-1 break-words text-sm text-label">
            {nombre ?? 'Eventos sobre la plataforma y sus accesos.'}
          </p>
        </div>
        <ButtonLink href={RUTA_AUDITORIA} variant="secondary">
          Toda la auditoría
        </ButtonLink>
      </div>
      {/* La plataforma ya está fijada: sin filtros de área ni plataforma. */}
      <AuditHistory cargar={cargar} conAlcance={false} onDatos={nombrar} />
    </div>
  );
}
