/**
 * DIS-025: menú de navegación en móvil (botón y panel de `AppShell`).
 * DIS-031: trampa de foco compartida con `Modal` (`useFocusTrap`).
 * DIS-038: velo por token y bloqueo del desplazamiento con clase en `<html>`.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Session } from '@/lib/types';

const ruta = vi.hoisted(() => ({ actual: '/' }));
vi.mock('next/navigation', () => ({ usePathname: () => ruta.actual }));
vi.mock('@/lib/api', () => ({
  api: { session: vi.fn() },
  ApiError: class ApiError extends Error {},
}));

import { api } from '@/lib/api';
import { AppShell } from '@/components/app-shell';
import { CLASE_SCROLL_BLOQUEADO } from '@/lib/use-scroll-lock';
import { crearRaiz, simularCajas } from '../utils/dom-simulado';

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

let raiz: HTMLElement;

beforeEach(() => {
  simularCajas();
  raiz = crearRaiz();
});

async function montar(rol: Rol = 'usuario') {
  sesionSimulada.mockResolvedValue(sesion(rol));
  // Como en el navegador: la pantalla dentro de la raíz de `layout.tsx`.
  render(<AppShell>contenido</AppShell>, { container: raiz });
  const boton = await screen.findByRole('button', { name: 'Menú' });
  // El panel va en un portal que se crea al montar en el cliente.
  await waitFor(() => expect(document.getElementById(boton.getAttribute('aria-controls')!)).not.toBeNull());
  return boton;
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

  // DIS-008: la barra lateral también se usa con el dedo (tabletas desde `md`): 48 px en ambas.
  it('los enlaces del menú móvil y de la barra lateral tienen área táctil de 48 px', async () => {
    const panel = abrir(await montar());
    for (const enlace of within(panel).getAllByRole('link')) {
      expect(enlace.className).toContain('min-h-12');
    }
    for (const enlace of within(document.querySelector('aside')!).getAllByRole('link')) {
      expect(enlace.className).toContain('min-h-12');
    }
    expect(screen.getByRole('button', { name: 'Menú' }).className).toContain('min-h-12');
    expect(within(panel).getByRole('button', { name: 'Cerrar' }).className).toContain('min-h-12');
  });

  it('se cierra si la ventana cruza md con el menú abierto', async () => {
    const oyentes: ((e: { matches: boolean }) => void)[] = [];
    vi.stubGlobal('matchMedia', (consulta: string) => ({
      matches: false,
      media: consulta,
      addEventListener: (_: string, fn: (e: { matches: boolean }) => void) => oyentes.push(fn),
      removeEventListener: (_: string, fn: (e: { matches: boolean }) => void) => {
        oyentes.splice(oyentes.indexOf(fn), 1);
      },
    }));
    const boton = await montar();
    abrir(boton);
    expect(oyentes).toHaveLength(1);
    act(() => oyentes[0]({ matches: true }));
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(boton);
    expect(oyentes).toHaveLength(0);
  });

  it('botones y enlaces del menú móvil y de la barra lateral tienen foco visible', async () => {
    const panel = abrir(await montar());
    const controles = [
      screen.getByRole('button', { name: 'Menú' }),
      within(panel).getByRole('button', { name: 'Cerrar' }),
      ...within(panel).getAllByRole('link'),
    ];
    for (const control of controles) {
      expect(control.className).toContain('focus-visible:ring-2');
      expect(control.className).toContain('focus-visible:ring-primary');
    }
    for (const enlace of within(document.querySelector('aside')!).getAllByRole('link')) {
      expect(enlace.className).toContain('focus-visible:ring-2');
      expect(enlace.className).toContain('focus-visible:ring-primary');
    }
    expect(panel.className).toContain('border-primary');
  });

  it('con el panel abierto hay velo por token, la raíz queda bloqueada e inert (clase, sin estilos inline)', async () => {
    const boton = await montar();
    expect(raiz.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(false);
    const panel = abrir(boton);
    expect(raiz.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(true);
    expect(raiz.hasAttribute('inert')).toBe(true);
    // El panel va en un portal fuera de la raíz: no queda `inert`.
    expect(raiz.contains(panel)).toBe(false);
    expect(raiz.getAttribute('style')).toBeNull();
    expect(document.body.getAttribute('style')).toBeNull();
    const velo = panel.parentElement!.querySelector('[aria-hidden="true"]')!;
    expect(velo.className).toContain('bg-overlay');

    // El clic en el velo cuenta como clic fuera: cierra, libera la raíz y el foco vuelve al botón.
    fireEvent.pointerDown(velo);
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    expect(raiz.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(false);
    expect(raiz.hasAttribute('inert')).toBe(false);
    expect(document.activeElement).toBe(boton);
  });

  it('el área de contenido es el contenedor desplazable y el foco alterno', async () => {
    await montar();
    const main = screen.getByRole('main');
    expect(main.hasAttribute('data-desplazable')).toBe(true);
    expect(main.className).toContain('overflow-y-auto');
    expect(main.className).toContain('min-h-0');
    expect(main.getAttribute('tabindex')).toBe('-1');
    // El marco ocupa la ventana: la cabecera y la barra lateral no se desplazan con el contenido.
    expect(main.closest('.h-dvh')).not.toBeNull();
  });
});
