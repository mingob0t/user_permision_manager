/** FNC-032: el tema se aplica como clase de `<html>`, se guarda y se restaura. */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ThemeSelector } from '@/components/theme-selector';
import {
  CLAVE_TEMA, SCRIPT_RESTAURAR_TEMA, TEMAS, TEMAS_RETIRADOS, aplicarTema, elegirTema, leerTema,
  normalizarTema, restaurarTema,
} from '@/lib/tema';

const raiz = () => document.documentElement;

beforeEach(() => { window.localStorage.clear(); raiz().className = ''; });
afterEach(cleanup);

describe('tema', () => {
  it('aplica la clase de cada tema y deja solo una', () => {
    for (const t of TEMAS) {
      aplicarTema(t.id);
      expect(raiz().className).toBe(t.clase ?? '');
    }
  });

  it('conserva clases ajenas a los temas', () => {
    raiz().classList.add('scroll-bloqueado');
    aplicarTema('oscuro');
    aplicarTema('claro');
    expect(raiz().classList.contains('scroll-bloqueado')).toBe(true);
    expect(raiz().classList.contains('dark')).toBe(false);
    expect(raiz().classList.contains('light')).toBe(true);
  });

  it('persiste la elección y la restaura', () => {
    elegirTema('oscuro');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('oscuro');
    raiz().className = '';
    expect(restaurarTema()).toBe('oscuro');
    expect(raiz().classList.contains('dark')).toBe(true);
  });

  it('un valor guardado inválido cae al tema del sistema', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'inexistente');
    expect(leerTema()).toBe('sistema');
    expect(restaurarTema()).toBe('sistema');
    expect(raiz().className).toBe('');
  });

  it('ignora un id inválido al elegir', () => {
    elegirTema('x');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBeNull();
  });

  it('el script de <head> restaura la clase antes de hidratar', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'oscuro');
    new Function(SCRIPT_RESTAURAR_TEMA)();
    expect(raiz().classList.contains('dark')).toBe(true);
  });

  it('el script traduce los temas retirados sin destello (DIS-054)', () => {
    for (const [viejo, clase] of [['esmeralda', 'light'], ['rosa', 'light'], ['obsidiana', 'dark'], ['violeta', 'dark']]) {
      raiz().className = '';
      window.localStorage.setItem(CLAVE_TEMA, viejo);
      new Function(SCRIPT_RESTAURAR_TEMA)();
      expect(raiz().className, viejo).toBe(clase);
    }
  });

  it('el script no falla con un valor desconocido', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'otro');
    expect(() => new Function(SCRIPT_RESTAURAR_TEMA)()).not.toThrow();
    expect(raiz().className).toBe('');
  });
});

describe('temas retirados (DIS-054)', () => {
  it('traducen: esmeralda y rosa a claro; obsidiana y violeta a oscuro', () => {
    expect(TEMAS_RETIRADOS).toEqual({
      esmeralda: 'claro', rosa: 'claro', obsidiana: 'oscuro', violeta: 'oscuro',
    });
    for (const [viejo, nuevo] of Object.entries(TEMAS_RETIRADOS)) {
      expect(normalizarTema(viejo), viejo).toBe(nuevo);
    }
  });

  it('los vigentes se conservan y todo lo demás cae a «sistema»', () => {
    for (const id of ['sistema', 'claro', 'oscuro']) expect(normalizarTema(id)).toBe(id);
    for (const v of ['', 'light', 'constructor', '__proto__', 'theme-rose-light', 5, null, undefined, {}]) {
      expect(normalizarTema(v), String(v)).toBe('sistema');
    }
  });

  it('leerTema traduce un valor retirado de localStorage', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'esmeralda');
    expect(leerTema()).toBe('claro');
    expect(restaurarTema()).toBe('claro');
    expect(raiz().className).toBe('light');
  });
});

describe('ThemeSelector', () => {
  it('lista los 3 temas, aplica y guarda al elegir', () => {
    render(<ThemeSelector />);
    const combo = screen.getByRole('combobox', { name: 'Tema de la interfaz' });
    expect(combo.querySelectorAll('option')).toHaveLength(3);
    expect([...combo.querySelectorAll('option')].map((o) => o.textContent))
      .toEqual(['Según el sistema', 'Claro', 'Oscuro']);
    fireEvent.change(combo, { target: { value: 'claro' } });
    expect(raiz().className).toBe('light');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('claro');
    fireEvent.change(combo, { target: { value: 'oscuro' } });
    expect(raiz().className).toBe('dark');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('oscuro');
    fireEvent.change(combo, { target: { value: 'sistema' } });
    expect(raiz().className).toBe('');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('sistema');
  });

  it('un tema retirado guardado se muestra y aplica como su equivalente', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'violeta');
    render(<ThemeSelector />);
    expect(screen.getByRole('combobox')).toHaveProperty('value', 'oscuro');
    expect(raiz().classList.contains('dark')).toBe(true);
  });

  it('al montar muestra y aplica el tema guardado', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'oscuro');
    render(<ThemeSelector />);
    expect(screen.getByRole('combobox')).toHaveProperty('value', 'oscuro');
    expect(raiz().classList.contains('dark')).toBe(true);
  });
});
