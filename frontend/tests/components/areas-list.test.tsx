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
    api: {
      areas: vi.fn(),
      users: vi.fn(),
      createArea: vi.fn(),
      updateArea: vi.fn(),
      deleteArea: vi.fn(),
      setAreaUsers: vi.fn(),
      updateUser: vi.fn(),
    },
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
import { ToastProvider } from '@/components/toast';
import { mensajeDeError } from '@/components/areas/area-errors';

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
  vi.mocked(api.setAreaUsers).mockResolvedValue({ status: 'success' });
  vi.mocked(api.updateUser).mockResolvedValue({ status: 'success' });
  vi.mocked(usersApi.setManagedAreas).mockResolvedValue({ status: 'success', user: LUIS });
});

afterEach(() => {
  cleanup();
});

function dialogo() {
  return within(screen.queryByRole('alertdialog') ?? screen.getByRole('dialog'));
}

describe('AreasList por rol', () => {
  it('usuario: estado sin permiso y no llama a la API', () => {
    rolActual = 'usuario';
    render(<AreasList />);
    expect(screen.getByText(FORBIDDEN_MESSAGE)).toBeTruthy();
    expect(api.areas).not.toHaveBeenCalled();
  });

  it('admin de área: no ve "Nueva área", gestiona solo las suyas y no ve el panel de admins', async () => {
    rolActual = 'admin_area';
    render(<AreasList />);
    await screen.findByText('Sistemas');

    expect(screen.queryByText('Nueva área')).toBeNull();
    expect(screen.queryByText('Administradores')).toBeNull();
    expect(screen.queryByText('Admins')).toBeNull();

    // Finanzas está en sus áreas administradas: botones de barra habilitados
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    expect((screen.getByRole('button', { name: 'Editar Finanzas' }) as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByRole('button', { name: 'Eliminar Finanzas' }) as HTMLButtonElement).disabled).toBe(false);

    // Sistemas no está en sus áreas administradas: botones de barra deshabilitados
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByLabelText('Seleccionar Sistemas'));
    expect(screen.getByRole('button', { name: 'Editar Sistemas' }).getAttribute('aria-disabled')).toBe('true');
    expect(screen.getByRole('button', { name: 'Eliminar Sistemas' }).getAttribute('aria-disabled')).toBe('true');

    // DIS-089: el motivo del botón deshabilitado es texto accesible (describedby), el nombre no cambia
    const eliminar = screen.getByRole('button', { name: 'Eliminar Sistemas' });
    const motivo = document.getElementById(eliminar.getAttribute('aria-describedby')!);
    expect(motivo?.textContent).toBe('No tienes permisos para eliminar alguna de las áreas seleccionadas');
    fireEvent.click(screen.getByLabelText('Seleccionar Sistemas'));
    const sinSeleccion = screen.getByRole('button', { name: 'Eliminar' });
    expect(document.getElementById(sinSeleccion.getAttribute('aria-describedby')!)?.textContent).toBe(
      'Selecciona al menos 1 área para eliminar',
    );
  });

  it('superadmin: el alta no envía color y el área nueva queda gestionable', async () => {
    rolActual = 'administrador';
    render(<AreasList />);
    fireEvent.click(await screen.findByText('Nueva área'));
    fireEvent.change(dialogo().getByLabelText('Nombre'), { target: { value: 'Compras' } });
    vi.mocked(api.areas).mockResolvedValue([FINANZAS, SISTEMAS, area(9, 'Compras')]);
    fireEvent.click(dialogo().getByText('Siguiente'));
    fireEvent.click(dialogo().getByText('Guardar'));

    await waitFor(() => expect(api.createArea).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.createArea).mock.calls[0][0]).not.toHaveProperty('color');
    await screen.findByText('Compras');
    fireEvent.click(screen.getByLabelText('Seleccionar Compras'));
    expect((screen.getByRole('button', { name: 'Editar Compras' }) as HTMLButtonElement).disabled).toBe(false);
  });

  it('superadmin: ve todas las áreas y el botón Administradores en cada una', async () => {
    render(<AreasList />);
    await screen.findByText('Sistemas');
    expect(screen.getByText('Nueva área')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    expect(screen.getByRole('button', { name: 'Administradores de Finanzas' })).toBeTruthy();
  });

  it('renderiza exactamente las columnas: Área, Descripción, Admin, Plataformas, Usuarios y Estado, sin columna de Alcance', async () => {
    render(<AreasList />);
    await screen.findByText('Finanzas');

    expect(screen.getByRole('columnheader', { name: 'Área' })).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: 'Descripción' })).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: 'Admin' })).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: 'Plataformas' })).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: 'Usuarios' })).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: 'Estado' })).toBeTruthy();
    expect(screen.queryByRole('columnheader', { name: 'Alcance' })).toBeNull();
  });

  it('la columna Admin muestra el nombre del administrador o Sin asignar', async () => {
    const areaConAdmin: Area = {
      ...area(10, 'Operaciones'),
      admins: [{ id: 9, name: 'Carlos Admin', email: 'carlos@empresa.com' }],
    };
    const areaSinAdmin: Area = {
      ...area(11, 'Logística'),
      admins: [],
    };
    vi.mocked(api.areas).mockResolvedValue([areaConAdmin, areaSinAdmin]);
    render(<AreasList />);

    expect(await screen.findByText('Carlos Admin')).toBeTruthy();
    expect(screen.getByText('Sin asignar')).toBeTruthy();
  });

  it('en la barra de herramientas los botones están en el orden: Accesos, Admins, Editar, Eliminar y Nuevo', async () => {
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));

    const btnAccesos = screen.getByRole('button', { name: 'Accesos de Finanzas' });
    const btnAdmins = screen.getByRole('button', { name: 'Administradores de Finanzas' });
    expect(btnAccesos).toBeTruthy();
    expect(btnAdmins).toBeTruthy();
    expect(btnAccesos.compareDocumentPosition(btnAdmins) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe('Administradores del área (superadmin)', () => {
  it('lista solo admin_area, busca y asigna con managed-areas', async () => {
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Administradores de Finanzas' }));

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
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Administradores de Finanzas' }));
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
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Administradores de Finanzas' }));
    expect(await screen.findByText('No hay cuentas con rol de administrador de área.')).toBeTruthy();
  });

  it('409 rol_no_admin: muestra el mensaje del contrato y recarga', async () => {
    vi.mocked(usersApi.setManagedAreas).mockRejectedValue(
      new ApiError(409, 'x', { code: 'rol_no_admin' }));
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Administradores de Finanzas' }));
    fireEvent.click(await dialogo().findByLabelText('Eva · eva@ejemplo.local'));
    fireEvent.click(dialogo().getByText('Guardar'));

    expect(await screen.findByText(
      'El usuario no es administrador de área. Se muestran los datos actuales.')).toBeTruthy();
    await waitFor(() => expect(api.users).toHaveBeenCalledTimes(2));
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
    fireEvent.click(dialogo().getByText('Siguiente'));
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
    fireEvent.click(dialogo().getByText('Siguiente'));
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
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar Finanzas' }));
    fireEvent.click(dialogo().getByText('Eliminar'));

    await waitFor(() => expect(api.deleteArea).toHaveBeenCalledWith(3));
    expect(await screen.findByText(mensaje)).toBeTruthy();
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.queryByRole('alertdialog')).toBeNull();
  });

  it('permite eliminar múltiples áreas seleccionadas si tiene permisos', async () => {
    rolActual = 'administrador';
    vi.mocked(api.deleteArea).mockResolvedValue({ ok: true } as never);
    render(<AreasList />);
    await screen.findByText('Finanzas');
    await screen.findByText('Sistemas');

    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByLabelText('Seleccionar Sistemas'));

    const btnEliminar = screen.getByRole('button', { name: 'Eliminar 2 áreas seleccionadas' });
    expect((btnEliminar as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(btnEliminar);
    const dialog = await screen.findByRole('alertdialog', { name: 'Eliminar áreas' });
    expect(dialog).toBeTruthy();
    expect(within(dialog).getByText(/Se eliminarán las 2 áreas seleccionadas/)).toBeTruthy();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Eliminar' }));
    await waitFor(() => {
      expect(api.deleteArea).toHaveBeenCalledWith(3);
      expect(api.deleteArea).toHaveBeenCalledWith(7);
    });
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

describe('Accesibilidad (auditor-accesibilidad)', () => {
  it('acciones de barra con el nombre del área en su nombre accesible', async () => {
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    expect(screen.getByRole('button', { name: 'Editar Finanzas' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Administradores de Finanzas' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Eliminar Finanzas' })).toBeTruthy();
  });

  it('nombre vacío: error ligado al campo y foco en él al intentar avanzar', async () => {
    render(<AreasList />);
    fireEvent.click(await screen.findByText('Nueva área'));
    fireEvent.click(dialogo().getByText('Siguiente'));

    const nombre = dialogo().getByLabelText('Nombre');
    expect(nombre.getAttribute('aria-invalid')).toBe('true');
    expect(nombre.getAttribute('aria-describedby')).toBe('area-name-error');
    expect(document.getElementById('area-name-error')?.textContent).toBe('El nombre es obligatorio.');
    expect(document.activeElement).toBe(nombre);
    expect(api.createArea).not.toHaveBeenCalled();
  });

  it('asistente de 2 pasos: navegación entre Paso 1 (Descripción) y Paso 2 (Estilo visual) con vista previa', async () => {
    render(<AreasList />);
    fireEvent.click(await screen.findByText('Nueva área'));

    // Paso 1: Descripción
    expect(dialogo().getByRole('button', { name: /Descripción/i })).toBeTruthy();
    expect(dialogo().getByRole('button', { name: /Estilo/i })).toBeTruthy();
    expect(dialogo().getByLabelText('Nombre')).toBeTruthy();
    expect(dialogo().getByLabelText('Descripción')).toBeTruthy();
    expect(dialogo().queryByLabelText('Color del área')).toBeNull();

    // Llenar datos y avanzar
    fireEvent.change(dialogo().getByLabelText('Nombre'), { target: { value: 'Marketing' } });
    fireEvent.change(dialogo().getByLabelText('Descripción'), { target: { value: 'Área de marketing y marca' } });
    fireEvent.click(dialogo().getByText('Siguiente'));

    // Paso 2: Estilo visual
    expect(await dialogo().findByLabelText(/^Color/)).toBeTruthy();
    expect(dialogo().getByText('Vista previa')).toBeTruthy();
    expect(dialogo().getByText('MA')).toBeTruthy();
    // DIS-114: el estado ya no se edita en el formulario.
    expect(dialogo().queryByLabelText('Activa')).toBeNull();

    // Retroceder al Paso 1
    fireEvent.click(dialogo().getByText('Atrás'));
    expect(dialogo().getByLabelText('Nombre')).toBeTruthy();
    expect((dialogo().getByLabelText('Nombre') as HTMLInputElement).value).toBe('Marketing');
  });

  it('panel: la región de estado existe antes de guardar y solo cambia su texto', async () => {
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Administradores de Finanzas' }));
    await dialogo().findByLabelText('Eva · eva@ejemplo.local');
    const estado = dialogo().getByTestId('estado-guardado');
    expect(estado.getAttribute('role')).toBe('status');
    expect(estado.textContent).toBe('');

    fireEvent.click(dialogo().getByLabelText('Eva · eva@ejemplo.local'));
    fireEvent.click(dialogo().getByText('Guardar'));
    await waitFor(() => expect(estado.textContent).toBe('Cambios guardados'));
    expect(dialogo().getByTestId('estado-guardado')).toBe(estado);
  });
});

describe('Accesos del área (gestión de usuarios)', () => {
  it('el botón Accesos se habilita solo al seleccionar 1 área gestionable', async () => {
    rolActual = 'admin_area';
    render(<AreasList />);
    await screen.findByText('Finanzas');

    // Sin seleccionar área: botón Accesos deshabilitado
    const botonAccesos = screen.getByRole('button', { name: 'Accesos' }) as HTMLButtonElement;
    expect(botonAccesos.getAttribute('aria-disabled')).toBe('true');

    // Selecciona Finanzas (área administrada): botón Accesos habilitado con aria-label contextual
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    const botonFinanzas = screen.getByRole('button', { name: 'Accesos de Finanzas' }) as HTMLButtonElement;
    expect(botonFinanzas.disabled).toBe(false);

    // Selecciona Sistemas (área no administrada por Luis): botón Accesos deshabilitado
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByLabelText('Seleccionar Sistemas'));
    const botonSistemas = screen.getByRole('button', { name: 'Accesos de Sistemas' }) as HTMLButtonElement;
    expect(botonSistemas.getAttribute('aria-disabled')).toBe('true');
  });

  it('abre el panel de accesos con Dual Picklist y permite transferir y guardar usuarios', async () => {
    // Definimos usuarios con y sin área Finanzas (id: 3)
    const anaConFinanzas: ManagedUser = {
      ...ANA,
      areas: [{ id: 3, name: 'Finanzas' }],
    };
    const luisSinFinanzas: ManagedUser = {
      ...LUIS,
      areas: [],
    };
    vi.mocked(api.users).mockResolvedValue([anaConFinanzas, luisSinFinanzas]);

    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Accesos de Finanzas' }));

    const modal = dialogo();
    expect(await modal.findByText('Accesos — Finanzas')).toBeTruthy();

    // Verificamos que Ana aparece en "Con acceso" y Luis en "Sin acceso"
    expect(modal.getByLabelText('Agregar Luis al área')).toBeTruthy();
    expect(modal.getByLabelText('Retirar a Ana del área')).toBeTruthy();

    // Transferir a Luis a "Con acceso"
    fireEvent.click(modal.getByLabelText('Agregar Luis al área'));

    // Ahora Luis está en "Con acceso" (aparece el botón para retirarlo)
    expect(modal.getByLabelText('Retirar a Luis del área')).toBeTruthy();

    // Guardar los cambios
    fireEvent.click(modal.getByText('Guardar'));

    // Debe llamar a api.setAreaUsers con el ID del área (3) y los IDs de Ana y Luis ([8, 5])
    await waitFor(() => {
      expect(api.setAreaUsers).toHaveBeenCalledWith(3, expect.arrayContaining([8, 5]));
    });
  });

  it('modal de nueva área: paso 3 de Accesos con Dual Picklist y asignación de Admin', async () => {
    vi.mocked(api.createArea).mockResolvedValue({ status: 'success', area: area(15, 'Operaciones') });
    vi.mocked(api.users).mockResolvedValue([LUIS, EVA, ANA]);

    render(<AreasList />);
    fireEvent.click(await screen.findByText('Nueva área'));

    const modal = dialogo();
    // Paso 1: Descripción
    fireEvent.change(modal.getByLabelText('Nombre'), { target: { value: 'Operaciones' } });
    fireEvent.click(modal.getByText('Siguiente'));

    // Paso 2: Estilo
    expect(modal.getByText('Color')).toBeTruthy();
    fireEvent.click(modal.getByText('Siguiente: Accesos'));

    // Paso 3: Accesos (Dual Picklist)
    expect(await modal.findByText('Asignación rápida de accesos y administradores')).toBeTruthy();

    // Verificamos que Luis está en Sin acceso
    const btnAgregarLuis = modal.getByLabelText('Agregar Luis al área');
    expect(btnAgregarLuis).toBeTruthy();

    // Transferir Luis a Con acceso
    fireEvent.click(btnAgregarLuis);

    // En Con acceso, Luis ahora tiene casilla de Admin
    const chkAdminLuis = modal.getByLabelText('Hacer admin de área a Luis') as HTMLInputElement;
    expect(chkAdminLuis).toBeTruthy();
    expect(chkAdminLuis.checked).toBe(false);

    // Marcarlo como administrador de área
    fireEvent.click(chkAdminLuis);
    expect(chkAdminLuis.checked).toBe(true);

    // Guardar (Crear área)
    fireEvent.click(modal.getByText('Crear área'));

    // Verificamos que se crea el área, se asigna el usuario y se nombra admin
    await waitFor(() => {
      expect(api.createArea).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Operaciones' }),
      );
      expect(api.setAreaUsers).toHaveBeenCalledWith(15, [5]);
      expect(usersApi.setManagedAreas).toHaveBeenCalledWith(5, expect.arrayContaining([15]));
    });
  });
});

describe('AreasList: alta según la regla «área activa requiere admin» (DIS-165, FNC-220)', () => {
  async function crearOperaciones(marcarAdmin: boolean) {
    vi.mocked(api.createArea).mockResolvedValue({ status: 'success', area: { ...area(15, 'Operaciones'), status: 'Inactivo' } });
    vi.mocked(api.updateArea).mockResolvedValue({ status: 'success', area: area(15, 'Operaciones') });
    render(<ToastProvider><AreasList /></ToastProvider>);
    fireEvent.click(await screen.findByText('Nueva área'));
    const modal = dialogo();
    fireEvent.change(modal.getByLabelText('Nombre'), { target: { value: 'Operaciones' } });
    fireEvent.click(modal.getByText('Siguiente'));
    fireEvent.click(modal.getByText('Siguiente: Accesos'));
    await modal.findByText('Asignación rápida de accesos y administradores');
    fireEvent.click(modal.getByLabelText('Agregar Luis al área'));
    if (marcarAdmin) fireEvent.click(modal.getByLabelText('Hacer admin de área a Luis'));
    fireEvent.click(modal.getByText('Crear área'));
    await waitFor(() => expect(api.createArea).toHaveBeenCalledTimes(1));
  }

  it('superadmin con administrador: crea Inactiva, asigna el admin y después la activa', async () => {
    await crearOperaciones(true);
    expect(vi.mocked(api.createArea).mock.calls[0][0]).toHaveProperty('status', 'Inactivo');
    await waitFor(() => expect(api.updateArea).toHaveBeenCalledWith(15, { status: 'Activo' }));
    const ordenAdmin = vi.mocked(usersApi.setManagedAreas).mock.invocationCallOrder[0];
    const ordenActivar = vi.mocked(api.updateArea).mock.invocationCallOrder[0];
    expect(ordenAdmin).toBeLessThan(ordenActivar);
  });

  it('superadmin sin administrador: queda Inactiva y lo avisa', async () => {
    await crearOperaciones(false);
    expect(await screen.findByText(/«Operaciones» se creó inactiva: asígnale un administrador/)).toBeTruthy();
    // Un solo aviso: el de éxito no tapa al de acción pendiente.
    expect(screen.queryByText(/creada correctamente/)).toBeNull();
    expect(api.updateArea).not.toHaveBeenCalled();
  });

  it('409 `area_sin_admin` al activar: mensaje en español', () => {
    const err = new ApiError(409, 'Conflict', { code: 'area_sin_admin' });
    expect(mensajeDeError(err, 'respaldo')).toBe('Asigna al menos un administrador antes de activar el área.');
  });
});

describe('AreasList: estado con badge (DIS-114)', () => {
  it('la tabla muestra el estado como botón para quien puede editar el área y guarda {status}', async () => {
    rolActual = 'administrador';
    vi.mocked(api.updateArea).mockResolvedValue({ status: 'success', area: { ...FINANZAS, status: 'Inactivo' } });
    render(<AreasList />);
    fireEvent.click(await screen.findByRole('button', { name: 'Activa, desactivar área Finanzas' }));
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Desactivar' }));
    await waitFor(() => expect(api.updateArea).toHaveBeenCalledWith(3, { status: 'Inactivo' }));
  });

  it('admin de área: solo las suyas son botón; las demás, badge normal', async () => {
    rolActual = 'admin_area';
    render(<AreasList />);
    await screen.findByText('Sistemas');
    expect(screen.getByRole('button', { name: 'Activa, desactivar área Finanzas' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Activa, desactivar área Sistemas' })).toBeNull();
  });

  it('el formulario de área no tiene control de estado; el superadmin crea Inactiva (DIS-165)', async () => {
    rolActual = 'administrador';
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByText('Nueva área'));
    fireEvent.change(dialogo().getByLabelText('Nombre'), { target: { value: 'Compras' } });
    fireEvent.change(dialogo().getByLabelText('Descripción'), { target: { value: 'Área de compras' } });
    fireEvent.click(dialogo().getByText('Siguiente'));
    await dialogo().findByLabelText(/^Color/);
    expect(dialogo().queryByLabelText('Activa')).toBeNull();
    fireEvent.click(dialogo().getByText('Siguiente: Accesos'));
    fireEvent.click(await dialogo().findByText('Crear área'));
    await waitFor(() => expect(api.createArea).toHaveBeenCalledTimes(1));
    // DIS-165 (FNC-220): sin administradores no se puede activar; se crea Inactiva y no se activa.
    expect(vi.mocked(api.createArea).mock.calls[0][0]).toHaveProperty('status', 'Inactivo');
    expect(api.updateArea).not.toHaveBeenCalled();
  });

  it('editar un área no envía status (no pisa el estado)', async () => {
    rolActual = 'administrador';
    vi.mocked(api.updateArea).mockResolvedValue({ status: 'success', area: FINANZAS });
    render(<AreasList />);
    await screen.findByText('Finanzas');
    fireEvent.click(screen.getByLabelText('Seleccionar Finanzas'));
    fireEvent.click(screen.getByRole('button', { name: 'Editar Finanzas' }));
    fireEvent.click(dialogo().getByText('Siguiente'));
    expect(dialogo().queryByLabelText('Activa')).toBeNull();
    fireEvent.click(dialogo().getByText('Siguiente: Accesos'));
    fireEvent.click(await dialogo().findByText('Guardar cambios'));
    await waitFor(() => expect(api.updateArea).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.updateArea).mock.calls[0][1]).not.toHaveProperty('status');
  });
});
