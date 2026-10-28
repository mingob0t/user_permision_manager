'use client';

/**
 * Auditoría (`/audit`; FNC-025, DIS-020): registros dentro del alcance de
 * quien consulta (`GET /audit` paginado, contrato `auditoria.md`), con
 * filtros, paginación y detalle con antes y después.
 */

import { auditApi } from '@/lib/access/audit';
import { PageHeader } from './page-header';
import { AuditHistory } from './audit/audit-history';

export function AuditLog() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Auditoría"
        description="Registro de acciones sobre el sistema."
      />
      <AuditHistory cargar={auditApi.list} />
    </div>
  );
}
