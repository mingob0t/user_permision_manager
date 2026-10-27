/**
 * DIS-014: Mis solicitudes y Mis accesos (`/requests`; contratos
 * `solicitudes.md` 1.1 y `accesos.md` 1.1).
 * - Pestañas; superadmin con estado vacío explicado y sin llamadas a la API.
 * - Solicitudes: estado, motivo de rechazo, filtro, paginación, vacío y error.
 * - Accesos: `vigente` por defecto, estado explicado, origen, vacío y error.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Access, AccessRequest, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/requests', () => ({ requestsApi: { mine: vi.fn() } }));
vi.mock('@/lib/access/grants', () => ({ grantsApi: { mine: vi.fn() } }));

let esSuperadmin = false;
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      role: esSuperadmin ? 'administrador' : 'usuario',
      managed_areas: [],
      preferences: { refresh_interval: 60 },
      permissions: {
        is_admin: esSuperadmin, is_area_admin: false,
        can_manage_areas: esSuperadmin, can_manage_system: esSuperadmin,
      },
    },
  }),
}));

import { ApiError } from '@/lib/api';
import { grantsApi } from '@/lib/access/grants';
import { requestsApi } from '@/lib/access/requests';
import { MOCK_ACCESS, MOCK_REQUEST } from '@/lib/access/mocks';
import { MyRequestsView, MENSAJE_SUPERADMIN } from '@/components/access/my-requests-view';
import { EXPLICACION_ESTADO } from '@/components/access/my-access';

function pagina<T>(items: T[], extra: Partial<Paginated<T>> = {}): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length, ...extra };
}

const RECHAZADA: AccessRequest = MOCK_REQUEST;
const APROBADA: AccessRequest = {
  ...MOCK_REQUEST, id: 42, status: 'aprobada', platform: { id: 13, name: 'Nómina' },
  rejection_reason: null, justification: null, current_level: 'usuario', level: 'admin',
  access: { id: 90, status: 'en_proceso' },
};
const ACTIVO: Access = { ...MOCK_ACCESS, id: 77, status: 'activo', origin: 'solicitud', level: 'usuario' };
const FALLIDO: Access = {
  ...MOCK_ACCESS, id: 79, status: 'fallido', platform: { ...MOCK_ACCESS.platform, id: 14, name: 'Wiki' },
};

function fila(nombre: string) {
  return screen.getByRole('listitem', { name: nombre });
}

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  vi.mocked(requestsApi.mine).mockResolvedValue(pagina([RECHAZADA, APROBADA]));
  vi.mocked(grantsApi.mine).mockResolvedValue(pagina([ACTIVO, FALLIDO]));
});

afterEach(cleanup);

describe('MyRequestsView', () => {
  it('superadmin: estado vacío explicado, sin pestañas ni llamadas a la API', () => {
    esSuperadmin = true;
    render(<MyRequestsView />);
    expect(screen.getByText(MENSAJE_SUPERADMIN)).toBeTruthy();
    expect(screen.queryByRole('tablist')).toBeNull();
    expect(requestsApi.mine).not.toHaveBeenCalled();
    expect(grantsApi.mine).not.toHaveBeenCalled();
  });

  it('abre en Mis solicitudes y cambia a Mis accesos', async () => {
    render(<MyRequestsView />);
    const solicitudes = screen.getByRole('tab', { name: 'Mis solicitudes' });
    expect(solicitudes.getAttribute('aria-selected')).toBe('true');
    await screen.findByRole('listitem', { name: 'Solicitud de Contabilidad' });
    expect(grantsApi.mine).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('tab', { name: 'Mis accesos' }));
    expect(screen.getByRole('tabpanel', { name: 'Mis accesos' })).toBeTruthy();
    await screen.findByRole('listitem', { name: 'Acceso a Contabilidad' });
    expect(grantsApi.mine).toHaveBeenCalledWith({ status: 'vigente', page: 1 });
  });
});

describe('Pestañas con teclado (WAI-ARIA)', () => {
  it('roving tabindex: solo la pestaña activa entra en el orden de Tab', () => {
    render(<MyRequestsView />);
    expect(screen.getByRole('tab', { name: 'Mis solicitudes' }).tabIndex).toBe(0);
    expect(screen.getByRole('tab', { name: 'Mis accesos' }).tabIndex).toBe(-1);
    expect(screen.getByRole('tabpanel').tabIndex).toBe(0);
  });

  it('flechas, Inicio y Fin mueven el foco y seleccionan', () => {
    render(<MyRequestsView />);
    const solicitudes = screen.getByRole('tab', { name: 'Mis solicitudes' });
    const accesos = screen.getByRole('tab', { name: 'Mis accesos' });
    fireEvent.keyDown(solicitudes, { key: 'ArrowRight' });
    expect(document.activeElement).toBe(accesos);
    expect(accesos.getAttribute('aria-selected')).toBe('true');
    expect(accesos.tabIndex).toBe(0);
    fireEvent.keyDown(accesos, { key: 'ArrowRight' });
    expect(document.activeElement).toBe(solicitudes);
    fireEvent.keyDown(solicitudes, { key: 'ArrowLeft' });
    expect(document.activeElement).toBe(accesos);
    fireEvent.keyDown(accesos, { key: 'Home' });
    expect(document.activeElement).toBe(solicitudes);
    fireEvent.keyDown(solicitudes, { key: 'End' });
    expect(document.activeElement).toBe(accesos);
    expect(screen.getByRole('tabpanel', { name: 'Mis accesos' })).toBeTruthy();
  });
});

describe('Mis solicitudes', () => {
  it('muestra estado, motivo de rechazo y el estado del acceso aprobado', async () => {
    render(<MyRequestsView />);
    const rechazada = await screen.findByRole('listitem', { name: 'Solicitud de Contabilidad' });
    expect(within(rechazada).getByText('Rechazada')).toBeTruthy();
    expect(within(rechazada).getByText('Motivo del rechazo')).toBeTruthy();
    expect(within(rechazada).getByText('Usa el reporte compartido del área.')).toBeTruthy();
    expect(within(rechazada).getByText(/por Luis Paz/)).toBeTruthy();

    const aprobada = fila('Solicitud de Nómina');
    expect(within(aprobada).getByText('Aprobada')).toBeTruthy();
    expect(within(aprobada).getByText('Acceso en proceso')).toBeTruthy();
    expect(within(aprobada).getByText('Al pedirla tenías Usuario')).toBeTruthy();
    expect(within(aprobada).queryByText('Motivo del rechazo')).toBeNull();
  });

  it('el filtro por estado pide la página 1 con ese estado', async () => {
    render(<MyRequestsView />);
    await screen.findByRole('listitem', { name: 'Solicitud de Contabilidad' });
    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrar mis solicitudes por estado' }),
      { target: { value: 'pendiente' } });
    await waitFor(() =>
      expect(requestsApi.mine).toHaveBeenLastCalledWith({ status: 'pendiente', page: 1 }));
  });

  it('pagina con Anterior y Siguiente', async () => {
    vi.mocked(requestsApi.mine).mockResolvedValue(pagina([RECHAZADA], { total: 30 }));
    render(<MyRequestsView />);
    const nav = await screen.findByRole('navigation', { name: 'Páginas de mis solicitudes' });
    expect(within(nav).getByText('Página 1 de 2 · 30 en total')).toBeTruthy();
    expect((within(nav).getByRole('button', { name: 'Anterior' }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(within(nav).getByRole('button', { name: 'Siguiente' }));
    await waitFor(() =>
      expect(requestsApi.mine).toHaveBeenLastCalledWith({ status: undefined, page: 2 }));
  });

  it('la región viva anuncia solo la página, no el total', async () => {
    vi.mocked(requestsApi.mine).mockResolvedValue(pagina([RECHAZADA], { total: 30 }));
    render(<MyRequestsView />);
    const nav = await screen.findByRole('navigation', { name: 'Páginas de mis solicitudes' });
    const vivas = nav.querySelectorAll('[aria-live]');
    expect(vivas).toHaveLength(1);
    expect(vivas[0].textContent).toBe('Página 1');
  });

  it('sin una segunda página no muestra la paginación', async () => {
    render(<MyRequestsView />);
    await screen.findByRole('listitem', { name: 'Solicitud de Contabilidad' });
    expect(screen.queryByRole('navigation', { name: 'Páginas de mis solicitudes' })).toBeNull();
  });

  it('vacío: invita a usar el catálogo', async () => {
    vi.mocked(requestsApi.mine).mockResolvedValue(pagina([]));
    render(<MyRequestsView />);
    expect(await screen.findByText('Aún no has solicitado accesos. Pídelos desde el catálogo.')).toBeTruthy();
  });

  it('error: mensaje propio sin texto del servidor y reintento', async () => {
    vi.mocked(requestsApi.mine).mockRejectedValueOnce(new ApiError(500, 'Traceback interno'));
    render(<MyRequestsView />);
    expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar tus solicitudes.');
    expect(screen.queryByText(/Traceback/)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    await screen.findByRole('listitem', { name: 'Solicitud de Contabilidad' });
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('sin permiso (403): mensaje de permiso', async () => {
    vi.mocked(requestsApi.mine).mockRejectedValue(new ApiError(403, 'Forbidden'));
    render(<MyRequestsView />);
    expect((await screen.findByRole('alert')).textContent).toBe('No tienes permiso para ver tus solicitudes.');
  });

  it('carga: indicador mientras no hay datos', () => {
    vi.mocked(requestsApi.mine).mockReturnValue(new Promise(() => {}));
    render(<MyRequestsView />);
    expect(screen.getByRole('status').textContent).toContain('Cargando tus solicitudes…');
  });
});

describe('Mis accesos', () => {
  async function abrirAccesos() {
    render(<MyRequestsView />);
    fireEvent.click(screen.getByRole('tab', { name: 'Mis accesos' }));
  }

  it('explica cada estado y el origen del acceso', async () => {
    await abrirAccesos();
    const activo = await screen.findByRole('listitem', { name: 'Acceso a Contabilidad' });
    expect(within(activo).getByText('Con acceso')).toBeTruthy();
    expect(within(activo).getByText(EXPLICACION_ESTADO.activo)).toBeTruthy();
    expect(within(activo).getByText('Por solicitud')).toBeTruthy();

    const fallido = fila('Acceso a Wiki');
    expect(within(fallido).getByText('Acceso fallido')).toBeTruthy();
    expect(within(fallido).getByText(EXPLICACION_ESTADO.fallido)).toBeTruthy();
    expect(within(fallido).getByText('Automático: administras el área')).toBeTruthy();
  });

  it('revocado: muestra el motivo', async () => {
    vi.mocked(grantsApi.mine).mockResolvedValue(pagina([{
      ...ACTIVO, status: 'revocado', revoked_at: '2026-10-15T10:00:00Z', revoke_reason: 'Cambio de puesto',
    }]));
    await abrirAccesos();
    const revocado = await screen.findByRole('listitem', { name: 'Acceso a Contabilidad' });
    expect(within(revocado).getByText('Motivo: Cambio de puesto')).toBeTruthy();
    expect(within(revocado).getByText(/^Retirado:/)).toBeTruthy();
  });

  it('el filtro por estado pide la página 1 con ese estado', async () => {
    await abrirAccesos();
    await screen.findByRole('listitem', { name: 'Acceso a Contabilidad' });
    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrar mis accesos por estado' }),
      { target: { value: 'revocado' } });
    await waitFor(() =>
      expect(grantsApi.mine).toHaveBeenLastCalledWith({ status: 'revocado', page: 1 }));
  });

  it('vacío con el filtro por defecto: invita a usar el catálogo', async () => {
    vi.mocked(grantsApi.mine).mockResolvedValue(pagina([]));
    await abrirAccesos();
    expect(await screen.findByText('Aún no tienes accesos. Solicítalos desde el catálogo.')).toBeTruthy();
  });

  it('error: mensaje propio y reintento', async () => {
    vi.mocked(grantsApi.mine).mockRejectedValueOnce(new Error('fallo de red'));
    await abrirAccesos();
    expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar tus accesos.');
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    await screen.findByRole('listitem', { name: 'Acceso a Contabilidad' });
  });

  it('sesión vencida (401): pide volver a iniciar sesión', async () => {
    vi.mocked(grantsApi.mine).mockRejectedValue(new ApiError(401, 'Unauthorized'));
    await abrirAccesos();
    expect((await screen.findByRole('alert')).textContent).toBe('Tu sesión terminó. Vuelve a iniciar sesión.');
  });
});

describe('Refresco solo con estados transitorios (DIS-033)', () => {
  afterEach(() => { vi.useRealTimers(); });

  async function avanzar(ms: number) {
    await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
  }

  it('solicitudes: sin pendientes ni accesos en proceso se detiene; con ellos refresca', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(requestsApi.mine).mockResolvedValue(pagina([RECHAZADA]));
    render(<MyRequestsView />);
    await avanzar(0);
    await avanzar(120_000);
    expect(requestsApi.mine).toHaveBeenCalledTimes(1);

    cleanup();
    vi.mocked(requestsApi.mine).mockClear();
    vi.mocked(requestsApi.mine).mockResolvedValue(pagina([APROBADA]));
    render(<MyRequestsView />);
    await avanzar(0);
    await avanzar(61_000);
    expect(vi.mocked(requestsApi.mine).mock.calls.length).toBeGreaterThanOrEqual(2);

    cleanup();
    vi.mocked(requestsApi.mine).mockClear();
    vi.mocked(requestsApi.mine).mockResolvedValue(pagina([{ ...RECHAZADA, status: 'pendiente' }]));
    render(<MyRequestsView />);
    await avanzar(0);
    await avanzar(61_000);
    expect(vi.mocked(requestsApi.mine).mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it('solicitudes: deja de refrescar cuando la respuesta ya no trae transitorios', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(requestsApi.mine)
      .mockResolvedValueOnce(pagina([APROBADA]))
      .mockResolvedValue(pagina([{ ...APROBADA, access: { id: 90, status: 'activo' } }]));
    render(<MyRequestsView />);
    await avanzar(0);
    await avanzar(61_000);
    expect(requestsApi.mine).toHaveBeenCalledTimes(2);
    await avanzar(180_000);
    expect(requestsApi.mine).toHaveBeenCalledTimes(2);
  });

  it('accesos: solo en_proceso o revocando refrescan', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(<MyRequestsView />);
    fireEvent.click(screen.getByRole('tab', { name: 'Mis accesos' }));
    await avanzar(0);
    await avanzar(120_000);
    expect(grantsApi.mine).toHaveBeenCalledTimes(1);

    cleanup();
    vi.mocked(grantsApi.mine).mockClear();
    vi.mocked(grantsApi.mine).mockResolvedValue(pagina([{ ...ACTIVO, status: 'revocando' }]));
    render(<MyRequestsView />);
    fireEvent.click(screen.getByRole('tab', { name: 'Mis accesos' }));
    await avanzar(0);
    await avanzar(61_000);
    expect(vi.mocked(grantsApi.mine).mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
