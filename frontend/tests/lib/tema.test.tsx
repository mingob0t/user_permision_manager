/** FNC-032: el tema se aplica como clase de `<html>`, se guarda y se restaura. */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ThemeSelector } from '@/components/theme-selector';
import {
  CLAVE_TEMA, SCRIPT_RESTAURAR_TEMA, TEMAS, aplicarTema, elegirTema, leerTema, restaurarTema,
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
    aplicarTema('rosa');
    expect(raiz().classList.contains('scroll-bloqueado')).toBe(true);
    expect(raiz().classList.contains('dark')).toBe(false);
    expect(raiz().classList.contains('theme-rose-light')).toBe(true);
  });

  it('persiste la elección y la restaura', () => {
    elegirTema('violeta');
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('violeta');
    raiz().className = '';
    expect(restaurarTema()).toBe('violeta');
    expect(raiz().classList.contains('theme-violet-dark')).toBe(true);
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
    window.localStorage.setItem(CLAVE_TEMA, 'obsidiana');
    new Function(SCRIPT_RESTAURAR_TEMA)();
    expect(raiz().classList.contains('theme-obsidian-dark')).toBe(true);
  });

  it('el script no falla con un valor desconocido', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'otro');
    expect(() => new Function(SCRIPT_RESTAURAR_TEMA)()).not.toThrow();
    expect(raiz().className).toBe('');
  });
});

describe('ThemeSelector', () => {
  it('lista los 7 temas, aplica y guarda al elegir', () => {
    render(<ThemeSelector />);
    const combo = screen.getByRole('combobox', { name: 'Tema de la interfaz' });
    expect(combo.querySelectorAll('option')).toHaveLength(7);
    fireEvent.change(combo, { target: { value: 'esmeralda' } });
    expect(raiz().classList.contains('theme-emerald-light')).toBe(true);
    expect(window.localStorage.getItem(CLAVE_TEMA)).toBe('esmeralda');
  });

  it('al montar muestra y aplica el tema guardado', () => {
    window.localStorage.setItem(CLAVE_TEMA, 'oscuro');
    render(<ThemeSelector />);
    expect(screen.getByRole('combobox')).toHaveProperty('value', 'oscuro');
    expect(raiz().classList.contains('dark')).toBe(true);
  });
});
