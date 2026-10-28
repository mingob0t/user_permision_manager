/** FNC-123: el selector de tema lee y guarda el tema en la cuenta (`preferences.theme`). */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const estado = vi.hoisted(() => ({ session: null as unknown }));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({ session: estado.session, loading: false, error: null }),
}));
vi.mock('@/lib/api', () => ({ api: { savePreferences: vi.fn() } }));

import { api } from '@/lib/api';
import { ThemeSelector } from '@/components/theme-selector';
import { ToastProvider } from '@/components/toast';
import { CLAVE_TEMA, aplicarTemaDeCuenta } from '@/lib/tema';

const guardar = vi.mocked(api.savePreferences);
const raiz = () => document.documentElement;
const conTema = (theme: unknown) => ({ preferences: { theme } });
const montar = () => render(<ToastProvider><ThemeSelector /></ToastProvider>);

beforeEach(() => {
  window.localStorage.clear();
  raiz().className = '';
  estado.session = null;
  guardar.mockReset();
  guardar.mockResolvedValue({ status: 'ok', preferences: {} as never });
});
afterEach(cleanup);

describe('ThemeSelector con la cuenta', () => {
  it('al elegir aplica, guarda en localStorage y envía el tema a la API', async () => {
    montar();
    fireEvent.change(screen.getByRole('combobox', { name: 'Tema de la interfaz' }), { target: { value: 'claro' } });
    expect(raiz().classList.contains('light')).toBe(true);
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('claro');
    await waitFor(() => expect(guardar).toHaveBeenCalledWith({ theme: 'claro' }));
  });

  it('si el guardado falla avisa y no revierte la vista', async () => {
    guardar.mockRejectedValue(new Error('500'));
    montar();
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'oscuro' } });
    await waitFor(() => expect(screen.getByRole('alert').textContent)
      .toContain('No se pudo guardar el tema en tu cuenta'));
    expect(screen.getByRole('combobox')).toHaveProperty('value', 'oscuro');
    expect(raiz().classList.contains('dark')).toBe(true);
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('oscuro');
  });

  it('el tema de la cuenta manda sobre el del navegador al cargar', async () => {
    window.localStorage.setItem(CLAVE_TEMA, 'claro');
    estado.session = conTema('oscuro');
    montar();
    await waitFor(() => expect(screen.getByRole('combobox')).toHaveProperty('value', 'oscuro'));
    expect(raiz().classList.contains('dark')).toBe(true);
    expect(raiz().classList.contains('light')).toBe(false);
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('oscuro');
    expect(guardar).not.toHaveBeenCalled();
  });

  it('un tema retirado de la cuenta (antes de migrar) se traduce a su equivalente', async () => {
    estado.session = conTema('obsidiana');
    montar();
    await waitFor(() => expect(screen.getByRole('combobox')).toHaveProperty('value', 'oscuro'));
    expect(raiz().className).toBe('dark');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('oscuro');
  });

  it('un valor inválido de la API cae a «sistema» sin usarse como clase', async () => {
    window.localStorage.setItem(CLAVE_TEMA, 'oscuro');
    estado.session = conTema('"><img src=x onerror=alert(1)>');
    montar();
    await waitFor(() => expect(screen.getByRole('combobox')).toHaveProperty('value', 'sistema'));
    expect(raiz().className).toBe('');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('sistema');
  });

  it('sin tema en la cuenta conserva el del navegador', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'oscuro');
    estado.session = conTema(undefined);
    montar();
    expect(screen.getByRole('combobox')).toHaveProperty('value', 'oscuro');
    expect(raiz().classList.contains('dark')).toBe(true);
  });
});

describe('aplicarTemaDeCuenta', () => {
  it('esmeralda y rosa pasan a claro; obsidiana y violeta, a oscuro', () => {
    for (const [v, id, clase] of [['esmeralda', 'claro', 'light'], ['rosa', 'claro', 'light'],
      ['obsidiana', 'oscuro', 'dark'], ['violeta', 'oscuro', 'dark']]) {
      raiz().className = '';
      expect(aplicarTemaDeCuenta(v), v).toBe(id);
      expect(raiz().className, v).toBe(clase);
    }
  });

  it('valores no válidos o de otro tipo caen a «sistema»', () => {
    for (const v of ['', 'light', 'theme-rose-light', 5, {}, ['dark']]) {
      raiz().className = 'dark';
      expect(aplicarTemaDeCuenta(v)).toBe('sistema');
      expect(raiz().className).toBe('');
    }
  });

  it('ausente no aplica nada', () => {
    act(() => { raiz().classList.add('dark'); });
    expect(aplicarTemaDeCuenta(undefined)).toBeNull();
    expect(aplicarTemaDeCuenta(null)).toBeNull();
    expect(raiz().classList.contains('dark')).toBe(true);
  });
});
