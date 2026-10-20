import { RequestCatalog } from '@/components/access/request-catalog';
import { AppShell } from '@/components/app-shell';
import { PlatformCatalog } from '@/components/platform-catalog';

/** Catálogo solicitable (DIS-013) y, debajo, las plataformas que ya puede abrir. */
export default function Page() {
  return (
    <AppShell>
      <div className="space-y-10">
        <RequestCatalog />
        <PlatformCatalog />
      </div>
    </AppShell>
  );
}
