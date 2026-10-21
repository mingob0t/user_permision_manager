/**
 * DIS-015: Bandeja de aprobaciones (`/approvals`; contrato `solicitudes.md` 1.1).
 * - Lista `inbox` con `pendiente` por defecto, filtros por estado y área.
 * - Aprobar con confirmación; rechazar con motivo de 10 a 500 caracteres.
 * - Tras decidir: la fila se actualiza sin recargar y se anuncia el resultado.
 * - Errores del contrato en español; carga, vacío y error de la lista.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AccessRequest, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/requests', () => ({
  requestsApi: { inbox: vi.fn(), approve: vi.fn(), reject: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { areas: vi.fn() },
}));

let esSuperadmin = false;
const MI_ID = 2;
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: MI_ID,
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
import { requestsApi } from '@/lib/access/requests';
import { MOCK_REQUEST } from '@/lib/access/mocks';
import { ApprovalsInbox, MENSAJE_PROPIA, mensajeVacio } from '@/components/access/approvals-inbox';
import { pistaMotivo } from '@/components/access/reject-dialog';
import { MENSAJES_DECISION, MOTIVO_MAX, describeDecisionError } from '@/components/access/request-errors';

function pagina<T>(items: T[], extra: Partial<Paginated<T>> = {}): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length, ...extra };
}

const PENDIENTE: AccessRequest = {
  ...MOCK_REQUEST, id: 41, status: 'pendiente', rejection_reason: null, decided_at: null,
  decided_by: null, justification: '<b>Cierre</b> mensual',
};
const PROPIA: AccessRequest = {
  ...PENDIENTE, id: 43, requester: { id: MI_ID, name: 'Luis Paz', email: 'luis@ejemplo.local' },
  platform: { id: 14, name: 'Wiki' },
};
const MOTIVO = 'Usa el reporte compartido del área.';

function fila(nombre: string) {
  return screen.getByRole('listitem', { name: nombre });
}
const FILA_ANA = 'Solicitud de Ana Ruiz para Contabilidad';

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  vi.mocked(requestsApi.inbox).mockResolvedValue(pagina([PENDIENTE, PROPIA]));
  vi.mocked(api.areas).mockResolvedValue([
    { id: 3, name: 'Finanzas' }, { id: 5, name: 'Ventas' },
  ] as Awaited<ReturnType<typeof api.areas>>);
});

afterEach(cleanup);

describe('ApprovalsInbox: lista', () => {
  it('pide pendientes por defecto y muestra solicitante, plataforma, nivel, estado y justificación escapada', async () => {
    render(<ApprovalsInbox />);
    const ana = await screen.findByRole('listitem', { name: FILA_ANA });
    expect(requestsApi.inbox).toHaveBeenCalledWith({ status: 'pendiente', area_id: undefined, page: 1 });
    expect(within(ana).getByText('Ana Ruiz')).toBeTruthy();
    expect(within(ana).getByText('ana@ejemplo.local')).toBeTruthy();
    expect(within(ana).getByText('Finanzas')).toBeTruthy();
    expect(within(ana).getByText('Pendiente')).toBeTruthy();
    // Texto, no HTML.
    expect(within(ana).getByText('<b>Cierre</b> mensual')).toBeTruthy();
    expect(ana.querySelector('b')).toBeNull();
  });

  it('la solicitud propia no tiene acciones y lo explica', async () => {
    render(<ApprovalsInbox />);
    const propia = await screen.findByRole('listitem', { name: 'Solicitud de Luis Paz para Wiki' });
    expect(within(propia).getByText(MENSAJE_PROPIA)).toBeTruthy();
    expect(within(propia).queryByRole('button')).toBeNull();
  });

  it('filtra por estado y por área (admin: sus áreas) y vuelve a la página 1', async () => {
    render(<ApprovalsInbox />);
    await screen.findByRole('listitem', { name: FILA_ANA });
    fireEvent.change(screen.getByLabelText('Filtrar la bandeja por estado'), { target: { value: 'rechazada' } });
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'rechazada', area_id: undefined, page: 1 }));
    const area = screen.getByLabelText('Filtrar la bandeja por área');
    expect(within(area).getAllByRole('option').map((o) => o.textContent))
      .toEqual(['Todas mis áreas', 'Finanzas']);
    expect(api.areas).not.toHaveBeenCalled();
    fireEvent.change(area, { target: { value: '3' } });
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'rechazada', area_id: 3, page: 1 }));
  });

  it('superadmin: el filtro de área lista todas las áreas', async () => {
    esSuperadmin = true;
    render(<ApprovalsInbox />);
    const area = screen.getByLabelText('Filtrar la bandeja por área');
    await waitFor(() => expect(within(area).getAllByRole('option').map((o) => o.textContent))
      .toEqual(['Todas las áreas', 'Finanzas', 'Ventas']));
  });

  it('carga, vacío y error con reintento', async () => {
    let resolver: (value: Paginated<AccessRequest>) => void = () => {};
    vi.mocked(requestsApi.inbox).mockReturnValueOnce(new Promise((r) => { resolver = r; }));
    render(<ApprovalsInbox />);
    expect(screen.getByText('Cargando la bandeja…')).toBeTruthy();
    resolver(pagina([]));
    expect(await screen.findByText(mensajeVacio('pendiente', false))).toBeTruthy();
    cleanup();

    vi.mocked(requestsApi.inbox).mockRejectedValueOnce(new ApiError(403, 'Forbidden'));
    render(<ApprovalsInbox />);
    expect(await screen.findByText('No tienes permiso para ver las solicitudes de tu bandeja.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByRole('listitem', { name: FILA_ANA })).toBeTruthy();
  });

  it('paginación', async () => {
    vi.mocked(requestsApi.inbox).mockResolvedValue(pagina([PENDIENTE], { total: 30 }));
    render(<ApprovalsInbox />);
    fireEvent.click(await screen.findByRole('button', { name: 'Siguiente' }));
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'pendiente', area_id: undefined, page: 2 }));
  });
});

describe('ApprovalsInbox: aprobar', () => {
  it('pide confirmación, aprueba con `approve(id)`, actualiza la fila y anuncia', async () => {
    vi.mocked(requestsApi.approve).mockResolvedValue({
      status: 'success',
      request: { ...PENDIENTE, status: 'aprobada', access: { id: 90, status: 'en_proceso' } },
    });
    render(<ApprovalsInbox />);
    const ana = await screen.findByRole('listitem', { name: FILA_ANA });
    fireEvent.click(within(ana).getByRole('button', { name: 'Aprobar la solicitud de Ana Ruiz para Contabilidad' }));
    const dialogo = screen.getByRole('dialog', { name: 'Aprobar solicitud' });
    expect(requestsApi.approve).not.toHaveBeenCalled();
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Aprobar' }));

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(requestsApi.approve).toHaveBeenCalledWith(41);
    expect(requestsApi.inbox).toHaveBeenCalledTimes(1);
    const actualizada = fila(FILA_ANA);
    expect(within(actualizada).getByText('Aprobada')).toBeTruthy();
    expect(within(actualizada).queryByRole('button')).toBeNull();
    const aviso = screen.getByText(/Solicitud aprobada: Ana Ruiz en Contabilidad/);
    expect(aviso.closest('[role="status"]')).toBeTruthy();
    await waitFor(() => expect(document.activeElement).toBe(aviso.closest('[role="status"]')));
  });

  it('cancelar no llama a la API y devuelve el foco al botón', async () => {
    render(<ApprovalsInbox />);
    const boton = within(await screen.findByRole('listitem', { name: FILA_ANA }))
      .getByRole('button', { name: /^Aprobar/ });
    fireEvent.click(boton);
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(requestsApi.approve).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(boton);
  });

  it.each([
    [new ApiError(409, 'x', { code: 'plataforma_no_disponible' }), MENSAJES_DECISION.plataforma_no_disponible, false],
    [new ApiError(409, 'x', { code: 'cuenta_inactiva' }), MENSAJES_DECISION.cuenta_inactiva, false],
    [new ApiError(409, 'x', { code: 'solicitud_ya_decidida' }), MENSAJES_DECISION.solicitud_ya_decidida, true],
    [new ApiError(404, 'x'), 'La solicitud ya no está en tu bandeja. La lista se actualizó.', true],
  ])('error %#: mensaje en español y recarga si quedó desactualizada', async (error, mensaje, recarga) => {
    vi.mocked(requestsApi.approve).mockRejectedValue(error);
    render(<ApprovalsInbox />);
    fireEvent.click(within(await screen.findByRole('listitem', { name: FILA_ANA }))
      .getByRole('button', { name: /^Aprobar/ }));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Aprobar' }));
    expect(await within(screen.getByRole('dialog')).findByText(mensaje)).toBeTruthy();
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenCalledTimes(recarga ? 2 : 1));
  });
});

describe('ApprovalsInbox: rechazar', () => {
  async function abrirRechazo() {
    render(<ApprovalsInbox />);
    fireEvent.click(within(await screen.findByRole('listitem', { name: FILA_ANA }))
      .getByRole('button', { name: /^Rechazar/ }));
    const dialogo = screen.getByRole('dialog', { name: 'Rechazar solicitud' });
    return {
      dialogo,
      motivo: within(dialogo).getByLabelText('Motivo del rechazo') as HTMLTextAreaElement,
      enviar: within(dialogo).getByRole('button', { name: 'Rechazar' }) as HTMLButtonElement,
    };
  }

  it('sin motivo suficiente no habilita el envío y lo explica', async () => {
    const { motivo, enviar } = await abrirRechazo();
    expect(enviar.disabled).toBe(true);
    expect(enviar.getAttribute('aria-describedby')).toBe('rechazo-motivo-pista');
    expect(motivo.getAttribute('aria-describedby')).toContain('rechazo-motivo-pista');
    expect(screen.getByText(pistaMotivo(0))).toBeTruthy();
    fireEvent.change(motivo, { target: { value: '   corto   ' } });
    expect(screen.getByText(pistaMotivo(5))).toBeTruthy();
    expect(enviar.disabled).toBe(true);
    fireEvent.change(motivo, { target: { value: 'x'.repeat(MOTIVO_MAX + 1) } });
    expect(enviar.disabled).toBe(true);
    expect(motivo.getAttribute('aria-invalid')).toBe('true');
    expect(requestsApi.reject).not.toHaveBeenCalled();
  });

  it('rechaza con el motivo recortado, actualiza la fila y anuncia', async () => {
    vi.mocked(requestsApi.reject).mockResolvedValue({
      status: 'success', request: { ...PENDIENTE, status: 'rechazada', rejection_reason: MOTIVO },
    });
    const { motivo, enviar } = await abrirRechazo();
    fireEvent.change(motivo, { target: { value: `  ${MOTIVO}  ` } });
    expect(enviar.disabled).toBe(false);
    fireEvent.click(enviar);
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(requestsApi.reject).toHaveBeenCalledWith(41, MOTIVO);
    const actualizada = fila(FILA_ANA);
    expect(within(actualizada).getByText('Rechazada')).toBeTruthy();
    expect(within(actualizada).getByText(MOTIVO)).toBeTruthy();
    expect(screen.getByText(/Solicitud rechazada: Ana Ruiz en Contabilidad/)).toBeTruthy();
  });

  it('422 en `reason`: error del campo con el foco; 403 `solicitud_propia` en español', async () => {
    vi.mocked(requestsApi.reject).mockRejectedValueOnce(
      new ApiError(422, 'x', { code: 'validacion', fields: { reason: 'Escribe entre 10 y 500 caracteres.' } }));
    const { dialogo, motivo, enviar } = await abrirRechazo();
    fireEvent.change(motivo, { target: { value: MOTIVO } });
    fireEvent.click(enviar);
    expect(await within(dialogo).findByText(MENSAJES_DECISION.validacion)).toBeTruthy();
    expect(within(dialogo).getByText('Escribe entre 10 y 500 caracteres.')).toBeTruthy();
    expect(motivo.getAttribute('aria-invalid')).toBe('true');
    expect(document.activeElement).toBe(motivo);

    vi.mocked(requestsApi.reject).mockRejectedValueOnce(new ApiError(403, 'x', { code: 'solicitud_propia' }));
    fireEvent.click(enviar);
    expect(await within(dialogo).findByText('No puedes decidir tu propia solicitud.')).toBeTruthy();
  });
});

describe('describeDecisionError', () => {
  it('cubre los códigos del contrato y no muestra texto del servidor', () => {
    for (const code of ['solicitud_propia', 'solicitud_ya_decidida', 'plataforma_no_disponible',
      'nivel_vigente', 'estado_invalido', 'cuenta_inactiva', 'validacion']) {
      const view = describeDecisionError(new ApiError(409, 'detalle interno', { code }));
      expect(view.message).toBe(MENSAJES_DECISION[code]);
    }
    expect(describeDecisionError(new ApiError(500, 'detalle interno')).message)
      .toBe('No se pudo guardar la decisión. Inténtalo de nuevo.');
    expect(describeDecisionError(new Error('x')).stale).toBe(false);
    expect(describeDecisionError(new ApiError(404, 'x')).stale).toBe(true);
  });
});
