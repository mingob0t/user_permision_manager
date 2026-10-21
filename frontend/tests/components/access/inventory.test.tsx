/**
 * DIS-021: Inventario de permisos (`/inventory`; contrato `accesos.md` 1.1).
 * - Columnas: quién, plataforma, área, nivel, origen, desde, quién aprobó y estado.
 * - Filtros (área, plataforma, nivel, origen, estado y búsqueda) a la página 1.
 * - Áreas: admin las suyas; superadmin `GET /areas`. Plataformas del alcance.
 * - Búsqueda sin caracteres de control y ≤ 100.
 * - Carga, vacío (con y sin filtros), error con reintento, recarga y paginación.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Access, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/inventory', () => ({ inventoryApi: { list: vi.fn() } }));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { areas: vi.fn(), platforms: vi.fn() },
}));

let esSuperadmin = false;
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 2,
      role: esSuperadmin ? 'administrador' : 'admin_area',
      managed_areas: [{ id: 3, name: 'Finanzas' }],
      preferences: { refresh_interval: 60 },
      permissions: {
        is_admin: esSuperadmin, is_area_admin: !esSuperadmin,
        can_manage_areas: esSuperadmin, can_manage_system: esSuperadmin,
      },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { inventoryApi } from '@/lib/access/inventory';
import { MOCK_ACCESS } from '@/lib/access/mocks';
import { Inventory, VACIO_CON_FILTROS, VACIO_SIN_FILTROS, aParametros } from '@/components/access/inventory';
import { BUSQUEDA_MAX, FILTROS_INICIALES, limpiarBusqueda } from '@/components/access/inventory-filters';
import { APROBO_SISTEMA } from '@/components/access/inventory-table';

function pagina<T>(items: T[], extra: Partial<Paginated<T>> = {}): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length, ...extra };
}

const ANA: Access = {
  ...MOCK_ACCESS, id: 77, status: 'activo', level: 'admin', origin: 'solicitud',
  user: { id: 8, name: 'Ana Ruiz', email: 'ana@ejemplo.local' },
  platform: { id: 12, name: 'Contabilidad', integration_type: 'ldap' },
  area: { id: 3, name: 'Finanzas' },
  granted_by: { id: 2, name: 'Luis Paz' }, granted_at: '2026-10-14T15:10:00Z',
  revoked_by: null, revoked_at: null, revoke_reason: null,
};
const LUIS: Access = {
  ...ANA, id: 78, status: 'en_proceso', level: 'usuario', origin: 'admin_de_area',
  user: { id: 2, name: 'Luis Paz', email: 'luis@ejemplo.local' }, granted_by: null,
};

const PLATAFORMAS = [
  { id: 12, name: 'Contabilidad', area_id: 3 },
  { id: 14, name: 'Wiki', area_id: 3 },
  { id: 20, name: 'CRM', area_id: 5 },
] as unknown as Awaited<ReturnType<typeof api.platforms>>;

const BASE = { status: 'vigente', area_id: undefined, platform_id: undefined, level: undefined,
  origin: undefined, q: undefined, page: 1 };

function opciones(etiqueta: string) {
  return within(screen.getByLabelText(etiqueta)).getAllByRole('option').map((o) => o.textContent);
}

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  vi.mocked(inventoryApi.list).mockResolvedValue(pagina([ANA, LUIS]));
  vi.mocked(api.platforms).mockResolvedValue(PLATAFORMAS);
  vi.mocked(api.areas).mockResolvedValue([
    { id: 3, name: 'Finanzas' }, { id: 5, name: 'Ventas' },
  ] as Awaited<ReturnType<typeof api.areas>>);
});

afterEach(cleanup);

describe('Inventory: lista', () => {
  it('pide vigentes por defecto y muestra las columnas del contrato', async () => {
    render(<Inventory />);
    const ana = await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' });
    expect(inventoryApi.list).toHaveBeenCalledWith(BASE);
    for (const texto of ['Ana Ruiz', 'ana@ejemplo.local', 'Contabilidad', 'Finanzas', 'Admin',
      'Por solicitud', 'Luis Paz', 'Con acceso']) {
      expect(within(ana).getByText(texto)).toBeTruthy();
    }
    expect(within(ana).getByText(/2026/)).toBeTruthy();
    for (const etiqueta of ['Usuario', 'Plataforma', 'Área', 'Nivel', 'Origen', 'Desde', 'Aprobó', 'Estado']) {
      expect(within(ana).getByText(etiqueta, { selector: 'dt' })).toBeTruthy();
    }
  });

  it('origen automático: aprobó "Sistema"', async () => {
    render(<Inventory />);
    const luis = await screen.findByRole('listitem', { name: 'Acceso de Luis Paz a Contabilidad' });
    expect(within(luis).getByText(APROBO_SISTEMA)).toBeTruthy();
    expect(within(luis).getByText('Automático (admin del área)')).toBeTruthy();
    expect(within(luis).getByText('Acceso en proceso')).toBeTruthy();
  });

  it('acceso retirado: fecha y quién lo retiró', async () => {
    vi.mocked(inventoryApi.list).mockResolvedValue(pagina([{
      ...ANA, status: 'revocado', revoked_at: '2026-10-18T10:00:00Z', revoked_by: { id: 1, name: 'Eva Sol' },
    }]));
    render(<Inventory />);
    const fila = await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' });
    expect(within(fila).getByText('Sin acceso')).toBeTruthy();
    expect(within(fila).getByText(/Retirado: .* por Eva Sol/)).toBeTruthy();
  });
});

describe('Inventory: filtros', () => {
  it('admin: áreas propias, plataformas de su alcance y acotadas al área', async () => {
    render(<Inventory />);
    await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' });
    expect(opciones('Área')).toEqual(['Todas mis áreas', 'Finanzas']);
    expect(api.areas).not.toHaveBeenCalled();
    await waitFor(() => expect(opciones('Plataforma'))
      .toEqual(['Todas las plataformas', 'Contabilidad', 'Wiki']));
  });

  it('superadmin: todas las áreas y todas las plataformas', async () => {
    esSuperadmin = true;
    render(<Inventory />);
    await waitFor(() => expect(opciones('Área'))
      .toEqual(['Todas las áreas', 'Finanzas', 'Ventas']));
    await waitFor(() => expect(opciones('Plataforma'))
      .toEqual(['Todas las plataformas', 'Contabilidad', 'Wiki', 'CRM']));
    fireEvent.change(screen.getByLabelText('Área'), { target: { value: '5' } });
    expect(opciones('Plataforma')).toEqual(['Todas las plataformas', 'CRM']);
  });

  it('cada filtro llega al contrato y vuelve a la página 1', async () => {
    vi.mocked(inventoryApi.list).mockResolvedValue(pagina([ANA], { total: 60 }));
    render(<Inventory />);
    await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' });
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    await waitFor(() => expect(inventoryApi.list).toHaveBeenLastCalledWith({ ...BASE, page: 2 }));

    await waitFor(() => expect(opciones('Plataforma')).toContain('Wiki'));
    fireEvent.change(screen.getByLabelText('Área'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Plataforma'), { target: { value: '14' } });
    fireEvent.change(screen.getByLabelText('Nivel'), { target: { value: 'admin' } });
    fireEvent.change(screen.getByLabelText('Origen'), { target: { value: 'admin_de_area' } });
    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'fallido' } });
    await waitFor(() => expect(inventoryApi.list).toHaveBeenLastCalledWith({
      ...BASE, status: 'fallido', area_id: 3, platform_id: 14, level: 'admin', origin: 'admin_de_area',
    }));
  });

  it('cambiar de área quita la plataforma que no le pertenece', async () => {
    esSuperadmin = true;
    render(<Inventory />);
    await waitFor(() => expect(opciones('Plataforma')).toContain('CRM'));
    fireEvent.change(screen.getByLabelText('Plataforma'), { target: { value: '20' } });
    fireEvent.change(screen.getByLabelText('Área'), { target: { value: '3' } });
    await waitFor(() => expect(inventoryApi.list).toHaveBeenLastCalledWith({ ...BASE, area_id: 3 }));
  });

  it('la búsqueda se aplica al enviar, limpia y sin caracteres de control', async () => {
    render(<Inventory />);
    await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' });
    const buscador = screen.getByLabelText('Buscar en el inventario por nombre o correo del usuario');
    expect(buscador.getAttribute('maxlength')).toBe(String(BUSQUEDA_MAX));
    fireEvent.change(buscador, { target: { value: '  ana\u0007@ejemplo ' } });
    expect(inventoryApi.list).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await waitFor(() => expect(inventoryApi.list).toHaveBeenLastCalledWith({ ...BASE, q: 'ana@ejemplo' }));
  });
});

describe('Inventory: historial (DIS-020)', () => {
  it('con una plataforma elegida enlaza su historial en Auditoría', async () => {
    render(<Inventory />);
    await waitFor(() => expect(opciones('Plataforma')).toContain('Wiki'));
    expect(screen.queryByRole('link', { name: /Historial/ })).toBeNull();
    fireEvent.change(screen.getByLabelText('Plataforma'), { target: { value: '14' } });
    const enlace = screen.getByRole('link', { name: 'Historial de Wiki en Auditoría' });
    expect(enlace.getAttribute('href')).toBe('/audit/platforms/14');
  });
});

describe('Inventory: estados', () => {
  it('carga', () => {
    vi.mocked(inventoryApi.list).mockReturnValue(new Promise(() => {}));
    render(<Inventory />);
    expect(screen.getByText('Cargando el inventario…')).toBeTruthy();
  });

  it('vacío sin filtros y con filtros', async () => {
    vi.mocked(inventoryApi.list).mockResolvedValue(pagina([]));
    render(<Inventory />);
    expect(await screen.findByText(VACIO_SIN_FILTROS)).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Nivel'), { target: { value: 'usuario' } });
    expect(await screen.findByText(VACIO_CON_FILTROS)).toBeTruthy();
  });

  it('error 403 en español y reintento', async () => {
    vi.mocked(inventoryApi.list).mockRejectedValueOnce(new ApiError(403, 'Forbidden'));
    render(<Inventory />);
    expect(await screen.findByText('No tienes permiso para ver los accesos del inventario.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' })).toBeTruthy();
  });

  it('error genérico sin detalles del servidor', async () => {
    vi.mocked(inventoryApi.list).mockRejectedValueOnce(new ApiError(500, 'Traceback interno'));
    render(<Inventory />);
    expect(await screen.findByText('No se pudieron cargar los accesos del inventario.')).toBeTruthy();
    expect(screen.queryByText(/Traceback/)).toBeNull();
  });

  it('Recargar vuelve a pedir la misma página sin refresco periódico', async () => {
    render(<Inventory />);
    await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' });
    fireEvent.click(screen.getByRole('button', { name: 'Recargar' }));
    await waitFor(() => expect(inventoryApi.list).toHaveBeenCalledTimes(2));
    expect(inventoryApi.list).toHaveBeenLastCalledWith(BASE);
  });

  it('Recargar conserva el foco mientras carga, lo anuncia e ignora otro clic', async () => {
    render(<Inventory />);
    await screen.findByRole('listitem', { name: 'Acceso de Ana Ruiz a Contabilidad' });
    let terminar: (valor: Paginated<Access>) => void = () => {};
    vi.mocked(inventoryApi.list).mockReturnValueOnce(new Promise((r) => { terminar = r; }));
    const boton = screen.getByRole('button', { name: 'Recargar' });
    boton.focus();
    fireEvent.click(boton);
    await waitFor(() => expect(boton.getAttribute('aria-disabled')).toBe('true'));
    expect(boton.hasAttribute('disabled')).toBe(false);
    expect(document.activeElement).toBe(boton);
    expect(screen.getByText('Recargando…').getAttribute('aria-live')).toBe('polite');
    fireEvent.click(boton);
    expect(inventoryApi.list).toHaveBeenCalledTimes(2);
    terminar(pagina([ANA, LUIS]));
    await waitFor(() => expect(boton.getAttribute('aria-disabled')).toBeNull());
    expect(document.activeElement).toBe(boton);
  });

  it('vacío con filtros en role="status" y error en role="alert"', async () => {
    vi.mocked(inventoryApi.list).mockResolvedValue(pagina([]));
    render(<Inventory />);
    fireEvent.change(screen.getByLabelText('Nivel'), { target: { value: 'admin' } });
    const vacio = await screen.findByText(VACIO_CON_FILTROS);
    expect(vacio.closest('[role="status"]')).toBeTruthy();
    vi.mocked(inventoryApi.list).mockRejectedValueOnce(new ApiError(500, 'x'));
    fireEvent.click(screen.getByRole('button', { name: 'Recargar' }));
    expect((await screen.findByRole('alert')).textContent)
      .toBe('No se pudieron cargar los accesos del inventario.');
  });
});

describe('Inventory: utilidades', () => {
  it('limpiarBusqueda quita control, recorta y limita a 100', () => {
    expect(limpiarBusqueda('\u0000 a\tb \u007f')).toBe('ab');
    expect(limpiarBusqueda('x'.repeat(150))).toHaveLength(BUSQUEDA_MAX);
    // DIS-020: también C1 (categoría Cc del servidor).
    expect(limpiarBusqueda('a\u0085b\u009f')).toBe('ab');
  });

  it('aParametros omite los filtros vacíos', () => {
    expect(aParametros(FILTROS_INICIALES, 3)).toEqual({ ...BASE, page: 3 });
  });
});
