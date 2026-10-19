'use client';

/** Marco de la aplicación: navegación lateral y cabecera con la sesión. */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { meetsRequirement, type RoleRequirement } from './require-role';
import { SessionProvider, useSession } from './session-provider';
import { ErrorNote, Spinner } from './ui';

interface NavItem {
  href: string;
  label: string;
  /** Permiso mínimo; sin él el enlace no se muestra. */
  requires?: RoleRequirement;
}

/** Entradas por rol según la tabla de pantallas (REQUERIMIENTOS §4, FNC-070). */
const NAV: NavItem[] = [
  { href: '/', label: 'Panel' },
  { href: '/platforms', label: 'Catálogo' },
  { href: '/requests', label: 'Mis solicitudes', requires: 'requester' },
  { href: '/favorites', label: 'Favoritos' },
  { href: '/notifications', label: 'Notificaciones' },
  { href: '/approvals', label: 'Aprobaciones', requires: 'any_admin' },
  { href: '/admin/platforms', label: 'Administrar plataformas', requires: 'any_admin' },
  { href: '/areas', label: 'Áreas', requires: 'any_admin' },
  { href: '/users', label: 'Usuarios', requires: 'any_admin' },
  { href: '/inventory', label: 'Inventario' },
  { href: '/audit', label: 'Auditoría' },
  { href: '/admin/connectors', label: 'Conectores', requires: 'admin' },
  { href: '/settings', label: 'Ajustes' },
];

function Nav() {
  const { session } = useSession();
  const pathname = usePathname();
  if (!session) return null;

  const visible = NAV.filter((item) =>
    meetsRequirement(item.requires, session.permissions),
  );

  return (
    <nav className="flex flex-col gap-1" aria-label="Principal">
      {visible.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? 'page' : undefined}
            className={`rounded-lg px-3 py-2 text-sm transition-colors ${
              active
                ? 'bg-primary/15 font-medium text-primary-text'
                : 'text-label hover:bg-surface-container hover:text-body-text'
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function RoleLabel({ role }: { role: string }) {
  const labels: Record<string, string> = {
    administrador: 'Administrador global',
    admin_area: 'Administrador de área',
    usuario: 'Usuario',
  };
  return <>{labels[role] ?? role}</>;
}

function Frame({ children }: { children: React.ReactNode }) {
  const { session, loading, error } = useSession();

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center">
        <Spinner label="Cargando sesión…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-lg p-8">
        <ErrorNote message={error} />
      </div>
    );
  }

  if (!session) return null;

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 border-r border-panel-border bg-panel-fill p-4 md:block">
        <p className="px-3 pb-4 text-lg font-semibold">Nexus</p>
        <Nav />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-panel-border bg-panel-fill px-6 py-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{session.name}</p>
            <p className="truncate text-xs text-label">
              <RoleLabel role={session.role} />
              {session.managed_areas.length > 0
                ? ` · ${session.managed_areas.length} área(s)`
                : ''}
            </p>
          </div>
          <a
            href="/logout"
            className="rounded-lg border border-panel-border px-3 py-1.5 text-sm text-label hover:text-body-text"
          >
            Salir
          </a>
        </header>

        <main className="min-w-0 flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <Frame>{children}</Frame>
    </SessionProvider>
  );
}
