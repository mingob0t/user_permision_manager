/**
 * DIS-016: pantalla `/areas` por rol (`docs/contratos/areas-y-roles.md` v2).
 * - Admin de área: "Nueva área", gestiona solo las suyas, sin panel de admins.
 * - Superadmin: todas las áreas y "Administradores del área" (managed-areas).
 * - Errores: `422` con `fields` por campo y mensajes de los `409`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Area, ManagedUser, Session } from '@/lib/types';

vi.mock('@/lib/api', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/lib/api')>();
  return {
    ApiError: real.ApiError,
    api: { areas: vi.fn(), users: vi.fn(), createArea: vi.fn(), updateArea: vi.fn(), deleteArea: vi.fn() },
  };
});
vi.mock('@/lib/access/users', () => ({ usersApi: { setManagedAreas: vi.fn() } }));

type Rol = Session['role'];
let rolActual: Rol = 'administrador';
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      role: rolActual,
      managed_areas: rolActual === 'admin_area' ? [{ id: 3, name: 'Finanzas' }] : [],
      permissions: {
        is_admin: rolActual === 'administrador',
        is_area_admin: rolActual === 'admin_area',
        // Como en el backend hoy (FNC-045): solo el superadmin.
        can_manage_areas: rolActual === 'administrador',
        can_manage_system: rolActual === 'administrador',
      },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { usersApi } from '@/lib/access/users';
import { AreasList } from '@/components/areas-list';
import { FORBIDDEN_MESSAGE } from '@/components/require-role';

/** El color no interviene en estas pruebas: va vacío. */
function area(id: number, name: string): Area {
  return {
    id, name, description: null, icon: 'box', color: '', status: 'Activo',
    platforms_count: 0, users_count: 0,
  };
}

const FINANZAS = area(3, 'Finanzas');
const SISTEMAS = area(7, 'Sistemas');

function usuario(id: number, name: string, role: Rol, managed: number[]): ManagedUser {
  return {
    id, name, email: `${name.toLowerCase()}@ejemplo.local`, role, is_active: true,
    auth_source: 'ldap', areas: [], last_login_at: null,
    managed_areas: managed.map((m) => ({ id: m, name: `Área ${m}` })),
  };
}

const LUIS = usuario(5, 'Luis', 'admin_area', [3]);
const EVA = usuario(6, 'Eva', 'admin_area', [7]);
const ANA = usuario(8, 'Ana', 'usuario', []);

beforeEach(() => {
  vi.clearAllMocks();
  rolActual = 'administrador';
  vi.mocked(api.areas).mockResolvedValue([FINANZAS, SISTEMAS]);
  vi.mocked(api.users).mockResolvedValue([LUIS, EVA, ANA]);
  vi.mocked(api.createArea).mockResolvedValue({ status: 'success', area: area(9, 'Compras') });
  vi.mocked(api.deleteArea).mockResolvedValue({ status: 'success' });
  vi.mocked(usersApi.setManagedAreas).mockResolvedValue({ status: 'success', user: LUIS });
});

afterEach(() => {
  cleanup();
});

function dialogo() {
  return within(screen.getByRole('dialog'));
}

function tarjeta(nombre: string) {
  return within(screen.getByText(nombre).closest('div.rounded-xl') as HTMLElement);
}

describe('AreasList por rol', () => {
  it('usuario: estado sin permiso y no llama a la API', () => {
    rolActual = 'usuario';
    render(<AreasList />);
    expect(screen.getByText(FORBIDDEN_MESSAGE)).toBeTruthy();
    expect(api.areas).not.toHaveBeenCalled();
  });

  it('admin de área: ve "Nueva área", gestiona solo las suyas y no ve el panel de admins', async () => {
    rolActual = 'admin_area';
    render(<AreasList />);
    await screen.findByText('Sistemas');

    expect(screen.getByText('Nueva área')).toBeTruthy();
    expect(screen.queryByText('Administradores')).toBeNull();
    expect(tarjeta('Finanzas').getByText('Editar')).toBeTruthy();
    expect(tarjeta('Finanzas').getByText('Eliminar')).toBeTruthy();
    expect(tarjeta('Sistemas').queryByText('Editar')).toBeNull();
    expect(tarjeta('Sistemas').queryByText('Eliminar')).toBeNull();
  });

  it('admin de área: el alta no envía color y el área nueva queda gestionable', async () => {
    rolActual = 'admin_area';
    render(<AreasList />);
    fireEvent.click(await screen.findByText('Nueva área'));
    fireEvent.change(dialogo().getByLabelText('Nombre'), { target: { value: 'Compras' } });
    vi.mocked(api.areas).mockResolvedValue([FINANZAS, SISTEMAS, area(9, 'Compras')]);
    fireEvent.click(dialogo().getByText('Guardar'));

    await waitFor(() => expect(api.createArea).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.createArea).mock.calls[0][0]).not.toHaveProperty('color');
    await screen.findByText('Compras');
    expect(tarjeta('Compras').getByText('Editar')).toBeTruthy();
    expect(tarjeta('Compras').getByText('Administras')).toBeTruthy();
  });

  it('superadmin: ve todas las áreas y el botón Administradores en cada una', async () => {
    render(<AreasList />);
    await screen.findByText('Sistemas');
    expect(screen.getByText('Nueva área')).toBeTruthy();
    expect(screen.getAllByText('Administradores')).toHaveLength(2);
  });
});

describe('Administradores del área (superadmin)', () => {
  it('lista solo admin_area, busca y asigna con managed-areas', async () => {
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(tarjeta('Finanzas').getByText('Administradores'));

    const modal = dialogo();
    await modal.findByText('Luis · luis@ejemplo.local');
    expect(modal.queryByText(/Ana/)).toBeNull();
    expect((modal.getByLabelText('Luis · luis@ejemplo.local') as HTMLInputElement).checked).toBe(true);
    expect((modal.getByText('Guardar') as HTMLButtonElement).disabled).toBe(true);

    fireEvent.change(modal.getByLabelText('Buscar administrador'), { target: { value: 'eva' } });
    expect(modal.queryByText('Luis · luis@ejemplo.local')).toBeNull();
    fireEvent.click(modal.getByLabelText('Eva · eva@ejemplo.local'));
    fireEvent.click(modal.getByText('Guardar'));

    await waitFor(() => expect(usersApi.setManagedAreas).toHaveBeenCalledWith(6, [7, 3]));
    expect(await screen.findByText('Cambios guardados')).toBeTruthy();
  });

  it('quitar a un admin se confirma antes de guardar', async () => {
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(tarjeta('Finanzas').getByText('Administradores'));
    fireEvent.click(await dialogo().findByLabelText('Luis · luis@ejemplo.local'));
    fireEvent.click(dialogo().getByText('Guardar'));

    expect(dialogo().getByText(/Dejarán de administrar "Finanzas": Luis/)).toBeTruthy();
    expect(usersApi.setManagedAreas).not.toHaveBeenCalled();
    fireEvent.click(dialogo().getByText('Quitar'));
    await waitFor(() => expect(usersApi.setManagedAreas).toHaveBeenCalledWith(5, []));
  });

  it('sin cuentas admin_area: estado vacío', async () => {
    vi.mocked(api.users).mockResolvedValue([ANA]);
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(tarjeta('Finanzas').getByText('Administradores'));
    expect(await screen.findByText('No hay cuentas con rol de administrador de área.')).toBeTruthy();
  });

  it('409 rol_no_admin: muestra el mensaje del contrato y recarga', async () => {
    vi.mocked(usersApi.setManagedAreas).mockRejectedValue(
      new ApiError(409, 'x', { code: 'rol_no_admin' }));
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(tarjeta('Finanzas').getByText('Administradores'));
    fireEvent.click(await dialogo().findByLabelText('Eva · eva@ejemplo.local'));
    fireEvent.click(dialogo().getByText('Guardar'));

    expect(await screen.findByText(
      'El usuario no es administrador de área. Se muestran los datos actuales.')).toBeTruthy();
    expect(api.users).toHaveBeenCalledTimes(2);
  });
});

describe('Errores del formulario y de la baja', () => {
  it('422: mensaje por campo ligado al control', async () => {
    vi.mocked(api.createArea).mockRejectedValue(new ApiError(422, 'Revisa', {
      code: 'validacion', fields: { name: 'Entre 2 y 100 caracteres.' },
    }));
    render(<AreasList />);
    fireEvent.click(await screen.findByText('Nueva área'));
    fireEvent.change(dialogo().getByLabelText('Nombre'), { target: { value: 'X' } });
    fireEvent.click(dialogo().getByText('Guardar'));

    expect(await screen.findByText('Entre 2 y 100 caracteres.')).toBeTruthy();
    expect(screen.getByText('Revisa los campos marcados.')).toBeTruthy();
    const nombre = dialogo().getByLabelText('Nombre');
    expect(nombre.getAttribute('aria-invalid')).toBe('true');
    expect(nombre.getAttribute('aria-describedby')).toBe('area-name-error');
  });

  it('409 area_duplicada en el alta', async () => {
    vi.mocked(api.createArea).mockRejectedValue(
      new ApiError(409, 'dup', { code: 'area_duplicada' }));
    render(<AreasList />);
    fireEvent.click(await screen.findByText('Nueva área'));
    fireEvent.change(dialogo().getByLabelText('Nombre'), { target: { value: 'Sistemas' } });
    fireEvent.click(dialogo().getByText('Guardar'));
    expect(await screen.findByText('Ya existe un área con ese nombre.')).toBeTruthy();
  });

  it.each([
    ['area_con_plataformas', 'El área tiene plataformas; muévelas o elimínalas antes.'],
    ['area_con_accesos', 'El área tiene accesos vigentes.'],
    ['area_con_otros_admins',
      'El área tiene otros administradores; solo el superadmin puede darla de baja.'],
  ])('baja con 409 %s: confirma y muestra el mensaje', async (code, mensaje) => {
    rolActual = 'admin_area';
    vi.mocked(api.deleteArea).mockRejectedValue(new ApiError(409, 'x', { code }));
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(tarjeta('Finanzas').getByText('Eliminar'));
    fireEvent.click(dialogo().getByText('Eliminar'));

    await waitFor(() => expect(api.deleteArea).toHaveBeenCalledWith(3));
    expect(await screen.findByText(mensaje)).toBeTruthy();
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});

describe('Estados de la lista', () => {
  it('vacío', async () => {
    vi.mocked(api.areas).mockResolvedValue([]);
    render(<AreasList />);
    expect(await screen.findByText('No hay áreas dentro de tu alcance.')).toBeTruthy();
  });

  it('error de carga', async () => {
    vi.mocked(api.areas).mockRejectedValue(new Error('Servicio no disponible'));
    render(<AreasList />);
    expect(await screen.findByText('Servicio no disponible')).toBeTruthy();
  });
});
