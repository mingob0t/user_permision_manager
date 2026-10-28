import { AppShell } from '@/components/app-shell';
import { PageHeader } from '@/components/page-header';
import { PlatformsView } from '@/components/platforms-view';

/**
 * Plataformas: encabezado con PageHeader y una sola vista (DIS-030) con el catálogo
 * solicitable, el enlace y el favorito de cada plataforma.
 */
export default function Page() {
  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Plataformas"
          description="Catálogo de plataformas disponibles y accesos directos."
        />
        <PlatformsView />
      </div>
    </AppShell>
  );
}

