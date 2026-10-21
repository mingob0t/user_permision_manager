import { AppShell } from '@/components/app-shell';
import { Inventory } from '@/components/access/inventory';
import { RequireRole } from '@/components/require-role';

/**
 * Inventario de permisos (DIS-021): admin de área (sus áreas) y superadmin
 * (todo). El usuario recibe 403 del backend; aquí ve "sin permiso".
 */
export default function Page() {
  return (
    <AppShell>
      <RequireRole requires="any_admin">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold">Inventario</h1>
            <p className="mt-1 text-sm text-label">
              Quién tiene qué plataforma, con qué nivel, desde cuándo y quién lo aprobó, en tus
              áreas (todas, si eres superadmin).
            </p>
          </div>
          <Inventory />
        </div>
      </RequireRole>
    </AppShell>
  );
}
