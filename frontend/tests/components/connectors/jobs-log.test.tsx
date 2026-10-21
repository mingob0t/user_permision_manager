/**
 * DIS-022: bitácora de ejecuciones (`GET /provisioning/jobs`, detalle y reintento;
 * contrato `conectores-y-ejecuciones.md` 1.1).
 * - Filas, estados con texto (incluido `cancelado`), filtros al contrato y a la página 1.
 * - Carga, vacío con y sin filtros, error sin texto del servidor.
 * - Detalle con intentos (texto escapado) y foco de vuelta.
 * - Reintentar: solo superadmin y `fallido`, con confirmación, fila actualizada,
 *   aviso con foco y 409/403 con mensaje propio.
 * - Refresco solo con ejecuciones transitorias.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Job, JobDetail, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/provisioning', () => ({
  provisioningApi: { jobs: vi.fn(), job: vi.fn(), retry: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { platforms: vi.fn(), areas: vi.fn() },
}));

let esSuperadmin = true;
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 1, role: esSuperadmin ? 'administrador' : 'admin_area',
      managed_areas: [{ id: 3, name: 'Finanzas' }], preferences: { refresh_interval: 15 },
      permissions: {
        is_admin: esSuperadmin, is_area_admin: !esSuperadmin,
        can_manage_areas: esSuperadmin, can_manage_system: esSuperadmin,
      },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { provisioningApi } from '@/lib/access/provisioning';
import {
  JobsLog, VACIO_EJECUCIONES, VACIO_EJECUCIONES_FILTROS, avisoReintento,
} from '@/components/connectors/jobs-log';
import { ESTADOS_EJECUCION, hayTransitorios, sePuedeReintentar } from '@/components/connectors/job-catalog';
import { describeRetryError } from '@/components/connectors/job-errors';
import { efectoReintento } from '@/components/connectors/job-retry-dialog';

function pagina<T>(items: T[], extra: Partial<Paginated<T>> = {}): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length, ...extra };
}

const FALLIDA: Job = {
  id: 301, status: 'fallido', operation: 'otorgar', provider: 'conector', access_id: 77,
  user: { id: 8, name: 'Ana Ruiz' }, platform: { id: 12, name: 'Contabilidad' },
  area: { id: 3, name: 'Finanzas' }, attempts_count: 5, max_attempts: 5,
  next_attempt_at: null, created_at: '2026-10-14T15:10:00Z', finished_at: '2026-10-14T15:40:00Z',
};
const CANCELADA: Job = { ...FALLIDA, id: 303, status: 'cancelado' };
const EXITOSA: Job = { ...FALLIDA, id: 304, status: 'exitoso', operation: 'revocar', provider: 'ldap' };
const DETALLE: JobDetail = {
  ...FALLIDA,
  attempts: [
    { n: 4, started_at: '2026-10-14T15:30:00Z', finished_at: '2026-10-14T15:30:02Z',
      result: 'error_transitorio', error: '<img src=x> Tiempo de espera agotado.' },
    { n: 5, started_at: '2026-10-14T15:39:58Z', finished_at: '2026-10-14T15:40:00Z',
      result: 'error_permanente', error: null },
  ],
};

const jobs = vi.mocked(provisioningApi.jobs);
const job = vi.mocked(provisioningApi.job);
const retry = vi.mocked(provisioningApi.retry);

beforeEach(() => {
  esSuperadmin = true;
  vi.mocked(api.areas).mockResolvedValue([{ id: 3, name: 'Finanzas' }] as never);
  vi.mocked(api.platforms).mockResolvedValue([]);
  jobs.mockResolvedValue(pagina([FALLIDA, CANCELADA, EXITOSA]));
  job.mockResolvedValue(DETALLE);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.useRealTimers();
});

async function lista() {
  render(<JobsLog />);
  return screen.findByRole('list', { name: 'Bitácora de ejecuciones' });
}

describe('reglas', () => {
  it('cada estado tiene texto; reintentar solo superadmin y fallido', () => {
    expect(ESTADOS_EJECUCION.cancelado.texto).toBe('Cancelada');
    expect(sePuedeReintentar(FALLIDA, true)).toBe(true);
    expect(sePuedeReintentar(FALLIDA, false)).toBe(false);
    expect(sePuedeReintentar(CANCELADA, true)).toBe(false);
    expect(hayTransitorios([FALLIDA, EXITOSA])).toBe(false);
    expect(hayTransitorios([{ ...FALLIDA, status: 'reintentando' }])).toBe(true);
  });

  it('mensajes del reintento sin el texto del servidor', () => {
    expect(describeRetryError(new ApiError(409, 'srv', { code: 'estado_invalido' })))
      .toMatchObject({ stale: true });
    expect(describeRetryError(new ApiError(403, 'srv')).message).toBe('Solo el superadmin reintenta ejecuciones.');
    expect(describeRetryError(new Error('srv')).message).not.toContain('srv');
  });
});

describe('lista', () => {
  it('muestra las filas con estado, intentos y operación', async () => {
    const ul = await lista();
    const filas = within(ul).getAllByRole('listitem');
    expect(filas).toHaveLength(3);
    expect(within(filas[0]).getByText('Fallida')).toBeTruthy();
    expect(within(filas[0]).getByText('Intentos: 5 de 5')).toBeTruthy();
    expect(within(filas[1]).getByText('Cancelada')).toBeTruthy();
    expect(within(filas[2]).getByText('Revocar · Directorio')).toBeTruthy();
  });

  it('los filtros van al contrato y vuelven a la página 1', async () => {
    jobs.mockResolvedValue(pagina([FALLIDA], { total: 60 }));
    await lista();
    fireEvent.click(screen.getByRole('button', { name: /Siguiente/ }));
    await waitFor(() => expect(jobs).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })));
    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'cancelado' } });
    fireEvent.change(screen.getByLabelText('Proveedor'), { target: { value: 'conector' } });
    await waitFor(() => expect(jobs).toHaveBeenLastCalledWith({
      status: 'cancelado', operation: undefined, provider: 'conector',
      area_id: undefined, platform_id: undefined, page: 1,
    }));
  });

  it('carga, vacío sin y con filtros', async () => {
    jobs.mockResolvedValue(pagina([]));
    render(<JobsLog />);
    expect(screen.getByText('Cargando las ejecuciones…')).toBeTruthy();
    expect(await screen.findByText(VACIO_EJECUCIONES)).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Operación'), { target: { value: 'revocar' } });
    expect(await screen.findByText(VACIO_EJECUCIONES_FILTROS)).toBeTruthy();
  });

  it('error sin texto del servidor', async () => {
    jobs.mockRejectedValue(new ApiError(500, 'Traceback interno'));
    render(<JobsLog />);
    expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar las ejecuciones.');
  });

  it('sin ejecuciones transitorias no refresca; con ellas sí', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(<JobsLog />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(jobs).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(30_000); });
    expect(jobs).toHaveBeenCalledTimes(1);

    cleanup();
    jobs.mockClear();
    jobs.mockResolvedValue(pagina([{ ...FALLIDA, status: 'reintentando' }]));
    render(<JobsLog />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(jobs).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(16_000); });
    expect(jobs).toHaveBeenCalledTimes(2);
  });
});

describe('anuncio de recarga', () => {
  it('"Recargando…" solo tras pulsar Recargar, no en el refresco automático', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    jobs.mockResolvedValue(pagina([{ ...FALLIDA, status: 'reintentando' }]));
    render(<JobsLog />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(screen.getByText('1 ejecución')).toBeTruthy();

    let resolver: (v: Paginated<Job>) => void = () => {};
    jobs.mockImplementationOnce(() => new Promise((r) => { resolver = r; }));
    await act(async () => { await vi.advanceTimersByTimeAsync(16_000); });
    expect(jobs).toHaveBeenCalledTimes(2);
    expect(screen.queryByText('Recargando…')).toBeNull();
    await act(async () => { resolver(pagina([{ ...FALLIDA, status: 'reintentando' }])); });

    jobs.mockImplementationOnce(() => new Promise((r) => { resolver = r; }));
    fireEvent.click(screen.getByRole('button', { name: 'Recargar' }));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(screen.getByText('Recargando…')).toBeTruthy();
    await act(async () => { resolver(pagina([FALLIDA])); });
    expect(screen.queryByText('Recargando…')).toBeNull();
  });
});

describe('detalle', () => {
  it('muestra los intentos como texto y devuelve el foco al cerrar', async () => {
    const ul = await lista();
    const boton = within(ul).getByRole('button', { name: 'Ver el detalle de la ejecución n.º 301' });
    fireEvent.click(boton);
    const dialogo = screen.getByRole('dialog', { name: 'Ejecución n.º 301' });
    expect(await within(dialogo).findByText('Error transitorio')).toBeTruthy();
    expect(within(dialogo).getByText('Error permanente')).toBeTruthy();
    expect(within(dialogo).getByText('Error: <img src=x> Tiempo de espera agotado.')).toBeTruthy();
    expect(dialogo.querySelector('img')).toBeNull();
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Cerrar' }));
    expect(document.activeElement).toBe(boton);
  });
});

describe('reintentar', () => {
  it('el admin de área no ve el botón', async () => {
    esSuperadmin = false;
    const ul = await lista();
    expect(within(ul).queryByRole('button', { name: /Reintentar/ })).toBeNull();
  });

  it('pide confirmación con el efecto, actualiza la fila y enfoca el aviso', async () => {
    retry.mockResolvedValue({ status: 'success', job: { ...DETALLE, status: 'pendiente' } });
    const ul = await lista();
    expect(within(ul).getAllByRole('button', { name: /^Reintentar/ })).toHaveLength(1);
    fireEvent.click(within(ul).getByRole('button', { name: 'Reintentar la ejecución n.º 301' }));
    const dialogo = screen.getByRole('dialog', { name: 'Reintentar ejecución' });
    expect(within(dialogo).getByText(efectoReintento(FALLIDA))).toBeTruthy();
    expect(retry).not.toHaveBeenCalled();
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Reintentar' }));
    await waitFor(() => expect(retry).toHaveBeenCalledWith(301));
    const aviso = await screen.findByText(avisoReintento(FALLIDA));
    await waitFor(() => expect(document.activeElement).toBe(aviso.closest('[role="status"]')));
    expect(within(ul).getByText('Pendiente')).toBeTruthy();
    expect(within(ul).queryByRole('button', { name: 'Reintentar la ejecución n.º 301' })).toBeNull();
  });

  it('409 estado_invalido: mensaje propio y recarga la lista', async () => {
    retry.mockRejectedValue(new ApiError(409, 'Solo se reintenta...', { code: 'estado_invalido' }));
    const ul = await lista();
    fireEvent.click(within(ul).getByRole('button', { name: 'Reintentar la ejecución n.º 301' }));
    const dialogo = screen.getByRole('dialog', { name: 'Reintentar ejecución' });
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Reintentar' }));
    expect(await within(dialogo).findByText(/Ya no se puede reintentar/)).toBeTruthy();
    await waitFor(() => expect(jobs).toHaveBeenCalledTimes(2));
  });
});
