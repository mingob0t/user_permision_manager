import { Suspense } from 'react';
import { AppShell } from '@/components/app-shell';
import { ApprovalsView } from '@/components/access/approvals-view';
import { RequireRole } from '@/components/require-role';
import { Skeleton } from '@/components/ui';

/**
 * Historial de solicitudes con URL limpia (DIS-163): misma vista que `/approvals?status=…`; los
 * filtros se conservan en la pestaña (`sessionStorage`), no en la URL.
 */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="any_admin">
        <Suspense fallback={<Skeleton variant="fila" count={5} ariaLabel="Cargando solicitudes…" />}>
          <ApprovalsView />
        </Suspense>
      </RequireRole>
    </AppShell>
  );
}
