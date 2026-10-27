/**
 * `useTokenColors` (DIS-003): hex y funciones de color tal cual, "r g b" y
 * "r g b / a" dentro de `rgb()`, y relectura al cambiar la clase de `<html>`.
 */
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { aColor, useTokenColors } from '@/lib/use-token-colors';

const TOKENS = { hex: '--t-hex', rgb: '--t-rgb', alfa: '--t-alfa' };

afterEach(() => {
  cleanup();
  document.documentElement.className = '';
  document.documentElement.removeAttribute('style');
});

describe('aColor', () => {
  it('respeta hex y funciones, envuelve los tripletes y no inventa vacíos', () => {
    expect(aColor(' #0f172a ')).toBe('#0f172a');
    expect(aColor('rgb(1 2 3)')).toBe('rgb(1 2 3)');
    expect(aColor('37 99 235')).toBe('rgb(37 99 235)');
    expect(aColor('37 99 235 / 0.5')).toBe('rgb(37 99 235 / 0.5)');
    expect(aColor('')).toBe('currentColor');
  });
});

describe('useTokenColors', () => {
  it('lee un token hex, uno "r g b" y uno "r g b / a"', () => {
    const raiz = document.documentElement;
    raiz.style.setProperty('--t-hex', '#0f172a');
    raiz.style.setProperty('--t-rgb', '37 99 235');
    raiz.style.setProperty('--t-alfa', '37 99 235 / 0.5');
    const { result } = renderHook(() => useTokenColors(TOKENS));
    expect(result.current).toEqual({
      hex: '#0f172a', rgb: 'rgb(37 99 235)', alfa: 'rgb(37 99 235 / 0.5)',
    });
  });

  it('vuelve a leer al cambiar la clase de <html>', async () => {
    const raiz = document.documentElement;
    raiz.style.setProperty('--t-rgb', '1 2 3');
    const { result } = renderHook(() => useTokenColors(TOKENS));
    expect(result.current.rgb).toBe('rgb(1 2 3)');
    act(() => {
      raiz.style.setProperty('--t-rgb', '9 9 9');
      raiz.className = 'dark';
    });
    await waitFor(() => expect(result.current.rgb).toBe('rgb(9 9 9)'));
  });
});
