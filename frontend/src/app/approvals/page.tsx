import { Suspense } from 'react';
import { AppShell } from '@/components/app-shell';
import { ApprovalsInbox } from '@/components/access/approvals-inbox';
import { RequireRole } from '@/components/require-role';
import { Spinner } from '@/components/ui';

/** Bandeja de aprobaciones (DIS-015): admin de área (sus áreas) y superadmin (todas). */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="any_admin">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold">Aprobaciones</h1>
            <p className="mt-1 text-sm text-label">
              Solicitudes de acceso de tus áreas (todas, si eres superadmin). Aprueba o rechaza con un motivo.
            </p>
          </div>
          <Suspense fallback={<Spinner label="Cargando…" />}>
            <ApprovalsInbox />
          </Suspense>
        </div>
      </RequireRole>
    </AppShell>
  );
}
