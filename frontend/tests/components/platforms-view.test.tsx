/**
 * DIS-030: vista única de `/platforms` (catálogo solicitable + enlace y favorito
 * de "Mis plataformas"), por rol y por estado. La solicitud no cambia: su
 * comportamiento lo cubre `access/request-catalog.test.tsx`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { CatalogItem } from '@/lib/access/types';
import type { Platform } from '@/lib/types';

vi.mock('@/lib/access/requests', () => ({
  requestsApi: { catalog: vi.fn(), create: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { platforms: vi.fn(), toggleFavorite: vi.fn(), registerVisit: vi.fn() },
}));

let esSuperadmin = false;
let administradas: { id: number; name: string }[] = [];
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      role: esSuperadmin ? 'administrador' : 'usuario',
      managed_areas: administradas,
      permissions: {
        is_admin: esSuperadmin, is_area_admin: administradas.length > 0,
        can_manage_areas: esSuperadmin, can_manage_system: esSuperadmin,
      },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { requestsApi } from '@/lib/access/requests';
import { unirCatalogo } from '@/components/access/catalog-union';
import { PlatformsView } from '@/components/platforms-view';

function entrada(id: number, name: string, area: [number, string], extra: Partial<CatalogItem> = {}): CatalogItem {
  return {
    platform: { id, name, description: `Descripción de ${name}`, icon: 'box' },
    area: { id: area[0], name: area[1] },
    my_level: null, my_access_status: null, pending_request_id: null,
    can_request: true, requestable_levels: ['usuario', 'admin'],
    ...extra,
  };
}

function plataforma(id: number, name: string, extra: Partial<Platform> = {}): Platform {
  return {
    id, name, description: `Descripción de ${name}`, area_id: 3, area_name: 'Finanzas',
    area_color: '', direct_link: `https://${name.toLowerCase()}.ejemplo.local`,
    status: 'Activo', is_favorite: false, bg_color: '', text_color: '', ...extra,
  } as unknown as Platform;
}

const CONTA = entrada(12, 'Contabilidad', [3, 'Finanzas'], {
  my_level: 'usuario', my_access_status: 'activo', requestable_levels: ['admin'],
});
const NOMINA = entrada(13, 'Nómina', [3, 'Finanzas']);
const WIKI = entrada(5, 'Wiki', [1, 'TI'], { pending_request_id: 40, can_request: false, requestable_levels: [] });

const tarjeta = (n: string) => screen.getByRole('article', { name: n });

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  administradas = [];
  vi.mocked(requestsApi.catalog).mockResolvedValue([CONTA, NOMINA, WIKI]);
  vi.mocked(api.platforms).mockResolvedValue([plataforma(12, 'Contabilidad', { is_favorite: true })]);
  vi.mocked(api.registerVisit).mockResolvedValue({ status: 'success' } as never);
  vi.mocked(api.toggleFavorite).mockResolvedValue({ is_favorite: false } as never);
});

afterEach(() => cleanup());

describe('vista única', () => {
  it('una sola sección "Catálogo", un buscador y un filtro de área (sin "Mis plataformas")', async () => {
    render(<PlatformsView />);
    await screen.findByRole('article', { name: 'Wiki' });
    expect(screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)).toEqual(['Catálogo']);
    expect(screen.queryByText('Mis plataformas')).toBeNull();
    expect(screen.getAllByRole('searchbox')).toHaveLength(1);
    expect(screen.getAllByRole('combobox')).toHaveLength(1);
    expect(screen.getByRole('search', { name: 'Filtros del catálogo' })).toBeTruthy();
    expect(api.platforms).toHaveBeenCalledTimes(1);
  });

  it('usuario: la plataforma con acceso trae Abrir y favorito; la sin acceso solo solicitar', async () => {
    render(<PlatformsView />);
    const conta = await screen.findByRole('article', { name: 'Contabilidad' });
    const abrir = within(conta).getByRole('link', { name: 'Abrir Contabilidad' });
    expect(abrir.getAttribute('href')).toBe('https://contabilidad.ejemplo.local/');
    expect(abrir.getAttribute('rel')).toBe('noopener noreferrer');
    expect(within(conta).getByRole('button', { name: 'Quitar de favoritos' }).getAttribute('aria-pressed')).toBe('true');
    expect(within(conta).getByRole('button', { name: 'Solicitar acceso a Contabilidad' })).toBeTruthy();

    const nomina = tarjeta('Nómina');
    expect(within(nomina).queryByRole('link')).toBeNull();
    expect(within(nomina).queryByRole('button', { name: /favoritos/ })).toBeNull();
    expect(within(nomina).getByRole('button', { name: 'Solicitar acceso a Nómina' })).toBeTruthy();
    expect(within(tarjeta('Wiki')).getByText('Solicitud pendiente')).toBeTruthy();
  });

  it('abrir cuenta la visita; el favorito se alterna sin abrir el enlace', async () => {
    render(<PlatformsView />);
    const conta = await screen.findByRole('article', { name: 'Contabilidad' });
    fireEvent.click(within(conta).getByRole('link', { name: 'Abrir Contabilidad' }));
    expect(api.registerVisit).toHaveBeenCalledWith(12);

    fireEvent.click(within(conta).getByRole('button', { name: 'Quitar de favoritos' }));
    await waitFor(() => expect(api.toggleFavorite).toHaveBeenCalledWith(12));
    expect(await within(conta).findByRole('button', { name: 'Añadir a favoritos' })).toBeTruthy();
  });

  it('enlace no https o ausente: sin enlace, con el aviso en texto', async () => {
    vi.mocked(api.platforms).mockResolvedValue([
      plataforma(12, 'Contabilidad', { direct_link: 'http://inseguro.ejemplo.local' }),
    ]);
    render(<PlatformsView />);
    const conta = await screen.findByRole('article', { name: 'Contabilidad' });
    expect(within(conta).queryByRole('link')).toBeNull();
    expect(within(conta).getByText('Sin enlace')).toBeTruthy();
  });

  it('una plataforma abrible que el catálogo no trae se agrega, con enlace y sin solicitar', async () => {
    vi.mocked(api.platforms).mockResolvedValue([plataforma(99, 'Intranet', { area_id: 8, area_name: 'RH' })]);
    render(<PlatformsView />);
    const intranet = await screen.findByRole('article', { name: 'Intranet' });
    expect(within(intranet).getByRole('link', { name: 'Abrir Intranet' })).toBeTruthy();
    expect(within(intranet).getByText('Con acceso')).toBeTruthy();
    expect(within(intranet).queryByRole('button', { name: /Solicitar/ })).toBeNull();
    expect(within(intranet).queryByText('No disponible para solicitar.')).toBeNull();
  });

  it('el filtro y la búsqueda alcanzan a toda la vista (área y texto)', async () => {
    render(<PlatformsView />);
    await screen.findByRole('article', { name: 'Wiki' });
    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrar el catálogo por área' }), { target: { value: '3' } });
    expect(screen.queryByRole('article', { name: 'Wiki' })).toBeNull();
    fireEvent.change(screen.getByRole('searchbox', { name: 'Buscar en el catálogo' }), { target: { value: 'nómi' } });
    expect(screen.getAllByRole('article')).toHaveLength(1);
    expect(api.platforms).toHaveBeenCalledTimes(1);
    expect(requestsApi.catalog).toHaveBeenCalledTimes(1);
  });

  it('solicitar no cambia: envía la solicitud y la tarjeta pasa a pendiente', async () => {
    vi.mocked(requestsApi.create).mockResolvedValue({
      status: 'success', request: { id: 77, status: 'pendiente', level: 'usuario' },
    } as never);
    render(<PlatformsView />);
    fireEvent.click(await screen.findByRole('button', { name: 'Solicitar acceso a Nómina' }));
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));
    await waitFor(() => expect(requestsApi.create).toHaveBeenCalledWith({ platform_id: 13, level: 'usuario' }));
    expect(await within(tarjeta('Nómina')).findByText('Solicitud pendiente')).toBeTruthy();
  });
});

describe('por rol', () => {
  it('admin de área: su área sin acción de solicitar y con enlace y favorito', async () => {
    administradas = [{ id: 3, name: 'Finanzas' }];
    vi.mocked(requestsApi.catalog).mockResolvedValue([{ ...CONTA, can_request: false, my_level: null, my_access_status: null }]);
    render(<PlatformsView />);
    const conta = await screen.findByRole('article', { name: 'Contabilidad' });
    expect(within(conta).getByRole('link', { name: 'Abrir Contabilidad' })).toBeTruthy();
    expect(within(conta).getByText('Administras esta área: tienes acceso automático.')).toBeTruthy();
    expect(within(conta).getByText('Con acceso')).toBeTruthy();
    expect(within(conta).queryByText('Sin acceso')).toBeNull();
    expect(within(conta).queryByRole('button', { name: /Solicitar/ })).toBeNull();
  });

  it('superadmin: solo consulta; enlace y favorito de todas', async () => {
    esSuperadmin = true;
    vi.mocked(requestsApi.catalog).mockResolvedValue([{ ...NOMINA, can_request: false }]);
    vi.mocked(api.platforms).mockResolvedValue([plataforma(13, 'Nómina')]);
    render(<PlatformsView />);
    const nomina = await screen.findByRole('article', { name: 'Nómina' });
    expect(screen.getByText(/Como superadmin solo puedes consultarlas/)).toBeTruthy();
    expect(within(nomina).getByRole('link', { name: 'Abrir Nómina' })).toBeTruthy();
    expect(within(nomina).getByText('Como superadmin ya tienes acceso a todas las plataformas.')).toBeTruthy();
    expect(within(nomina).queryByRole('button', { name: /Solicitar/ })).toBeNull();
  });
});

describe('estados', () => {
  it('carga: un solo indicador mientras llegan los dos orígenes', () => {
    vi.mocked(api.platforms).mockReturnValue(new Promise(() => undefined));
    render(<PlatformsView />);
    expect(screen.getAllByText('Cargando catálogo…')).toHaveLength(1);
    expect(screen.queryByRole('article')).toBeNull();
  });

  it('vacío: sin catálogo ni plataformas', async () => {
    vi.mocked(requestsApi.catalog).mockResolvedValue([]);
    vi.mocked(api.platforms).mockResolvedValue([]);
    render(<PlatformsView />);
    expect(await screen.findByText('No hay plataformas en el catálogo de tus áreas.')).toBeTruthy();
  });

  it('error de /platforms: el catálogo se ve sin enlaces y se puede reintentar', async () => {
    vi.mocked(api.platforms).mockRejectedValueOnce(new ApiError(500, 'Traceback'));
    render(<PlatformsView />);
    expect((await screen.findByRole('alert')).textContent)
      .toBe('No se pudieron cargar los enlaces y favoritos de tus plataformas.');
    expect(within(tarjeta('Contabilidad')).queryByRole('link')).toBeNull();
    expect(within(tarjeta('Contabilidad')).getByRole('button', { name: 'Solicitar acceso a Contabilidad' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Reintentar enlaces' }));
    await screen.findByRole('article', { name: 'Contabilidad' });
    expect(within(tarjeta('Contabilidad')).getByRole('link', { name: 'Abrir Contabilidad' })).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(api.platforms).toHaveBeenCalledTimes(2);
  });

  it('error del catálogo: mensaje sin detalles y reintento', async () => {
    vi.mocked(requestsApi.catalog).mockRejectedValueOnce(new ApiError(500, 'Traceback'));
    vi.mocked(api.platforms).mockResolvedValue([]);
    render(<PlatformsView />);
    expect((await screen.findByRole('alert')).textContent).toBe('No se pudo cargar el catálogo.');
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByRole('article', { name: 'Wiki' })).toBeTruthy();
  });

  it('sin permiso al catálogo (403): lo dice y aun así muestra sus plataformas abribles', async () => {
    vi.mocked(requestsApi.catalog).mockRejectedValue(new ApiError(403, 'Prohibido'));
    render(<PlatformsView />);
    expect((await screen.findByRole('alert')).textContent).toBe('No tienes permiso para ver el catálogo.');
    expect(await screen.findByRole('article', { name: 'Contabilidad' })).toBeTruthy();
  });

  it('error del catálogo y sin plataformas propias: solo el error, sin el vacío', async () => {
    vi.mocked(requestsApi.catalog).mockRejectedValue(new ApiError(500, 'x'));
    vi.mocked(api.platforms).mockResolvedValue([]);
    render(<PlatformsView />);
    await screen.findByRole('alert');
    expect(screen.queryByText('No hay plataformas en el catálogo de tus áreas.')).toBeNull();
  });
});

describe('unirCatalogo', () => {
  it('cruza por id, no duplica y conserva el orden del catálogo', () => {
    const { items, mias } = unirCatalogo([CONTA, NOMINA], [plataforma(12, 'Contabilidad'), plataforma(99, 'Intranet')]);
    expect(items.map((i) => i.platform.id)).toEqual([12, 13, 99]);
    expect(mias.has(12) && mias.has(99) && !mias.has(13)).toBe(true);
    expect(unirCatalogo([], [plataforma(7, 'X', { area_name: null })]).items[0].area.name).toBe('Sin área');
    expect(items[2]).toMatchObject({ my_access_status: 'activo', can_request: false, requestable_levels: [] });
  });
});
