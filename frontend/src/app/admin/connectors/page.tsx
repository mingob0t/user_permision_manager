import { AppShell } from '@/components/app-shell';
import { ConnectorsAdmin } from '@/components/connectors/connectors-admin';
import { PageHeader } from '@/components/page-header';
import { RequireRole } from '@/components/require-role';

/** Conectores y bitácora de ejecuciones (DIS-022); guarda `admin` (FNC-070). */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="admin">
        <div className="space-y-6">
          <PageHeader
            title="Conectores"
            description="Configuración de conectores y bitácora de ejecuciones."
          />
          <ConnectorsAdmin />
        </div>
      </RequireRole>
    </AppShell>
  );
}
