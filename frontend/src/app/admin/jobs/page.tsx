import { AppShell } from '@/components/app-shell';
import { JobsLog } from '@/components/connectors/jobs-log';
import { RequireRole } from '@/components/require-role';

/** Bitácora de ejecuciones para el admin de área (DIS-041); guarda `any_admin`, solo lectura. */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="any_admin">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold">Ejecuciones</h1>
            <p className="mt-1 text-sm text-label">Bitácora de ejecuciones de aprovisionamiento en tu alcance.</p>
          </div>
          <JobsLog />
        </div>
      </RequireRole>
    </AppShell>
  );
}
