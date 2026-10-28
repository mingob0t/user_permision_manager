import { AppShell } from '@/components/app-shell';
import { JobsLog } from '@/components/connectors/jobs-log';
import { PageHeader } from '@/components/page-header';
import { RequireRole } from '@/components/require-role';

/** Bitácora de ejecuciones para el admin de área (DIS-041); guarda `any_admin`, solo lectura. */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="any_admin">
        <div className="space-y-6">
          <PageHeader
            title="Ejecuciones"
            description="Bitácora de ejecuciones de aprovisionamiento en tu alcance."
          />
          <JobsLog />
        </div>
      </RequireRole>
    </AppShell>
  );
}
