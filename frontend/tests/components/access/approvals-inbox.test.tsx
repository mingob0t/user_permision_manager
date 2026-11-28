/**
 * DIS-015: Bandeja de aprobaciones (`/approvals`; contrato `solicitudes.md` 1.1).
 * - Lista `inbox` con `pendiente` por defecto, filtros por estado y área.
 * - Aprobar con confirmación; rechazar con motivo de 10 a 500 caracteres.
 * - Tras decidir: la fila se actualiza sin recargar y se anuncia el resultado.
 * - Errores del contrato en español; carga, vacío y error de la lista.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastProvider } from '@/components/toast';

/** Con el proveedor de avisos: los resultados se anuncian con toast (DIS-091). */
function renderConToast(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>);
}
import type { AccessRequest, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/requests', () => ({
  requestsApi: { inbox: vi.fn(), approve: vi.fn(), reject: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { areas: vi.fn(), platforms: vi.fn() },
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
import { elegirEnSelector, opcionesSelector, valorSelector } from '../../utils/selector-toolbar';
import { requestsApi } from '@/lib/access/requests';
import { MOCK_REQUEST } from '@/lib/access/mocks';
import { ApprovalsInbox, MENSAJE_PROPIA, mensajeVacio } from '@/components/access/approvals-inbox';
import { pistaMotivo } from '@/components/access/reject-dialog';
import { MENSAJES_DECISION, MOTIVO_MAX, describeDecisionError } from '@/components/access/request-errors';

function pagina<T>(items: T[], extra: Partial<Paginated<T>> = {}): Paginated<T> {
  return { items, page: 1, per_page: 8, total: items.length, ...extra };
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

/** Fila de la tabla (DIS-156) que contiene al solicitante. */
function fila(nombre: string): HTMLElement {
  const celda = screen.getByText(nombre);
  return celda.closest('tr') as HTMLElement;
}
async function filaAsync(nombre: string): Promise<HTMLElement> {
  await screen.findByText(nombre);
  return fila(nombre);
}
const FILA_ANA = 'Ana Ruiz';

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  // DIS-163: los filtros se guardan en la pestaña; cada prueba parte limpia.
  window.sessionStorage.clear();
  window.history.replaceState(null, '', '/');
  vi.mocked(requestsApi.inbox).mockResolvedValue(pagina([PENDIENTE, PROPIA]));
  vi.mocked(api.platforms).mockResolvedValue([
    { id: 12, name: 'Contabilidad' }, { id: 14, name: 'Wiki' },
  ] as unknown as Awaited<ReturnType<typeof api.platforms>>);
  vi.mocked(api.areas).mockResolvedValue([
    { id: 3, name: 'Finanzas' }, { id: 5, name: 'Ventas' },
  ] as Awaited<ReturnType<typeof api.areas>>);
});

afterEach(cleanup);

describe('ApprovalsInbox: lista', () => {
  it('pide pendientes por defecto y muestra solicitante, plataforma, nivel, estado y justificación escapada', async () => {
    render(<ApprovalsInbox />);
    const ana = await filaAsync(FILA_ANA);
    expect(requestsApi.inbox).toHaveBeenCalledWith({ status: 'pendiente', area_id: undefined, page: 1, per_page: 8 });
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
    const propia = await filaAsync('Luis Paz');
    expect(within(propia).getByText(MENSAJE_PROPIA, { exact: false })).toBeTruthy();
    expect(within(propia).queryByRole('button')).toBeNull();
  });

  it('filtra por estado y por área (admin: sus áreas) y vuelve a la página 1', async () => {
    render(<ApprovalsInbox />);
    await filaAsync(FILA_ANA);
    elegirEnSelector('Filtrar la bandeja por estado', 'Rechazadas');
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'rechazada', area_id: undefined, page: 1, per_page: 8 }));
    expect(opcionesSelector('Filtrar la bandeja por área')).toEqual(['Todas mis áreas', 'Finanzas']);
    expect(api.areas).not.toHaveBeenCalled();
    elegirEnSelector('Filtrar la bandeja por área', 'Finanzas');
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'rechazada', area_id: 3, page: 1, per_page: 8 }));
  });

  it('superadmin: el filtro de área lista todas las áreas', async () => {
    esSuperadmin = true;
    render(<ApprovalsInbox />);
    await waitFor(() => expect(opcionesSelector('Filtrar la bandeja por área')).toEqual(['Todas', 'Finanzas', 'Ventas']));
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
    renderConToast(<ApprovalsInbox />);
    // DIS-157: el mensaje sale en un toast; sin datos queda solo Reintentar.
    const aviso = await screen.findByText('No tienes permiso para ver las solicitudes de tu bandeja.');
    expect(aviso.closest('.nx-toast')).toBeTruthy();
    expect(screen.getByText('No se pudo cargar la lista.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar la carga de solicitudes' }));
    expect(await filaAsync(FILA_ANA)).toBeTruthy();
  });

  it('DIS-157: con la tabla cargada, el fallo de carga sale en un solo toast y la tabla sigue', async () => {
    vi.mocked(requestsApi.inbox).mockResolvedValueOnce(pagina([PENDIENTE]));
    renderConToast(<ApprovalsInbox />);
    expect(await filaAsync(FILA_ANA)).toBeTruthy();

    vi.mocked(requestsApi.inbox).mockRejectedValue(new ApiError(403, 'Forbidden'));
    elegirEnSelector('Filtrar la bandeja por estado', 'Rechazadas');
    const mensaje = 'No tienes permiso para ver las solicitudes de tu bandeja.';
    const aviso = await screen.findByText(mensaje);
    expect(aviso.closest('.nx-toast')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Reintentar la carga de solicitudes' })).toBeNull();
    expect(await filaAsync(FILA_ANA)).toBeTruthy();

    // Otro fallo seguido no repite el aviso.
    elegirEnSelector('Filtrar la bandeja por estado', 'Aprobadas');
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenCalledTimes(3));
    await waitFor(() => expect(screen.getAllByText(mensaje)).toHaveLength(1));
  });

  it('paginación', async () => {
    vi.mocked(requestsApi.inbox).mockResolvedValue(pagina([PENDIENTE], { total: 30 }));
    render(<ApprovalsInbox />);
    fireEvent.click(await screen.findByRole('button', { name: /Página siguiente/ }));
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'pendiente', area_id: undefined, page: 2, per_page: 8 }));
  });
});

describe('ApprovalsInbox: historial con filtros (DIS-156)', () => {
  it('barra de herramientas: Volver, buscador, estado, área y plataforma', async () => {
    render(<ApprovalsInbox volverHref="/approvals" />);
    await filaAsync(FILA_ANA);
    const volver = screen.getByRole('link', { name: 'Volver al resumen de Solicitudes' });
    expect(volver.getAttribute('href')).toBe('/approvals');
    expect(volver.className).toContain('nx-btn-toolbar');
    expect(screen.getByRole('searchbox').className).toContain('nx-buscador-toolbar');
    expect(opcionesSelector('Filtrar la bandeja por estado')).toEqual(['Todas', 'Pendientes', 'Aprobadas', 'Rechazadas']);
    expect(valorSelector('Filtrar la bandeja por estado')).toBe('Pendientes');
    expect(screen.getByLabelText('Filtrar la bandeja por plataforma')).toBeTruthy();
  });

  it('la tabla tiene las columnas compactas, justificación truncada con título y pie de registros', async () => {
    render(<ApprovalsInbox />);
    const ana = await filaAsync(FILA_ANA);
    const cabeceras = screen.getAllByRole('columnheader').map((c) => c.textContent);
    expect(cabeceras).toEqual(['Solicitante', 'Plataforma', 'Nivel', 'Estado', 'Justificación', 'Acciones']);
    expect(within(ana).getByText('<b>Cierre</b> mensual').getAttribute('title')).toBe('<b>Cierre</b> mensual');
    expect(within(ana).getByRole('button', { name: /^Aprobar/ })).toBeTruthy();
    expect(screen.getByText('2 de 2 registros')).toBeTruthy();
  });

  it('«Todas»: pide `status=todas`, muestra el estado de cada fila y acciones solo en pendientes', async () => {
    const aprobada: AccessRequest = {
      ...PENDIENTE, id: 50, status: 'aprobada', requester: { id: 9, name: 'Eva Lara', email: 'eva@ejemplo.local' },
      decided_at: '2026-10-13T12:30:00Z', decided_by: { id: 2, name: 'Luis Paz' },
    };
    const rechazada: AccessRequest = {
      ...PENDIENTE, id: 51, status: 'rechazada', rejection_reason: MOTIVO,
      requester: { id: 10, name: 'Raúl Soto', email: 'raul@ejemplo.local' },
    };
    vi.mocked(requestsApi.inbox).mockResolvedValue(pagina([PENDIENTE, aprobada, rechazada]));
    render(<ApprovalsInbox />);
    await filaAsync(FILA_ANA);
    elegirEnSelector('Filtrar la bandeja por estado', 'Todas');
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'todas', area_id: undefined, page: 1, per_page: 8 }));
    expect(within(fila('Ana Ruiz')).getByText('Pendiente')).toBeTruthy();
    expect(within(fila('Eva Lara')).getByText('Aprobada')).toBeTruthy();
    expect(within(fila('Eva Lara')).queryByRole('button')).toBeNull();
    expect(within(fila('Raúl Soto')).getByText('Rechazada')).toBeTruthy();
    expect(within(fila('Raúl Soto')).getByText(MOTIVO)).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: 'Motivo del rechazo' })).toBeTruthy();
  });

  it('el buscador envía `q` recortado al backend con retraso y vuelve a la página 1', async () => {
    render(<ApprovalsInbox />);
    await filaAsync(FILA_ANA);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: '  ana  ' } });
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'pendiente', area_id: undefined, q: 'ana', page: 1, per_page: 8 }));
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar búsqueda' }));
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'pendiente', area_id: undefined, page: 1, per_page: 8 }));
  });

  it('sin resultados con búsqueda: lo explica y permite limpiarla', async () => {
    vi.mocked(requestsApi.inbox).mockResolvedValue(pagina([]));
    render(<ApprovalsInbox />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'zzz' } });
    expect(await screen.findByText(/No hay solicitudes que coincidan con «zzz»/)).toBeTruthy();
    expect(screen.getAllByRole('button', { name: /Limpiar búsqueda/ })).toHaveLength(2);
  });

  it('área > plataforma en cascada: la plataforma se pide por área y cambiar el área la limpia', async () => {
    render(<ApprovalsInbox />);
    await filaAsync(FILA_ANA);
    expect(api.platforms).toHaveBeenLastCalledWith({});
    elegirEnSelector('Filtrar la bandeja por área', 'Finanzas');
    await waitFor(() => expect(api.platforms).toHaveBeenLastCalledWith({ areaId: 3 }));
    await waitFor(() => expect(opcionesSelector('Filtrar la bandeja por plataforma')).toHaveLength(3));
    elegirEnSelector('Filtrar la bandeja por plataforma', 'Wiki');
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'pendiente', area_id: 3, platform_id: 14, page: 1, per_page: 8 }));
    elegirEnSelector('Filtrar la bandeja por área', 'Todas mis áreas');
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenLastCalledWith(
      { status: 'pendiente', area_id: undefined, page: 1, per_page: 8 }));
    expect(valorSelector('Filtrar la bandeja por plataforma')).toBe('Todas');
  });

  it('DIS-163: URL limpia; los filtros se guardan en la pestaña y se recuperan al recargar', async () => {
    window.history.replaceState(null, '', '/approvals?status=pendiente&area_id=3');
    render(<ApprovalsInbox />);
    await filaAsync(FILA_ANA);
    elegirEnSelector('Filtrar la bandeja por estado', 'Aprobadas');
    elegirEnSelector('Filtrar la bandeja por área', 'Finanzas');
    await waitFor(() => expect(window.location.pathname).toBe('/approvals/historial'));
    expect(window.location.search).toBe('');
    cleanup();

    // «F5»: sin parámetros en la URL, se usan los guardados.
    vi.mocked(requestsApi.inbox).mockClear();
    render(<ApprovalsInbox />);
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'aprobada', area_id: 3 })));
  });

  it('DIS-163: sin sessionStorage disponible usa los valores por defecto y no falla', async () => {
    const obtener = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('bloqueado'); });
    const guardar = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('bloqueado'); });
    render(<ApprovalsInbox />);
    expect(await filaAsync(FILA_ANA)).toBeTruthy();
    expect(requestsApi.inbox).toHaveBeenCalledWith(expect.objectContaining({ status: 'pendiente' }));
    obtener.mockRestore();
    guardar.mockRestore();
  });
});

describe('ApprovalsInbox: aprobar', () => {
  it('pide confirmación, aprueba con `approve(id)`, actualiza la fila y anuncia', async () => {
    vi.mocked(requestsApi.approve).mockResolvedValue({
      status: 'success',
      request: { ...PENDIENTE, status: 'aprobada', access: { id: 90, status: 'en_proceso' } },
    });
    renderConToast(<ApprovalsInbox />);
    const ana = await filaAsync(FILA_ANA);
    fireEvent.click(within(ana).getByRole('button', { name: 'Aprobar la solicitud de Ana Ruiz para Contabilidad' }));
    const dialogo = screen.getByRole('alertdialog', { name: 'Aprobar solicitud' });
    expect(requestsApi.approve).not.toHaveBeenCalled();
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Aprobar' }));

    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
    expect(requestsApi.approve).toHaveBeenCalledWith(41);
    expect(requestsApi.inbox).toHaveBeenCalledTimes(1);
    const actualizada = fila(FILA_ANA);
    expect(within(actualizada).getByText('Aprobada')).toBeTruthy();
    expect(within(actualizada).queryByRole('button')).toBeNull();
    // DIS-091: el resultado sale en un toast (`status`); el foco va al filtro de estado.
    const aviso = screen.getByText(/Solicitud aprobada: Ana Ruiz en Contabilidad/);
    expect(aviso.closest('.nx-toast')).toBeTruthy();
    expect(aviso.closest('[role="status"]')).toBeTruthy();
    await waitFor(() => expect(document.activeElement?.id).toBe('bandeja-filtro-estado'));
  });

  it('cancelar no llama a la API y devuelve el foco al botón', async () => {
    render(<ApprovalsInbox />);
    const boton = within(await filaAsync(FILA_ANA))
      .getByRole('button', { name: /^Aprobar/ });
    fireEvent.click(boton);
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
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
    fireEvent.click(within(await filaAsync(FILA_ANA))
      .getByRole('button', { name: /^Aprobar/ }));
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Aprobar' }));
    expect(await within(screen.getByRole('alertdialog')).findByText(mensaje)).toBeTruthy();
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenCalledTimes(recarga ? 2 : 1));
  });
});

describe('ApprovalsInbox: foco (auditor-accesibilidad)', () => {
  it('mientras se aprueba el botón queda `aria-disabled` con el foco; si falla, el foco sigue ahí', async () => {
    let fallar: (e: unknown) => void = () => {};
    vi.mocked(requestsApi.approve).mockReturnValue(new Promise((_, rej) => { fallar = rej; }));
    render(<ApprovalsInbox />);
    fireEvent.click(within(await filaAsync(FILA_ANA))
      .getByRole('button', { name: /^Aprobar/ }));
    const boton = within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Aprobar' }) as HTMLButtonElement;
    boton.focus();
    fireEvent.click(boton);
    const enviando = within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Aprobando…' }) as HTMLButtonElement;
    expect(enviando.disabled).toBe(false);
    expect(enviando.getAttribute('aria-disabled')).toBe('true');
    expect(document.activeElement).toBe(enviando);
    fireEvent.click(enviando);
    expect(requestsApi.approve).toHaveBeenCalledTimes(1);
    fallar(new ApiError(409, 'x', { code: 'nivel_vigente' }));
    expect(await screen.findByText(MENSAJES_DECISION.nivel_vigente)).toBeTruthy();
    expect(document.activeElement).toBe(boton);
  });

  it('mientras se rechaza el botón queda `aria-disabled` con el foco', async () => {
    vi.mocked(requestsApi.reject).mockReturnValue(new Promise(() => {}));
    render(<ApprovalsInbox />);
    fireEvent.click(within(await filaAsync(FILA_ANA))
      .getByRole('button', { name: /^Rechazar/ }));
    const dialogo = screen.getByRole('alertdialog');
    fireEvent.change(within(dialogo).getByLabelText('Motivo del rechazo'), { target: { value: MOTIVO } });
    const boton = within(dialogo).getByRole('button', { name: 'Rechazar' }) as HTMLButtonElement;
    boton.focus();
    fireEvent.click(boton);
    const enviando = await within(dialogo).findByRole('button', { name: 'Rechazando…' }) as HTMLButtonElement;
    expect(enviando.disabled).toBe(false);
    expect(enviando.getAttribute('aria-disabled')).toBe('true');
    expect(document.activeElement).toBe(enviando);
  });

  it('al cerrar, si el botón de la fila ya no existe, el foco va al filtro de estado', async () => {
    render(<ApprovalsInbox />);
    const boton = within(await filaAsync(FILA_ANA))
      .getByRole('button', { name: /^Aprobar/ });
    fireEvent.click(boton);
    boton.remove();
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Cancelar' }));
    expect(document.activeElement).toBe(screen.getByLabelText('Filtrar la bandeja por estado'));
  });
});

describe('ApprovalsInbox: rechazar', () => {
  async function abrirRechazo(renderizar: (ui: React.ReactElement) => unknown = render) {
    renderizar(<ApprovalsInbox />);
    fireEvent.click(within(await filaAsync(FILA_ANA))
      .getByRole('button', { name: /^Rechazar/ }));
    const dialogo = screen.getByRole('alertdialog', { name: 'Rechazar solicitud' });
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
    const { motivo, enviar } = await abrirRechazo(renderConToast);
    fireEvent.change(motivo, { target: { value: `  ${MOTIVO}  ` } });
    expect(enviar.disabled).toBe(false);
    fireEvent.click(enviar);
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
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
