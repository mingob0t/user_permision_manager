/**
 * FNC-034 (H-14): semántica accesible.
 * - Áreas: Editar, Administradores y Eliminar nombran el área.
 * - Notificaciones: el tipo tiene texto accesible (no solo color y glifo).
 * - `th scope="col"` y columna de acciones con texto: ya probados con `DataTable`
 *   (componentes-comunes.test.tsx) y Administrar plataformas (platform-admin.test.tsx).
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Area, AppNotification } from '@/lib/types';

vi.mock('@/lib/api', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/lib/api')>();
  return {
    ApiError: real.ApiError,
    api: {
      areas: vi.fn(), users: vi.fn(), notifications: vi.fn(),
      markNotificationsRead: vi.fn(), clearNotifications: vi.fn(),
    },
  };
});
vi.mock('@/lib/access/users', () => ({ usersApi: { setManagedAreas: vi.fn() } }));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      role: 'administrador',
      managed_areas: [],
      permissions: { is_admin: true, is_area_admin: false, can_manage_areas: true, can_manage_system: true },
    },
  }),
}));

import { api } from '@/lib/api';
import { AreasList } from '@/components/areas-list';
import { NotificationsList } from '@/components/notifications-list';

const AREA: Area = {
  id: 3, name: 'Finanzas', description: null, icon: 'box', color: '', status: 'Activo',
  platforms_count: 0, users_count: 0,
};

function aviso(id: number, type: AppNotification['type'], title: string): AppNotification {
  return { id, type, title, message: 'Detalle', is_read: false, time: 'hace 1 min', timestamp: '' };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.areas).mockResolvedValue([AREA]);
  vi.mocked(api.users).mockResolvedValue([]);
});

afterEach(cleanup);

describe('FNC-034: nombres accesibles contextuales', () => {
  it('Áreas: Editar, Administradores y Eliminar llevan el nombre del área', async () => {
    render(<AreasList />);
    for (const nombre of ['Editar Finanzas', 'Administradores de Finanzas', 'Eliminar Finanzas']) {
      expect(await screen.findByRole('button', { name: nombre })).toBeTruthy();
    }
  });
});

describe('FNC-034: tipo de notificación con texto', () => {
  it('cada tipo antepone su texto oculto al título y el glifo sigue oculto', async () => {
    vi.mocked(api.notifications).mockResolvedValue([
      aviso(1, 'success', 'Copia lista'),
      aviso(2, 'error', 'Falló el envío'),
      aviso(3, 'warning', 'Cuota alta'),
      aviso(4, 'info', 'Nueva versión'),
    ]);
    render(<NotificationsList />);
    await screen.findByText('Copia lista');
    const esperado: Array<[string, string]> = [
      ['Copia lista', 'Éxito'],
      ['Falló el envío', 'Error'],
      ['Cuota alta', 'Advertencia'],
      ['Nueva versión', 'Información'],
    ];
    for (const [titulo, tipo] of esperado) {
      const p = screen.getByText(titulo, { exact: false }).closest('p') as HTMLElement;
      expect(p.textContent).toBe(`${tipo}: ${titulo}`);
      expect(p.querySelector('span.sr-only')?.textContent).toBe(`${tipo}: `);
      expect(p.closest('div.flex.gap-3')?.querySelector('[aria-hidden="true"]')).toBeTruthy();
    }
  });

  it('un tipo desconocido cae en Información', async () => {
    vi.mocked(api.notifications).mockResolvedValue([
      aviso(9, 'otro' as AppNotification['type'], 'Raro'),
    ]);
    render(<NotificationsList />);
    const p = (await screen.findByText('Raro', { exact: false })).closest('p') as HTMLElement;
    expect(p.textContent).toBe('Información: Raro');
  });
});
