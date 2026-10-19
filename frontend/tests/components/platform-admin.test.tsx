/**
 * DIS-017: formulario de plataforma con tipo de integración y grupos por nivel
 * (contrato `plataformas-integracion.md`), por rol, con errores y avisos.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/lib/api';
import type { Area, Platform } from '@/lib/types';

vi.mock('@/lib/api', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/lib/api')>();
  return {
    ApiError: real.ApiError,
    api: {
      areas: vi.fn(), platforms: vi.fn(),
      createPlatform: vi.fn(), updatePlatform: vi.fn(), deletePlatform: vi.fn(),
    },
  };
});

const permisos = { is_admin: false, is_area_admin: true };
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({ session: { permissions: permisos }, loading: false, error: null }),
}));
vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>{children}</a>
  ),
}));

import { api } from '@/lib/api';
import { PlatformAdmin } from '@/components/platform-admin';

const AREAS = [{ id: 3, name: 'Finanzas' }] as Area[];
const PLATAFORMA = {
  id: 12, name: 'Contabilidad', description: 'ERP contable', area_id: 3, area_name: 'Finanzas',
  direct_link: 'https://erp.ejemplo.local', bg_color: '', text_color: '', status: 'Activo',
} as Platform;
const DN_USUARIO = 'cn=conta-usuario,ou=finanzas,ou=plataformas,dc=ejemplo,dc=local';
const DN_ADMIN = 'cn=conta-admin,ou=finanzas,ou=plataformas,dc=ejemplo,dc=local';

function comoSuperadmin() {
  permisos.is_admin = true;
  permisos.is_area_admin = false;
}

function respuesta(warnings: { code: string; message: string }[] = []) {
  return { status: 'success', platform: { ...PLATAFORMA, name: 'Nueva' }, warnings };
}

beforeEach(() => {
  vi.clearAllMocks();
  permisos.is_admin = false;
  permisos.is_area_admin = true;
  vi.mocked(api.areas).mockResolvedValue(AREAS);
  vi.mocked(api.platforms).mockResolvedValue([PLATAFORMA]);
  vi.mocked(api.createPlatform).mockResolvedValue(respuesta());
  vi.mocked(api.updatePlatform).mockResolvedValue(respuesta());
});

afterEach(() => cleanup());

function dialogo() {
  return within(screen.getByRole('dialog'));
}

async function abrirAlta() {
  render(<PlatformAdmin />);
  await screen.findByText('Contabilidad');
  fireEvent.click(screen.getByText('Nueva plataforma'));
  const modal = dialogo();
  fireEvent.change(modal.getByLabelText(/^Nombre/), { target: { value: 'Nueva' } });
  fireEvent.change(modal.getByLabelText(/^Descripción/), { target: { value: 'Descripción' } });
  return modal;
}

describe('PlatformAdmin: alta por rol', () => {
  it('admin de área: exige el tipo, no ve ni envía DN', async () => {
    const modal = await abrirAlta();
    fireEvent.click(modal.getByText('Guardar'));
    expect(await modal.findByText('Selecciona el tipo de integración.')).toBeTruthy();
    expect(api.createPlatform).not.toHaveBeenCalled();

    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'ldap' } });
    expect(modal.queryByLabelText(/^Grupo de acceso/)).toBeNull();
    expect(modal.getByText(/Solo el superadmin\s+puede definirlos/)).toBeTruthy();
    fireEvent.click(modal.getByText('Guardar'));

    await waitFor(() => expect(api.createPlatform).toHaveBeenCalledTimes(1));
    const enviado = vi.mocked(api.createPlatform).mock.calls[0][0];
    expect(enviado).toMatchObject({ name: 'Nueva', description: 'Descripción', area_id: 3, integration_type: 'ldap' });
    expect(enviado).not.toHaveProperty('ldap_group_user_dn');
    expect(enviado).not.toHaveProperty('ldap_group_admin_dn');
    // Sin color elegido no se envía: el servidor aplica el suyo por omisión.
    expect(enviado).not.toHaveProperty('bg_color');
    expect(enviado).not.toHaveProperty('text_color');
  });

  it('superadmin: ve los grupos por nivel y los envía', async () => {
    comoSuperadmin();
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'ldap' } });
    fireEvent.change(modal.getByLabelText(/^Grupo de acceso: nivel usuario/), { target: { value: DN_USUARIO } });
    fireEvent.change(modal.getByLabelText(/^Grupo de acceso: nivel admin/), { target: { value: DN_ADMIN } });
    fireEvent.click(modal.getByText('Guardar'));

    await waitFor(() => expect(api.createPlatform).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.createPlatform).mock.calls[0][0]).toMatchObject({
      integration_type: 'ldap', ldap_group_user_dn: DN_USUARIO, ldap_group_admin_dn: DN_ADMIN,
    });
  });

  it('superadmin: DN vacíos no se envían (el backend los deriva)', async () => {
    comoSuperadmin();
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'ldap' } });
    fireEvent.click(modal.getByText('Guardar'));
    await waitFor(() => expect(api.createPlatform).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.createPlatform).mock.calls[0][0]).not.toHaveProperty('ldap_group_user_dn');
  });

  it('superadmin con conector: sin DN y con enlace a conectores', async () => {
    comoSuperadmin();
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'conector' } });
    expect(modal.queryByLabelText(/^Grupo de acceso/)).toBeNull();
    expect(modal.getByText('Configurar conectores').getAttribute('href')).toBe('/admin/connectors');
  });

  it('grupos iguales se rechazan antes de enviar', async () => {
    comoSuperadmin();
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'ldap' } });
    fireEvent.change(modal.getByLabelText(/^Grupo de acceso: nivel usuario/), { target: { value: DN_USUARIO } });
    fireEvent.change(modal.getByLabelText(/^Grupo de acceso: nivel admin/), { target: { value: DN_USUARIO.toUpperCase() } });
    fireEvent.click(modal.getByText('Guardar'));
    expect(await modal.findByText('Los grupos de usuario y admin deben ser distintos.')).toBeTruthy();
    expect(api.createPlatform).not.toHaveBeenCalled();
  });

  it('enlace que no es https: error en el campo, sin enviar', async () => {
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'conector' } });
    fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'javascript:alert(1)' } });
    fireEvent.click(modal.getByText('Guardar'));
    expect(await modal.findByText('Usa una dirección https://.')).toBeTruthy();
    expect(api.createPlatform).not.toHaveBeenCalled();
  });
});

describe('PlatformAdmin: edición por rol', () => {
  it('admin de área: no envía el tipo ni DN', async () => {
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Editar'));
    const modal = dialogo();
    expect(modal.getByText(/Solo el superadmin cambia el tipo/)).toBeTruthy();
    fireEvent.click(modal.getByText('Guardar'));
    await waitFor(() => expect(api.updatePlatform).toHaveBeenCalledTimes(1));
    const [, enviado] = vi.mocked(api.updatePlatform).mock.calls[0];
    expect(enviado).not.toHaveProperty('integration_type');
    expect(enviado).not.toHaveProperty('ldap_group_user_dn');
  });

  it('superadmin: "Sin cambiar" no envía el tipo', async () => {
    comoSuperadmin();
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Editar'));
    fireEvent.click(dialogo().getByText('Guardar'));
    await waitFor(() => expect(api.updatePlatform).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.updatePlatform).mock.calls[0][1]).not.toHaveProperty('integration_type');
  });

  it('con accesos vigentes: tipo, grupos y área deshabilitados', async () => {
    comoSuperadmin();
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, integration_type: 'ldap', active_grants: 4 }]);
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Editar'));
    const modal = dialogo();
    expect(modal.getByText(/accesos vigentes: no se\s+puede cambiar/)).toBeTruthy();
    expect((modal.getByLabelText(/^Tipo de integración/) as HTMLSelectElement).disabled).toBe(true);
    expect((modal.getByLabelText(/^Área/) as HTMLSelectElement).disabled).toBe(true);
    expect((modal.getByLabelText(/^Grupo de acceso: nivel usuario/) as HTMLInputElement).disabled).toBe(true);
  });
});

describe('PlatformAdmin: errores del backend', () => {
  async function guardarConError(error: ApiError) {
    comoSuperadmin();
    vi.mocked(api.createPlatform).mockRejectedValue(error);
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'ldap' } });
    fireEvent.click(modal.getByText('Guardar'));
    return modal;
  }

  it('422: errores por campo y mensaje general', async () => {
    const modal = await guardarConError(new ApiError(422, 'Datos no válidos.', {
      code: 'validacion',
      fields: { ldap_group_user_dn: 'El grupo debe estar en la OU de plataformas.', icon: 'Debe ser texto.' },
    }));
    expect(await modal.findByText('El grupo debe estar en la OU de plataformas.')).toBeTruthy();
    expect(modal.getByText('Revisa los campos marcados. Icono: Debe ser texto.')).toBeTruthy();
  });

  it.each([
    ['dn_solo_superadmin', 403, 'Solo el superadmin define los grupos del directorio o cambia el tipo de integración.'],
    ['plataforma_con_accesos', 409, 'No se puede cambiar el tipo, los grupos ni el área con accesos vigentes.'],
    ['grupo_en_uso', 409, 'El grupo ya pertenece a otra plataforma.'],
  ])('%s: mensaje del contrato', async (code, status, mensaje) => {
    const modal = await guardarConError(new ApiError(status, 'x', { code }));
    expect(await modal.findByText(mensaje)).toBeTruthy();
  });

  it('409 grupos_iguales: mensaje y marca el grupo admin', async () => {
    const modal = await guardarConError(new ApiError(409, 'x', { code: 'grupos_iguales' }));
    expect((await modal.findAllByText('Los grupos de usuario y admin deben ser distintos.')).length).toBe(2);
    expect(modal.getByLabelText(/^Grupo de acceso: nivel admin/).getAttribute('aria-invalid')).toBe('true');
  });

  it('404: área o plataforma fuera de alcance', async () => {
    const modal = await guardarConError(new ApiError(404, 'No encontrado'));
    expect(await modal.findByText(/ya no está en tu alcance/)).toBeTruthy();
  });
});

describe('PlatformAdmin: avisos y estados', () => {
  it('muestra los warnings tras guardar', async () => {
    vi.mocked(api.createPlatform).mockResolvedValue(respuesta([
      { code: 'grupo_no_existe', message: 'El grupo de nivel usuario no existe en el directorio.' },
    ]));
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'ldap' } });
    fireEvent.click(modal.getByText('Guardar'));
    expect(await screen.findByText('Guardada con avisos')).toBeTruthy();
    expect(screen.getByText('El grupo de nivel usuario no existe en el directorio.')).toBeTruthy();
    expect(screen.queryByRole('dialog')).toBeNull();
    fireEvent.click(screen.getByText('Cerrar aviso'));
    expect(screen.queryByText('Guardada con avisos')).toBeNull();
  });

  it('sin avisos: confirma el guardado', async () => {
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'conector' } });
    fireEvent.click(modal.getByText('Guardar'));
    expect(await screen.findByText('Guardada')).toBeTruthy();
  });

  it('enlace no https en la tabla: se muestra "Sin enlace"', async () => {
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, direct_link: 'javascript:alert(1)' }]);
    render(<PlatformAdmin />);
    expect(await screen.findByText('Sin enlace')).toBeTruthy();
    expect(screen.queryByText('javascript:alert(1)')).toBeNull();
  });

  it('vacío y error de carga', async () => {
    vi.mocked(api.platforms).mockResolvedValue([]);
    render(<PlatformAdmin />);
    expect(await screen.findByText('No hay plataformas en tu alcance.')).toBeTruthy();
    cleanup();
    vi.mocked(api.platforms).mockRejectedValue(new Error('Falla de red'));
    render(<PlatformAdmin />);
    expect(await screen.findByText('Falla de red')).toBeTruthy();
  });

  it('usuario sin rol de admin: sin permiso y sin llamar a la API', () => {
    permisos.is_area_admin = false;
    render(<PlatformAdmin />);
    expect(screen.getByText('No tienes permiso para ver esta sección.')).toBeTruthy();
    expect(api.platforms).not.toHaveBeenCalled();
  });
});

describe('PlatformAdmin: accesibilidad (revisión de DIS-017)', () => {
  function descripcionDe(control: HTMLElement) {
    return (control.getAttribute('aria-describedby') ?? '').split(' ')
      .map((id) => document.getElementById(id)?.textContent ?? '').join(' ');
  }

  it('errores por campo y pistas ligados al control con aria-describedby', async () => {
    comoSuperadmin();
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Nombre/), { target: { value: '' } });
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'ldap' } });
    fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'http://x.ejemplo.local' } });
    fireEvent.click(modal.getByText('Guardar'));
    const nombre = await modal.findByLabelText(/^Nombre/);
    expect(descripcionDe(nombre)).toContain('El nombre debe tener entre 2 y 100 caracteres.');
    const enlace = modal.getByLabelText(/^Enlace/);
    expect(descripcionDe(enlace)).toContain('Usa una dirección https://.');
    expect(descripcionDe(enlace)).toContain('Dirección https://');
    expect(descripcionDe(modal.getByLabelText(/^Tipo de integración/))).toContain('Cómo se da el acceso');
    expect(descripcionDe(modal.getByLabelText(/^Grupo de acceso: nivel usuario/))).toContain('nivel usuario');
  });

  it('nota de campos deshabilitados por aria-describedby', async () => {
    comoSuperadmin();
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, integration_type: 'ldap', active_grants: 2 }]);
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Editar'));
    const modal = dialogo();
    expect(descripcionDe(modal.getByLabelText(/^Tipo de integración/))).toMatch(/accesos vigentes/);
    expect(descripcionDe(modal.getByLabelText(/^Área/))).toMatch(/accesos vigentes/);
  });

  it('la región de estado está montada antes de guardar', async () => {
    render(<PlatformAdmin />);
    await screen.findByText('Contabilidad');
    const region = screen.getByRole('status');
    expect(region.textContent).toBe('');
    fireEvent.click(screen.getByText('Nueva plataforma'));
    const modal = dialogo();
    fireEvent.change(modal.getByLabelText(/^Nombre/), { target: { value: 'Nueva' } });
    fireEvent.change(modal.getByLabelText(/^Descripción/), { target: { value: 'D' } });
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'conector' } });
    fireEvent.click(modal.getByText('Guardar'));
    await waitFor(() => expect(region.textContent).toContain('Se guardó'));
  });

  it('foco: al primer campo con error, al disparador al cancelar y al aviso al guardar', async () => {
    render(<PlatformAdmin />);
    await screen.findByText('Contabilidad');
    const nueva = screen.getByText('Nueva plataforma');
    nueva.focus();
    fireEvent.click(nueva);
    fireEvent.click(dialogo().getByText('Guardar'));
    await waitFor(() => expect(document.activeElement).toBe(dialogo().getByLabelText(/^Nombre/)));
    fireEvent.click(dialogo().getByText('Cancelar'));
    await waitFor(() => expect(document.activeElement).toBe(nueva));

    const modal = await abrirAltaSinRender();
    fireEvent.change(modal.getByLabelText(/^Tipo de integración/), { target: { value: 'conector' } });
    fireEvent.click(modal.getByText('Guardar'));
    const aviso = await screen.findByText(/Se guardó/);
    await waitFor(() => expect(aviso.closest('[tabindex="-1"]')).toBe(document.activeElement));
  });

  it('Editar y Eliminar con el nombre de la plataforma', async () => {
    render(<PlatformAdmin />);
    expect(await screen.findByRole('button', { name: 'Editar Contabilidad' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Eliminar Contabilidad' })).toBeTruthy();
  });

  it.each([
    [404, 'La plataforma ya no existe o no está en tu alcance. Recarga la lista.'],
    [409, 'No se puede eliminar una plataforma con accesos vigentes.'],
  ])('error %s al eliminar: mensaje fijo', async (status, mensaje) => {
    vi.mocked(api.deletePlatform).mockRejectedValue(new ApiError(status, 'detalle interno', { code: 'x' }));
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByRole('button', { name: 'Eliminar Contabilidad' }));
    fireEvent.click(within(screen.getByRole('dialog')).getByText('Eliminar'));
    expect(await screen.findByText(mensaje)).toBeTruthy();
  });
});

async function abrirAltaSinRender() {
  fireEvent.click(screen.getByText('Nueva plataforma'));
  const modal = within(screen.getByRole('dialog'));
  fireEvent.change(modal.getByLabelText(/^Nombre/), { target: { value: 'Nueva' } });
  fireEvent.change(modal.getByLabelText(/^Descripción/), { target: { value: 'Descripción' } });
  return modal;
}
