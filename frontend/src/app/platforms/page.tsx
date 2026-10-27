import { AppShell } from '@/components/app-shell';
import { PlatformsView } from '@/components/platforms-view';

/**
 * Plataformas: `h1` de la página y una sola vista (DIS-030) con el catálogo
 * solicitable, el enlace y el favorito de cada plataforma.
 */
export default function Page() {
  return (
    <AppShell>
      <div className="space-y-10">
        <h1 className="text-2xl font-semibold">Plataformas</h1>
        <PlatformsView />
      </div>
    </AppShell>
  );
}
