'use client';

/**
 * Historial de una plataforma (`/audit/platforms/[id]`; DIS-020, F-AUD-04;
 * `GET /audit/platforms/<id>`). Solo admin (sus áreas; 404 fuera de ellas) y
 * superadmin: la ruta va dentro de `RequireRole any_admin` (el usuario recibe 403).
 */

import { ButtonLink } from '../form';
import { PageHeader } from '../page-header';
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
      <PageHeader
        title="Historial de la plataforma"
        description={nombre ?? 'Eventos sobre la plataforma y sus accesos.'}
        actions={
          <ButtonLink href={RUTA_AUDITORIA} variant="secondary">
            Toda la auditoría
          </ButtonLink>
        }
      />
      {/* La plataforma ya está fijada: sin filtros de área ni plataforma. */}
      <AuditHistory cargar={cargar} conAlcance={false} onDatos={nombrar} />
    </div>
  );
}
