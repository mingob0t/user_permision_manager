/**
 * DIS-017: formulario de plataforma con tipo de integración y grupos por nivel
 * (contrato `plataformas-integracion.md`), por rol, con errores y avisos.
 */
import { cleanup, fireEvent, render as rtlRender, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastProvider } from '@/components/toast';
import { ApiError } from '@/lib/api';
import type { Area, ManagedUser, Platform } from '@/lib/types';

function render(ui: React.ReactElement, options?: Parameters<typeof rtlRender>[1]) {
  return rtlRender(<ToastProvider>{ui}</ToastProvider>, options);
}

vi.mock('@/lib/api', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/lib/api')>();
  return {
    ApiError: real.ApiError,
    api: {
      areas: vi.fn(), platforms: vi.fn(), users: vi.fn(),
      createPlatform: vi.fn(), updatePlatform: vi.fn(), deletePlatform: vi.fn(),
      createArea: vi.fn(), updateArea: vi.fn(), deleteArea: vi.fn(),
      platformAccess: vi.fn(), grantPlatformAccess: vi.fn(), revokeAccess: vi.fn(),
    },
  };
});

// DIS-137: resumen de la bandeja para «N por aprobar» de la tarjeta de área.
vi.mock('@/lib/access/requests', () => ({ requestsApi: { inboxStats: vi.fn() } }));

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
import { requestsApi } from '@/lib/access/requests';
import { PlatformAdmin } from '@/components/platform-admin';
import { DESCRIPCION_OMITIR_ENLACE } from '@/components/platforms/platform-form';
import { clearAsyncCache } from '@/lib/use-async';

const AREAS = [{ id: 3, name: 'Finanzas' }] as Area[];
const PLATAFORMA = {
  id: 12, name: 'Contabilidad', description: 'ERP contable', area_id: 3, area_name: 'Finanzas',
  direct_link: 'https://erp.ejemplo.local', bg_color: '', text_color: '', status: 'Activo',
} as Platform;

function comoSuperadmin() {
  permisos.is_admin = true;
  permisos.is_area_admin = false;
}

function respuesta(warnings: { code: string; message: string }[] = []) {
  return { status: 'success', platform: { ...PLATAFORMA, name: 'Nueva' }, warnings };
}

beforeEach(() => {
  vi.clearAllMocks();
  if (typeof window !== 'undefined') {
    window.history.replaceState({}, '', '/');
    window.localStorage.clear();
  }
  permisos.is_admin = false;
  permisos.is_area_admin = true;
  vi.mocked(api.areas).mockResolvedValue(AREAS);
  vi.mocked(api.platforms).mockResolvedValue([PLATAFORMA]);
  vi.mocked(api.users).mockResolvedValue([]);
  vi.mocked(api.platformAccess).mockResolvedValue({ items: [], total: 0 });
  vi.mocked(api.createPlatform).mockResolvedValue(respuesta());
  vi.mocked(api.updatePlatform).mockResolvedValue(respuesta());
  vi.mocked(requestsApi.inboxStats).mockResolvedValue({
    total: 0, by_status: { pendiente: 0, aprobada: 0, rechazada: 0 }, by_area: [], by_platform: [],
    pending_by_area: [],
  });
});

describe('PlatformAdmin: por aprobar en la tarjeta de área (DIS-137, DIS-162)', () => {
  it('muestra los pendientes del área (pending_by_area) con enlace a su bandeja', async () => {
    vi.mocked(requestsApi.inboxStats).mockResolvedValue({
      total: 2, by_status: { pendiente: 2, aprobada: 0, rechazada: 0 },
      by_area: [{ area_id: 3, area: 'Finanzas', count: 2 }], by_platform: [],
      pending_by_area: [{ area_id: 3, area: 'Finanzas', count: 2 }],
    });
    render(<PlatformAdmin />);
    const enlace = await screen.findByRole('link', { name: /Solicitudes pendientes: 2, en Finanzas/ });
    expect(enlace.getAttribute('href')).toBe('/approvals?status=pendiente&area_id=3');
  });

  it('sin pendientes o si el resumen falla, no hay enlace', async () => {
    vi.mocked(requestsApi.inboxStats).mockRejectedValue(new Error('sin red'));
    render(<PlatformAdmin />);
    await screen.findByText('Finanzas');
    expect(screen.queryByRole('link', { name: /solicitudes pendientes/ })).toBeNull();
  });
});

afterEach(() => cleanup());

function dialogo() {
  return within(screen.queryByRole('alertdialog') ?? screen.getByRole('dialog'));
}

async function abrirAlta() {
  render(<PlatformAdmin />);
  fireEvent.click(await screen.findByText('Finanzas'));
  await screen.findByText('Contabilidad');
  fireEvent.click(screen.getByRole('button', { name: /nuevo/i }));
  const modal = dialogo();
  fireEvent.change(modal.getByLabelText(/^Nombre/), { target: { value: 'Nueva' } });
  fireEvent.change(modal.getByLabelText(/^Descripción/), { target: { value: 'Descripción' } });
  // DIS-133: sin «Omitir enlace» el enlace es obligatorio.
  fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'https://nueva.ejemplo.local' } });
  return modal;
}

function avanzarYGuardar(modal: ReturnType<typeof dialogo>) {
  // Límite de pasos: si una validación bloquea el avance, la prueba falla en
  // lugar de quedarse en un bucle infinito.
  for (let i = 0; i < 5 && modal.queryByText('Guardar') === null && modal.queryByText('Siguiente') !== null; i++) {
    fireEvent.click(modal.getByText('Siguiente'));
  }
  fireEvent.click(modal.getByText('Guardar'));
}

describe('PlatformAdmin: alta por rol', () => {
  it('asistente de 3 pasos: Paso 1 (Descripción), Paso 2 (Diseño con vista previa, sin control de estado) y Paso 3 (Accesos con Dual Picklist)', async () => {
    const modal = await abrirAlta();
    // Paso 1: muestra controles de descripción y no los de diseño, sin área ni conector
    expect(modal.getByLabelText(/^Nombre/)).toBeTruthy();
    expect(modal.getByLabelText(/^Descripción/)).toBeTruthy();
    expect(modal.getByLabelText(/^Enlace/)).toBeTruthy();
    expect(modal.queryByRole('combobox', { name: /^Área/ })).toBeNull();
    expect(modal.queryByLabelText(/^Tipo de integración/)).toBeNull();
    expect(modal.queryByLabelText('Color de fondo')).toBeNull();

    // Avanzar a Paso 2: Diseño (con vista previa; el estado se conmuta con el badge, DIS-114)
    fireEvent.click(modal.getByText('Siguiente'));
    expect(modal.getByText('Diseño')).toBeTruthy();
    expect(await modal.findByLabelText('Color de fondo')).toBeTruthy();
    expect(modal.getByLabelText(/Color del icono|Color de texto/i)).toBeTruthy();
    expect(modal.getByText('Elegir icono')).toBeTruthy();
    expect(modal.getByText('Subir imagen')).toBeTruthy();
    expect(modal.getByText('Vista previa de la plataforma')).toBeTruthy();
    expect(modal.queryByRole('switch', { name: /activa/i })).toBeNull();

    // Avanzar a Paso 3: Accesos con Dual Picklist
    fireEvent.click(modal.getByText('Siguiente'));
    expect(modal.getByText('Accesos')).toBeTruthy();
    expect(modal.getByText('Sin acceso')).toBeTruthy();
    expect(modal.getByText('Con acceso')).toBeTruthy();

    // Retroceder a Paso 2: Diseño
    fireEvent.click(modal.getByText('Atrás'));
    expect(modal.getByText('Diseño')).toBeTruthy();
    expect(modal.getByText('Vista previa de la plataforma')).toBeTruthy();

    // Retroceder a Paso 1
    fireEvent.click(modal.getByText('Atrás'));
    expect(modal.getByLabelText(/^Nombre/)).toBeTruthy();
    expect((modal.getByLabelText(/^Nombre/) as HTMLInputElement).value).toBe('Nueva');
  });

  it('Paso 3 Dual Picklist: permite asignar accesos a usuarios del área y llama a grantPlatformAccess al guardar', async () => {
    const usuarioFinanzas = {
      id: 88,
      name: 'Carlos Finanzas',
      email: 'carlos@ejemplo.local',
      role: 'usuario',
      areas: [{ id: 3, name: 'Finanzas' }],
      platforms: [],
    } as unknown as ManagedUser;
    vi.mocked(api.users).mockResolvedValue([usuarioFinanzas]);
    vi.mocked(api.platformAccess).mockResolvedValue({ items: [], total: 0 });

    const modal = await abrirAlta();
    // Paso 1 -> Paso 2
    fireEvent.click(modal.getByText('Siguiente'));
    // Paso 2 -> Paso 3
    fireEvent.click(modal.getByText('Siguiente'));
    expect(modal.getByText('Accesos')).toBeTruthy();

    // El usuario debe aparecer en la columna "Sin acceso"
    expect(await modal.findByText('Carlos Finanzas')).toBeTruthy();

    // Click en el usuario para pasarlo a "Con acceso"
    fireEvent.click(modal.getByRole('button', { name: /Otorgar acceso a Carlos Finanzas/i }));

    // Click en Guardar
    fireEvent.click(modal.getByText('Guardar'));

    await waitFor(() => expect(api.createPlatform).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.grantPlatformAccess).toHaveBeenCalledWith(PLATAFORMA.id, 88, 'usuario'));
  });

  it('alta simplificada: crea la plataforma en el área seleccionada con conector por omisión', async () => {
    const modal = await abrirAlta();
    avanzarYGuardar(modal);

    await waitFor(() => expect(api.createPlatform).toHaveBeenCalledTimes(1));
    const enviado = vi.mocked(api.createPlatform).mock.calls[0][0];
    expect(enviado).toMatchObject({
      name: 'Nueva',
      description: 'Descripción',
      area_id: 3,
      integration_type: 'conector',
    });
    expect(enviado).not.toHaveProperty('ldap_group_user_dn');
    expect(enviado).not.toHaveProperty('ldap_group_admin_dn');
    // Sin color elegido no se envía: el servidor aplica el suyo por omisión.
    expect(enviado).not.toHaveProperty('bg_color');
    expect(enviado).not.toHaveProperty('text_color');
  });

  it('enlace que no es https: error en el campo, sin enviar', async () => {
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'javascript:alert(1)' } });
    fireEvent.click(modal.getByText('Siguiente'));
    expect(await modal.findByText('Usa una dirección https://.')).toBeTruthy();
    expect(api.createPlatform).not.toHaveBeenCalled();
  });

  it('enlace sin https: antepone https:// automáticamente y permite guardar sin error', async () => {
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'sistema.empresa.local' } });
    avanzarYGuardar(modal);
    await waitFor(() => expect(api.createPlatform).toHaveBeenCalledTimes(1));
    const [enviado] = vi.mocked(api.createPlatform).mock.calls[0];
    expect(enviado.direct_link).toBe('https://sistema.empresa.local');
  });
});

describe('PlatformAdmin: edición por rol', () => {
  it('admin de área: no envía el tipo ni DN y no expone área ni integración', async () => {
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    fireEvent.click(await screen.findByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: /Editar Contabilidad/i }));
    const modal = dialogo();
    expect(modal.queryByRole('combobox', { name: /^Área/ })).toBeNull();
    expect(modal.queryByLabelText(/^Tipo de integración/)).toBeNull();
    avanzarYGuardar(modal);
    await waitFor(() => expect(api.updatePlatform).toHaveBeenCalledTimes(1));
    const [, enviado] = vi.mocked(api.updatePlatform).mock.calls[0];
    expect(enviado).not.toHaveProperty('integration_type');
    expect(enviado).not.toHaveProperty('ldap_group_user_dn');
  });

  it('superadmin: "Sin cambiar" no envía el tipo', async () => {
    comoSuperadmin();
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    fireEvent.click(await screen.findByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: /Editar Contabilidad/i }));
    avanzarYGuardar(dialogo());
    await waitFor(() => expect(api.updatePlatform).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.updatePlatform).mock.calls[0][1]).not.toHaveProperty('integration_type');
  });

  it('con accesos vigentes: el formulario simplificado omite área e integración', async () => {
    comoSuperadmin();
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, integration_type: 'ldap', active_grants: 4 }]);
    render(<PlatformAdmin initialAreaId={3} />);
    fireEvent.click(await screen.findByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: /Editar Contabilidad/i }));
    const modal = dialogo();
    expect(modal.queryByRole('combobox', { name: /^Área/ })).toBeNull();
    expect(modal.queryByLabelText(/^Tipo de integración/)).toBeNull();
    expect(modal.getByLabelText(/^Nombre/)).toBeTruthy();
  });
});

describe('PlatformAdmin: errores del backend', () => {
  async function guardarConError(error: ApiError) {
    comoSuperadmin();
    vi.mocked(api.createPlatform).mockRejectedValue(error);
    const modal = await abrirAlta();
    avanzarYGuardar(modal);
    return modal;
  }

  it('422: errores por campo y mensaje general', async () => {
    const modal = await guardarConError(new ApiError(422, 'Datos no válidos.', {
      code: 'validacion',
      fields: { direct_link: 'Usa una dirección https://.', icon: 'Debe ser texto.' },
    }));
    expect(await modal.findByText('Usa una dirección https://.')).toBeTruthy();
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

  it('409 grupos_iguales en edición: mensaje general del contrato', async () => {
    comoSuperadmin();
    vi.mocked(api.updatePlatform).mockRejectedValue(new ApiError(409, 'x', { code: 'grupos_iguales' }));
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    fireEvent.click(await screen.findByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: /Editar Contabilidad/i }));
    const modal = dialogo();
    avanzarYGuardar(modal);
    expect(await modal.findByText('Los grupos de usuario y admin deben ser distintos.')).toBeTruthy();
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
    avanzarYGuardar(modal);
    expect(await screen.findByText('Guardada con avisos')).toBeTruthy();
    expect(screen.getByText(/El grupo de nivel usuario no existe en el directorio\./)).toBeTruthy();
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.queryByRole('alertdialog')).toBeNull();
    fireEvent.click(screen.getByLabelText('Cerrar aviso'));
    expect(screen.queryByText('Guardada con avisos')).toBeNull();
  });

  it('sin avisos: confirma el guardado', async () => {
    const modal = await abrirAlta();
    avanzarYGuardar(modal);
    expect(await screen.findByText('Guardada')).toBeTruthy();
  });

  it('enlace no https en la tabla: se muestra "Sin enlace"', async () => {
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, direct_link: 'javascript:alert(1)' }]);
    render(<PlatformAdmin initialAreaId={3} />);
    expect(await screen.findByText('Sin enlace')).toBeTruthy();
    expect(screen.queryByText('javascript:alert(1)')).toBeNull();
  });

  it('DIS-138: sin enlace («Omitir enlace») se muestra como «No requiere enlace web» y sin aviso de pendiente', async () => {
    // Sin la caché de `useAsync`, que guarda las plataformas de la prueba anterior.
    clearAsyncCache();
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, direct_link: '' }]);
    render(<PlatformAdmin initialAreaId={3} />);
    expect(await screen.findByText('No requiere enlace web')).toBeTruthy();
    expect(screen.queryByText('Sin enlace')).toBeNull();
    expect(screen.queryByText('Enlace pendiente')).toBeNull();
    expect(screen.queryByText('Enlace no válido')).toBeNull();
  });

  it('DIS-138: un enlace no https sí avisa como «Enlace no válido»', async () => {
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, direct_link: 'http://inseguro.ejemplo.local' }]);
    render(<PlatformAdmin initialAreaId={3} />);
    expect(await screen.findByText('Enlace no válido')).toBeTruthy();
    expect(screen.getByText('1 plataforma tiene un enlace no válido (debe ser https).')).toBeTruthy();
  });

  it('DIS-138: «Omitir enlace» explica que no necesita un enlace web', async () => {
    const modal = await abrirAlta();
    expect(modal.getByText(DESCRIPCION_OMITIR_ENLACE)).toBeTruthy();
    expect(modal.queryByText(/no se puede abrir/)).toBeNull();
  });

  it('vacío y error de carga', async () => {
    vi.mocked(api.platforms).mockResolvedValue([]);
    render(<PlatformAdmin initialAreaId={3} />);
    expect(await screen.findByText('Sin plataformas en Finanzas')).toBeTruthy();
    cleanup();
    vi.mocked(api.platforms).mockRejectedValue(new Error('Falla de red'));
    render(<PlatformAdmin initialAreaId={3} />);
    expect(await screen.findByText('Falla de red')).toBeTruthy();
  });

  it('usuario sin rol de admin: sin permiso y sin llamar a la API', () => {
    permisos.is_area_admin = false;
    render(<PlatformAdmin />);
    expect(screen.getByText('No tienes permiso para ver esta sección.')).toBeTruthy();
    expect(api.platforms).not.toHaveBeenCalled();
  });
});

describe('PlatformAdmin: cuadrícula de áreas y navegación a plataformas', () => {
  it('renderiza la barra de herramientas y las cards de áreas con badges de conteo y ghost cards para simetría 4x2', async () => {
    const { container } = render(<PlatformAdmin />);
    expect(await screen.findByLabelText('Buscar áreas')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Filtrar por estado/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Configurar cuadrícula/i })).toBeTruthy();
    expect(screen.getByText('Finanzas')).toBeTruthy();
    expect(screen.getByLabelText('Área Finanzas, 1 plataforma. Ver plataformas.')).toBeTruthy();
    // 5 huecos para completar la cuadrícula 2×3 por omisión (6 en total): la rejilla ocupa todo el alto
    const ghostCards = container.querySelectorAll('.border-dashed[aria-hidden="true"]');
    expect(ghostCards).toHaveLength(5);
  });

  it('el botón de filtrar por estado permite alternar entre Todos, Activas e Inactivas', async () => {
    vi.mocked(api.areas).mockResolvedValueOnce([
      { id: 1, name: 'Finanzas Activa', status: 'Activo' } as Area,
      { id: 2, name: 'Legales Inactiva', status: 'Inactivo' } as Area,
    ]);
    render(<PlatformAdmin />);
    expect(await screen.findByText('Finanzas Activa')).toBeTruthy();
    expect(screen.getByText('Legales Inactiva')).toBeTruthy();

    // Abrir menú de estado
    fireEvent.click(screen.getByRole('button', { name: /Filtrar por estado/i }));
    // Filtrar por Activas (exacto)
    fireEvent.click(screen.getByRole('option', { name: /^Activas$/i }));
    expect(screen.getByText('Finanzas Activa')).toBeTruthy();
    expect(screen.queryByText('Legales Inactiva')).toBeNull();

    // Abrir menú y filtrar por Inactivas (exacto)
    fireEvent.click(screen.getByRole('button', { name: /Filtrar por estado/i }));
    fireEvent.click(screen.getByRole('option', { name: /^Inactivas$/i }));
    expect(screen.queryByText('Finanzas Activa')).toBeNull();
    expect(screen.getByText('Legales Inactiva')).toBeTruthy();
  });

  it('la cuadrícula ofrece 2×2, 2×3, 3×2 y 3×3, y recuerda la elegida (DIS-103, DIS-111)', async () => {
    const { container } = render(<PlatformAdmin />);
    await screen.findByText('Finanzas');
    const huecos = () => container.querySelectorAll('.border-dashed[aria-hidden="true"]');

    // Por omisión 2×3 (6 slots: 1 real + 5 huecos)
    expect(huecos()).toHaveLength(5);

    fireEvent.click(screen.getByRole('button', { name: /Configurar cuadrícula/i }));
    for (const quitada of ['2×4', '3×4', '4×2', '4×3', '4×4', '4 filas', '4 columnas']) {
      expect(screen.queryByRole('button', { name: quitada })).toBeNull();
    }

    // DIS-109: sin el texto «Combinaciones» (pedido del dueño)
    expect(screen.queryByText('Combinaciones')).toBeNull();
    // DIS-111: 2×2 (4 slots: 1 real + 3 huecos)
    fireEvent.click(screen.getByRole('button', { name: '2×2' }));
    expect(huecos()).toHaveLength(3);
    fireEvent.click(screen.getByRole('button', { name: '3×2' }));
    expect(huecos()).toHaveLength(5);

    fireEvent.click(screen.getByRole('button', { name: '3×3' }));
    expect(huecos()).toHaveLength(8);
    expect(window.localStorage.getItem('portal_grid_filas')).toBe('3');
    expect(window.localStorage.getItem('portal_grid_columnas')).toBe('3');

    cleanup();
    const segundo = render(<PlatformAdmin />);
    await segundo.findByText('Finanzas');
    expect(segundo.container.querySelectorAll('.border-dashed[aria-hidden="true"]')).toHaveLength(8);
  });

  it('una cuadrícula guardada que ya no existe (2×4) vuelve a 2×3', async () => {
    window.localStorage.setItem('portal_grid_filas', '2');
    window.localStorage.setItem('portal_grid_columnas', '4');
    const { container } = render(<PlatformAdmin />);
    await screen.findByText('Finanzas');
    expect(container.querySelectorAll('.border-dashed[aria-hidden="true"]')).toHaveLength(5);
  });

  it('el buscador de áreas filtra la cuadrícula', async () => {
    render(<PlatformAdmin />);
    await screen.findByText('Finanzas');
    const buscador = screen.getByLabelText('Buscar áreas');
    fireEvent.change(buscador, { target: { value: 'Inexistente' } });
    expect(screen.queryByText('Finanzas')).toBeNull();
    expect(screen.getByText(/No hay áreas que coincidan/)).toBeTruthy();
  });

  it('hacer click en una card de área abre la sección 2 con toolbar y tabla, y volver regresa a áreas', async () => {
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    expect(await screen.findByText('Contabilidad')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Volver a áreas' })).toBeTruthy();
    expect(screen.getByLabelText('Buscar plataformas en Finanzas')).toBeTruthy();

    // Volver a áreas
    fireEvent.click(screen.getByRole('button', { name: 'Volver a áreas' }));
    expect(await screen.findByText('Finanzas')).toBeTruthy();
    expect(screen.queryByText('Contabilidad')).toBeNull();
  });

  it('en la sección 2 no muestra badge redundante de área pero sí los botones de accesos, editar y eliminar con las reglas de selección', async () => {
    comoSuperadmin();
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    expect(await screen.findByText('Contabilidad')).toBeTruthy();

    // El badge redundante del área después del buscador fue removido
    expect(screen.queryByTitle('Área activa: Finanzas')).toBeNull();

    // Sin selección: botones de toolbar deshabilitados con nombres genéricos
    const btnAccesos = screen.getByRole('button', { name: 'Accesos' });
    const btnEditar = screen.getByRole('button', { name: 'Editar' });
    const btnEliminar = screen.getByRole('button', { name: 'Eliminar' });
    const btnNuevo = screen.getByRole('button', { name: 'Nuevo' });

    expect(btnAccesos.getAttribute('aria-disabled')).toBe('true');
    expect(btnEditar.getAttribute('aria-disabled')).toBe('true');
    expect(btnEliminar.getAttribute('aria-disabled')).toBe('true');
    expect((btnNuevo as HTMLButtonElement).disabled).toBe(false);

    // Al seleccionar 1 plataforma (Contabilidad) se habilitan con el contexto correspondiente
    fireEvent.click(screen.getByLabelText('Seleccionar Contabilidad'));

    const btnAccesosActivo = screen.getByRole('button', { name: 'Accesos de Contabilidad' });
    const btnEditarActivo = screen.getByRole('button', { name: 'Editar Contabilidad' });
    const btnEliminarActivo = screen.getByRole('button', { name: 'Eliminar Contabilidad' });

    expect((btnAccesosActivo as HTMLButtonElement).disabled).toBe(false);
    expect((btnEditarActivo as HTMLButtonElement).disabled).toBe(false);
    expect((btnEliminarActivo as HTMLButtonElement).disabled).toBe(false);

    // Abrir modal de Accesos de la plataforma
    fireEvent.click(btnAccesosActivo);
    const dialogAccesos = await screen.findByRole('dialog', { name: /Accesos — Contabilidad/i });
    expect(dialogAccesos).toBeTruthy();
    fireEvent.click(within(dialogAccesos).getAllByRole('button', { name: 'Cerrar' })[0]);

    // Abrir modal de Editar plataforma
    fireEvent.click(btnEditarActivo);
    const dialogEditar = await screen.findByRole('dialog', { name: 'Editar plataforma' });
    expect(dialogEditar).toBeTruthy();
    fireEvent.click(within(dialogEditar).getByText('Cancelar'));

    // Abrir diálogo de Eliminar plataforma
    fireEvent.click(btnEliminarActivo);
    const dialogEliminar = await screen.findByRole('alertdialog', { name: 'Eliminar plataforma' });
    expect(dialogEliminar).toBeTruthy();
    fireEvent.click(within(dialogEliminar).getByRole('button', { name: 'Cancelar' }));
  });

  it('indica con badge "Inactiva" y tratamiento visual cuando el área tiene status Inactivo', async () => {
    vi.mocked(api.areas).mockResolvedValueOnce([
      { id: 4, name: 'Operaciones', status: 'Inactivo' } as Area,
    ]);
    render(<PlatformAdmin />);
    expect(await screen.findByText('Operaciones')).toBeTruthy();
    expect(screen.getByText('Inactiva')).toBeTruthy();
    expect(screen.getByLabelText(/Área Operaciones \(Inactiva\)/)).toBeTruthy();
    expect(screen.getByLabelText(/Área Operaciones \(Inactiva\)/).closest('[data-state]')?.getAttribute('data-state')).toBe('inactiva');
  });

  it('el botón de diseño está a la izquierda del filtro de estado y abre el panel lateral de diseño de tarjetas de área', async () => {
    render(<PlatformAdmin />);
    await screen.findByText('Finanzas');

    const btnDiseno = screen.getByRole('button', { name: /diseño/i });
    const btnEstado = screen.getByRole('button', { name: /filtrar por estado/i });
    const btnGrid = screen.getByRole('button', { name: /configurar cuadrícula/i });

    // Simetría dimensional exacta: los 3 botones comparten w-48 min-w-48 y h-12 min-h-12
    expect(btnDiseno.className).toContain('w-48');
    expect(btnDiseno.className).toContain('min-w-48');
    expect(btnDiseno.className).toContain('h-12');
    expect(btnEstado.className).toContain('w-48');
    expect(btnGrid.className).toContain('w-48');

    // Verificar que el botón de diseño precede al botón de estado en el DOM (ubicado a su izquierda)
    expect(btnDiseno.compareDocumentPosition(btnEstado) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    // Abrir el drawer lateral de diseño
    fireEvent.click(btnDiseno);

    // Se despliega el panel lateral con las opciones de tarjetas de área
    const drawer = await screen.findByRole('dialog', { name: 'Diseño de Tarjetas de Área' });
    expect(drawer).toBeTruthy();
    // Ahora incluye la sección de vista previa en vivo estandarizada con CapsulePager
    expect(within(drawer).getByText('Vista Previa en Vivo')).toBeTruthy();
    expect(within(drawer).getByText('Tarjeta de Área')).toBeTruthy();
    expect(within(drawer).queryByRole('button', { name: 'Listo' })).toBeNull();

    // El botón de cierre en la cabecera y el botón Cerrar en el pie están presentes
    const botonesCerrar = within(drawer).getAllByRole('button', { name: 'Cerrar' });
    expect(botonesCerrar.length).toBeGreaterThanOrEqual(2);

    // En el footer debe existir el botón Reestablecer a la derecha
    const btnReestablecer = within(drawer).getByRole('button', { name: 'Reestablecer' });
    expect(btnReestablecer).toBeTruthy();

    // Interruptor de forzar diseño
    const toggleForzar = within(drawer).getByRole('switch', { name: /forzar diseño/i });
    expect(toggleForzar.getAttribute('aria-checked')).toBe('false');

    // Activar forzar diseño
    fireEvent.click(toggleForzar);
    expect(toggleForzar.getAttribute('aria-checked')).toBe('true');
    expect(window.localStorage.getItem('nexus.platforms.force_area_card_design')).toBe('true');

    // Navegar a la página 1 mediante CapsulePager para seleccionar Onda Curva SVG
    const btnAnterior = within(drawer).getByRole('button', { name: 'Página anterior' });
    fireEvent.click(btnAnterior);

    // Seleccionar otra variante (ej. Onda Curva SVG)
    const radioOnda = within(drawer).getByRole('radio', { name: /Onda Curva/i });
    fireEvent.click(radioOnda);
    expect(window.localStorage.getItem('nexus.platforms.area_card_design')).toBe('onda');

    // Pulsar Reestablecer: restaura diseño a 'estandar' y desactiva forzar diseño
    fireEvent.click(btnReestablecer);
    expect(window.localStorage.getItem('nexus.platforms.area_card_design')).toBe('estandar');
    expect(window.localStorage.getItem('nexus.platforms.force_area_card_design')).toBe('false');
    expect(toggleForzar.getAttribute('aria-checked')).toBe('false');

    // Cerrar el drawer pulsando el botón Cerrar del footer
    fireEvent.click(botonesCerrar[1]);
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Diseño de Tarjetas de Área' })).toBeNull());
  });

  it('en la sección 2 (plataformas) implementa el botón de diseño a la izquierda de accesos y abre el panel lateral con vista previa en vivo', async () => {
    comoSuperadmin();
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    expect(await screen.findByText('Contabilidad')).toBeTruthy();

    const btnDiseno = screen.getByRole('button', { name: 'Diseño' });
    const btnAccesos = screen.getByRole('button', { name: 'Accesos' });

    // Verificar que el botón de diseño está inmediatamente a la izquierda del botón de accesos en el DOM
    expect(btnDiseno.compareDocumentPosition(btnAccesos) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    // Abrir el drawer lateral de diseño de plataformas
    fireEvent.click(btnDiseno);

    // Se despliega el panel lateral con vista previa en vivo
    const drawer = await screen.findByRole('dialog', { name: 'Diseño de Tarjetas de Plataforma' });
    expect(drawer).toBeTruthy();
    expect(within(drawer).getByText('Vista Previa en Vivo')).toBeTruthy();
    expect(within(drawer).getByText('Tarjeta de Plataforma')).toBeTruthy();

    // Paginador de 4 diseños por página (cuadrícula 2x2 para eliminar scroll)
    expect(within(drawer).getByText('Pág. 2 de 3')).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Editorial/i })).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Estándar/i })).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Compacto/i })).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: 'Diseño Horizontal en fila' })).toBeTruthy();

    // Navegar a Página 1
    const btnPagAnt = within(drawer).getByRole('button', { name: 'Página anterior' });
    fireEvent.click(btnPagAnt);
    expect(within(drawer).getByText('Pág. 1 de 3')).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Duotono/i })).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Enmarcada/i })).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Split 50\/50/i })).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Glassmorphism/i })).toBeTruthy();

    // Navegar a Página 3 (muestra los últimos 2 diseños + 2 ghost cards para simetría 2x2)
    const btnPagSig = within(drawer).getByRole('button', { name: 'Página siguiente' });
    fireEvent.click(btnPagSig); // Página 2
    fireEvent.click(btnPagSig); // Página 3
    expect(within(drawer).getByText('Pág. 3 de 3')).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Hero Banner/i })).toBeTruthy();
    expect(within(drawer).getByRole('radio', { name: /Flotante Inmersiva/i })).toBeTruthy();
    const ghostCards = within(drawer).getAllByTestId('platform-design-ghost-card');
    expect(ghostCards).toHaveLength(2);

    // Toggle para forzar diseño de plataforma (compacto, sin texto de descripción)
    const toggleForzar = within(drawer).getByRole('switch', { name: /forzar diseño/i });
    expect(toggleForzar.getAttribute('aria-checked')).toBe('false');

    fireEvent.click(toggleForzar);
    expect(toggleForzar.getAttribute('aria-checked')).toBe('true');
    expect(window.localStorage.getItem('nexus.platforms.force_platform_card_design')).toBe('true');

    // Cambiar a diseño flotante en página 3
    const radioFlotante = within(drawer).getByRole('radio', { name: /Flotante Inmersiva/i });
    fireEvent.click(radioFlotante);
    expect(window.localStorage.getItem('nexus.platforms.card_design')).toBe('flotante');

    // Botones de footer simétricos: Cerrar y Reestablecer
    const btnReestablecer = within(drawer).getByRole('button', { name: 'Reestablecer' });
    const botonesCerrar = within(drawer).getAllByRole('button', { name: 'Cerrar' });

    // Pulsar Reestablecer restaura a estandar y desactiva forzado
    fireEvent.click(btnReestablecer);
    expect(window.localStorage.getItem('nexus.platforms.card_design')).toBe('estandar');
    expect(window.localStorage.getItem('nexus.platforms.force_platform_card_design')).toBe('false');
    expect(toggleForzar.getAttribute('aria-checked')).toBe('false');

    // Cerrar el drawer
    fireEvent.click(botonesCerrar[1]);
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Diseño de Tarjetas de Plataforma' })).toBeNull());
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
    fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'http://x.ejemplo.local' } });
    fireEvent.click(modal.getByText('Siguiente'));
    const nombre = await modal.findByLabelText(/^Nombre/);
    expect(descripcionDe(nombre)).toContain('El nombre debe tener entre 2 y 100 caracteres.');
    const enlace = modal.getByLabelText(/^Enlace/);
    expect(descripcionDe(enlace)).toContain('Usa una dirección https://.');
    expect(descripcionDe(enlace)).toContain('Dirección https://');
  });

  it('edición simplificada no expone controles de área ni integración bloqueados', async () => {
    comoSuperadmin();
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, integration_type: 'ldap', active_grants: 2 }]);
    render(<PlatformAdmin initialAreaId={3} />);
    fireEvent.click(await screen.findByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: /Editar Contabilidad/i }));
    const modal = dialogo();
    expect(modal.queryByLabelText(/^Tipo de integración/)).toBeNull();
    expect(modal.queryByRole('combobox', { name: /^Área/ })).toBeNull();
  });

  it('la región de estado está montada antes de guardar', async () => {
    render(<PlatformAdmin initialAreaId={3} />);
    await screen.findByText('Contabilidad');
    const region = screen.getByRole('status');
    expect(region.textContent).toBe('');
    fireEvent.click(screen.getByRole('button', { name: /nuevo/i }));
    const modal = dialogo();
    fireEvent.change(modal.getByLabelText(/^Nombre/), { target: { value: 'Nueva' } });
    fireEvent.change(modal.getByLabelText(/^Descripción/), { target: { value: 'D' } });
    fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'https://nueva.ejemplo.local' } });
    avanzarYGuardar(modal);
    await waitFor(() => expect(region.textContent).toContain('Se guardó'));
  });

  it('foco: al primer campo con error, al disparador al cancelar y aviso tras guardar', async () => {
    render(<PlatformAdmin initialAreaId={3} />);
    await screen.findByText('Contabilidad');
    const nueva = screen.getByRole('button', { name: /nuevo/i });
    nueva.focus();
    fireEvent.click(nueva);
    fireEvent.click(dialogo().getByText('Siguiente'));
    await waitFor(() => expect(document.activeElement).toBe(dialogo().getByLabelText(/^Nombre/)));
    fireEvent.click(dialogo().getByText('Cancelar'));
    await waitFor(() => expect(document.activeElement).toBe(nueva));

    const modal = await abrirAltaSinRender();
    avanzarYGuardar(modal);
    expect(await screen.findByText(/Se guardó/)).toBeTruthy();
  });

  it('Editar y Eliminar con el nombre de la plataforma al seleccionarla', async () => {
    render(<PlatformAdmin initialAreaId={3} />);
    await screen.findByText('Contabilidad');
    // Sin selección: botones deshabilitados con nombre genérico
    const btnEditar = screen.getByRole('button', { name: 'Editar' });
    const btnEliminar = screen.getByRole('button', { name: 'Eliminar' });
    expect(btnEditar.getAttribute('aria-disabled')).toBe('true');
    expect(btnEliminar.getAttribute('aria-disabled')).toBe('true');

    // Con 1 plataforma seleccionada: botones habilitados con el nombre de la plataforma
    fireEvent.click(screen.getByLabelText('Seleccionar Contabilidad'));
    const btnEditarPlat = screen.getByRole('button', { name: 'Editar Contabilidad' });
    const btnEliminarPlat = screen.getByRole('button', { name: 'Eliminar Contabilidad' });
    expect((btnEditarPlat as HTMLButtonElement).disabled).toBe(false);
    expect((btnEliminarPlat as HTMLButtonElement).disabled).toBe(false);
  });

  it('DIS-035: acciones en la barra de herramientas al seleccionar plataforma', async () => {
    render(<PlatformAdmin initialAreaId={3} />);
    await screen.findByText('Contabilidad');
    const checkbox = await screen.findByLabelText('Seleccionar Contabilidad');
    fireEvent.click(checkbox);
    const acciones = [
      screen.getByRole('button', { name: 'Editar Contabilidad' }),
      screen.getByRole('button', { name: 'Eliminar Contabilidad' }),
    ];
    for (const accion of acciones) {
      expect(accion.className).toContain('min-h-12');
      expect(accion.className).toContain('min-w-12');
      expect(accion.className).toContain('focus-visible:ring-primary');
    }
  });

  it('DIS-161: la tabla de plataformas del área muestra sus pendientes con enlace al Historial filtrado', async () => {
    vi.mocked(requestsApi.inboxStats).mockResolvedValue({
      total: 2, by_status: { pendiente: 2, aprobada: 0, rechazada: 0 },
      by_area: [{ area_id: 3, area: 'Finanzas', count: 2 }], by_platform: [],
      pending_by_area: [{ area_id: 3, area: 'Finanzas', count: 2 }],
      pending_by_platform: [{ platform_id: 12, platform: 'Contabilidad', area_id: 3, area: 'Finanzas', count: 2 }],
    });
    render(<PlatformAdmin initialAreaId={3} />);
    await screen.findByRole('region', { name: 'Plataformas de Finanzas' });
    expect(await screen.findByRole('columnheader', { name: 'Solicitudes pendientes' })).toBeTruthy();
    const enlace = screen.getByRole('link', { name: 'Solicitudes pendientes: 2, en Contabilidad. Abrir Historial.' });
    expect(enlace.getAttribute('href')).toBe('/approvals?status=pendiente&area_id=3&platform_id=12');
  });

  it('DIS-008: la tabla desplazable es una región con nombre, enfocable y con foco visible; la cabecera de selección tiene checkbox', async () => {
    render(<PlatformAdmin initialAreaId={3} />);
    const region = await screen.findByRole('region', { name: 'Plataformas de Finanzas' });
    expect(region.getAttribute('tabindex')).toBe('0');
    expect(region.className).toContain('overflow-x-auto');
    expect(region.className).toContain('focus-visible:ring-primary');
    expect(screen.getByRole('checkbox', { name: 'Seleccionar todas las plataformas' })).toBeTruthy();
  });

  it.each([
    [404, 'La plataforma ya no existe o no está en tu alcance. Recarga la lista.'],
    [409, 'No se puede eliminar una plataforma con accesos vigentes.'],
  ])('error %s al eliminar: mensaje fijo', async (status, mensaje) => {
    vi.mocked(api.deletePlatform).mockRejectedValue(new ApiError(status, 'detalle interno', { code: 'x' }));
    render(<PlatformAdmin initialAreaId={3} />);
    await screen.findByText('Contabilidad');
    fireEvent.click(screen.getByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar Contabilidad' }));
    fireEvent.click(within(screen.queryByRole('alertdialog') ?? screen.getByRole('dialog')).getByText('Eliminar'));
    expect(await screen.findByText(mensaje)).toBeTruthy();
  });

  it('permite eliminar múltiples plataformas seleccionadas en el área activa', async () => {
    const plat2 = {
      id: 15, name: 'Facturación', description: 'Módulo de facturas', area_id: 3, area_name: 'Finanzas',
      direct_link: 'https://facturas.ejemplo.local', bg_color: '', text_color: '', status: 'Activo',
    } as Platform;
    vi.mocked(api.platforms).mockResolvedValue([PLATAFORMA, plat2]);
    vi.mocked(api.deletePlatform).mockResolvedValue({ ok: true } as never);

    render(<PlatformAdmin initialAreaId={3} />);
    await screen.findByText('Contabilidad');
    await screen.findByText('Facturación');

    fireEvent.click(screen.getByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByLabelText('Seleccionar Facturación'));

    const btnEliminar = screen.getByRole('button', { name: 'Eliminar 2 plataformas seleccionadas' });
    expect((btnEliminar as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(btnEliminar);
    const dialog = await screen.findByRole('alertdialog', { name: 'Eliminar plataformas' });
    expect(dialog).toBeTruthy();
    expect(within(dialog).getByText(/Se eliminarán las 2 plataformas seleccionadas/)).toBeTruthy();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Eliminar' }));
    await waitFor(() => {
      expect(api.deletePlatform).toHaveBeenCalledWith(12);
      expect(api.deletePlatform).toHaveBeenCalledWith(15);
    });
  });
});

async function abrirAltaSinRender() {
  fireEvent.click(screen.getByRole('button', { name: /nuevo/i }));
  const modal = within(screen.queryByRole('alertdialog') ?? screen.getByRole('dialog'));
  fireEvent.change(modal.getByLabelText(/^Nombre/), { target: { value: 'Nueva' } });
  fireEvent.change(modal.getByLabelText(/^Descripción/), { target: { value: 'Descripción' } });
  fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: 'https://nueva.ejemplo.local' } });
  return modal;
}

describe('PlatformAdmin: estado con badge (DIS-114)', () => {
  async function abrirArea() {
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    await screen.findByText('Contabilidad');
  }

  it('tarjeta de área: el badge activa confirma, guarda Inactivo, recarga y no abre el área', async () => {
    comoSuperadmin();
    vi.mocked(api.areas).mockResolvedValue([{ ...AREAS[0], status: 'Activo' } as Area]);
    vi.mocked(api.updateArea).mockResolvedValue({ status: 'success', area: { ...AREAS[0], status: 'Inactivo' } as Area });
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByRole('button', { name: 'Activa, desactivar área Finanzas' }));
    expect(screen.queryByText('Contabilidad')).toBeNull();
    expect(api.updateArea).not.toHaveBeenCalled();
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Desactivar' }));
    await waitFor(() => expect(api.updateArea).toHaveBeenCalledWith(3, { status: 'Inactivo' }));
    await waitFor(() => expect(api.areas).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole('button', { name: 'Editar Contabilidad' })).toBeNull();
  });

  it('tarjeta de área inactiva: el badge activa directo con PUT Activo', async () => {
    comoSuperadmin();
    vi.mocked(api.areas).mockResolvedValue([{ ...AREAS[0], status: 'Inactivo' } as Area]);
    vi.mocked(api.updateArea).mockResolvedValue({ status: 'success', area: AREAS[0] });
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByRole('button', { name: 'Inactiva, activar área Finanzas' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    await waitFor(() => expect(api.updateArea).toHaveBeenCalledWith(3, { status: 'Activo' }));
  });

  it('admin de área sin esa área a su cargo: el badge de la tarjeta no es botón', async () => {
    vi.mocked(api.areas).mockResolvedValue([{ ...AREAS[0], status: 'Activo' } as Area]);
    render(<PlatformAdmin />);
    await screen.findByText('Finanzas');
    expect(screen.queryByRole('button', { name: /(Activar|Desactivar) área/ })).toBeNull();
  });

  it('tabla de plataformas: el badge activa confirma y guarda solo {status: Inactivo}; no selecciona la fila', async () => {
    await abrirArea();
    fireEvent.click(screen.getByRole('button', { name: 'Activa, desactivar plataforma Contabilidad' }));
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Desactivar' }));
    await waitFor(() => expect(api.updatePlatform).toHaveBeenCalledWith(12, { status: 'Inactivo' }));
    await waitFor(() => expect(api.platforms).toHaveBeenCalledTimes(2));
    expect((screen.getByLabelText('Seleccionar Contabilidad') as HTMLInputElement).checked).toBe(false);
  });

  it('tabla de plataformas inactiva: el badge activa directo', async () => {
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, status: 'Inactivo' } as Platform]);
    await abrirArea();
    fireEvent.click(screen.getByRole('button', { name: 'Inactiva, activar plataforma Contabilidad' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    await waitFor(() => expect(api.updatePlatform).toHaveBeenCalledWith(12, { status: 'Activo' }));
  });

  it('error 409 al desactivar una plataforma: toast con el mensaje y la fila sigue Activa', async () => {
    vi.mocked(api.updatePlatform).mockRejectedValue(
      new ApiError(409, 'Los grupos están en inactivos.', { code: 'grupos_en_inactivos' }),
    );
    await abrirArea();
    fireEvent.click(screen.getByRole('button', { name: 'Activa, desactivar plataforma Contabilidad' }));
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Desactivar' }));
    expect(await screen.findByText('Los grupos están en inactivos.')).toBeTruthy();
    expect(api.platforms).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Activa, desactivar plataforma Contabilidad' })).toBeTruthy();
  });

  it('formulario de plataforma: sin control de estado; el alta no envía status', async () => {
    const modal = await abrirAlta();
    fireEvent.click(modal.getByText('Siguiente'));
    expect(modal.queryByRole('switch')).toBeNull();
    expect(modal.queryByLabelText(/^Activa/)).toBeNull();
    avanzarYGuardar(modal);
    await waitFor(() => expect(api.createPlatform).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.createPlatform).mock.calls[0][0]).not.toHaveProperty('status');
  });

  it('formulario de plataforma: la edición no envía status (no pisa el estado)', async () => {
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    fireEvent.click(await screen.findByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: /Editar Contabilidad/i }));
    avanzarYGuardar(dialogo());
    await waitFor(() => expect(api.updatePlatform).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.updatePlatform).mock.calls[0][1]).not.toHaveProperty('status');
  });
});

describe('PlatformAdmin: interruptor «Omitir enlace» (DIS-133)', () => {
  it('sin el interruptor el enlace es obligatorio', async () => {
    const modal = await abrirAlta();
    fireEvent.change(modal.getByLabelText(/^Enlace/), { target: { value: '' } });
    fireEvent.click(modal.getByText('Siguiente'));
    expect(await modal.findByText('Escribe el enlace o activa «Omitir enlace».')).toBeTruthy();
    expect(modal.queryByLabelText('Color de fondo')).toBeNull();
  });

  it('con el interruptor se oculta el campo y se guarda sin enlace', async () => {
    const modal = await abrirAlta();
    const interruptor = modal.getByRole('switch', { name: 'Omitir enlace' });
    expect(interruptor.getAttribute('aria-checked')).toBe('false');
    fireEvent.click(interruptor);
    expect(interruptor.getAttribute('aria-checked')).toBe('true');
    expect(modal.queryByLabelText(/^Enlace/)).toBeNull();
    avanzarYGuardar(modal);
    await waitFor(() => expect(api.createPlatform).toHaveBeenCalled());
    const enviado = vi.mocked(api.createPlatform).mock.calls[0][0];
    expect(enviado.direct_link ?? '').toBe('');
  });

  it('al editar una plataforma sin enlace el interruptor nace encendido', async () => {
    vi.mocked(api.platforms).mockResolvedValue([{ ...PLATAFORMA, direct_link: '' }]);
    render(<PlatformAdmin />);
    fireEvent.click(await screen.findByText('Finanzas'));
    fireEvent.click(await screen.findByLabelText('Seleccionar Contabilidad'));
    fireEvent.click(screen.getByRole('button', { name: /Editar Contabilidad/i }));
    const modal = dialogo();
    expect(modal.getByRole('switch', { name: 'Omitir enlace' }).getAttribute('aria-checked')).toBe('true');
  });
});
