/**
 * DIS-131: pantalla Solicitudes (`/approvals`): resumen con tarjetas por estado, gráficas por
 * área y plataforma. DIS-141: fila de KPI con la dona por estado, conectores y usuarios por rol
 * (sin «Abrir») y panel «Solicitudes» con las pendientes (8 por página, aprobar/rechazar). Las
 * tablas por estado (`?status=`) siguen con Volver al resumen.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastProvider } from '@/components/toast';
import type { AccessRequest, InboxStats } from '@/lib/access/types';
import { crearRaiz, simularCajas } from '../../utils/dom-simulado';

const url = { consulta: '' };
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(url.consulta),
  usePathname: () => '/approvals',
}));
vi.mock('@/lib/access/requests', () => ({
  requestsApi: { inbox: vi.fn(), inboxStats: vi.fn(), approve: vi.fn(), reject: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { areas: vi.fn().mockResolvedValue([]), stats: vi.fn() },
}));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 2, role: 'admin_area', managed_areas: [{ id: 3, name: 'Finanzas' }],
      preferences: { refresh_interval: 60 },
      permissions: { is_admin: false, is_area_admin: true, can_manage_areas: false, can_manage_system: false },
    },
  }),
}));

import { requestsApi } from '@/lib/access/requests';
import { MOCK_REQUEST } from '@/lib/access/mocks';
import { ApprovalsView } from '@/components/access/approvals-view';
import { MAX_BARRAS } from '@/components/access/approvals-resumen';
import { SOLICITUDES_POR_PAGINA } from '@/components/access/solicitudes-panel';
import { NOMBRE_OTRAS, filasPorArea } from '@/components/access/dona-areas';
import { ApiError, api } from '@/lib/api';
import type { Stats } from '@/lib/types';

/** `GET /stats` (FNC-214): 9 usuarios (6 + 3 administradores) y 4 conectores (3 asociados). */
const PANEL: Stats = {
  areas: 2, platforms: 5, visits: 0, users: 9, requests: 12, connectors: 4, most_visited: [], platforms_by_area: [],
  desglose: { users_by_role: { parte: 6, resto: 3 }, connectors: { parte: 3, resto: 1 } },
};

const STATS: InboxStats = {
  total: 12,
  by_status: { pendiente: 3, aprobada: 7, rechazada: 2 },
  by_area: [{ area_id: 3, area: 'Finanzas', count: 8 }, { area_id: 4, area: 'Ventas', count: 4 }],
  by_platform: [{ platform_id: 12, platform: 'Contabilidad', area: 'Finanzas', count: 5 }],
  pending_by_area: [{ area_id: 3, area: 'Finanzas', count: 2 }, { area_id: 4, area: 'Ventas', count: 1 }],
};
const BASE: AccessRequest = {
  ...MOCK_REQUEST, id: 41, status: 'pendiente', rejection_reason: null, decided_at: null, decided_by: null,
};

function render_() {
  return render(<ToastProvider><ApprovalsView /></ToastProvider>);
}

beforeEach(() => {
  // recharts (`ResponsiveContainer`) necesita ResizeObserver, que jsdom no trae.
  vi.stubGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
  simularCajas();
  crearRaiz();
  window.localStorage.clear();
  vi.clearAllMocks();
  url.consulta = '';
  vi.mocked(requestsApi.inboxStats).mockResolvedValue(STATS);
  vi.mocked(api.stats).mockResolvedValue(PANEL);
  vi.mocked(requestsApi.inbox).mockResolvedValue({ items: [BASE], page: 1, per_page: 25, total: 1 });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('DIS-131: resumen', () => {
  it('DIS-141: KPI = dona por estado, conectores y usuarios por rol; sin tarjetas de aprobadas/rechazadas ni «Abrir»', async () => {
    render_();
    const leyenda = await screen.findByRole('list', { name: 'Solicitudes por estado' });
    const items = within(leyenda).getAllByRole('listitem').map((li) => li.textContent);
    expect(items[0]).toContain('Pendientes');
    expect(items[0]).toContain('25 %');
    expect(items[1]).toContain('58 %');
    expect(items[2]).toContain('17 %');
    const conectores = await screen.findByRole('group', { name: 'Conectores' });
    expect(within(conectores).getAllByText('4').length).toBeGreaterThan(0);
    const usuarios = screen.getByRole('group', { name: 'Usuarios' });
    expect(within(usuarios).getAllByText('9').length).toBeGreaterThan(0);
    expect(usuarios.textContent).toMatch(/administradores/);
    expect(screen.queryByRole('group', { name: 'Aprobadas' })).toBeNull();
    expect(screen.queryByRole('group', { name: 'Rechazadas' })).toBeNull();
    expect(screen.queryByRole('link', { name: /^Abrir solicitudes/ })).toBeNull();
  });

  it('DIS-141: sin conectores en /stats (admin de área) no hay KPI de conectores; si /stats falla solo queda la dona', async () => {
    vi.mocked(api.stats).mockResolvedValue({ ...PANEL, connectors: undefined });
    render_();
    await screen.findByRole('group', { name: 'Usuarios' });
    expect(screen.queryByRole('group', { name: 'Conectores' })).toBeNull();
    cleanup();
    vi.mocked(api.stats).mockRejectedValue(new ApiError(500, 'x'));
    render_();
    await screen.findByRole('list', { name: 'Solicitudes por estado' });
    expect(screen.queryByRole('group', { name: 'Usuarios' })).toBeNull();
  });

  it('DIS-141: panel «Solicitudes»: pendientes, 8 por página, usuario, área/plataforma, fecha y acciones', async () => {
    render_();
    const panel = await screen.findByRole('list', { name: 'Solicitudes pendientes' });
    expect(requestsApi.inbox).toHaveBeenCalledWith({ status: 'pendiente', page: 1, per_page: SOLICITUDES_POR_PAGINA });
    expect(SOLICITUDES_POR_PAGINA).toBe(8);
    const fila = within(panel).getByRole('listitem', { name: 'Solicitud de Ana Ruiz para Contabilidad' });
    expect(within(fila).getByText('Ana Ruiz')).toBeTruthy();
    expect(within(fila).getAllByText('Finanzas').length).toBeGreaterThan(0);
    expect(within(fila).getByRole('button', { name: 'Aprobar la solicitud de Ana Ruiz para Contabilidad' })).toBeTruthy();
    expect(within(fila).getByRole('button', { name: 'Rechazar la solicitud de Ana Ruiz para Contabilidad' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Ver todo' }).getAttribute('href')).toBe('/approvals?status=pendiente');
  });

  it('DIS-141: la solicitud propia no tiene botones', async () => {
    vi.mocked(requestsApi.inbox).mockResolvedValue({
      items: [{ ...BASE, requester: { id: 2, name: 'Luis Paz', email: 'luis@ejemplo.local' } }],
      page: 1, per_page: 8, total: 1,
    });
    render_();
    const fila = await screen.findByRole('listitem', { name: /Solicitud de Luis Paz/ });
    expect(within(fila).queryByRole('button')).toBeNull();
    expect(within(fila).getByText('Tu solicitud')).toBeTruthy();
  });

  it('DIS-141: paginación de 8 en 8', async () => {
    vi.mocked(requestsApi.inbox).mockResolvedValue({ items: [BASE], page: 1, per_page: 8, total: 20 });
    render_();
    await screen.findByRole('list', { name: 'Solicitudes pendientes' });
    expect(screen.getByText('1/3')).toBeTruthy();
    expect(screen.getByText('1 de 20 registros')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Página siguiente de solicitudes' }));
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'pendiente', page: 2, per_page: SOLICITUDES_POR_PAGINA }));
  });

  it('DIS-141: aprobar desde el panel abre el diálogo de la bandeja', async () => {
    render_();
    fireEvent.click(await screen.findByRole('button', { name: 'Aprobar la solicitud de Ana Ruiz para Contabilidad' }));
    expect(await screen.findByRole('alertdialog')).toBeTruthy();
  });

  it('gráficas por área y plataforma con su tabla alternativa', async () => {
    render_();
    // DIS-145: la dona es «pendientes por área»; «Solicitudes por área» queda solo en las barras.
    expect((await screen.findAllByRole('heading', { name: 'Solicitudes por área' })).length).toBe(1);
    expect(screen.getByRole('heading', { name: 'Solicitudes pendientes por área' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Solicitudes por plataforma' })).toBeTruthy();
    expect(screen.getByRole('table', { name: 'Solicitudes por área' })).toBeTruthy();
    expect(screen.getByText('Contabilidad')).toBeTruthy();
  });

  it('recorta las gráficas al máximo de barras', async () => {
    const muchas = Array.from({ length: MAX_BARRAS + 5 }, (_, i) => (
      { area_id: i + 1, area: `Área ${i + 1}`, count: 100 - i }));
    vi.mocked(requestsApi.inboxStats).mockResolvedValue({ ...STATS, by_area: muchas });
    render_();
    const tabla = await screen.findByRole('table', { name: 'Solicitudes por área' });
    expect(within(tabla).getAllByRole('row')).toHaveLength(MAX_BARRAS + 1);
  });

  it('sin solicitudes: estados vacíos y panel sin pendientes', async () => {
    vi.mocked(requestsApi.inboxStats).mockResolvedValue({
      total: 0, by_status: { pendiente: 0, aprobada: 0, rechazada: 0 }, by_area: [], by_platform: [], pending_by_area: [],
    });
    render_();
    expect(await screen.findByText('Sin solicitudes por área')).toBeTruthy();
    expect(screen.getByText('Sin solicitudes pendientes')).toBeTruthy();
    expect(screen.getByText('Sin solicitudes por plataforma')).toBeTruthy();
    vi.mocked(requestsApi.inbox).mockResolvedValue({ items: [], page: 1, per_page: 8, total: 0 });
    expect(screen.getByText('Sin solicitudes')).toBeTruthy();
  });

  it('error: mensaje y reintento', async () => {
    vi.mocked(requestsApi.inboxStats).mockRejectedValueOnce(new ApiError(500, 'Error'));
    render_();
    expect(await screen.findByRole('alert')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByRole('list', { name: 'Solicitudes por estado' })).toBeTruthy();
  });

  it('la vista principal no incluye la tabla de la bandeja (sin filtros)', async () => {
    render_();
    await screen.findByRole('list', { name: 'Solicitudes por estado' });
    expect(screen.queryByLabelText('Filtrar la bandeja por área')).toBeNull();
    expect(screen.queryByLabelText('Filtrar la bandeja por estado')).toBeNull();
  });

  it('DIS-132: la vista principal no lleva texto descriptivo bajo el título', async () => {
    render_();
    await screen.findByRole('list', { name: 'Solicitudes por estado' });
    expect(screen.queryByText(/Resumen de las solicitudes de acceso/)).toBeNull();
  });
});

describe('DIS-131: tablas por estado (`?status=`)', () => {
  it('pendientes: tabla con Aprobar/Rechazar, sin selector de estado y con Volver', async () => {
    url.consulta = 'status=pendiente';
    render_();
    const fila = await screen.findByRole('listitem', { name: /Solicitud de Ana Ruiz/ });
    expect(requestsApi.inbox).toHaveBeenCalledWith({ status: 'pendiente', area_id: undefined, page: 1 });
    expect(within(fila).getByRole('button', { name: /Aprobar/ })).toBeTruthy();
    expect(within(fila).getByRole('button', { name: /Rechazar/ })).toBeTruthy();
    expect(screen.queryByLabelText('Filtrar la bandeja por estado')).toBeNull();
    expect(screen.getByLabelText('Filtrar la bandeja por área')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Volver' }).getAttribute('href')).toBe('/approvals');
    expect(requestsApi.inboxStats).not.toHaveBeenCalled();
  });

  it.each([['aprobada', 'Aprobada'], ['rechazada', 'Rechazada']])(
    '%s: solo ese estado y sin botones de acción',
    async (estado, etiqueta) => {
      url.consulta = `status=${estado}`;
      vi.mocked(requestsApi.inbox).mockResolvedValue({
        items: [{ ...BASE, status: estado as AccessRequest['status'], rejection_reason: estado === 'rechazada' ? 'Sin necesidad.' : null }],
        page: 1, per_page: 25, total: 1,
      });
      render_();
      const fila = await screen.findByRole('listitem', { name: /Solicitud de Ana Ruiz/ });
      await waitFor(() => expect(requestsApi.inbox).toHaveBeenCalledWith({ status: estado, area_id: undefined, page: 1 }));
      expect(within(fila).getByText(etiqueta)).toBeTruthy();
      expect(within(fila).queryByRole('button', { name: /Aprobar|Rechazar/ })).toBeNull();
      if (estado === 'rechazada') expect(within(fila).getByText(/Sin necesidad/)).toBeTruthy();
    },
  );

  it('un estado inválido en la URL muestra el resumen', async () => {
    url.consulta = 'status=otro';
    render_();
    expect(await screen.findByRole('list', { name: 'Solicitudes por estado' })).toBeTruthy();
  });
});

describe('DIS-144/145: KPI por área y espaciado', () => {
  it('KPI «Solicitudes pendientes por área» con cifra y porcentaje de cada área', async () => {
    render_();
    const leyenda = await screen.findByRole('list', { name: 'Solicitudes pendientes por área' });
    const items = within(leyenda).getAllByRole('listitem').map((li) => li.textContent);
    expect(items[0]).toContain('Finanzas');
    expect(items[0]).toContain('67 %');
    expect(items[1]).toContain('Ventas');
    expect(items[1]).toContain('33 %');
  });

  it('más de 5 áreas: 4 con color propio y «Otras» con el resto', () => {
    const pending_by_area = Array.from({ length: 7 }, (_, i) => ({ area_id: i + 1, area: `Área ${i + 1}`, count: 10 - i }));
    const filas = filasPorArea({ ...STATS, pending_by_area });
    expect(filas.map((f) => f.nombre)).toEqual(['Área 1', 'Área 2', 'Área 3', 'Área 4', NOMBRE_OTRAS]);
    expect(filas[4].cantidad).toBe(6 + 5 + 4);
    expect(new Set(filas.map((f) => f.color)).size).toBe(5);
    expect(filasPorArea({ ...STATS, pending_by_area: pending_by_area.slice(0, 5) }).map((f) => f.nombre)).not.toContain(NOMBRE_OTRAS);
  });

  it('sin doble espacio: la vista usa flex con gap (el h1 oculto no suma margen) y llena el alto', async () => {
    const { container } = render_();
    await screen.findByRole('list', { name: 'Solicitudes por estado' });
    const vista = container.querySelector('section[aria-label="Resumen de solicitudes"]')!.parentElement!;
    expect(vista.className).not.toMatch(/space-y-/);
    expect(vista.className).toMatch(/flex-col/);
    expect(vista.className).toMatch(/h-full/);
    expect(container.querySelector('section[aria-label="Resumen de solicitudes"]')!.className).toMatch(/flex-1/);
  });
});
