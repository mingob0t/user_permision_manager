import { AppShell } from '@/components/app-shell';
import { EmptyNote } from '@/components/ui';

/**
 * Ruta reservada por FNC-070; el contenido llega con DIS-021.
 * Visible para todos: el backend limita el alcance por rol.
 */
export default function Page() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Inventario</h1>
          <p className="mt-1 text-sm text-label">Permisos vigentes dentro de tu alcance.</p>
        </div>
        <EmptyNote message="Esta sección todavía no está disponible." />
      </div>
    </AppShell>
  );
}
