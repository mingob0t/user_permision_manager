/**
 * DIS-023: pestaña Directorio de Ajustes (`GET /auth-config` y `POST
 * /auth-config/test`, contrato `usuarios-directorio.md`; solo superadmin).
 * - Solo lectura: valores con su variable y origen; sin contraseña ni mapeos de rol.
 * - Estados: carga, sin configurar, configuración inválida y error (sin texto del servidor).
 * - Prueba de conexión: texto propio en `status` o `alert`, foco en el aviso,
 *   `aria-disabled` cuando no hay configuración válida.
 * DIS-034: pestañas de Ajustes con ←/→/Inicio/Fin y `tabpanel`; Directorio solo para el superadmin.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { DirectoryConfig } from '@/lib/access/types';

vi.mock('@/lib/access/directory', () => ({
  directoryApi: { config: vi.fn(), reload: vi.fn(), test: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { settings: vi.fn(), smtp: vi.fn(), templates: vi.fn() },
}));
const sesion = vi.hoisted(() => ({ isAdmin: true }));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 1, role: sesion.isAdmin ? 'administrador' : 'usuario', managed_areas: [],
      preferences: { notifications: true, email_notifications: false, tour_enabled: false, refresh_interval: 60 },
      permissions: { is_admin: sesion.isAdmin, is_area_admin: false, can_manage_areas: false, can_manage_system: sesion.isAdmin },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { directoryApi } from '@/lib/access/directory';
import { DirectoryTab } from '@/components/settings/directory-tab';
import { SettingsPanel } from '@/components/settings-panel';
import {
  ETIQUETA_CONTRASENA, MENSAJE_INVALIDA, MENSAJE_SIN_CONFIGURAR, PISTA_PRUEBA_NO_DISPONIBLE,
} from '@/components/settings/directory-catalog';
import { ERROR_CARGA, ERROR_NO_DISPONIBLE, PRUEBA_OK } from '@/components/settings/directory-errors';

const TEXTO_SERVIDOR = 'Detalle interno del servidor ldap.interno';

const ACTIVO: DirectoryConfig = {
  active: true, source: 'env', editable: false, error: null,
  config: {
    url: 'ldaps://ldap.ejemplo.local', host: 'ldap.ejemplo.local', port: 636, tls: 'ldaps',
    ca_cert: 'custom', bind_dn: 'cn=portal,dc=ejemplo,dc=local',
    users_base_dn: 'ou=personas,dc=ejemplo,dc=local', groups_base_dn: 'ou=grupos,dc=ejemplo,dc=local',
    user_attr: 'uid', group_object_class: 'groupOfNames', group_member_attr: 'member',
    timeout_seconds: 5, user_object_classes: ['inetOrgPerson'], placeholder_member: '',
  },
  origins: {
    url: 'env', ca_cert: 'env', bind_dn: 'env', users_base_dn: 'env', groups_base_dn: 'env',
    user_attr: 'default', group_object_class: 'default', group_member_attr: 'default',
    timeout_seconds: 'default', user_object_classes: 'default', placeholder_member: 'default',
  },
  variables: {
    url: 'LDAP_URL', ca_cert: 'LDAP_CA_CERT_FILE', bind_dn: 'LDAP_BIND_DN',
    users_base_dn: 'LDAP_USERS_BASE_DN', groups_base_dn: 'LDAP_GROUPS_BASE_DN',
    user_attr: 'LDAP_USER_ATTR', group_object_class: 'LDAP_GROUP_OBJECT_CLASS',
    group_member_attr: 'LDAP_GROUP_MEMBER_ATTR', timeout_seconds: 'LDAP_TIMEOUT_SECONDS',
    user_object_classes: 'LDAP_USER_OBJECT_CLASSES', placeholder_member: 'LDAP_GROUP_PLACEHOLDER_MEMBER',
  },
};
const INACTIVO: DirectoryConfig = { ...ACTIVO, active: false, config: null };
const INVALIDO: DirectoryConfig = { ...ACTIVO, config: null, error: 'configuracion_invalida' };

const mocks = { config: vi.mocked(directoryApi.config), test: vi.mocked(directoryApi.test) };

beforeEach(() => {
  vi.clearAllMocks();
  sesion.isAdmin = true;
  mocks.config.mockResolvedValue(ACTIVO);
  // Las demás pestañas quedan cargando: aquí solo importa la navegación.
  vi.mocked(api.settings).mockReturnValue(new Promise(() => {}));
  vi.mocked(api.smtp).mockReturnValue(new Promise(() => {}));
  vi.mocked(api.templates).mockReturnValue(new Promise(() => {}));
});
afterEach(cleanup);

function boton() {
  return screen.getByRole('button', { name: 'Probar conexión' });
}

describe('pestaña Directorio', () => {
  it('muestra la configuración con su variable y origen, sin contraseña ni roles', async () => {
    const { container } = render(<DirectoryTab />);
    expect(screen.getByText('Cargando la configuración del directorio…')).toBeTruthy();
    expect(await screen.findByText('ldaps://ldap.ejemplo.local')).toBeTruthy();
    expect(screen.getByText('Activo')).toBeTruthy();
    expect(screen.getByText('ldap.ejemplo.local:636')).toBeTruthy();
    expect(screen.getByText('CA propia')).toBeTruthy();
    expect(screen.getByText('LDAP_BIND_DN · definida en el entorno')).toBeTruthy();
    expect(screen.getByText('LDAP_USER_ATTR · valor por defecto')).toBeTruthy();
    expect(screen.getByText('Sin definir')).toBeTruthy();
    expect(screen.getByText(ETIQUETA_CONTRASENA)).toBeTruthy();
    // Solo lectura: ningún control editable; nada de grupos de rol ni sAMAccountName.
    expect(container.querySelectorAll('input, select, textarea')).toHaveLength(0);
    expect(screen.queryByText(/Grupo de administradores|sAMAccountName/)).toBeNull();
    expect(boton().getAttribute('aria-disabled')).toBeNull();
  });

  it('sin configurar: estado vacío explicado y prueba deshabilitada', async () => {
    mocks.config.mockResolvedValue(INACTIVO);
    render(<DirectoryTab />);
    expect(await screen.findByText(MENSAJE_SIN_CONFIGURAR)).toBeTruthy();
    expect(screen.getByText('Sin configurar')).toBeTruthy();
    expect(boton().getAttribute('aria-disabled')).toBe('true');
    expect(screen.getByText(PISTA_PRUEBA_NO_DISPONIBLE)).toBeTruthy();
    fireEvent.click(boton());
    expect(mocks.test).not.toHaveBeenCalled();
  });

  it('configuración inválida: alerta propia y prueba deshabilitada', async () => {
    mocks.config.mockResolvedValue(INVALIDO);
    render(<DirectoryTab />);
    expect(await screen.findByText(MENSAJE_INVALIDA)).toBeTruthy();
    expect(screen.getByText('Configuración inválida')).toBeTruthy();
    expect(boton().getAttribute('aria-disabled')).toBe('true');
  });

  it('error al cargar: mensaje propio y reintento', async () => {
    mocks.config.mockRejectedValueOnce(new ApiError(500, TEXTO_SERVIDOR));
    render(<DirectoryTab />);
    expect(await screen.findByText(ERROR_CARGA)).toBeTruthy();
    expect(screen.queryByText(TEXTO_SERVIDOR)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByText('Activo')).toBeTruthy();
  });

  it('sin permiso: 403 con texto propio', async () => {
    mocks.config.mockRejectedValueOnce(new ApiError(403, TEXTO_SERVIDOR));
    render(<DirectoryTab />);
    expect(await screen.findByText('Solo el superadmin consulta la configuración del directorio.')).toBeTruthy();
  });

  it('prueba correcta: texto propio en status y foco en el aviso', async () => {
    mocks.test.mockResolvedValue({ status: 'success', message: TEXTO_SERVIDOR });
    render(<DirectoryTab />);
    await screen.findByText('Activo');
    fireEvent.click(boton());
    expect(mocks.test).toHaveBeenCalledWith();
    const status = await waitFor(() => {
      const region = screen.getAllByRole('status').find((el) => el.textContent === PRUEBA_OK);
      expect(region).toBeTruthy();
      return region!;
    });
    expect(screen.queryByText(TEXTO_SERVIDOR)).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(status.parentElement));
  });

  it('prueba fallida (503): alerta propia sin el texto del servidor', async () => {
    mocks.test.mockRejectedValue(new ApiError(503, TEXTO_SERVIDOR, { code: 'directorio_no_disponible' }));
    render(<DirectoryTab />);
    await screen.findByText('Activo');
    fireEvent.click(boton());
    expect(await screen.findByText(ERROR_NO_DISPONIBLE)).toBeTruthy();
    expect(screen.queryByText(TEXTO_SERVIDOR)).toBeNull();
    expect(screen.getByText(ERROR_NO_DISPONIBLE).closest('[role="alert"]')).toBeTruthy();
  });

  it('prueba con 409: avisa y vuelve a leer la configuración', async () => {
    mocks.test.mockRejectedValue(new ApiError(409, TEXTO_SERVIDOR, { code: 'directorio_no_configurado' }));
    render(<DirectoryTab />);
    await screen.findByText('Activo');
    mocks.config.mockResolvedValue(INACTIVO);
    fireEvent.click(boton());
    await waitFor(() => expect(mocks.config).toHaveBeenCalledTimes(2));
    expect((await screen.findAllByText(MENSAJE_SIN_CONFIGURAR)).length).toBeGreaterThan(0);
  });
});

describe('pestañas de Ajustes (DIS-034)', () => {
  it('el superadmin ve Directorio y las flechas, Inicio y Fin mueven el foco', async () => {
    render(<SettingsPanel />);
    const lista = screen.getByRole('tablist', { name: 'Ajustes' });
    const pestanas = within(lista).getAllByRole('tab');
    expect(pestanas.map((p) => p.textContent)).toEqual(
      ['Portal', 'Correo', 'Plantillas', 'Directorio', 'Respaldo', 'Mis preferencias']);
    const [portal, , , , , preferencias] = pestanas;
    expect(portal.tabIndex).toBe(0);
    expect(pestanas[1].tabIndex).toBe(-1);
    fireEvent.keyDown(portal, { key: 'ArrowLeft' });
    expect(document.activeElement).toBe(preferencias);
    fireEvent.keyDown(preferencias, { key: 'Home' });
    expect(document.activeElement).toBe(portal);
    fireEvent.keyDown(portal, { key: 'End' });
    expect(document.activeElement).toBe(preferencias);
    fireEvent.keyDown(preferencias, { key: 'ArrowRight' });
    fireEvent.keyDown(portal, { key: 'ArrowRight' });
    fireEvent.keyDown(pestanas[1], { key: 'ArrowRight' });
    fireEvent.keyDown(pestanas[2], { key: 'ArrowRight' });
    const directorio = pestanas[3];
    expect(document.activeElement).toBe(directorio);
    expect(directorio.getAttribute('aria-selected')).toBe('true');
    const panel = screen.getByRole('tabpanel', { name: 'Directorio' });
    expect(directorio.getAttribute('aria-controls')).toBe(panel.id);
    expect(await within(panel).findByText('Activo')).toBeTruthy();
  });

  it('quien no es superadmin no ve la pestaña Directorio', () => {
    sesion.isAdmin = false;
    render(<SettingsPanel />);
    expect(screen.queryByRole('tab', { name: 'Directorio' })).toBeNull();
    expect(mocks.config).not.toHaveBeenCalled();
  });
});
