/**
 * DIS-019: elevación a admin de área (contrato `areas-y-roles.md` 2.1).
 * - Solo el superadmin ve "Hacer admin", "Áreas admin" y "Quitar admin"; el
 *   admin de área no ve opciones de rol (criterio de aceptación).
 * - Hacer admin: `PUT /users/<id>` con `admin_area` y luego `managed-areas`;
 *   al menos un área; el efecto nombra las áreas antes de confirmar.
 * - Fallo del segundo paso: se explica y se recarga la lista.
 * - Quitar admin: `role: usuario` con el efecto explicado.
 * - Errores del contrato sin texto del servidor; `aria-disabled` al enviar.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AreaRef, ManagedUser } from '@/lib/types';

vi.mock('@/lib/access/users', () => ({
  usersApi: { setManagedAreas: vi.fn(), createDirectoryAccount: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { users: vi.fn(), areas: vi.fn(), platforms: vi.fn(), updateUser: vi.fn() },
}));

let esSuperadmin = true;
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    session: {
      managed_areas: [{ id: 3, name: 'Finanzas' }],
      permissions: { is_admin: esSuperadmin, is_area_admin: !esSuperadmin },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { usersApi } from '@/lib/access/users';
import { UsersList } from '@/components/users-list';
import {
  AdminAreasDialog, RemoveAdminDialog, efectoAdmin,
} from '@/components/users/admin-role-dialog';
import { MENSAJE_SIN_AREAS, describeRoleError } from '@/components/users/admin-role-errors';

const AREAS: AreaRef[] = [{ id: 3, name: 'Finanzas' }, { id: 7, name: 'TI' }];
const ANA: ManagedUser = {
  id: 8, email: 'ana@ejemplo.local', name: 'Ana Ruiz', role: 'usuario', is_active: true,
  auth_source: 'ldap', areas: [], managed_areas: [], last_login_at: null,
};
const LUIS: ManagedUser = {
  ...ANA, id: 5, email: 'luis@ejemplo.local', name: 'Luis Paz', role: 'admin_area',
  managed_areas: [{ id: 3, name: 'Finanzas' }],
};
const JEFA: ManagedUser = { ...ANA, id: 1, name: 'Jefa', role: 'administrador' };

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = true;
  vi.mocked(api.updateUser).mockResolvedValue({ status: 'success' });
  vi.mocked(usersApi.setManagedAreas).mockResolvedValue({ status: 'success', user: LUIS });
});

afterEach(() => {
  cleanup();
});

function elevar(user = ANA) {
  const props = { onClose: vi.fn(), onSaved: vi.fn(), onStale: vi.fn() };
  render(<AdminAreasDialog user={user} areas={AREAS} {...props} />);
  return props;
}

describe('AdminAreasDialog: hacer admin', () => {
  it('sin área no envía, explica y enfoca la primera casilla', () => {
    elevar();
    fireEvent.click(screen.getByText('Hacer admin'));
    expect(api.updateUser).not.toHaveBeenCalled();
    expect(screen.getByText(MENSAJE_SIN_AREAS)).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText('Finanzas'));
  });

  it('explica el efecto con las áreas y luego cambia rol y áreas, en ese orden', async () => {
    const { onSaved } = elevar();
    fireEvent.click(screen.getByLabelText('TI'));
    expect(screen.getByText('Ana Ruiz pasará a ser admin de área de: TI.')).toBeTruthy();
    expect(screen.getByText(/Podrá aprobar y rechazar solicitudes/)).toBeTruthy();
    fireEvent.click(screen.getByText('Hacer admin'));

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith('Ana Ruiz ahora es admin de área de: TI.'));
    expect(api.updateUser).toHaveBeenCalledWith(8, { role: 'admin_area' });
    expect(usersApi.setManagedAreas).toHaveBeenCalledWith(8, [7]);
    expect(vi.mocked(api.updateUser).mock.invocationCallOrder[0])
      .toBeLessThan(vi.mocked(usersApi.setManagedAreas).mock.invocationCallOrder[0]);
  });

  it('si falla la asignación de áreas tras el rol: lo explica y recarga', async () => {
    vi.mocked(usersApi.setManagedAreas).mockRejectedValue(new ApiError(500, 'servidor'));
    const { onSaved, onStale } = elevar();
    fireEvent.click(screen.getByLabelText('Finanzas'));
    fireEvent.click(screen.getByText('Hacer admin'));
    expect(await screen.findByText(/Ana Ruiz ya es admin de área, pero no se asignaron sus áreas/))
      .toBeTruthy();
    expect(onStale).toHaveBeenCalled();
    expect(onSaved).not.toHaveBeenCalled();
    expect(screen.queryByText('servidor')).toBeNull();
  });

  it('403 operacion_propia en el rol: mensaje del contrato y no asigna áreas', async () => {
    vi.mocked(api.updateUser).mockRejectedValue(
      new ApiError(403, 'servidor', { code: 'operacion_propia' }));
    elevar();
    fireEvent.click(screen.getByLabelText('Finanzas'));
    fireEvent.click(screen.getByText('Hacer admin'));
    expect(await screen.findByText('No puedes cambiar tu propio rol.')).toBeTruthy();
    expect(usersApi.setManagedAreas).not.toHaveBeenCalled();
  });

  it('durante el envío el botón queda aria-disabled y no reenvía', async () => {
    vi.mocked(api.updateUser).mockReturnValue(new Promise(() => {}));
    elevar();
    fireEvent.click(screen.getByLabelText('Finanzas'));
    fireEvent.click(screen.getByText('Hacer admin'));
    const boton = await screen.findByText('Guardando…');
    expect(boton.getAttribute('aria-disabled')).toBe('true');
    fireEvent.click(boton);
    expect(api.updateUser).toHaveBeenCalledTimes(1);
  });
});

describe('AdminAreasDialog: cambiar áreas de un admin', () => {
  it('solo managed-areas, con lo que agrega y lo que quita', async () => {
    const { onSaved } = elevar(LUIS);
    fireEvent.click(screen.getByLabelText('Finanzas'));
    fireEvent.click(screen.getByLabelText('TI'));
    expect(screen.getByText(/Empezará a administrar: TI/)).toBeTruthy();
    expect(screen.getByText(/Dejará de administrar: Finanzas/)).toBeTruthy();
    fireEvent.click(screen.getByText('Guardar áreas'));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(api.updateUser).not.toHaveBeenCalled();
    expect(usersApi.setManagedAreas).toHaveBeenCalledWith(5, [7]);
  });

  it('409 rol_no_admin: mensaje y recarga', async () => {
    vi.mocked(usersApi.setManagedAreas).mockRejectedValue(
      new ApiError(409, 'servidor', { code: 'rol_no_admin' }));
    const { onStale } = elevar(LUIS);
    fireEvent.click(screen.getByText('Guardar áreas'));
    expect(await screen.findByText('La cuenta ya no es administradora de área. La lista se actualizó.'))
      .toBeTruthy();
    expect(onStale).toHaveBeenCalled();
  });

  it('efectoAdmin: sin cambios', () => {
    expect(efectoAdmin(LUIS, AREAS, [3])).toEqual(['Sin cambios en sus áreas.']);
    expect(efectoAdmin(ANA, AREAS, [])).toEqual([]);
  });
});

describe('RemoveAdminDialog', () => {
  it('explica el efecto y envía role usuario', async () => {
    const props = { onClose: vi.fn(), onSaved: vi.fn(), onStale: vi.fn() };
    render(<RemoveAdminDialog user={LUIS} {...props} />);
    expect(screen.getByText('Luis Paz volverá a ser Usuario y dejará de administrar: Finanzas.'))
      .toBeTruthy();
    expect(screen.getByText(/Se revocarán sus accesos automáticos/)).toBeTruthy();
    fireEvent.click(screen.getByText('Quitar admin'));
    await waitFor(() => expect(props.onSaved).toHaveBeenCalledWith('Luis Paz ya no es admin de área.'));
    expect(api.updateUser).toHaveBeenCalledWith(5, { role: 'usuario' });
  });

  it('404: mensaje y recarga', async () => {
    vi.mocked(api.updateUser).mockRejectedValue(new ApiError(404, 'servidor'));
    const props = { onClose: vi.fn(), onSaved: vi.fn(), onStale: vi.fn() };
    render(<RemoveAdminDialog user={LUIS} {...props} />);
    fireEvent.click(screen.getByText('Quitar admin'));
    expect(await screen.findByText('La cuenta ya no está en tu alcance. La lista se actualizó.'))
      .toBeTruthy();
    expect(props.onStale).toHaveBeenCalled();
  });
});

describe('describeRoleError', () => {
  it('mensajes por código y estado, sin texto del servidor', () => {
    expect(describeRoleError(new ApiError(403, 's', { code: 'rol_reservado' })).message)
      .toBe('Ese rol no se puede asignar.');
    expect(describeRoleError(new ApiError(403, 's')).message)
      .toBe('Solo el superadmin cambia roles y áreas administradas.');
    expect(describeRoleError(new ApiError(422, 's', { code: 'validacion' })).stale).toBe(true);
    expect(describeRoleError(new Error('s')).message)
      .toBe('No se pudo guardar el cambio. Inténtalo de nuevo.');
  });
});

describe('UsersList: acciones de rol', () => {
  beforeEach(() => {
    vi.mocked(api.users).mockResolvedValue([ANA, LUIS, JEFA]);
    vi.mocked(api.areas).mockResolvedValue(AREAS as never);
    vi.mocked(api.platforms).mockResolvedValue([]);
  });

  it('admin de área: no ve opciones de rol', async () => {
    esSuperadmin = false;
    render(<UsersList />);
    await screen.findByText('Ana Ruiz');
    expect(screen.queryByText('Hacer admin')).toBeNull();
    expect(screen.queryByText('Áreas admin')).toBeNull();
    expect(screen.queryByText('Quitar admin')).toBeNull();
  });

  it('superadmin: Hacer admin para usuario, Áreas admin y Quitar admin para admin, nada para sí', async () => {
    render(<UsersList />);
    await screen.findByText('Ana Ruiz');
    expect(screen.getByRole('button', { name: 'Hacer admin de área a Ana Ruiz' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Áreas admin de Luis Paz' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Quitar admin de área a Luis Paz' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Accesos de Jefa' })).toBeTruthy(); // "Accesos de Jefa"
    expect(screen.queryByRole('button', { name: 'Hacer admin de área a Jefa' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Quitar admin de área a Jefa' })).toBeNull();
  });

  it('el diálogo no pierde el foco cuando la pantalla se vuelve a renderizar', async () => {
    let resolverAreas: (v: AreaRef[]) => void = () => {};
    vi.mocked(api.areas).mockReturnValue(new Promise((r) => { resolverAreas = r; }) as never);
    render(<UsersList />);
    fireEvent.click(await screen.findByRole('button', { name: 'Hacer admin de área a Ana Ruiz' }));
    const cancelar = within(screen.getByRole('dialog')).getByText('Cancelar');
    cancelar.focus();
    // Llegan las áreas: `UsersList` se vuelve a renderizar con el diálogo abierto.
    resolverAreas(AREAS);
    expect(await screen.findByLabelText('Finanzas')).toBeTruthy();
    expect(document.activeElement).toBe(cancelar);
  });

  it('Hacer admin: aviso con foco y recarga; Cancelar devuelve el foco al botón', async () => {
    render(<UsersList />);
    const boton = await screen.findByRole('button', { name: 'Hacer admin de área a Ana Ruiz' });
    fireEvent.click(boton);
    fireEvent.click(within(screen.getByRole('dialog')).getByText('Cancelar'));
    expect(document.activeElement).toBe(boton);

    fireEvent.click(boton);
    const modal = within(screen.getByRole('dialog'));
    fireEvent.click(modal.getByLabelText('Finanzas'));
    fireEvent.click(modal.getByText('Hacer admin'));
    const aviso = await screen.findByText('Ana Ruiz ahora es admin de área de: Finanzas.');
    await waitFor(() => expect(document.activeElement).toBe(aviso.closest('[role="status"]')));
    expect(api.users).toHaveBeenCalledTimes(2);
  });
});
