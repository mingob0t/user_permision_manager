/**
 * DIS-013: catálogo solicitable y formulario de solicitud
 * (`docs/contratos/solicitudes.md` 1.1).
 * - Estados: carga, vacío, error (con reintento) y sin permiso.
 * - Envío: nivel y justificación opcional; la tarjeta pasa a pendiente sin recargar.
 * - Errores del contrato: 409, 403 `sin_permiso` y 422 `validacion`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { CatalogItem } from '@/lib/access/types';

vi.mock('@/lib/access/requests', () => ({
  requestsApi: { catalog: vi.fn(), create: vi.fn() },
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

import { ApiError } from '@/lib/api';
import { requestsApi } from '@/lib/access/requests';
import { MOCK_REQUEST } from '@/lib/access/mocks';
import { RequestCatalog } from '@/components/access/request-catalog';
import { MENSAJES_SOLICITUD } from '@/components/access/request-errors';

function entrada(id: number, name: string, area: [number, string], extra: Partial<CatalogItem> = {}): CatalogItem {
  return {
    platform: { id, name, description: `Descripción de ${name}`, icon: 'box' },
    area: { id: area[0], name: area[1] },
    my_level: null, my_access_status: null, pending_request_id: null,
    can_request: true, requestable_levels: ['usuario', 'admin'],
    ...extra,
  };
}

const CONTA = entrada(12, 'Contabilidad', [3, 'Finanzas'], {
  my_level: 'usuario', my_access_status: 'activo', requestable_levels: ['admin'],
});
const NOMINA = entrada(13, 'Nómina', [3, 'Finanzas']);
const WIKI = entrada(5, 'Wiki', [1, 'TI'], {
  pending_request_id: 40, can_request: false, requestable_levels: [],
});

/** Texto de las alertas del diálogo (general y del campo justificación). */
async function alertas(dialogo: HTMLElement) {
  await waitFor(() => expect(within(dialogo).getAllByRole('alert')
    .some((a) => (a.textContent ?? '') !== '')).toBe(true));
  return within(dialogo).getAllByRole('alert').map((a) => a.textContent ?? '').filter(Boolean);
}

function tarjeta(nombre: string) {
  return screen.getByRole('article', { name: nombre });
}

async function abrirSolicitud(nombre: string) {
  render(<RequestCatalog />);
  const boton = await screen.findByRole('button', { name: `Solicitar acceso a ${nombre}` });
  fireEvent.click(boton);
  return { boton, dialogo: screen.getByRole('dialog', { name: `Solicitar acceso a ${nombre}` }) };
}

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  administradas = [];
  vi.mocked(requestsApi.catalog).mockResolvedValue([CONTA, NOMINA, WIKI]);
  vi.mocked(requestsApi.create).mockResolvedValue({
    status: 'success',
    request: { ...MOCK_REQUEST, id: 77, status: 'pendiente', level: 'usuario', justification: null },
  });
});

afterEach(() => {
  cleanup();
});

describe('estados del catálogo', () => {
  it('muestra la carga mientras llega el catálogo', () => {
    vi.mocked(requestsApi.catalog).mockReturnValue(new Promise(() => undefined));
    render(<RequestCatalog />);
    expect(screen.getByText('Cargando catálogo…')).toBeTruthy();
  });

  it('muestra el vacío si no hay plataformas', async () => {
    vi.mocked(requestsApi.catalog).mockResolvedValue([]);
    render(<RequestCatalog />);
    expect(await screen.findByText('No hay plataformas en el catálogo de tus áreas.')).toBeTruthy();
  });

  it('muestra el error sin detalles del servidor y reintenta', async () => {
    vi.mocked(requestsApi.catalog).mockRejectedValueOnce(new ApiError(500, 'Traceback interno'));
    render(<RequestCatalog />);
    const alerta = await screen.findByRole('alert');
    expect(alerta.textContent).toBe('No se pudo cargar el catálogo.');

    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByRole('article', { name: 'Contabilidad' })).toBeTruthy();
    expect(requestsApi.catalog).toHaveBeenCalledTimes(2);
  });

  it('muestra "sin permiso" ante un 403', async () => {
    vi.mocked(requestsApi.catalog).mockRejectedValue(new ApiError(403, 'Prohibido'));
    render(<RequestCatalog />);
    expect((await screen.findByRole('alert')).textContent).toBe('No tienes permiso para ver el catálogo.');
  });
});

describe('tarjetas', () => {
  it('la sección se titula con un h2 "Catálogo" (el h1 es de la página)', async () => {
    render(<RequestCatalog />);
    await screen.findByRole('article', { name: 'Wiki' });
    expect(screen.getByRole('heading', { level: 2, name: 'Catálogo' })).toBeTruthy();
    expect(screen.queryByRole('heading', { level: 1 })).toBeNull();
  });

  it('indica el estado con texto y solo ofrece solicitar si el contrato lo permite', async () => {
    render(<RequestCatalog />);
    const conta = await screen.findByRole('article', { name: 'Contabilidad' });
    expect(within(conta).getByText('Con acceso · Usuario')).toBeTruthy();
    expect(within(conta).getByRole('button', { name: 'Solicitar acceso a Contabilidad' })).toBeTruthy();

    expect(within(tarjeta('Nómina')).getByText('Sin acceso')).toBeTruthy();

    const wiki = tarjeta('Wiki');
    expect(within(wiki).getByText('Solicitud pendiente')).toBeTruthy();
    expect(within(wiki).queryByRole('button')).toBeNull();
    expect(within(wiki).getByText('Espera la decisión del administrador del área.')).toBeTruthy();
  });

  it('filtra por área y por búsqueda en el cliente', async () => {
    render(<RequestCatalog />);
    await screen.findByRole('article', { name: 'Wiki' });

    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrar el catálogo por área' }), {
      target: { value: '1' },
    });
    expect(screen.queryByRole('article', { name: 'Contabilidad' })).toBeNull();
    expect(tarjeta('Wiki')).toBeTruthy();

    fireEvent.change(screen.getByRole('searchbox', { name: 'Buscar en el catálogo' }), {
      target: { value: 'conta' },
    });
    expect(screen.getByText('Ninguna plataforma coincide con el filtro.')).toBeTruthy();
    expect(requestsApi.catalog).toHaveBeenCalledTimes(1);
  });

  it('superadmin: solo consulta, sin acción', async () => {
    esSuperadmin = true;
    vi.mocked(requestsApi.catalog).mockResolvedValue([{ ...NOMINA, can_request: false }]);
    render(<RequestCatalog />);
    const nomina = await screen.findByRole('article', { name: 'Nómina' });
    expect(within(nomina).queryByRole('button')).toBeNull();
    expect(within(nomina).getByText('Como superadmin ya tienes acceso a todas las plataformas.')).toBeTruthy();
  });

  it('admin de área: su área se ve sin acción', async () => {
    administradas = [{ id: 3, name: 'Finanzas' }];
    vi.mocked(requestsApi.catalog).mockResolvedValue([{ ...NOMINA, can_request: false }]);
    render(<RequestCatalog />);
    const nomina = await screen.findByRole('article', { name: 'Nómina' });
    expect(within(nomina).getByText('Administras esta área: tienes acceso automático.')).toBeTruthy();
  });
});

describe('envío de la solicitud', () => {
  it('sin justificación: envía solo nivel y plataforma, y la tarjeta pasa a pendiente', async () => {
    const { dialogo } = await abrirSolicitud('Nómina');
    expect(within(dialogo).getByRole('radio', { name: /Usuario/ })).toHaveProperty('checked', true);
    fireEvent.click(within(dialogo).getByRole('radio', { name: /Admin/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(requestsApi.create).toHaveBeenCalledWith({ platform_id: 13, level: 'admin' });

    const nomina = tarjeta('Nómina');
    expect(within(nomina).getByText('Solicitud pendiente')).toBeTruthy();
    expect(within(nomina).queryByRole('button')).toBeNull();
    expect(requestsApi.catalog).toHaveBeenCalledTimes(1);

    const aviso = screen.getByRole('status');
    expect(aviso.textContent).toContain('Solicitud enviada: Nómina');
    await waitFor(() => expect(document.activeElement).toBe(aviso));

    // Al cerrar el aviso el foco va al buscador, no a `body`.
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar aviso' }));
    expect(aviso.textContent).toBe('');
    expect(document.activeElement).toBe(screen.getByRole('searchbox', { name: 'Buscar en el catálogo' }));
  });

  it('con justificación: la envía recortada y muestra el contador', async () => {
    const { dialogo } = await abrirSolicitud('Contabilidad');
    expect(within(dialogo).getByText(/Nivel actual: Usuario/)).toBeTruthy();
    const campo = within(dialogo).getByRole('textbox', { name: 'Justificación (opcional)' });
    fireEvent.change(campo, { target: { value: '  Cierre mensual  ' } });
    expect(within(dialogo).getByText('14/500 caracteres')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));
    await waitFor(() => expect(requestsApi.create).toHaveBeenCalledWith(
      { platform_id: 12, level: 'admin', justification: 'Cierre mensual' }));
  });

  it('justificación de más de 500: la marca, la anuncia y no envía', async () => {
    const { dialogo } = await abrirSolicitud('Nómina');
    const campo = within(dialogo).getByRole('textbox', { name: 'Justificación (opcional)' });
    fireEvent.change(campo, { target: { value: 'x'.repeat(501) } });

    expect(campo.getAttribute('aria-invalid')).toBe('true');
    const descrito = campo.getAttribute('aria-describedby') ?? '';
    expect(descrito).toContain('solicitud-justificacion-error');
    expect(document.getElementById('solicitud-justificacion-error')?.textContent)
      .toBe('Escribe como máximo 500 caracteres.');

    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));
    expect(await alertas(dialogo)).toEqual(
      ['Escribe como máximo 500 caracteres.', MENSAJES_SOLICITUD.validacion]);
    expect(document.activeElement).toBe(campo);
    expect(requestsApi.create).not.toHaveBeenCalled();
  });

  it('Escape cierra el diálogo y devuelve el foco al botón', async () => {
    const { boton } = await abrirSolicitud('Nómina');
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(boton);
    expect(requestsApi.create).not.toHaveBeenCalled();
  });
});

describe('errores del contrato', () => {
  it.each([
    [409, 'solicitud_duplicada', 'Ya tienes una solicitud pendiente para esta plataforma.'],
    [409, 'nivel_vigente', 'Ya tienes ese nivel o uno superior en esta plataforma.'],
    [409, 'estado_invalido',
      'Tu acceso actual todavía no está activo. Podrás pedir otro nivel cuando termine de aplicarse.'],
    [409, 'ya_administra_area', 'Ya administras esta área; tienes acceso automático.'],
    [409, 'plataforma_no_disponible', 'La plataforma está inactiva o sin integración configurada.'],
    [403, 'sin_permiso',
      'Tu rol no puede solicitar accesos: el superadmin ya tiene acceso a todas las plataformas.'],
  ])('%i %s: mensaje claro y el diálogo sigue abierto', async (estado, code, mensaje) => {
    vi.mocked(requestsApi.create).mockRejectedValue(new ApiError(estado, 'Texto del servidor', { code }));
    const { dialogo } = await abrirSolicitud('Nómina');
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));

    expect(await alertas(dialogo)).toEqual([mensaje]);
    expect(screen.getByRole('dialog')).toBeTruthy();
    expect(within(tarjeta('Nómina')).queryByText('Solicitud pendiente')).toBeNull();
  });

  it('422 validacion: error del campo ligado al control y con el foco', async () => {
    vi.mocked(requestsApi.create).mockRejectedValue(new ApiError(422, 'Datos inválidos', {
      code: 'validacion', fields: { justification: 'Escribe como máximo 500 caracteres.' },
    }));
    const { dialogo } = await abrirSolicitud('Nómina');
    const campo = within(dialogo).getByRole('textbox', { name: 'Justificación (opcional)' });
    fireEvent.change(campo, { target: { value: 'Motivo' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));

    expect(await alertas(dialogo)).toEqual(
      ['Escribe como máximo 500 caracteres.', MENSAJES_SOLICITUD.validacion]);
    expect(campo.getAttribute('aria-invalid')).toBe('true');
    expect(document.getElementById('solicitud-justificacion-error')?.textContent)
      .toBe('Escribe como máximo 500 caracteres.');
    expect(document.activeElement).toBe(campo);
  });

  it('error sin código (500): mensaje genérico, sin detalles internos', async () => {
    vi.mocked(requestsApi.create).mockRejectedValue(new ApiError(500, 'Traceback interno'));
    const { dialogo } = await abrirSolicitud('Nómina');
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));
    expect(await alertas(dialogo)).toEqual(['No se pudo enviar la solicitud. Inténtalo de nuevo.']);
  });

  it('muestra "Enviando…" y bloquea el doble envío', async () => {
    vi.mocked(requestsApi.create).mockReturnValue(new Promise(() => undefined));
    await abrirSolicitud('Nómina');
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }));
    const enviando = await screen.findByRole('button', { name: 'Enviando…' });
    expect(enviando).toHaveProperty('disabled', true);
    expect(requestsApi.create).toHaveBeenCalledTimes(1);
  });
});
