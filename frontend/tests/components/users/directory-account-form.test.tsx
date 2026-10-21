/**
 * DIS-019: alta en el directorio (`POST /users/directory`, contrato
 * `usuarios-directorio.md` v1).
 * - Campos de ADR-004 con etiqueta visible; sin contraseña (P8).
 * - Validación en el cliente espejo del servidor, foco en el primer error.
 * - Admin de área: al menos un área de las suyas; superadmin: opcional.
 * - 409 por campo, 422 sin texto del servidor, 404, 503 y genérico.
 * - `aria-disabled` durante el envío; carga, error y vacío de las áreas.
 * - Enganche en `UsersList`: aviso con foco y recarga tras crear.
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

let esSuperadmin = false;
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
import { DirectoryAccountForm } from '@/components/users/directory-account-form';
import {
  MENSAJES_CAMPO, MENSAJE_CORREO_DUPLICADO, MENSAJE_UID_DUPLICADO, cuerpoAlta,
  describeDirectoryAccountError, validarAlta,
} from '@/components/users/directory-account-errors';

const AREAS: AreaRef[] = [{ id: 3, name: 'Finanzas' }, { id: 7, name: 'TI' }];
const CREADA: ManagedUser = {
  id: 31, email: 'ana@ejemplo.local', name: 'Ana Ruiz', role: 'usuario', is_active: true,
  auth_source: 'ldap', areas: [{ id: 3, name: 'Finanzas' }], managed_areas: [], last_login_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  vi.mocked(usersApi.createDirectoryAccount).mockResolvedValue({ status: 'success', user: CREADA });
});

afterEach(() => {
  cleanup();
});

function montar(props: Partial<React.ComponentProps<typeof DirectoryAccountForm>> = {}) {
  const onCreated = vi.fn();
  render(
    <DirectoryAccountForm
      areas={AREAS} areasRequired onClose={vi.fn()} onCreated={onCreated} {...props}
    />,
  );
  return { onCreated };
}

function llenar(valores: Partial<Record<'uid' | 'email' | 'nombre' | 'apellidos', string>> = {}) {
  const v = { uid: 'ana.ruiz', email: 'ana@ejemplo.local', nombre: 'Ana', apellidos: 'Ruiz', ...valores };
  fireEvent.change(screen.getByLabelText('Identificador'), { target: { value: v.uid } });
  fireEvent.change(screen.getByLabelText('Correo'), { target: { value: v.email } });
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: v.nombre } });
  fireEvent.change(screen.getByLabelText('Apellidos'), { target: { value: v.apellidos } });
}

const enviar = () => fireEvent.click(screen.getByText('Crear cuenta'));

describe('DirectoryAccountForm', () => {
  it('campos con etiqueta visible y sin contraseña', () => {
    montar();
    for (const etiqueta of ['Identificador', 'Correo', 'Nombre', 'Apellidos']) {
      expect(screen.getByLabelText(etiqueta)).toBeTruthy();
    }
    expect(screen.getByRole('group', { name: 'Áreas a las que pertenece' })).toBeTruthy();
    expect(screen.queryByLabelText(/contraseña/i)).toBeNull();
    expect(document.querySelector('input[type="password"]')).toBeNull();
  });

  it('campos obligatorios marcados (AA 3.3.2) y aviso de que las áreas son la excepción', () => {
    montar();
    for (const etiqueta of ['Identificador', 'Correo', 'Nombre', 'Apellidos']) {
      const campo = screen.getByLabelText(etiqueta) as HTMLInputElement;
      expect(campo.required).toBe(true);
      expect(campo.getAttribute('aria-required')).toBe('true');
    }
    expect(screen.getByText('Todos los campos son obligatorios salvo las áreas.')).toBeTruthy();
    expect((screen.getByLabelText('Finanzas') as HTMLInputElement).required).toBe(false);
  });

  it('cada casilla de área ocupa la fila: área táctil de 48 px en la label', () => {
    montar();
    const fila = screen.getByLabelText('Finanzas').closest('li')!;
    expect(fila.className).toContain('[&>label]:min-h-12');
    expect(fila.className).toContain('[&>label]:w-full');
    expect(fila.querySelector(':scope > label')).toBeTruthy();
  });

  it('envía solo los campos del contrato, recortados, y entrega la cuenta creada', async () => {
    const { onCreated } = montar();
    llenar({ uid: ' ana.ruiz ', nombre: ' Ana ' });
    fireEvent.click(screen.getByLabelText('TI'));
    enviar();

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(CREADA));
    expect(usersApi.createDirectoryAccount).toHaveBeenCalledWith({
      uid: 'ana.ruiz', email: 'ana@ejemplo.local', given_name: 'Ana', surname: 'Ruiz', area_ids: [7],
    });
  });

  it('admin de área: sin área no envía, marca el error y enfoca la primera casilla', () => {
    montar();
    llenar();
    enviar();
    expect(usersApi.createDirectoryAccount).not.toHaveBeenCalled();
    expect(screen.getByText(MENSAJES_CAMPO.area_ids)).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText('Finanzas'));
  });

  it('superadmin: las áreas son opcionales', async () => {
    montar({ areasRequired: false });
    llenar();
    enviar();
    await waitFor(() => expect(usersApi.createDirectoryAccount).toHaveBeenCalled());
    expect(vi.mocked(usersApi.createDirectoryAccount).mock.calls[0][0].area_ids).toEqual([]);
  });

  it('identificador inválido: no envía, error ligado y foco en el campo', () => {
    montar();
    llenar({ uid: 'Ana Ruiz' });
    fireEvent.click(screen.getByLabelText('Finanzas'));
    enviar();
    const uid = screen.getByLabelText('Identificador');
    expect(usersApi.createDirectoryAccount).not.toHaveBeenCalled();
    expect(uid.getAttribute('aria-invalid')).toBe('true');
    expect(uid.getAttribute('aria-describedby')).toContain('alta-directorio-uid-error');
    expect(document.activeElement).toBe(uid);
  });

  it.each([
    ['uid_duplicado', 'Identificador', MENSAJE_UID_DUPLICADO],
    ['correo_duplicado', 'Correo', MENSAJE_CORREO_DUPLICADO],
  ])('409 %s: error en su campo y foco', async (code, etiqueta, mensaje) => {
    vi.mocked(usersApi.createDirectoryAccount).mockRejectedValue(
      new ApiError(409, 'texto del servidor', { code }));
    montar();
    llenar();
    fireEvent.click(screen.getByLabelText('Finanzas'));
    enviar();
    expect(await screen.findByText(mensaje)).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText(etiqueta));
    expect(screen.queryByText('texto del servidor')).toBeNull();
  });

  it('422: mensajes propios por campo, nunca el del servidor', async () => {
    vi.mocked(usersApi.createDirectoryAccount).mockRejectedValue(
      new ApiError(422, 'x', { code: 'validacion', fields: { email: '<b>servidor</b>' } }));
    montar();
    llenar();
    fireEvent.click(screen.getByLabelText('Finanzas'));
    enviar();
    expect(await screen.findByText(MENSAJES_CAMPO.email)).toBeTruthy();
    expect(screen.queryByText(/servidor/)).toBeNull();
  });

  it.each([
    [503, 'directorio_no_disponible', 'No se pudo crear la cuenta en el directorio; intenta más tarde.'],
    [404, 'no_encontrado', 'Alguna de las áreas elegidas ya no está en tu alcance. Recarga la página.'],
    [403, 'sin_permiso', 'No tienes permiso para crear cuentas.'],
    [500, 'error_interno', 'No se pudo crear la cuenta. Inténtalo de nuevo.'],
  ])('%i %s: mensaje en español', async (status, code, mensaje) => {
    vi.mocked(usersApi.createDirectoryAccount).mockRejectedValue(
      new ApiError(status, 'texto del servidor', { code }));
    montar();
    llenar();
    fireEvent.click(screen.getByLabelText('Finanzas'));
    enviar();
    expect(await screen.findByText(mensaje)).toBeTruthy();
  });

  it('durante el envío el botón queda aria-disabled y no reenvía', async () => {
    let resolver: (v: { status: 'success'; user: ManagedUser }) => void = () => {};
    vi.mocked(usersApi.createDirectoryAccount).mockReturnValue(
      new Promise((r) => { resolver = r; }));
    montar();
    llenar();
    fireEvent.click(screen.getByLabelText('Finanzas'));
    enviar();
    const boton = await screen.findByText('Creando…');
    expect(boton.getAttribute('aria-disabled')).toBe('true');
    fireEvent.click(boton);
    expect(usersApi.createDirectoryAccount).toHaveBeenCalledTimes(1);
    resolver({ status: 'success', user: CREADA });
  });

  it('áreas: carga, error y vacío', () => {
    montar({ areas: [], areasLoading: true });
    expect(screen.queryByLabelText('Finanzas')).toBeNull();
    cleanup();
    montar({ areas: [], areasError: 'No se pudieron cargar las áreas.' });
    expect(screen.getByText('No se pudieron cargar las áreas.')).toBeTruthy();
    cleanup();
    montar({ areas: [] });
    expect(screen.getByText('No hay áreas en tu alcance.')).toBeTruthy();
  });
});

describe('validación y errores del alta', () => {
  const base = { uid: 'ana', email: 'a@b.mx', given_name: 'A', surname: 'R', area_ids: [] };

  it('reglas del contrato', () => {
    expect(validarAlta(base, false)).toEqual({});
    expect(validarAlta({ ...base, uid: 'ab' }, false).uid).toBe(MENSAJES_CAMPO.uid);
    expect(validarAlta({ ...base, uid: '1ab' }, false).uid).toBe(MENSAJES_CAMPO.uid);
    expect(validarAlta({ ...base, uid: 'a'.repeat(65) }, false).uid).toBe(MENSAJES_CAMPO.uid);
    expect(validarAlta({ ...base, email: 'á@b.mx' }, false).email).toBe(MENSAJES_CAMPO.email);
    expect(validarAlta({ ...base, email: `${'a'.repeat(116)}@b.mx` }, false).email)
      .toBe(MENSAJES_CAMPO.email);
    expect(validarAlta({ ...base, surname: 'x'.repeat(101) }, false).surname)
      .toBe(MENSAJES_CAMPO.surname);
    expect(validarAlta({ ...base, given_name: '  ' }, false).given_name).toBe('Es obligatorio.');
    expect(validarAlta(base, true).area_ids).toBe(MENSAJES_CAMPO.area_ids);
  });

  it('el cuerpo no lleva campos fuera de la lista blanca', () => {
    expect(Object.keys(cuerpoAlta(base)).sort())
      .toEqual(['area_ids', 'email', 'given_name', 'surname', 'uid']);
  });

  it('un error que no es ApiError da el mensaje genérico', () => {
    expect(describeDirectoryAccountError(new Error('x')).message)
      .toBe('No se pudo crear la cuenta. Inténtalo de nuevo.');
  });
});

describe('UsersList: alta en el directorio', () => {
  beforeEach(() => {
    vi.mocked(api.users).mockResolvedValue([]);
    vi.mocked(api.areas).mockResolvedValue(AREAS as never);
    vi.mocked(api.platforms).mockResolvedValue([]);
  });

  it('admin de área: solo ve sus áreas; tras crear, aviso con foco y recarga', async () => {
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Nuevo usuario'));
    const modal = within(screen.getByRole('dialog'));
    expect(modal.getByLabelText('Finanzas')).toBeTruthy();
    expect(modal.queryByLabelText('TI')).toBeNull();
    llenar();
    fireEvent.click(modal.getByLabelText('Finanzas'));
    enviar();

    const aviso = await screen.findByText('Se creó la cuenta de Ana Ruiz.');
    expect(screen.queryByRole('dialog')).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(aviso.closest('[role="status"]')));
    expect(api.users).toHaveBeenCalledTimes(2);
  });

  it('superadmin: ve todas las áreas', async () => {
    esSuperadmin = true;
    render(<UsersList />);
    fireEvent.click(await screen.findByText('Nuevo usuario'));
    const modal = within(screen.getByRole('dialog'));
    expect(await modal.findByLabelText('TI')).toBeTruthy();
    expect(modal.getByText('Opcional.')).toBeTruthy();
  });
});
