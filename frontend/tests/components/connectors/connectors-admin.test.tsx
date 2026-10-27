/**
 * DIS-022: configuración de conectores (`/admin/connectors`; contrato
 * `conectores-y-ejecuciones.md` 1.1; solo superadmin).
 * - Lista solo las plataformas `conector`, con carga, vacío y error sin texto del servidor.
 * - Panel: `404` = sin configurar; formulario con obligatorios marcados y sin contraseñas.
 * - Guardar (cuerpo del contrato, parámetros conservados), probar (texto propio) y
 *   eliminar con confirmación; errores por código y por campo.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Connector } from '@/lib/access/types';
import type { Platform } from '@/lib/types';

vi.mock('@/lib/access/connectors', () => ({
  connectorsApi: { get: vi.fn(), save: vi.fn(), remove: vi.fn(), test: vi.fn() },
}));
vi.mock('@/lib/access/provisioning', () => ({
  provisioningApi: { jobs: vi.fn(), job: vi.fn(), retry: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { platforms: vi.fn(), areas: vi.fn() },
}));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 1, role: 'administrador', managed_areas: [], preferences: { refresh_interval: 60 },
      permissions: { is_admin: true, is_area_admin: false, can_manage_areas: true, can_manage_system: true },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { connectorsApi } from '@/lib/access/connectors';
import { provisioningApi } from '@/lib/access/provisioning';
import { ConnectorsAdmin, VACIO_CONECTORES } from '@/components/connectors/connectors-admin';
import {
  FORMULARIO_VACIO, MENSAJES_CAMPO, OBLIGATORIO, cuerpoConector, formularioDesde,
  parametrosConservados, validarConector,
} from '@/components/connectors/connector-catalog';
import {
  MENSAJES_GUARDAR, MENSAJE_REVISA, PRUEBA_ERROR, PRUEBA_OK, describeConnectorDeleteError,
  describeConnectorSaveError,
} from '@/components/connectors/connector-errors';
import { AVISO_ELIMINADO, AVISO_SIN_VERIFICAR } from '@/components/connectors/connector-panel';

function plataforma(extra: Partial<Platform>): Platform {
  return {
    id: 12, name: 'Contabilidad', description: '', area_id: 3, area_name: 'Finanzas', area_color: '',
    area_icon: '', direct_link: null, icon: '', logo_url: null, bg_color: '', text_color: '',
    status: 'active', visits: 0, is_favorite: false, integration_type: 'conector',
    ldap_group_user_dn: null, ldap_group_admin_dn: null, groups_status: 'sin_verificar',
    has_connector: true, active_grants: 2, ...extra,
  };
}

const CONTABILIDAD = plataforma({});
const NOMINA = plataforma({ id: 14, name: 'Nómina', has_connector: false, active_grants: 0 });
const WIKI = plataforma({ id: 5, name: 'Wiki', integration_type: 'ldap' });

/** `timeout` no tiene editor: se conserva sin cambios. */
const PARAMS_API = {
  base_path: '/usuarios', timeout: 30, auth: { esquema: 'bearer' },
  otorgar: { metodo: 'POST', ruta: '/usuarios', cuerpo: { email: '{correo}' } },
  revocar: { metodo: 'DELETE', ruta: '/usuarios/{correo}', sin_cambios: [404, 410] },
};

const CONECTOR: Connector = {
  platform_id: 12, type: 'api', host: 'erp.ejemplo.local', port: 443,
  params: PARAMS_API, credential_ref: 'pokemon/contabilidad-api',
  credential_status: 'ok', active: true, updated_at: '2026-10-14T14:00:00Z',
};

const mocks = {
  platforms: vi.mocked(api.platforms),
  get: vi.mocked(connectorsApi.get),
  save: vi.mocked(connectorsApi.save),
  remove: vi.mocked(connectorsApi.remove),
  test: vi.mocked(connectorsApi.test),
};

beforeEach(() => {
  vi.mocked(api.areas).mockResolvedValue([]);
  vi.mocked(provisioningApi.jobs).mockResolvedValue({ items: [], page: 1, per_page: 25, total: 0 });
  mocks.platforms.mockResolvedValue([CONTABILIDAD, NOMINA, WIKI]);
  mocks.get.mockResolvedValue(CONECTOR);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function abrir(nombre = 'Contabilidad') {
  render(<ConnectorsAdmin />);
  fireEvent.click(await screen.findByRole('button', { name: `Configurar el conector de ${nombre}` }));
  return screen.findByRole('region', { name: `Conector de ${nombre}` });
}

describe('reglas del formulario', () => {
  it('valida obligatorios, host, puerto y referencia como el servidor', () => {
    expect(validarConector(FORMULARIO_VACIO)).toEqual({
      host: OBLIGATORIO, port: OBLIGATORIO, credential_ref: OBLIGATORIO,
    });
    expect(validarConector({
      ...FORMULARIO_VACIO, host: 'https://erp', port: '70000', credential_ref: '/mal//ref',
    })).toEqual({
      host: MENSAJES_CAMPO.host, port: MENSAJES_CAMPO.port, credential_ref: MENSAJES_CAMPO.credential_ref,
    });
    expect(validarConector({
      ...FORMULARIO_VACIO, host: 'erp.ejemplo.local', port: '443', credential_ref: 'pokemon/erp-api',
    })).toEqual({});
  });

  it('arma el cuerpo del contrato: recorta, conserva parámetros sin editor y omite los vacíos', () => {
    const base = formularioDesde(CONECTOR);
    const form = { ...base, host: ' erp.ejemplo.local ', params: { ...base.params, base_path: '' } };
    const { base_path: _omitido, ...sinBase } = PARAMS_API;
    expect(cuerpoConector(form, CONECTOR)).toEqual({
      type: 'api', host: 'erp.ejemplo.local', port: 443, params: sinBase,
      credential_ref: 'pokemon/contabilidad-api', active: true,
    });
    // Cambiar de tipo descarta los parámetros del anterior.
    expect(parametrosConservados(CONECTOR, 'ssh')).toEqual({});
    expect(cuerpoConector({ ...form, type: 'ssh', params: {} }, CONECTOR).params).toEqual({});
  });

  it('describe los errores por código y por campo sin el texto del servidor', () => {
    const v422 = describeConnectorSaveError(new ApiError(422, 'texto del servidor', {
      code: 'validacion', fields: { host: 'x', 'params.password': 'y' },
    }));
    expect(v422).toEqual({
      message: MENSAJE_REVISA, stale: false, paramFields: {},
      fields: { host: MENSAJES_CAMPO.host, params: MENSAJES_CAMPO.params },
    });
    expect(describeConnectorSaveError(new ApiError(409, 'x', { code: 'conector_concurrente' })))
      .toMatchObject({ message: MENSAJES_GUARDAR.conector_concurrente, stale: true });
    expect(describeConnectorSaveError(new ApiError(409, 'x', { code: 'plataforma_con_accesos' })).fields.type)
      .toBeTruthy();
    expect(describeConnectorSaveError(new ApiError(415, 'x')).message).not.toContain('x');
    expect(describeConnectorDeleteError(new ApiError(409, 'x', { code: 'plataforma_con_accesos' })).message)
      .toMatch(/accesos vigentes/);
  });
});

describe('lista de plataformas', () => {
  it('muestra solo las plataformas con conector y su estado', async () => {
    render(<ConnectorsAdmin />);
    const lista = await screen.findByRole('list', { name: 'Plataformas con conector' });
    expect(within(lista).getAllByRole('listitem')).toHaveLength(2);
    expect(within(lista).getByText('Configurado')).toBeTruthy();
    expect(within(lista).getByText('Sin configurar')).toBeTruthy();
    expect(within(lista).queryByText('Wiki')).toBeNull();
  });

  it('vacío si ninguna plataforma usa conector', async () => {
    mocks.platforms.mockResolvedValue([WIKI]);
    render(<ConnectorsAdmin />);
    expect(await screen.findByText(VACIO_CONECTORES)).toBeTruthy();
  });

  it('error sin texto del servidor y con Reintentar', async () => {
    // También lo pide el filtro de la bitácora (`useOpcionesAlcance`).
    mocks.platforms.mockRejectedValue(new ApiError(500, 'Traceback interno'));
    render(<ConnectorsAdmin />);
    const alerta = await screen.findByRole('alert');
    expect(alerta.textContent).toBe('No se pudieron cargar las plataformas.');
    mocks.platforms.mockResolvedValue([CONTABILIDAD]);
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByRole('list', { name: 'Plataformas con conector' })).toBeTruthy();
  });
});

describe('panel del conector', () => {
  it('muestra la configuración y un formulario sin campos de contraseña', async () => {
    const panel = await abrir();
    await within(panel).findByText('erp.ejemplo.local:443');
    expect(within(panel).getByText('Credencial verificada')).toBeTruthy();
    expect(panel.querySelector('input[type="password"]')).toBeNull();
    const host = within(panel).getByLabelText('Host *') as HTMLInputElement;
    expect(host.value).toBe('erp.ejemplo.local');
    expect(host.required).toBe(true);
    expect(host.getAttribute('aria-required')).toBe('true');
    expect(within(panel).getByText(/Se conservan sin cambios: timeout/)).toBeTruthy();
  });

  it('404 al leer = sin configurar; valida antes de enviar y enfoca el primer error', async () => {
    mocks.get.mockRejectedValue(new ApiError(404, 'x', { code: 'no_encontrado' }));
    const panel = await abrir('Nómina');
    expect(await within(panel).findByText(/aún no tiene conector/)).toBeTruthy();
    expect(within(panel).queryByRole('button', { name: 'Probar conexión' })).toBeNull();
    fireEvent.click(within(panel).getByRole('button', { name: 'Guardar conector' }));
    expect(mocks.save).not.toHaveBeenCalled();
    await waitFor(() => expect(document.activeElement).toBe(within(panel).getByLabelText('Host *')));
  });

  it('guarda con el cuerpo del contrato y anuncia que la credencial queda sin verificar', async () => {
    mocks.save.mockResolvedValue({
      status: 'success',
      connector: { ...CONECTOR, port: 8443, credential_status: 'sin_verificar', updated_at: '2026-10-21T10:00:00Z' },
    });
    const panel = await abrir();
    await within(panel).findByText('erp.ejemplo.local:443');
    const pedidas = mocks.platforms.mock.calls.length;
    fireEvent.change(within(panel).getByLabelText('Puerto *'), { target: { value: '8443' } });
    fireEvent.click(within(panel).getByRole('button', { name: 'Guardar conector' }));
    await waitFor(() => expect(mocks.save).toHaveBeenCalledWith(12, {
      type: 'api', host: 'erp.ejemplo.local', port: 8443,
      params: PARAMS_API,
      credential_ref: 'pokemon/contabilidad-api', active: true,
    }));
    expect(await within(panel).findByText(AVISO_SIN_VERIFICAR)).toBeTruthy();
    expect(within(panel).getByText('Credencial sin verificar')).toBeTruthy();
    // La lista se recarga (cambia `has_connector`).
    expect(mocks.platforms).toHaveBeenCalledTimes(pedidas + 1);
  });

  it('422 marca el campo con un mensaje propio', async () => {
    mocks.save.mockRejectedValue(new ApiError(422, 'Usa un nombre de host autorizado.', {
      code: 'validacion', fields: { host: 'Usa un nombre de host autorizado.' },
    }));
    const panel = await abrir();
    await within(panel).findByText('erp.ejemplo.local:443');
    fireEvent.click(within(panel).getByRole('button', { name: 'Guardar conector' }));
    expect(await within(panel).findByText(MENSAJES_CAMPO.host)).toBeTruthy();
    expect(within(panel).getByLabelText('Host *').getAttribute('aria-invalid')).toBe('true');
  });

  it('422 en una clave de params sin campo: mensaje propio y foco en el fieldset de parámetros', async () => {
    mocks.save.mockRejectedValue(new ApiError(422, 'srv', {
      code: 'validacion', fields: { 'params.password': 'srv' },
    }));
    const panel = await abrir();
    await within(panel).findByText('erp.ejemplo.local:443');
    fireEvent.click(within(panel).getByRole('button', { name: 'Guardar conector' }));
    expect(await within(panel).findByText(MENSAJES_CAMPO.params)).toBeTruthy();
    await waitFor(() => expect(document.activeElement).toBe(
      within(panel).getByRole('group', { name: 'Parámetros del tipo' })));
  });

  it('422 en params.<ruta>: marca el campo con mensaje propio, lo asocia y le da el foco', async () => {
    mocks.save.mockRejectedValue(new ApiError(422, 'srv', {
      code: 'validacion', fields: { 'params.base_path': 'srv' },
    }));
    const panel = await abrir();
    await within(panel).findByText('erp.ejemplo.local:443');
    fireEvent.click(within(panel).getByRole('button', { name: 'Guardar conector' }));
    const campo = within(panel).getByLabelText('Ruta base');
    const aviso = await within(panel).findByText(/^Revisa «Ruta base»/);
    expect(campo.getAttribute('aria-invalid')).toBe('true');
    expect(campo.getAttribute('aria-describedby')).toContain(aviso.id);
    expect(aviso.textContent).not.toContain('srv');
    await waitFor(() => expect(document.activeElement).toBe(campo));
  });

  it('probar conexión muestra un texto propio y recarga el estado de la credencial', async () => {
    mocks.test.mockResolvedValueOnce({ status: 'success', result: 'ok', message: 'servidor' });
    const panel = await abrir();
    fireEvent.click(await within(panel).findByRole('button', { name: 'Probar conexión' }));
    expect(await within(panel).findByText(PRUEBA_OK)).toBeTruthy();
    expect(within(panel).getByText(PRUEBA_OK).closest('[role]')?.getAttribute('role')).toBe('status');
    await waitFor(() => expect(mocks.get).toHaveBeenCalledTimes(2));

    mocks.test.mockResolvedValueOnce({ status: 'success', result: 'error', message: 'detalle interno' });
    fireEvent.click(within(panel).getByRole('button', { name: 'Probar conexión' }));
    expect(await within(panel).findByText(PRUEBA_ERROR)).toBeTruthy();
    // El fallo se anuncia como alerta; el éxito anterior ya no está.
    expect(within(panel).getByText(PRUEBA_ERROR).closest('[role]')?.getAttribute('role')).toBe('alert');
    expect(within(panel).queryByText(PRUEBA_OK)).toBeNull();
    expect(within(panel).queryByText('detalle interno')).toBeNull();
  });

  it('eliminar pide confirmación, explica el efecto y muestra el 409 con accesos', async () => {
    mocks.remove.mockRejectedValueOnce(new ApiError(409, 'x', { code: 'plataforma_con_accesos' }));
    const panel = await abrir();
    fireEvent.click(await within(panel).findByRole('button', { name: 'Eliminar el conector de Contabilidad' }));
    const dialogo = screen.getByRole('dialog', { name: 'Eliminar conector' });
    expect(within(dialogo).getByText(/no podrán\s+aplicarse/)).toBeTruthy();
    expect(mocks.remove).not.toHaveBeenCalled();

    fireEvent.click(within(dialogo).getByRole('button', { name: 'Eliminar' }));
    expect(await within(dialogo).findByText(/Revócalos primero/)).toBeTruthy();

    mocks.remove.mockResolvedValueOnce({ status: 'success' });
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Eliminar' }));
    expect(await within(panel).findByText(AVISO_ELIMINADO)).toBeTruthy();
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(within(panel).getByText(/aún no tiene conector/)).toBeTruthy();
  });

  it('cerrar devuelve el foco al botón de la fila', async () => {
    const panel = await abrir();
    fireEvent.click(within(panel).getByRole('button', { name: 'Cerrar' }));
    await waitFor(() => expect(document.activeElement).toBe(
      screen.getByRole('button', { name: 'Configurar el conector de Contabilidad' })));
  });
});
