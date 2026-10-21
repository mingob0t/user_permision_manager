/**
 * DIS-024: resumen de inicio por rol (`GET /home/summary`, contrato `inicio.md`).
 * - Usuario: mis solicitudes y mis accesos, enlazados a `/requests`.
 * - Admin de área: pendientes, resumen de sus áreas y lo propio.
 * - Superadmin: pendientes y resumen global, sin lo propio.
 * - Estados de carga, vacío y error (sin texto del servidor, con reintento).
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { HomeSummary } from '@/lib/access/types';

vi.mock('@/lib/access/home', () => ({ homeApi: { summary: vi.fn() } }));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: { preferences: { refresh_interval: 60 } },
  }),
}));

import { ApiError } from '@/lib/api';
import { homeApi } from '@/lib/access/home';
import {
  MENSAJES_VACIO, RoleSummary, RUTAS_INICIO, TITULOS, gruposDelResumen, resumenVacio,
} from '@/components/home/role-summary';

const USUARIO: HomeSummary = {
  scope: 'propio',
  my_access: { activo: 2, en_proceso: 1, fallido: 0 },
  my_requests: { pendiente: 1, aprobada: 3, rechazada: 0 },
};
const ADMIN: HomeSummary = {
  scope: 'areas',
  my_access: { activo: 2, en_proceso: 0, fallido: 0 },
  my_requests: { pendiente: 1, aprobada: 3, rechazada: 0 },
  pending_approvals: 4, failed_access: 1, oldest_pending_at: '2026-10-13T09:00:00Z',
  totals: { areas: 2, platforms: 7, active_access: 35 },
};
const SUPERADMIN: HomeSummary = {
  scope: 'global', pending_approvals: 9, failed_access: 2, oldest_pending_at: null,
  totals: { areas: 5, platforms: 20, active_access: 140 },
};

function enlace(nombre: string) {
  return screen.getByRole('link', { name: nombre });
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(cleanup);

describe('gruposDelResumen', () => {
  it('usuario: solo mis solicitudes y mis accesos', () => {
    expect(gruposDelResumen(USUARIO).map((g) => g.id)).toEqual(['mis-solicitudes', 'mis-accesos']);
  });

  it('admin: pendientes, sus áreas y lo propio', () => {
    expect(gruposDelResumen(ADMIN).map((g) => g.id))
      .toEqual(['pendientes', 'totales', 'mis-solicitudes', 'mis-accesos']);
  });

  it('superadmin: pendientes y global, sin lo propio', () => {
    const grupos = gruposDelResumen(SUPERADMIN);
    expect(grupos.map((g) => g.id)).toEqual(['pendientes', 'totales']);
    expect(grupos[1].titulo).toBe('Todo el sistema');
  });

  it('vacío solo si todos los contadores son cero', () => {
    const cero: HomeSummary = {
      scope: 'propio',
      my_access: { activo: 0, en_proceso: 0, fallido: 0 },
      my_requests: { pendiente: 0, aprobada: 0, rechazada: 0 },
    };
    expect(resumenVacio(gruposDelResumen(cero))).toBe(true);
    expect(resumenVacio(gruposDelResumen(USUARIO))).toBe(false);
  });
});

describe('RoleSummary', () => {
  it('carga: muestra el indicador mientras no hay datos', () => {
    vi.mocked(homeApi.summary).mockReturnValue(new Promise(() => {}));
    render(<RoleSummary />);
    expect(screen.getByRole('status').textContent).toContain('Cargando el resumen…');
  });

  it('usuario: sus contadores enlazan a Mis solicitudes; sin pendientes ni totales', async () => {
    vi.mocked(homeApi.summary).mockResolvedValue(USUARIO);
    render(<RoleSummary />);
    expect(await screen.findByRole('heading', { name: TITULOS.propio })).toBeTruthy();
    expect(enlace('Pendientes: 1. Ir a Mis solicitudes').getAttribute('href')).toBe(RUTAS_INICIO.solicitudes);
    expect(enlace('Con acceso: 2. Ir a Mis accesos').getAttribute('href')).toBe(RUTAS_INICIO.solicitudes);
    expect(enlace('En proceso: 1. Ir a Mis accesos').getAttribute('href')).toBe(RUTAS_INICIO.solicitudes);
    expect(screen.queryByRole('link', { name: /Ir a Aprobaciones/ })).toBeNull();
    expect(screen.queryByRole('link', { name: /Ir a Inventario/ })).toBeNull();
    expect(enlace('Ver auditoría').getAttribute('href')).toBe('/audit');
  });

  it('admin: pendientes y resumen de sus áreas con sus enlaces, más lo propio', async () => {
    vi.mocked(homeApi.summary).mockResolvedValue(ADMIN);
    render(<RoleSummary />);
    expect(await screen.findByRole('heading', { name: TITULOS.areas })).toBeTruthy();
    expect(enlace('Por aprobar: 4. Ir a Aprobaciones').getAttribute('href')).toBe(RUTAS_INICIO.aprobaciones);
    expect(enlace('Accesos con falla: 1. Ir a Inventario').getAttribute('href')).toBe(RUTAS_INICIO.inventario);
    expect(enlace('Áreas: 2. Ir a Áreas').getAttribute('href')).toBe(RUTAS_INICIO.areas);
    expect(enlace('Plataformas: 7. Ir a Administrar plataformas').getAttribute('href')).toBe(RUTAS_INICIO.plataformas);
    expect(enlace('Accesos activos: 35. Ir a Inventario').getAttribute('href')).toBe(RUTAS_INICIO.inventario);
    expect(screen.getByRole('heading', { name: 'Tus áreas' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Mis solicitudes' })).toBeTruthy();
    expect(screen.getByText(/La solicitud pendiente más antigua es del/)).toBeTruthy();
  });

  it('superadmin: pendientes y resumen global, sin mis solicitudes ni mis accesos', async () => {
    vi.mocked(homeApi.summary).mockResolvedValue(SUPERADMIN);
    render(<RoleSummary />);
    expect(await screen.findByRole('heading', { name: TITULOS.global })).toBeTruthy();
    expect(enlace('Por aprobar: 9. Ir a Aprobaciones')).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Todo el sistema' })).toBeTruthy();
    expect(screen.queryByRole('heading', { name: 'Mis solicitudes' })).toBeNull();
    expect(screen.queryByRole('link', { name: /Ir a Mis/ })).toBeNull();
    expect(screen.queryByText(/más antigua/)).toBeNull();
  });

  it('vacío: usuario sin solicitudes ni accesos ve el mensaje y el enlace al catálogo', async () => {
    vi.mocked(homeApi.summary).mockResolvedValue({
      scope: 'propio',
      my_access: { activo: 0, en_proceso: 0, fallido: 0 },
      my_requests: { pendiente: 0, aprobada: 0, rechazada: 0 },
    });
    render(<RoleSummary />);
    expect(await screen.findByText(MENSAJES_VACIO.propio)).toBeTruthy();
    expect(enlace('Ir al catálogo').getAttribute('href')).toBe(RUTAS_INICIO.catalogo);
  });

  it('error: mensaje sin texto del servidor y Reintentar vuelve a consultar', async () => {
    vi.mocked(homeApi.summary)
      .mockRejectedValueOnce(new ApiError(500, 'Traceback interno'))
      .mockResolvedValueOnce(USUARIO);
    render(<RoleSummary />);
    const alerta = await screen.findByRole('alert');
    expect(alerta.textContent).toContain('No se pudieron cargar los datos del resumen.');
    expect(alerta.textContent).not.toContain('Traceback');
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    await waitFor(() => expect(homeApi.summary).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole('heading', { name: TITULOS.propio })).toBeTruthy();
  });

  it('sin permiso (403): mensaje claro', async () => {
    vi.mocked(homeApi.summary).mockRejectedValue(new ApiError(403, 'Forbidden'));
    render(<RoleSummary />);
    expect((await screen.findByRole('alert')).textContent).toContain('No tienes permiso para ver los datos del resumen.');
  });
});
