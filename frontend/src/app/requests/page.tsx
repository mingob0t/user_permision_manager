import { Suspense } from 'react';
import { AppShell } from '@/components/app-shell';
import { MyRequestsView } from '@/components/access/my-requests-view';
import { Spinner } from '@/components/ui';

/**
 * Mis solicitudes y mis accesos (DIS-014). Sin `RequireRole`: el superadmin
 * ve un estado vacío explicado en lugar de "sin permiso" (decisión en la ficha).
 */
export default function Page() {
  return (
    <AppShell>
      <Suspense fallback={<Spinner label="Cargando…" />}>
        <MyRequestsView />
      </Suspense>
    </AppShell>
  );
}
