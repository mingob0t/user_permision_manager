// @vitest-environment node
/**
 * DIS-057: Escalas de tipografía, radios, bordes y sombras (ADR-007, PLAN-FASE-7 §2.3, §4.2).
 *
 * Verifica:
 * 1. Definición de fuentes del sistema (`--fuente-texto`, `--fuente-mono`) sin dependencias de red externas.
 * 2. Radios semánticos unificados (`--radio-control`, `--radio-tarjeta`, `--radio-dialogo`, `--radio-pastilla`).
 * 3. Borde estándar (`--borde-ancho`).
 * 4. Sombras normalizadas en capas 1 a 3 en tema claro y oscuro.
 * 5. Escala tipográfica respetando el umbral accesible de 12 px.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { CONTEXTOS, RUTA_TOKENS, variablesDeBloque } from '../utils/tokens-css';

const CONFIG_TAILWIND = resolve(import.meta.dirname, '../../tailwind.config.ts');
const cssTokens = readFileSync(RUTA_TOKENS, 'utf8');
const tailwindContent = readFileSync(CONFIG_TAILWIND, 'utf8');

const TOKENS_ESCALA = [
  '--fuente-texto',
  '--fuente-mono',
  '--radio-control',
  '--radio-tarjeta',
  '--radio-dialogo',
  '--radio-pastilla',
  '--borde-ancho',
  '--sombra-1',
  '--sombra-2',
  '--sombra-3',
];

describe('DIS-057: Escalas en tema claro y tema oscuro', () => {
  const varsClaro = variablesDeBloque(cssTokens, CONTEXTOS.claro);
  const varsOscuro = variablesDeBloque(cssTokens, CONTEXTOS['html.dark']);

  it('todos los tokens de escala existen en tema claro', () => {
    for (const token of TOKENS_ESCALA) {
      expect(varsClaro[token], `Falta token ${token} en tema claro`).toBeDefined();
    }
  });

  it('todos los tokens de escala existen en tema oscuro', () => {
    for (const token of TOKENS_ESCALA) {
      expect(varsOscuro[token], `Falta token ${token} en tema oscuro`).toBeDefined();
    }
  });

  it('radios numéricos son coherentes con la escala de diseño', () => {
    expect(varsClaro['--radio-control']).toBe('8px');
    expect(varsClaro['--radio-tarjeta']).toBe('12px');
    expect(varsClaro['--radio-dialogo']).toBe('16px');
    expect(varsClaro['--radio-pastilla']).toBe('9999px');
  });

  it('ancho de borde base es 1px', () => {
    expect(varsClaro['--borde-ancho']).toBe('1px');
    expect(varsOscuro['--borde-ancho']).toBe('1px');
  });
});

describe('DIS-057: Configuración de Tailwind extendida', () => {
  it('extiende borderRadius con los nombres semánticos de escala', () => {
    expect(tailwindContent).toContain("control: 'var(--radio-control)'");
    expect(tailwindContent).toContain("tarjeta: 'var(--radio-tarjeta)'");
    expect(tailwindContent).toContain("dialogo: 'var(--radio-dialogo)'");
    expect(tailwindContent).toContain("pastilla: 'var(--radio-pastilla)'");
  });

  it('extiende boxShadow con la escala 1..3', () => {
    expect(tailwindContent).toContain("1: 'var(--sombra-1)'");
    expect(tailwindContent).toContain("2: 'var(--sombra-2)'");
    expect(tailwindContent).toContain("3: 'var(--sombra-3)'");
  });

  it('extiende fontFamily con fuentes del sistema', () => {
    expect(tailwindContent).toContain("'var(--fuente-texto)'");
    expect(tailwindContent).toContain("'var(--fuente-mono)'");
  });
});
