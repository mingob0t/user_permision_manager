import { AppShell } from '@/components/app-shell';
import { ConnectorsAdmin } from '@/components/connectors/connectors-admin';
import { RequireRole } from '@/components/require-role';

/** Conectores y bitácora de ejecuciones (DIS-022); guarda `admin` (FNC-070). */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="admin">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold">Conectores</h1>
            <p className="mt-1 text-sm text-label">Configuración de conectores y bitácora de ejecuciones.</p>
          </div>
          <ConnectorsAdmin />
        </div>
      </RequireRole>
    </AppShell>
  );
}
