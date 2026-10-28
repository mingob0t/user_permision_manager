/**
 * Lector de `src/styles/tokens.css` para las pruebas de contraste (FNC-025).
 *
 * Extrae las variables `--*` de cada bloque de tema y arma los contextos tal
 * como se aplican en el navegador: el bloque base (`:root, html.light`) más
 * las variables que cada tema redefine.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export const RUTA_TOKENS = resolve(import.meta.dirname, '../../src/styles/tokens.css');

export type Variables = Record<string, string>;

/** Selector de cada contexto y nombre legible. El base es `:root, html.light`. */
export const CONTEXTOS = {
  claro: ':root, html.light',
  // DIS-054: el oscuro del sistema es idéntico a `html.dark` (prueba tokens-so-oscuro).
  'so-oscuro': ':root:not(.light)',
  'html.dark': 'html.dark',
} as const;

export type NombreContexto = keyof typeof CONTEXTOS;

const DECLARACION = /(--[\w-]+)\s*:\s*([^;]+);/g;

/** Devuelve las variables declaradas en el bloque cuyo selector es exacto. */
export function variablesDeBloque(css: string, selector: string): Variables {
  const sinComentarios = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const bloque = new RegExp(`(^|[}\\s])${escapar(selector)}\\s*\\{([^}]*)\\}`, 'm');
  const encontrado = sinComentarios.match(bloque);
  if (!encontrado) throw new Error(`No se encontró el bloque "${selector}" en tokens.css`);
  const variables: Variables = {};
  for (const [, nombre, valor] of encontrado[2].matchAll(DECLARACION)) {
    variables[nombre] = valor.trim();
  }
  return variables;
}

function escapar(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Variables efectivas de cada contexto: base + redefiniciones del tema. */
export function cargarContextos(css = readFileSync(RUTA_TOKENS, 'utf8')) {
  const base = variablesDeBloque(css, CONTEXTOS.claro);
  const contextos = {} as Record<NombreContexto, Variables>;
  for (const [nombre, selector] of Object.entries(CONTEXTOS) as [NombreContexto, string][]) {
    contextos[nombre] = nombre === 'claro'
      ? { ...base }
      : { ...base, ...variablesDeBloque(css, selector) };
  }
  return contextos;
}

/** Resuelve `var(--x)` (encadenado) hasta obtener el valor final. */
export function resolver(variables: Variables, nombre: string, profundidad = 0): string {
  const valor = variables[nombre];
  if (valor === undefined) throw new Error(`Variable no definida: ${nombre}`);
  const referencia = valor.match(/^var\(\s*(--[\w-]+)\s*\)$/);
  if (!referencia) return valor;
  if (profundidad > 10) throw new Error(`Referencia circular en ${nombre}`);
  return resolver(variables, referencia[1], profundidad + 1);
}
