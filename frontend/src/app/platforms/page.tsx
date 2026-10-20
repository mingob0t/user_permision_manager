import { RequestCatalog } from '@/components/access/request-catalog';
import { AppShell } from '@/components/app-shell';
import { PlatformCatalog } from '@/components/platform-catalog';

/**
 * Plataformas: `h1` de la página y dos secciones hermanas con `h2`, el
 * catálogo solicitable (DIS-013) y las plataformas que ya puede abrir.
 */
export default function Page() {
  return (
    <AppShell>
      <div className="space-y-10">
        <h1 className="text-2xl font-semibold">Plataformas</h1>
        <RequestCatalog />
        <PlatformCatalog />
      </div>
    </AppShell>
  );
}
