// @vitest-environment node
/**
 * DIS-056: Tokens de interacción y estado (ADR-007, PLAN-FASE-7 §4.2-4.3).
 *
 * Verifica:
 * 1. Todos los tokens de interacción y estado están presentes en tema claro y oscuro.
 * 2. `prefers-reduced-motion` reduce las duraciones de transición a 0ms.
 * 3. Ausencia total de variantes `dark:` en TSX/TS.
 * 4. Control de opacidades heredadas (no se introducen nuevas opacidades arbitrarias).
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { CONTEXTOS, RUTA_TOKENS, variablesDeBloque } from '../utils/tokens-css';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const cssTokens = readFileSync(RUTA_TOKENS, 'utf8');

const TOKENS_INTERACCION = [
  '--foco-anillo',
  '--foco-ancho',
  '--foco-separacion',
  '--hover-capa',
  '--presionado-capa',
  '--seleccionado-fondo',
  '--seleccionado-borde',
  '--deshabilitado-fondo',
  '--deshabilitado-texto',
  '--deshabilitado-borde',
  '--invalido-borde',
  '--solo-lectura-fondo',
  '--duracion-corta',
  '--duracion-media',
  '--curva',
];

function listarArchivosTs(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return listarArchivosTs(ruta);
    return ['.ts', '.tsx'].includes(extname(entrada.name)) ? [ruta] : [];
  });
}

describe('DIS-056: Tokens de interacción y estado en ambos temas', () => {
  const varsClaro = variablesDeBloque(cssTokens, CONTEXTOS.claro);
  const varsOscuro = variablesDeBloque(cssTokens, CONTEXTOS['html.dark']);

  it('todos los tokens de interacción existen en tema claro', () => {
    for (const token of TOKENS_INTERACCION) {
      expect(varsClaro[token], `Falta token ${token} en tema claro`).toBeDefined();
    }
  });

  it('todos los tokens de interacción existen en tema oscuro', () => {
    for (const token of TOKENS_INTERACCION) {
      expect(varsOscuro[token], `Falta token ${token} en tema oscuro`).toBeDefined();
    }
  });

  it('duraciones de transición son válidas en ms', () => {
    expect(varsClaro['--duracion-corta']).toMatch(/^\d+ms$/);
    expect(varsClaro['--duracion-media']).toMatch(/^\d+ms$/);
    expect(varsOscuro['--duracion-corta']).toMatch(/^\d+ms$/);
    expect(varsOscuro['--duracion-media']).toMatch(/^\d+ms$/);
  });
});

describe('DIS-056: Reducción de movimiento (prefers-reduced-motion)', () => {
  it('existe bloque @media (prefers-reduced-motion: reduce) que anula duraciones', () => {
    const match = cssTokens.match(/@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([^}]+)\}/);
    expect(match, 'Falta bloque prefers-reduced-motion').not.toBeNull();
    const contenido = match![1];
    expect(contenido).toContain('--duracion-corta: 0ms');
    expect(contenido).toContain('--duracion-media: 0ms');
  });
});

describe('DIS-056: Sin clases dark: en TSX', () => {
  const archivos = listarArchivosTs(RAIZ_SRC);

  it('ningún archivo TS o TSX usa variantes dark:', () => {
    const conDark: string[] = [];
    for (const ruta of archivos) {
      const contenido = readFileSync(ruta, 'utf8');
      if (/(?<![\w-])dark:[a-zA-Z]/.test(contenido)) {
        conDark.push(ruta.replace(RAIZ_SRC, ''));
      }
    }
    expect(conDark, 'Se encontraron variantes dark: en TS/TSX; el tema debe gobernarse por tokens CSS').toEqual([]);
  });
});

describe('DIS-056: Control de opacidades heredadas en TSX', () => {
  const archivos = listarArchivosTs(RAIZ_SRC);

  it('las opacidades en TSX no superan la lista conocida (deuda en extinción para C1-C5)', () => {
    const hallazgos: string[] = [];
    for (const ruta of archivos) {
      const contenido = readFileSync(ruta, 'utf8');
      const matches = [...contenido.matchAll(/(?<![\w-])(?:aria-disabled:|disabled:)?opacity-(\d+)(?![\w/-])/g)];
      for (const m of matches) {
        hallazgos.push(`${ruta.replace(RAIZ_SRC, '')}:${m[0]}`);
      }
    }
    // Máximo histórico conocido: 21 ocurrencias heredadas a migrar en C1-C5
    expect(hallazgos.length).toBeLessThanOrEqual(21);
  });
});
