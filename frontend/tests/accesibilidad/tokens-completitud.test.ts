// @vitest-environment node
/**
 * DIS-055: Prueba de completitud de tokens por capas (ADR-007).
 * - Todo token semántico existe en los 2 temas (claro y oscuro).
 * - Los tokens primitivos (`--p-*`) solo existen en `tokens.css` y nunca se usan directamente en componentes/estilos.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { CONTEXTOS, RUTA_TOKENS, variablesDeBloque } from '../utils/tokens-css';

const cssTokens = readFileSync(RUTA_TOKENS, 'utf8');

const SEMANTICOS_ESPERADOS = [
  '--color-fondo',
  '--color-superficie',
  '--color-superficie-elevada',
  '--color-superficie-hundida',
  '--color-velo',
  '--color-texto',
  '--color-texto-secundario',
  '--color-texto-tenue',
  '--color-texto-sobre-accion',
  '--color-texto-sobre-peligro',
  '--color-texto-enlace',
  '--color-borde',
  '--color-borde-sutil',
  '--color-borde-fuerte',
  '--color-accion',
  '--color-accion-hover',
  '--color-accion-presionada',
  '--color-accion-tenue',
  '--color-accion-texto',
  '--color-exito-relleno',
  '--color-exito-tenue',
  '--color-exito-borde',
  '--color-exito-texto',
  '--color-aviso-relleno',
  '--color-aviso-tenue',
  '--color-aviso-borde',
  '--color-aviso-texto',
  '--color-peligro-relleno',
  '--color-peligro-tenue',
  '--color-peligro-borde',
  '--color-peligro-texto',
  '--color-info-relleno',
  '--color-info-tenue',
  '--color-info-borde',
  '--color-info-texto',
  '--color-neutro-relleno',
  '--color-neutro-tenue',
  '--color-neutro-borde',
  '--color-neutro-texto',
];

describe('DIS-055: Completitud de tokens semánticos', () => {
  const varsClaro = variablesDeBloque(cssTokens, CONTEXTOS.claro);
  const varsOscuro = variablesDeBloque(cssTokens, CONTEXTOS['html.dark']);

  it('todos los tokens semánticos esperados están definidos en tema claro', () => {
    for (const semantico of SEMANTICOS_ESPERADOS) {
      expect(varsClaro[semantico], `Falta en claro: ${semantico}`).toBeDefined();
    }
  });

  it('todos los tokens semánticos esperados están definidos en tema oscuro', () => {
    for (const semantico of SEMANTICOS_ESPERADOS) {
      expect(varsOscuro[semantico], `Falta en oscuro: ${semantico}`).toBeDefined();
    }
  });

  it('los primitivos (--p-*) solo existen en tokens.css y no se usan en archivos TSX ni en components.css', () => {
    const raizSrc = resolve(import.meta.dirname, '../../src');
    function buscarArchivos(dir: string): string[] {
      return readdirSync(dir, { withFileTypes: true }).flatMap((entrada) => {
        const ruta = join(dir, entrada.name);
        if (entrada.isDirectory()) return buscarArchivos(ruta);
        return ['.ts', '.tsx', '.css'].includes(extname(entrada.name)) ? [ruta] : [];
      });
    }

    const archivos = buscarArchivos(raizSrc).filter((r) => !r.endsWith('tokens.css'));
    for (const ruta of archivos) {
      const contenido = readFileSync(ruta, 'utf8');
      expect(contenido, `El archivo ${ruta} usa primitivos directamente`).not.toMatch(/--p-[a-z0-9-]+/);
    }
  });
});
