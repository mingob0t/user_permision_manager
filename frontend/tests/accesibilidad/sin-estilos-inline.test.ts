// @vitest-environment node
/**
 * Sin estilos inline (DIS-012): en `src/` ningún componente fija una propiedad
 * visual en línea. Lo único aceptado:
 * - el atributo `style` con `variablesCss({ '--chip-bg': valor })` (o un objeto cuyas
 *   claves empiecen por `--`): un valor que solo se conoce al ejecutar viaja como
 *   variable CSS y una clase de `styles/components.css` la consume;
 * - asignar variables con `setProperty('--x', …)`;
 * - las props de estilo de Recharts de `RECHARTS_CON_TOKENS`, cuyos valores salen
 *   de `useTokenColors` (DIS-003) porque la librería pinta en SVG y no resuelve
 *   clases: nombre de archivo → props permitidas.
 * Prohibidos: el atributo `style` con texto, un bloque de estilos, asignar
 * propiedades visuales desde JS y un objeto de estilo con propiedades visuales.
 * Los comentarios no cuentan.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');

/** DIS-003: la gráfica del Panel pinta en SVG; sus colores salen de tokens vía `useTokenColors`. */
const RECHARTS_CON_TOKENS: Record<string, string[]> = {
  'components/dashboard.tsx': ['contentStyle', 'itemStyle', 'labelStyle'],
};

function archivos(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta);
    return ['.ts', '.tsx'].includes(extname(entrada.name)) ? [ruta] : [];
  });
}

const blanco = (m: string): string => m.replace(/[^\n]/g, ' ');
/** Quita comentarios de bloque y de línea completa (conserva posiciones). */
function sinComentarios(texto: string): string {
  return texto
    .replace(/\/\*[\s\S]*?\*\//g, blanco)
    .replace(/^(\s*)(\/\/.*)$/gm, (_m, sangria: string, resto: string) => sangria + blanco(resto));
}

const linea = (texto: string, i: number): number => texto.slice(0, i).split('\n').length;
const claves = (objeto: string): string[] => [...objeto.matchAll(/([\w'"-]+)\s*:/g)].map((m) => m[1].replace(/['"]/g, ''));

/** Violaciones de un archivo, como `linea: descripción`. */
export function violaciones(texto: string, permitidas: string[] = []): string[] {
  const t = sinComentarios(texto);
  const salida: string[] = [];
  for (const m of t.matchAll(/(?<![\w-])style\s*=\s*(\{\{[\s\S]*?\}\}|\{\s*variablesCss\(|"[^"]*"|'[^']*')/g)) {
    const valor = m[1];
    if (valor.startsWith('{ variablesCss(') || valor.startsWith('{variablesCss(')) continue;
    const dentro = valor.startsWith('{{') ? valor.slice(2, -2) : valor.slice(1, -1);
    if (valor.startsWith('{{') ? claves(dentro).every((c) => c.startsWith('--')) : /^\s*(--[\w-]+\s*:[^;]*;?\s*)+$/.test(dentro)) continue;
    salida.push(`${linea(t, m.index ?? 0)}: style en línea con propiedades visuales`);
  }
  for (const m of t.matchAll(new RegExp('<' + 'style[\\s>]', 'gi'))) salida.push(`${linea(t, m.index ?? 0)}: bloque de estilos`);
  for (const m of t.matchAll(/\.style\b(?!\.setProperty\(\s*['"]--)/g)) {
    salida.push(`${linea(t, m.index ?? 0)}: asignación de estilo desde JS (.style)`);
  }
  for (const m of t.matchAll(/\b(\w+Style)\s*=\s*\{\{/g)) {
    if (!permitidas.includes(m[1])) salida.push(`${linea(t, m.index ?? 0)}: prop de estilo ${m[1]} fuera de RECHARTS_CON_TOKENS`);
  }
  return salida;
}

describe('sin estilos inline en src/', () => {
  it('el detector reconoce lo prohibido y lo permitido', () => {
    // Los ejemplos se arman por partes para que ni esta prueba lleve lo que prohíbe.
    const S = 'st' + 'yle';
    expect(violaciones(`<a ${S}={{ color: 'x' }} />`)).toHaveLength(1);
    expect(violaciones(`<a ${S}="color: x" />`)).toHaveLength(1);
    expect(violaciones(`<${S}>a{}</${S}>`)).toHaveLength(1);
    expect(violaciones(`el.${S}.color = 'x'; el.${S}.display = 'none'`)).toHaveLength(2);
    expect(violaciones(`<Tooltip content${'S'}${S.slice(1)}={{ color: x }} />`)).toHaveLength(1);
    expect(violaciones(`<Tooltip content${'S'}${S.slice(1)}={{ color: x }} />`, ['contentStyle'])).toHaveLength(0);
    expect(violaciones(`<a ${S}={{ '--chip-bg': x, '--chip-fg': y }} />`)).toHaveLength(0);
    expect(violaciones(`<a ${S}={variablesCss({ '--chip-bg': x })} />`)).toHaveLength(0);
    expect(violaciones(`el.${S}.setProperty('--x', v)`)).toHaveLength(0);
    expect(violaciones(`// ${S}={{ color: x }}\n/* ${S}="a:b" */`)).toHaveLength(0);
  });

  for (const ruta of archivos(RAIZ_SRC).sort()) {
    const clave = relative(RAIZ_SRC, ruta).split('\\').join('/');
    it(`${clave} no tiene estilos inline`, () => {
      expect(violaciones(readFileSync(ruta, 'utf8'), RECHARTS_CON_TOKENS[clave])).toEqual([]);
    });
  }

  it('las excepciones de Recharts nombran archivos que existen', () => {
    for (const clave of Object.keys(RECHARTS_CON_TOKENS)) {
      expect(readFileSync(join(RAIZ_SRC, clave), 'utf8')).toContain('useTokenColors');
    }
  });
});
