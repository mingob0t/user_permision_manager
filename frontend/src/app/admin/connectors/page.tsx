import { AppShell } from '@/components/app-shell';
import { RequireRole } from '@/components/require-role';
import { EmptyNote } from '@/components/ui';

/** Ruta reservada por FNC-070; el contenido llega con DIS-022. */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="admin">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold">Conectores</h1>
            <p className="mt-1 text-sm text-label">Configuración de conectores y bitácora de ejecuciones.</p>
          </div>
          <EmptyNote message="Esta sección todavía no está disponible." />
        </div>
      </RequireRole>
    </AppShell>
  );
}
