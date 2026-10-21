/**
 * Auditoría (FNC-025; evolucionada en DIS-020): `/audit` con `GET /audit`
 * paginado (contrato `auditoria.md`).
 * - Filtros (búsqueda, fechas, evento, resultado, área y plataforma) a la página 1.
 * - Rango de fechas inválido: se explica y no se pide nada.
 * - Usuario: sin filtros de área ni plataforma.
 * - Carga, vacío (con y sin filtros), error sin detalles, recarga y paginación.
 * - Detalle en modal: antes y después como lista de campos, escapado.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditEntryV1, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/audit', () => ({
  auditApi: { list: vi.fn(), ofUser: vi.fn(), ofPlatform: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { areas: vi.fn(), platforms: vi.fn() },
}));

let rol: 'administrador' | 'admin_area' | 'usuario' = 'admin_area';
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 2,
      email: 'luis@ejemplo.local',
      role: rol,
      managed_areas: rol === 'admin_area' ? [{ id: 3, name: 'Finanzas' }] : [],
      preferences: { refresh_interval: 60 },
      permissions: {
        is_admin: rol === 'administrador', is_area_admin: rol === 'admin_area',
        can_manage_areas: rol === 'administrador', can_manage_system: rol === 'administrador',
      },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { auditApi } from '@/lib/access/audit';
import { MOCK_AUDIT } from '@/lib/access/mocks';
import { AuditLog } from '@/components/audit-log';
import { VACIO_CON_FILTROS, VACIO_SIN_FILTROS } from '@/components/audit/audit-history';
import {
  FILTROS_INICIALES, MENSAJE_FECHAS_INVERTIDAS, MENSAJE_RANGO_LARGO, aParametros, validarFechas,
} from '@/components/audit/audit-filters';
import { TITULO_DETALLE } from '@/components/audit/audit-detail-modal';

function pagina<T>(items: T[], extra: Partial<Paginated<T>> = {}): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length, ...extra };
}

const CREADA: AuditEntryV1 = { ...MOCK_AUDIT };
const EDITADA: AuditEntryV1 = {
  ...MOCK_AUDIT, id: 9001, time: '2026-10-15T10:00:00Z', action: 'plataforma_editada',
  status: 'error', actor: null, user: 'sistema', detail: '<img src=x onerror=alert(1)>',
  before: { name: 'Conta', active: true }, after: { name: 'Contabilidad', active: true },
};

const BASE = { page: 1 };

const PLATAFORMAS = [
  { id: 12, name: 'Contabilidad', area_id: 3 },
  { id: 20, name: 'CRM', area_id: 5 },
] as unknown as Awaited<ReturnType<typeof api.platforms>>;

function ultimaLlamada() {
  return vi.mocked(auditApi.list).mock.lastCall?.[0];
}

beforeEach(() => {
  vi.clearAllMocks();
  rol = 'admin_area';
  vi.mocked(auditApi.list).mockResolvedValue(pagina([CREADA, EDITADA]));
  vi.mocked(api.platforms).mockResolvedValue(PLATAFORMAS);
  vi.mocked(api.areas).mockResolvedValue([
    { id: 3, name: 'Finanzas' }, { id: 5, name: 'Ventas' },
  ] as Awaited<ReturnType<typeof api.areas>>);
});

afterEach(cleanup);

async function filas() {
  return screen.findAllByRole('listitem', { name: /2026/ });
}

describe('AuditLog: lista', () => {
  it('pide la página 1 paginada y muestra quién, evento, sobre qué y resultado', async () => {
    render(<AuditLog />);
    const [creada] = await filas();
    expect(auditApi.list).toHaveBeenCalledWith(BASE);
    for (const texto of ['luis@ejemplo.local', 'Plataforma creada', 'Alta de plataforma',
      'Contabilidad', 'Contabilidad · Finanzas', 'Éxito']) {
      expect(within(creada).getByText(texto)).toBeTruthy();
    }
    for (const etiqueta of ['Fecha', 'Quién', 'Evento', 'Sobre', 'Resultado']) {
      expect(within(creada).getByText(etiqueta, { selector: 'dt' })).toBeTruthy();
    }
    expect(screen.getByText('2 registros')).toBeTruthy();
  });

  it('actor null: "Sistema"; acción fuera del catálogo, tal cual', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(pagina([
      EDITADA, { ...CREADA, id: 5, action: 'Creó el área Ventas', actor: null, user: 'ana' },
    ]));
    render(<AuditLog />);
    const [editada, libre] = await filas();
    expect(within(editada).getByText('Sistema')).toBeTruthy();
    expect(within(libre).getByText('Creó el área Ventas')).toBeTruthy();
    expect(within(libre).getByText('ana')).toBeTruthy();
  });

  it('el detalle con HTML se muestra como texto, sin interpretarlo', async () => {
    const { container } = render(<AuditLog />);
    await filas();
    expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeTruthy();
    expect(container.querySelector('img')).toBeNull();
  });
});

describe('AuditLog: filtros', () => {
  it('admin: búsqueda, evento, resultado, área y plataforma a la página 1', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(pagina([CREADA], { total: 60 }));
    render(<AuditLog />);
    await filas();
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    await waitFor(() => expect(ultimaLlamada()).toEqual({ page: 2 }));

    await waitFor(() => expect(
      within(screen.getByLabelText('Plataforma')).getAllByRole('option').map((o) => o.textContent),
    ).toEqual(['Todas las plataformas', 'Contabilidad']));
    fireEvent.change(screen.getByLabelText('Evento'), { target: { value: 'acceso_revocado' } });
    fireEvent.change(screen.getByLabelText('Resultado'), { target: { value: 'error' } });
    fireEvent.change(screen.getByLabelText('Área'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Plataforma'), { target: { value: '12' } });
    const buscador = screen.getByLabelText('Buscar en la auditoría por quién actuó o sobre qué');
    fireEvent.change(buscador, { target: { value: ' luis\u0007\u0085 ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await waitFor(() => expect(ultimaLlamada()).toEqual({
      page: 1, action: 'acceso_revocado', result: 'error', area_id: 3, platform_id: 12, q: 'luis',
    }));
    expect(api.areas).not.toHaveBeenCalled();
  });

  it('fechas válidas llegan como from/to (AAAA-MM-DD)', async () => {
    render(<AuditLog />);
    await filas();
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-10-01' } });
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-10-20' } });
    await waitFor(() => expect(ultimaLlamada()).toEqual({ page: 1, from: '2026-10-01', to: '2026-10-20' }));
  });

  it('rango invertido: se explica, se marca y no se pide nada', async () => {
    render(<AuditLog />);
    await filas();
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-10-01' } });
    await waitFor(() => expect(ultimaLlamada()).toEqual({ page: 1, to: '2026-10-01' }));
    const llamadas = vi.mocked(auditApi.list).mock.calls.length;
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-10-05' } });
    expect(screen.getByRole('alert').textContent).toBe(MENSAJE_FECHAS_INVERTIDAS);
    expect(screen.getByLabelText('Desde').getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByLabelText('Desde').getAttribute('aria-describedby')).toBeTruthy();
    expect(vi.mocked(auditApi.list).mock.calls.length).toBe(llamadas);
  });

  it('superadmin: todas las áreas (`GET /areas`)', async () => {
    rol = 'administrador';
    render(<AuditLog />);
    await waitFor(() => expect(
      within(screen.getByLabelText('Área')).getAllByRole('option').map((o) => o.textContent),
    ).toEqual(['Todas las áreas', 'Finanzas', 'Ventas']));
  });

  it('usuario: sin filtros de área ni plataforma y sin pedir catálogos', async () => {
    rol = 'usuario';
    render(<AuditLog />);
    await filas();
    expect(screen.queryByLabelText('Área')).toBeNull();
    expect(screen.queryByLabelText('Plataforma')).toBeNull();
    expect(api.platforms).not.toHaveBeenCalled();
    expect(api.areas).not.toHaveBeenCalled();
  });
});

describe('AuditLog: estados', () => {
  it('carga', () => {
    vi.mocked(auditApi.list).mockReturnValue(new Promise(() => {}));
    render(<AuditLog />);
    expect(screen.getByText('Cargando la auditoría…')).toBeTruthy();
  });

  it('vacío sin filtros y con filtros, anunciado', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(pagina([]));
    render(<AuditLog />);
    expect(await screen.findByText(VACIO_SIN_FILTROS)).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Resultado'), { target: { value: 'warning' } });
    const vacio = await screen.findByText(VACIO_CON_FILTROS);
    expect(vacio.closest('[role="status"]')).toBeTruthy();
  });

  it('error genérico sin detalles del servidor y reintento', async () => {
    vi.mocked(auditApi.list).mockRejectedValueOnce(new ApiError(500, 'Traceback interno'));
    render(<AuditLog />);
    expect((await screen.findByRole('alert')).textContent)
      .toBe('No se pudieron cargar los registros de auditoría.');
    expect(screen.queryByText(/Traceback/)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect((await filas()).length).toBe(2);
  });

  it('Recargar conserva el foco mientras carga y repite la misma página', async () => {
    render(<AuditLog />);
    await filas();
    let terminar: (valor: Paginated<AuditEntryV1>) => void = () => {};
    vi.mocked(auditApi.list).mockReturnValueOnce(new Promise((r) => { terminar = r; }));
    const boton = screen.getByRole('button', { name: 'Recargar' });
    boton.focus();
    fireEvent.click(boton);
    await waitFor(() => expect(boton.getAttribute('aria-disabled')).toBe('true'));
    expect(document.activeElement).toBe(boton);
    fireEvent.click(boton);
    expect(auditApi.list).toHaveBeenCalledTimes(2);
    expect(ultimaLlamada()).toEqual(BASE);
    terminar(pagina([CREADA]));
    await waitFor(() => expect(boton.getAttribute('aria-disabled')).toBeNull());
  });
});

describe('AuditLog: detalle', () => {
  it('antes y después como lista de campos; cerrar devuelve el foco', async () => {
    render(<AuditLog />);
    const [, editada] = await filas();
    const abrir = within(editada).getByRole('button', { name: /^Ver detalle/ });
    fireEvent.click(abrir);
    const dialogo = screen.getByRole('dialog', { name: TITULO_DETALLE });
    expect(within(dialogo).getByText('Antes y después')).toBeTruthy();
    expect(within(dialogo).getByText('name')).toBeTruthy();
    expect(within(dialogo).getByText('Conta')).toBeTruthy();
    expect(within(dialogo).getAllByText('Contabilidad').length).toBeGreaterThan(0);
    expect(within(dialogo).getAllByText('Sí')).toHaveLength(2);
    expect(within(dialogo).getAllByText('Cambió')).toHaveLength(1);
    expect(within(dialogo).queryByText(/[{}]/)).toBeNull();
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Cerrar' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(abrir));
  });

  it('solo `after`: "Valores registrados"; sin before/after ni IP (usuario): no se muestran', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(pagina([
      CREADA, { ...EDITADA, before: null, after: null, ip: null },
    ]));
    render(<AuditLog />);
    const [creada, editada] = await filas();
    fireEvent.click(within(creada).getByRole('button', { name: /^Ver detalle/ }));
    let dialogo = screen.getByRole('dialog');
    expect(within(dialogo).getByText('Valores registrados')).toBeTruthy();
    expect(within(dialogo).getByText('integration_type')).toBeTruthy();
    expect(within(dialogo).queryByText('Antes')).toBeNull();
    fireEvent.keyDown(document, { key: 'Escape' });
    fireEvent.click(within(editada).getByRole('button', { name: /^Ver detalle/ }));
    dialogo = screen.getByRole('dialog');
    expect(within(dialogo).queryByText('Antes y después')).toBeNull();
    expect(within(dialogo).queryByText('IP')).toBeNull();
  });
});

describe('AuditLog: utilidades', () => {
  it('validarFechas: invertidas, más de 366 días e incompletas', () => {
    expect(validarFechas('2026-10-05', '2026-10-01')).toBe(MENSAJE_FECHAS_INVERTIDAS);
    expect(validarFechas('2025-01-01', '2026-01-03')).toBe(MENSAJE_RANGO_LARGO);
    expect(validarFechas('2025-01-01', '2026-01-02')).toBeNull();
    expect(validarFechas('', '2026-01-02')).toBeNull();
  });

  it('aParametros omite los filtros vacíos', () => {
    expect(aParametros(FILTROS_INICIALES, 3)).toEqual({
      page: 3, q: undefined, from: undefined, to: undefined, action: undefined,
      result: undefined, area_id: undefined, platform_id: undefined,
    });
  });
});
