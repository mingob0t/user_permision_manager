/**
 * DIS-024 (auditor-accesibilidad): el hover de `.nexus-btn-primary` no cambia
 * los colores. Con `filter: brightness(1.1)` el texto `--color-on-primary`
 * sobre `--color-primary-solid` bajaba a 3,97:1 en el tema rose. Sin filtro,
 * el hover usa los mismos tokens que el par `nexus-btn-primary` de
 * `pares-contraste.ts`, que ya se mide en los 7 contextos.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RUTA_COMPONENTES = resolve(import.meta.dirname, '../../src/styles/components.css');

function bloque(css: string, selector: string): string {
  const inicio = css.indexOf(`${selector} {`);
  expect(inicio, `no existe ${selector}`).toBeGreaterThanOrEqual(0);
  return css.slice(inicio, css.indexOf('}', inicio));
}

describe('hover de botones', () => {
  const css = readFileSync(RUTA_COMPONENTES, 'utf8');

  it('.nexus-btn-primary:hover no usa filter ni cambia color o fondo', () => {
    const hover = bloque(css, '.nexus-btn-primary:hover:not([aria-disabled="true"])');
    expect(hover).not.toMatch(/\bfilter\s*:/);
    expect(hover).not.toMatch(/\b(color|background)\s*:/);
  });

  it('.nexus-btn-danger:hover no usa filter ni cambia color o fondo (DIS-010)', () => {
    const hover = bloque(css, '.nexus-btn-danger:hover:not([aria-disabled="true"])');
    expect(hover).not.toMatch(/\bfilter\s*:/);
    expect(hover).not.toMatch(/\b(color|background)\s*:/);
  });

  it('hover y pulsación no se aplican a botones con aria-disabled (DIS-031, H6)', () => {
    for (const selector of ['.nexus-btn:active', '.nexus-btn-primary:hover', '.nexus-btn-secondary:hover', '.nexus-btn-danger:hover']) {
      expect(css, selector).toContain(`${selector}:not([aria-disabled="true"]) {`);
      expect(css, selector).not.toContain(`${selector} {`);
    }
  });
});
