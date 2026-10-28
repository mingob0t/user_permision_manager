import { Suspense } from 'react';
import { AppShell } from '@/components/app-shell';
import { PageHeader } from '@/components/page-header';
import { ApprovalsInbox } from '@/components/access/approvals-inbox';
import { RequireRole } from '@/components/require-role';
import { Skeleton } from '@/components/ui';

/** Bandeja de aprobaciones (DIS-015): admin de área (sus áreas) y superadmin (todas). */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="any_admin">
        <div className="space-y-6">
          <PageHeader
            title="Aprobaciones"
            description="Solicitudes de acceso de tus áreas (todas, si eres superadmin). Aprueba o rechaza con un motivo."
          />
          <Suspense fallback={<Skeleton variant="fila" count={5} ariaLabel="Cargando aprobaciones…" />}>
            <ApprovalsInbox />
          </Suspense>
        </div>
      </RequireRole>
    </AppShell>
  );
}
