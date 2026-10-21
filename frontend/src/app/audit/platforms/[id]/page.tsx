import { AppShell } from '@/components/app-shell';
import { idDeRuta } from '@/components/audit/audit-routes';
import { PlatformAuditHistory } from '@/components/audit/platform-audit-history';
import { RequireRole } from '@/components/require-role';
import { ErrorNote } from '@/components/ui';

/**
 * Historial de una plataforma (DIS-020): admin de área (sus áreas) y
 * superadmin. El usuario recibe 403 del backend; aquí ve "sin permiso".
 */
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const platformId = idDeRuta((await params).id);
  return (
    <AppShell>
      <RequireRole requires="any_admin">
        {platformId === null
          ? <ErrorNote message="La plataforma indicada no es válida." />
          : <PlatformAuditHistory platformId={platformId} />}
      </RequireRole>
    </AppShell>
  );
}
