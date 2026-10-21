'use client';

/**
 * Auditoría (`/audit`; FNC-025, DIS-020): registros dentro del alcance de
 * quien consulta (`GET /audit` paginado, contrato `auditoria.md`), con
 * filtros, paginación y detalle con antes y después.
 */

import { auditApi } from '@/lib/access/audit';
import { AuditHistory } from './audit/audit-history';

export function AuditLog() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Auditoría</h1>
        <p className="mt-1 text-sm text-label">
          Registro de acciones sobre el sistema.
        </p>
      </div>
      <AuditHistory cargar={auditApi.list} />
    </div>
  );
}
