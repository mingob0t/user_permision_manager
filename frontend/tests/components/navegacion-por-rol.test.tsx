/**
 * FNC-070: menú y guarda de ruta por rol (tabla de pantallas, REQUERIMIENTOS §4).
 */
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import { useEffect } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Session } from '@/lib/types';

vi.mock('next/navigation', () => ({ usePathname: () => '/' }));
vi.mock('@/lib/api', () => ({
  api: { session: vi.fn() },
  ApiError: class ApiError extends Error {},
}));

import { api } from '@/lib/api';
import { AppShell } from '@/components/app-shell';
import { FORBIDDEN_MESSAGE, RequireRole, type RoleRequirement } from '@/components/require-role';

const sesionSimulada = vi.mocked(api.session);

type Rol = 'usuario' | 'admin_area' | 'administrador';

function sesion(rol: Rol): Session {
  return {
    id: 1,
    email: 'ana@ejemplo.test',
    name: 'Ana',
    role: rol,
    auth_source: 'local',
    areas: [],
    managed_areas: [],
    permissions: {
      is_admin: rol === 'administrador',
      is_area_admin: rol === 'admin_area',
      can_manage_areas: rol !== 'usuario',
      can_manage_system: rol === 'administrador',
    },
    preferences: {
      notifications: true, email_notifications: false, refresh_interval: 60, tour_enabled: false,
    },
  };
}

const COMUNES = ['Panel', 'Catálogo', 'Favoritos', 'Notificaciones', 'Auditoría', 'Ajustes'];

const ESPERADO: Record<Rol, string[]> = {
  usuario: [...COMUNES, 'Mis solicitudes'],
  admin_area: [
    ...COMUNES, 'Mis solicitudes', 'Aprobaciones', 'Administrar plataformas', 'Áreas', 'Usuarios',
    'Inventario', 'Ejecuciones',
  ],
  administrador: [
    ...COMUNES, 'Aprobaciones', 'Administrar plataformas', 'Áreas', 'Usuarios', 'Conectores',
    'Inventario', 'Ejecuciones',
  ],
};

afterEach(() => {
  cleanup();
  sesionSimulada.mockReset();
});

describe('Menú por rol', () => {
  it.each(Object.keys(ESPERADO) as Rol[])('%s ve exactamente sus entradas', async (rol) => {
    sesionSimulada.mockResolvedValue(sesion(rol));
    render(<AppShell>contenido</AppShell>);

    const nav = await screen.findByRole('navigation', { name: 'Principal' });
    const entradas = within(nav).getAllByRole('link').map((a) => a.textContent);
    expect([...entradas].sort()).toEqual([...ESPERADO[rol]].sort());
  });
});

describe('RequireRole', () => {
  const casos: [RoleRequirement, Rol, boolean][] = [
    ['admin', 'usuario', false],
    ['admin', 'admin_area', false],
    ['admin', 'administrador', true],
    ['any_admin', 'usuario', false],
    ['any_admin', 'admin_area', true],
    ['any_admin', 'administrador', true],
    ['requester', 'usuario', true],
    ['requester', 'admin_area', true],
    ['requester', 'administrador', false],
  ];

  it.each(casos)('exige %s; %s → permitido: %s', async (requisito, rol, permitido) => {
    sesionSimulada.mockResolvedValue(sesion(rol));
    const llamadaApi = vi.fn();

    function Pantalla() {
      useEffect(() => { llamadaApi(); }, []);
      return <p>pantalla protegida</p>;
    }

    render(
      <AppShell>
        <RequireRole requires={requisito}>
          <Pantalla />
        </RequireRole>
      </AppShell>,
    );
    await screen.findByRole('navigation', { name: 'Principal' });

    if (permitido) {
      expect(await screen.findByText('pantalla protegida')).toBeTruthy();
      await waitFor(() => expect(llamadaApi).toHaveBeenCalledTimes(1));
    } else {
      expect(screen.getByRole('alert').textContent).toBe(FORBIDDEN_MESSAGE);
      expect(screen.queryByText('pantalla protegida')).toBeNull();
      expect(llamadaApi).not.toHaveBeenCalled();
    }
  });
});
