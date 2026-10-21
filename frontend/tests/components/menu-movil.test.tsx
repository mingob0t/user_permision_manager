/**
 * DIS-025: menú de navegación en móvil (botón y panel de `AppShell`).
 */
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Session } from '@/lib/types';

const ruta = vi.hoisted(() => ({ actual: '/' }));
vi.mock('next/navigation', () => ({ usePathname: () => ruta.actual }));
vi.mock('@/lib/api', () => ({
  api: { session: vi.fn() },
  ApiError: class ApiError extends Error {},
}));

import { api } from '@/lib/api';
import { AppShell } from '@/components/app-shell';

const sesionSimulada = vi.mocked(api.session);

type Rol = 'usuario' | 'admin_area' | 'administrador';

function sesion(rol: Rol): Session {
  return {
    id: 1,
    email: 'ana@ejemplo.test',
    name: 'Ana',
    role: rol,
    auth_source: 'local',
    areas: [],
    managed_areas: [],
    permissions: {
      is_admin: rol === 'administrador',
      is_area_admin: rol === 'admin_area',
      can_manage_areas: rol !== 'usuario',
      can_manage_system: rol === 'administrador',
    },
    preferences: {
      notifications: true, email_notifications: false, refresh_interval: 60, tour_enabled: false,
    },
  };
}

async function montar(rol: Rol = 'usuario') {
  sesionSimulada.mockResolvedValue(sesion(rol));
  render(<AppShell>contenido</AppShell>);
  return screen.findByRole('button', { name: 'Menú' });
}

function abrir(boton: HTMLElement) {
  fireEvent.click(boton);
  return screen.getByRole('dialog', { name: 'Menú' });
}

afterEach(() => {
  cleanup();
  sesionSimulada.mockReset();
  ruta.actual = '/';
});

describe('Menú móvil', () => {
  it('el botón controla el panel y empieza cerrado', async () => {
    const boton = await montar();
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    const panelId = boton.getAttribute('aria-controls');
    expect(panelId).toBeTruthy();
    expect(document.getElementById(panelId!)?.hidden).toBe(true);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('abre con el foco en el primer enlace y aria-expanded en true', async () => {
    const boton = await montar();
    const panel = abrir(boton);
    expect(boton.getAttribute('aria-expanded')).toBe('true');
    expect(document.getElementById(boton.getAttribute('aria-controls')!)?.hidden).toBe(false);
    const enlaces = within(panel).getAllByRole('link');
    expect(document.activeElement).toBe(enlaces[0]);
  });

  it('Escape cierra y devuelve el foco al botón', async () => {
    const boton = await montar();
    abrir(boton);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(boton);
  });

  it('elegir una opción cierra el menú', async () => {
    const boton = await montar();
    const panel = abrir(boton);
    fireEvent.click(within(panel).getByRole('link', { name: 'Catálogo' }));
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(boton);
  });

  it('el clic fuera cierra; el clic dentro no', async () => {
    const boton = await montar();
    const panel = abrir(boton);
    fireEvent.pointerDown(within(panel).getByRole('link', { name: 'Panel' }));
    expect(boton.getAttribute('aria-expanded')).toBe('true');
    fireEvent.pointerDown(screen.getByText('contenido'));
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(boton);
  });

  it('el botón Cerrar y un segundo clic en Menú cierran', async () => {
    const boton = await montar();
    const panel = abrir(boton);
    fireEvent.click(within(panel).getByRole('button', { name: 'Cerrar' }));
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    abrir(boton);
    fireEvent.click(boton);
    expect(boton.getAttribute('aria-expanded')).toBe('false');
  });

  it('Tab y Mayús+Tab no sacan el foco del panel', async () => {
    const boton = await montar();
    const panel = abrir(boton);
    const enfocables = [
      within(panel).getByRole('button', { name: 'Cerrar' }),
      ...within(panel).getAllByRole('link'),
    ];
    const primero = enfocables[0];
    const ultimo = enfocables[enfocables.length - 1];

    ultimo.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(primero);

    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(ultimo);

    // Si el foco quedó fuera (p. ej. en el cuerpo), Tab lo regresa al panel.
    (document.activeElement as HTMLElement).blur();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(primero);
  });

  it.each<[Rol, number]>([
    ['usuario', 7],
    ['admin_area', 12],
    ['administrador', 12],
  ])('%s ve en el menú móvil las mismas entradas que en la barra lateral (%i)', async (rol, n) => {
    const boton = await montar(rol);
    const panel = abrir(boton);
    const movil = within(panel).getAllByRole('link').map((a) => a.textContent);
    const lateral = within(document.querySelector('aside')!)
      .getAllByRole('link')
      .map((a) => a.textContent);
    expect(movil).toEqual(lateral);
    expect(movil).toHaveLength(n);
  });

  it('el usuario no ve entradas de administración en el menú móvil', async () => {
    const panel = abrir(await montar('usuario'));
    expect(within(panel).queryByRole('link', { name: 'Aprobaciones' })).toBeNull();
    expect(within(panel).queryByRole('link', { name: 'Conectores' })).toBeNull();
  });

  it('marca la página actual con aria-current="page"', async () => {
    ruta.actual = '/favorites';
    const panel = abrir(await montar());
    const actuales = within(panel)
      .getAllByRole('link')
      .filter((a) => a.getAttribute('aria-current') === 'page');
    expect(actuales.map((a) => a.textContent)).toEqual(['Favoritos']);
  });

  it('los enlaces del menú móvil tienen área táctil de 48 px; los de la barra lateral no cambian', async () => {
    const panel = abrir(await montar());
    for (const enlace of within(panel).getAllByRole('link')) {
      expect(enlace.className).toContain('min-h-12');
    }
    for (const enlace of within(document.querySelector('aside')!).getAllByRole('link')) {
      expect(enlace.className).not.toContain('min-h-12');
    }
    expect(screen.getByRole('button', { name: 'Menú' }).className).toContain('min-h-12');
    expect(within(panel).getByRole('button', { name: 'Cerrar' }).className).toContain('min-h-12');
  });
});
