// @vitest-environment node
/**
 * DIS-054 (ADR-007): el oscuro de «Según el sistema» (`@media (prefers-color-scheme: dark)`)
 * debe ser idéntico a `html.dark`. Si un token difiere, hay dos oscuros distintos.
 */
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { CONTEXTOS, RUTA_TOKENS, variablesDeBloque } from '../utils/tokens-css';

const css = readFileSync(RUTA_TOKENS, 'utf8');

describe('oscuro del sistema = html.dark', () => {
  const soOscuro = variablesDeBloque(css, CONTEXTOS['so-oscuro']);
  const oscuro = variablesDeBloque(css, CONTEXTOS['html.dark']);

  it('declara los mismos tokens', () => {
    expect(Object.keys(soOscuro).sort()).toEqual(Object.keys(oscuro).sort());
  });

  it('cada token tiene el mismo valor', () => {
    const distintos = Object.keys(oscuro).filter((k) => soOscuro[k] !== oscuro[k]);
    expect(distintos.map((k) => `${k}: ${soOscuro[k]} != ${oscuro[k]}`)).toEqual([]);
  });

  it('tokens.css no conserva bloques de temas con nombre', () => {
    expect(css).not.toMatch(/theme-/);
  });

  it('el bloque del sistema está dentro de la consulta de color oscuro', () => {
    expect(css).toMatch(/@media \(prefers-color-scheme: dark\) \{\s*:root:not\(\.light\) \{/);
  });
});
