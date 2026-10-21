/**
 * DIS-018: accesos de un usuario y revocación (`/users`; contrato `accesos.md` 1.1).
 * - Lista `GET /users/<id>/access` con `vigente` por defecto, filtro y paginación.
 * - Revocar solo cuando el contrato lo permite; si no, se explica por qué.
 * - Confirmación con motivo opcional (≤ 500), fila actualizada y aviso con foco.
 * - Errores del contrato en español; carga, vacío, error y superadmin.
 * - Enganche en `UsersList`: botón "Accesos" que abre y cierra el panel.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Access, Paginated } from '@/lib/access/types';
import type { ManagedUser } from '@/lib/types';

vi.mock('@/lib/access/grants', () => ({
  grantsApi: { ofUser: vi.fn(), revoke: vi.fn(), mine: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { users: vi.fn(), areas: vi.fn(), platforms: vi.fn() },
}));
vi.mock('@/lib/access/users', () => ({ usersApi: { setManagedAreas: vi.fn() } }));

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
import { grantsApi } from '@/lib/access/grants';
import { UsersList } from '@/components/users-list';
import {
  ESTADO_PARA_ADMIN, MENSAJE_SUPERADMIN, SIN_ACCION, UserAccessPanel, avisoRevocacion,
  mensajeVacioAccesos, motivoSinRevocar,
} from '@/components/users/user-access-panel';
import { pistaMotivoRevocacion } from '@/components/users/revoke-access-dialog';
import {
  MENSAJE_MOTIVO_REVOCACION, MENSAJES_REVOCACION, REVOCACION_MOTIVO_MAX, describeRevokeError,
} from '@/components/users/revoke-errors';

function pagina<T>(items: T[], extra: Partial<Paginated<T>> = {}): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length, ...extra };
}

const ANA: ManagedUser = {
  id: 8, email: 'ana@ejemplo.local', name: 'Ana Ruiz', role: 'usuario', is_active: true,
  auth_source: 'ldap', areas: [{ id: 3, name: 'Finanzas' }], managed_areas: [], last_login_at: null,
};

const ACTIVO: Access = {
  id: 77, status: 'activo', level: 'usuario', origin: 'solicitud',
  user: { id: 8, name: 'Ana Ruiz', email: 'ana@ejemplo.local' },
  platform: { id: 12, name: 'Contabilidad', integration_type: 'ldap' },
  area: { id: 3, name: 'Finanzas' }, request_id: 41, granted_by: { id: 2, name: 'Luis Paz' },
  granted_at: '2026-10-14T15:10:00Z', revoked_by: null, revoked_at: null, revoke_reason: null,
  last_job_id: 301,
};
const AUTOMATICO: Access = {
  ...ACTIVO, id: 78, origin: 'admin_de_area', request_id: null, granted_by: null,
  platform: { id: 14, name: 'Wiki', integration_type: 'conector' },
};
const EN_PROCESO: Access = {
  ...ACTIVO, id: 79, status: 'en_proceso', platform: { id: 15, name: 'Nómina', integration_type: 'ldap' },
};
const REVOCADO: Access = {
  ...ACTIVO, id: 80, status: 'revocado', revoked_at: '2026-10-18T10:00:00Z',
  revoked_by: { id: 2, name: 'Luis Paz' }, revoke_reason: '<b>Cambio</b> de puesto',
  platform: { id: 16, name: 'CRM', integration_type: 'ldap' },
};

const FILA_CONTA = 'Acceso a Contabilidad';
const REVOCAR_CONTA = 'Revocar el acceso de Ana Ruiz a Contabilidad';

beforeEach(() => {
  vi.clearAllMocks();
  esSuperadmin = false;
  vi.mocked(grantsApi.ofUser).mockResolvedValue(pagina([ACTIVO, AUTOMATICO, EN_PROCESO]));
});

afterEach(cleanup);

describe('motivoSinRevocar (reglas del contrato)', () => {
  const sesion = { id: MI_ID, esSuperadmin: false };
  const propio: Access = { ...ACTIVO, user: { ...ACTIVO.user, id: MI_ID } };
  const adminDelArea: ManagedUser = { ...ANA, managed_areas: [{ id: 3, name: 'Finanzas' }] };
  const superadmin = { ...sesion, esSuperadmin: true };
  it.each<[string, Access, ManagedUser, typeof sesion, string | null]>([
    ['activo por solicitud', ACTIVO, ANA, sesion, null],
    ['no activo (409)', EN_PROCESO, ANA, sesion, SIN_ACCION.noActivo],
    ['propio (403)', propio, ANA, sesion, SIN_ACCION.propio],
    ['automático, admin de área (404)', AUTOMATICO, ANA, sesion, SIN_ACCION.automatico],
    ['automático, superadmin', AUTOMATICO, ANA, superadmin, null],
    ['de otro admin del área (404)', ACTIVO, adminDelArea, sesion, SIN_ACCION.adminDelArea],
    ['de otro admin del área, superadmin', ACTIVO, adminDelArea, superadmin, null],
    ['propio, también superadmin', propio, ANA, superadmin, SIN_ACCION.propio],
  ])('%s', (_caso, access, user, s, esperado) => {
    expect(motivoSinRevocar(access, user, s)).toBe(esperado);
  });
});

describe('UserAccessPanel: lista', () => {
  it('pide `vigente` y muestra plataforma, nivel, origen, quién aprobó, estado y última ejecución', async () => {
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    const conta = await screen.findByRole('listitem', { name: FILA_CONTA });
    expect(grantsApi.ofUser).toHaveBeenCalledWith(8, { status: 'vigente', page: 1 });
    expect(within(conta).getByText('Finanzas')).toBeTruthy();
    expect(within(conta).getByText('Usuario')).toBeTruthy();
    expect(within(conta).getByText('Por solicitud')).toBeTruthy();
    expect(within(conta).getByText('Aprobó Luis Paz')).toBeTruthy();
    expect(within(conta).getByText('Con acceso')).toBeTruthy();
    expect(within(conta).getByText(ESTADO_PARA_ADMIN.activo)).toBeTruthy();
    expect(within(conta).getByText('Última ejecución: n.º 301')).toBeTruthy();
    expect(within(conta).getByRole('button', { name: REVOCAR_CONTA })).toBeTruthy();
  });

  it('sin botón de revocar donde el contrato no lo permite, con el motivo', async () => {
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    const wiki = await screen.findByRole('listitem', { name: 'Acceso a Wiki' });
    expect(within(wiki).getByText('Por el sistema')).toBeTruthy();
    expect(within(wiki).getByText(SIN_ACCION.automatico)).toBeTruthy();
    expect(within(wiki).queryByRole('button')).toBeNull();
    const nomina = screen.getByRole('listitem', { name: 'Acceso a Nómina' });
    expect(within(nomina).getByText(SIN_ACCION.noActivo)).toBeTruthy();
    expect(within(nomina).queryByRole('button')).toBeNull();
  });

  it('el superadmin puede revocar el acceso automático', async () => {
    esSuperadmin = true;
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    const wiki = await screen.findByRole('listitem', { name: 'Acceso a Wiki' });
    expect(within(wiki).getByRole('button', { name: 'Revocar el acceso de Ana Ruiz a Wiki' })).toBeTruthy();
  });

  it('revocado: quién, cuándo y el motivo escapado', async () => {
    vi.mocked(grantsApi.ofUser).mockResolvedValue(pagina([REVOCADO]));
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    const crm = await screen.findByRole('listitem', { name: 'Acceso a CRM' });
    expect(within(crm).getByText(/por Luis Paz/)).toBeTruthy();
    expect(within(crm).getByText('Motivo: <b>Cambio</b> de puesto')).toBeTruthy();
    expect(crm.querySelector('b')).toBeNull();
  });

  it('filtra por estado y pagina', async () => {
    vi.mocked(grantsApi.ofUser).mockResolvedValue(pagina([ACTIVO], { total: 30 }));
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Siguiente' }));
    await waitFor(() => expect(grantsApi.ofUser).toHaveBeenLastCalledWith(8, { status: 'vigente', page: 2 }));
    fireEvent.change(screen.getByLabelText('Filtrar los accesos de Ana Ruiz por estado'),
      { target: { value: 'revocado' } });
    await waitFor(() => expect(grantsApi.ofUser).toHaveBeenLastCalledWith(8, { status: 'revocado', page: 1 }));
  });

  it('carga, vacío y error con reintento', async () => {
    let resolver: (value: Paginated<Access>) => void = () => {};
    vi.mocked(grantsApi.ofUser).mockReturnValueOnce(new Promise((r) => { resolver = r; }));
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    expect(screen.getByText('Cargando los accesos…')).toBeTruthy();
    resolver(pagina([]));
    expect(await screen.findByText(mensajeVacioAccesos('vigente'))).toBeTruthy();
    cleanup();

    vi.mocked(grantsApi.ofUser).mockRejectedValueOnce(new ApiError(404, 'Not found'));
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    expect(await screen.findByText('No se pudieron cargar los accesos de Ana Ruiz.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByRole('listitem', { name: FILA_CONTA })).toBeTruthy();
  });

  it('superadmin como usuario consultado: estado explicado y sin llamadas', () => {
    render(<UserAccessPanel user={{ ...ANA, role: 'administrador' }} onClose={() => {}} />);
    expect(screen.getByText(MENSAJE_SUPERADMIN)).toBeTruthy();
    expect(grantsApi.ofUser).not.toHaveBeenCalled();
  });

  it('al abrir, el foco va al título del panel', () => {
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Accesos de Ana Ruiz' }));
  });
});

describe('UserAccessPanel: revocar', () => {
  async function abrirRevocacion() {
    render(<UserAccessPanel user={ANA} onClose={() => {}} />);
    const boton = within(await screen.findByRole('listitem', { name: FILA_CONTA }))
      .getByRole('button', { name: REVOCAR_CONTA });
    fireEvent.click(boton);
    const dialogo = screen.getByRole('dialog', { name: 'Revocar acceso' });
    return {
      boton,
      dialogo,
      motivo: within(dialogo).getByLabelText('Motivo de la revocación') as HTMLTextAreaElement,
      enviar: within(dialogo).getByRole('button', { name: 'Revocar' }) as HTMLButtonElement,
    };
  }

  it('confirma sin motivo (opcional), actualiza la fila y anuncia con el foco', async () => {
    vi.mocked(grantsApi.revoke).mockResolvedValue({ status: 'success', access: { ...ACTIVO, status: 'revocando' } });
    const { dialogo, enviar } = await abrirRevocacion();
    expect(within(dialogo).getByText(/Se retirará el acceso de Ana Ruiz a Contabilidad/)).toBeTruthy();
    expect(grantsApi.revoke).not.toHaveBeenCalled();
    expect(enviar.disabled).toBe(false);
    fireEvent.click(enviar);

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(grantsApi.revoke).toHaveBeenCalledWith(77, null);
    expect(grantsApi.ofUser).toHaveBeenCalledTimes(1);
    const fila = screen.getByRole('listitem', { name: FILA_CONTA });
    expect(within(fila).getByText('Revocando acceso')).toBeTruthy();
    expect(within(fila).queryByRole('button')).toBeNull();
    const aviso = screen.getByText(avisoRevocacion(ACTIVO));
    await waitFor(() => expect(document.activeElement).toBe(aviso.closest('[role="status"]')));
  });

  it('envía el motivo recortado y el contador lo refleja', async () => {
    vi.mocked(grantsApi.revoke).mockResolvedValue({ status: 'success', access: { ...ACTIVO, status: 'revocando' } });
    const { dialogo, motivo, enviar } = await abrirRevocacion();
    expect(enviar.getAttribute('aria-describedby')).toBe('revocacion-motivo-pista');
    fireEvent.change(motivo, { target: { value: '  Cambio de puesto  ' } });
    expect(within(dialogo).getByText(pistaMotivoRevocacion(16))).toBeTruthy();
    fireEvent.click(enviar);
    await waitFor(() => expect(grantsApi.revoke).toHaveBeenCalledWith(77, 'Cambio de puesto'));
  });

  it('más de 500 caracteres: error ligado y envío deshabilitado', async () => {
    const { dialogo, motivo, enviar } = await abrirRevocacion();
    fireEvent.change(motivo, { target: { value: 'x'.repeat(REVOCACION_MOTIVO_MAX + 1) } });
    expect(within(dialogo).getByText(MENSAJE_MOTIVO_REVOCACION)).toBeTruthy();
    expect(motivo.getAttribute('aria-invalid')).toBe('true');
    expect(motivo.getAttribute('aria-describedby')).toContain('revocacion-motivo-error');
    expect(enviar.disabled).toBe(true);
  });

  it('cancelar no llama a la API y devuelve el foco al botón de la fila', async () => {
    const { boton, dialogo } = await abrirRevocacion();
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(grantsApi.revoke).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(boton);
  });

  it('mientras se revoca el botón queda `aria-disabled` con el foco', async () => {
    vi.mocked(grantsApi.revoke).mockReturnValue(new Promise(() => {}));
    const { dialogo, enviar } = await abrirRevocacion();
    enviar.focus();
    fireEvent.click(enviar);
    const enviando = await within(dialogo).findByRole('button', { name: 'Revocando…' }) as HTMLButtonElement;
    expect(enviando.disabled).toBe(false);
    expect(enviando.getAttribute('aria-disabled')).toBe('true');
    expect(document.activeElement).toBe(enviando);
    fireEvent.click(enviando);
    expect(grantsApi.revoke).toHaveBeenCalledTimes(1);
  });

  it.each<[unknown, string, boolean]>([
    [new ApiError(403, 'x', { code: 'operacion_propia' }), MENSAJES_REVOCACION.operacion_propia, false],
    [new ApiError(409, 'x', { code: 'estado_invalido' }), MENSAJES_REVOCACION.estado_invalido, true],
    [new ApiError(404, 'x'), 'Este acceso ya no está en tu alcance. La lista se actualizó.', true],
    [new Error('red'), 'No se pudo revocar el acceso. Inténtalo de nuevo.', false],
  ])('error %#: mensaje en español y recarga si quedó desactualizada', async (error, mensaje, recarga) => {
    vi.mocked(grantsApi.revoke).mockRejectedValue(error);
    const { dialogo, enviar } = await abrirRevocacion();
    fireEvent.click(enviar);
    expect(await within(dialogo).findByText(mensaje)).toBeTruthy();
    await waitFor(() => expect(grantsApi.ofUser).toHaveBeenCalledTimes(recarga ? 2 : 1));
  });

  it('422 en `reason`: error en el campo con el foco, sin el texto del servidor', async () => {
    vi.mocked(grantsApi.revoke).mockRejectedValue(
      new ApiError(422, 'Detalle interno', { code: 'validacion', fields: { reason: 'Máximo 500 caracteres.' } }));
    const { dialogo, motivo, enviar } = await abrirRevocacion();
    fireEvent.change(motivo, { target: { value: 'Motivo' } });
    fireEvent.click(enviar);
    expect(await within(dialogo).findByText(MENSAJE_MOTIVO_REVOCACION)).toBeTruthy();
    expect(within(dialogo).getByText(MENSAJES_REVOCACION.validacion)).toBeTruthy();
    expect(within(dialogo).queryByText('Detalle interno')).toBeNull();
    expect(document.activeElement).toBe(motivo);
  });

  it('describeRevokeError: 401 y estado desconocido', () => {
    expect(describeRevokeError(new ApiError(401, 'x')).message).toBe('Tu sesión terminó. Vuelve a iniciar sesión.');
    expect(describeRevokeError(new ApiError(500, 'stack')).message).toBe('No se pudo revocar el acceso. Inténtalo de nuevo.');
  });
});

describe('UsersList: botón "Accesos" (DIS-018)', () => {
  beforeEach(() => {
    vi.mocked(api.users).mockResolvedValue([ANA]);
    vi.mocked(api.areas).mockResolvedValue([]);
    vi.mocked(api.platforms).mockResolvedValue([]);
  });

  it('abre el panel del usuario y, al cerrarlo, devuelve el foco al botón', async () => {
    render(<UsersList />);
    const boton = await screen.findByRole('button', { name: 'Accesos de Ana Ruiz' });
    fireEvent.click(boton);
    expect(screen.getByRole('heading', { name: 'Accesos de Ana Ruiz' })).toBeTruthy();
    expect(await screen.findByRole('listitem', { name: FILA_CONTA })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar accesos' }));
    expect(screen.queryByRole('heading', { name: 'Accesos de Ana Ruiz' })).toBeNull();
    expect(document.activeElement).toBe(boton);
  });
});
