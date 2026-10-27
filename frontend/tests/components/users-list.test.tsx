/**
 * Regresión de FNC-069 sobre `UsersList`: tras FNC-044 el backend rechaza
 * `auth_source` y `managed_area_ids` en `POST/PUT /users` (`400
 * campo_no_permitido`).
 *
 * DIS-019: "Nuevo usuario" abre el alta en el directorio (`POST /users/directory`)
 * y la edición ya no ofrece rol, áreas administradas ni contraseña (salvo la
 * cuenta de emergencia); el rol cambia con "Hacer admin" / "Quitar admin"
 * (pruebas en `users/admin-role-dialog.test.tsx`).
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Area, ManagedUser } from '@/lib/types';

vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: {
    users: vi.fn(), areas: vi.fn(), platforms: vi.fn(),
    createUser: vi.fn(), updateUser: vi.fn(), setUserAreas: vi.fn(),
    setUserPlatforms: vi.fn(), searchDirectory: vi.fn(),
  },
}));
vi.mock('@/lib/access/users', () => ({
  usersApi: { setManagedAreas: vi.fn(), createDirectoryAccount: vi.fn() },
}));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    session: { managed_areas: [], permissions: { is_admin: true, is_area_admin: false } },
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
const EMERGENCIA: ManagedUser = {
  ...ADMIN_AREA, id: 1, email: 'admin', name: 'Emergencia', role: 'administrador', managed_areas: [],
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

describe('UsersList: alta y edición con las reglas de FNC-044 y DIS-019', () => {
  it('"Nuevo usuario" abre el alta en el directorio, sin contraseña ni rol, y no crea cuentas locales', async () => {
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Nuevo usuario'));

    const modal = dialogo();
    expect(modal.getByText('Nueva cuenta en el directorio')).toBeTruthy();
    expect(modal.getByLabelText('Identificador')).toBeTruthy();
    expect(modal.queryByLabelText(/Contraseña/)).toBeNull();
    expect(modal.queryByLabelText('Rol')).toBeNull();
    expect(api.createUser).not.toHaveBeenCalled();
  });

  it('edición: sin rol, áreas administradas ni contraseña; no envía role ni managed_area_ids', async () => {
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Editar'));
    const modal = dialogo();
    expect(modal.queryByLabelText('Rol')).toBeNull();
    expect(modal.queryByText('Áreas que administra')).toBeNull();
    expect(modal.queryByLabelText(/Contraseña/)).toBeNull();
    fireEvent.click(modal.getByText('Guardar'));

    await waitFor(() => expect(api.updateUser).toHaveBeenCalled());
    const enviado = vi.mocked(api.updateUser).mock.calls[0][1];
    expect(enviado).not.toHaveProperty('role');
    expect(enviado).not.toHaveProperty('managed_area_ids');
    expect(enviado).not.toHaveProperty('password');
    expect(usersApi.setManagedAreas).not.toHaveBeenCalled();
  });

  it('DIS-008: acciones de fila y chips de áreas de 48 px con foco visible', async () => {
    render(<UsersList />);
    await screen.findByText('Luis Paz');
    const acciones = ['Editar', 'Accesos de Luis Paz', 'Eliminar', 'Áreas que administra Luis Paz', 'Quitar admin de área a Luis Paz']
      .map((nombre) => screen.getByRole('button', { name: nombre }));
    for (const accion of acciones) {
      expect(accion.className).toContain('min-h-12');
      expect(accion.className).toContain('min-w-12');
      expect(accion.className).toContain('focus-visible:ring-primary');
    }
    fireEvent.click(acciones[0]);
    // 'TI': el primer chip toma el nombre de la etiqueta de `Field` (propuesta DIS-045).
    const chip = await dialogo().findByRole('button', { name: 'TI' });
    expect(chip.getAttribute('aria-pressed')).toBe('false');
    expect(chip.className).toContain('min-h-12');
    expect(chip.className).toContain('focus-visible:ring-primary');
  });

  it('edición de la cuenta de emergencia (superadmin local): ofrece la contraseña', async () => {
    vi.mocked(api.users).mockResolvedValue([EMERGENCIA]);
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Editar'));
    expect(dialogo().getByLabelText(/^Contraseña/)).toBeTruthy();
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
