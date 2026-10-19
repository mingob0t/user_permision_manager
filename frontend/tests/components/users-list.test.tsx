/**
 * Regresión de FNC-069 sobre `UsersList`: tras FNC-044 el backend rechaza
 * `auth_source` y `managed_area_ids` en `POST/PUT /users` (`400
 * campo_no_permitido`). El alta ya no los envía y las áreas administradas
 * van por `PUT /users/<id>/managed-areas`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Area, ManagedUser } from '@/lib/types';

vi.mock('@/lib/api', () => ({
  api: {
    users: vi.fn(), areas: vi.fn(), platforms: vi.fn(),
    createUser: vi.fn(), updateUser: vi.fn(), setUserAreas: vi.fn(),
    setUserPlatforms: vi.fn(), searchDirectory: vi.fn(),
  },
}));
vi.mock('@/lib/access/users', () => ({ usersApi: { setManagedAreas: vi.fn() } }));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    session: { permissions: { is_admin: true, is_area_admin: false } },
  }),
}));

import { api } from '@/lib/api';
import { usersApi } from '@/lib/access/users';
import { UsersList } from '@/components/users-list';

const AREAS = [{ id: 3, name: 'Finanzas' }, { id: 7, name: 'TI' }] as Area[];
const ADMIN_AREA: ManagedUser = {
  id: 5, email: 'luis@ejemplo.local', name: 'Luis Paz', role: 'admin_area', is_active: true,
  auth_source: 'local', areas: [], managed_areas: [{ id: 3, name: 'Finanzas' }],
  last_login_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.users).mockResolvedValue([ADMIN_AREA]);
  vi.mocked(api.areas).mockResolvedValue(AREAS);
  vi.mocked(api.platforms).mockResolvedValue([]);
  vi.mocked(api.createUser).mockResolvedValue({ status: 'success', id: 9 });
  vi.mocked(api.updateUser).mockResolvedValue({ status: 'success' });
  vi.mocked(api.setUserAreas).mockResolvedValue({ status: 'success', areas: [] });
  vi.mocked(api.searchDirectory).mockResolvedValue({
    count: 1, users: [{ name: 'Eva Mora', email: 'eva@ejemplo.local', account: 'eva', exists: false }],
  });
  vi.mocked(usersApi.setManagedAreas).mockResolvedValue(
    { status: 'success', user: ADMIN_AREA });
});

afterEach(() => {
  cleanup();
});

function dialogo() {
  return within(screen.getByRole('dialog'));
}

describe('UsersList: alta y edición con las reglas de FNC-044', () => {
  it('alta de admin de área: sin auth_source ni managed_area_ids; áreas por managed-areas', async () => {
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Nuevo usuario'));

    const modal = dialogo();
    fireEvent.change(modal.getByLabelText('Correo'), { target: { value: 'nuevo@ejemplo.local' } });
    fireEvent.change(modal.getByLabelText('Rol'), { target: { value: 'admin_area' } });
    const administra = within(modal.getByText('Áreas que administra').closest('label')!);
    fireEvent.click(administra.getByText('TI'));
    fireEvent.click(modal.getByText('Guardar'));

    await waitFor(() => expect(usersApi.setManagedAreas).toHaveBeenCalledWith(9, [7]));
    const enviado = vi.mocked(api.createUser).mock.calls[0][0];
    expect(enviado).not.toHaveProperty('auth_source');
    expect(enviado).not.toHaveProperty('managed_area_ids');
    expect(api.updateUser).not.toHaveBeenCalled();
  });

  it('edición de admin de área: updateUser sin managed_area_ids y managed-areas aparte', async () => {
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Editar'));
    fireEvent.click(dialogo().getByText('Guardar'));

    await waitFor(() => expect(usersApi.setManagedAreas).toHaveBeenCalledWith(5, [3]));
    expect(vi.mocked(api.updateUser).mock.calls[0][1]).not.toHaveProperty('managed_area_ids');
  });

  it('alta desde el directorio: no crea una cuenta local y lo explica', async () => {
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Buscar en directorio'));
    fireEvent.change(dialogo().getByPlaceholderText('Nombre, cuenta o correo'),
      { target: { value: 'eva' } });
    fireEvent.click(dialogo().getByText('Buscar'));
    fireEvent.click(await screen.findByText('Dar de alta'));
    fireEvent.click(dialogo().getByText('Guardar'));

    expect(await screen.findByText(
      'El alta de cuentas del directorio aún no está disponible en el portal.')).toBeTruthy();
    expect(api.createUser).not.toHaveBeenCalled();
  });
});
