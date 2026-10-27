// @vitest-environment node
/**
 * CSS sin uso (DIS-009): `src/styles/components.css` y `global.css` solo pueden
 * tener clases, ids, animaciones y variables `--nx-*` que algo use. Evita que el
 * CSS del portal original (DataTables, tour, KPI...) vuelva a acumularse.
 *
 * Cómo decide que una clase se usa (sin falsos positivos por clases armadas al
 * ejecutar):
 * - aparece como palabra completa en algún `.ts`/`.tsx` de `src/` (cadenas,
 *   `className`, condicionales, mapas de tonos); una utilidad con barra
 *   (`border-error/30`) no cuenta como la clase `border-error`;
 * - o su nombre empieza con un prefijo que el código completa al ejecutar:
 *   `` `nx-badge-${tono}` `` o `'nx-badge-' + tono`;
 * - o está en `CLASES_SIN_LLAMADOR` (hoy vacío, con el motivo de cada una).
 * Los comentarios no cuentan. `tokens.css` queda fuera (DIS-047).
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const CSS_REVISADOS = ['components.css', 'global.css'].map((n) => join(RAIZ_SRC, 'styles', n));
const CONFIG_TAILWIND = resolve(import.meta.dirname, '../../tailwind.config.ts');

/** Clases que se mantienen sin llamador en `src/`: nombre → motivo. */
const CLASES_SIN_LLAMADOR: Record<string, string> = {};

function archivos(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta);
    return ['.ts', '.tsx'].includes(extname(entrada.name)) ? [ruta] : [];
  });
}

const sinComentarios = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));
const escapar = (t: string): string => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const codigo = archivos(RAIZ_SRC).map((r) => readFileSync(r, 'utf8')).join('\n');
const textoTailwind = readFileSync(CONFIG_TAILWIND, 'utf8');
const css = CSS_REVISADOS.map((r) => sinComentarios(readFileSync(r, 'utf8'))).join('\n');

/** Texto de los selectores: lo que va antes de cada `{`, sin reglas `@…`. */
const selectores = [...css.matchAll(/([^{};]+)\{/g)].map((m) => m[1]).filter((s) => !s.trim().startsWith('@')).join('\n');

const CLASES = [...new Set([...selectores.matchAll(/\.([a-zA-Z_][\w-]*)/g)].map((m) => m[1]))].sort();
const IDS = [...new Set([...selectores.matchAll(/#([a-zA-Z_][\w-]*)/g)].map((m) => m[1]))].sort();
const ANIMACIONES = [...css.matchAll(/@keyframes\s+([\w-]+)/g)].map((m) => m[1]);
const VARIABLES_NX = [...new Set([...css.matchAll(/(--nx-[\w-]+)\s*:/g)].map((m) => m[1]))].sort();

/** Prefijos que el código completa al ejecutar: `nx-badge-${…}` o `'nx-badge-' + …`. */
const PREFIJOS_DINAMICOS = [
  ...new Set([
    ...[...codigo.matchAll(/([\w-]+-)\$\{/g)].map((m) => m[1]),
    ...[...codigo.matchAll(/['"`]([\w-]+-)['"`]\s*\+/g)].map((m) => m[1]),
  ]),
];

/** Prefijos de id con la misma lógica (`id={`x-${…}`}`). */
const usada = (clase: string): boolean =>
  new RegExp(`(?<![\\w-])${escapar(clase)}(?![\\w/-])`).test(codigo) ||
  PREFIJOS_DINAMICOS.some((p) => clase.startsWith(p) && clase.length > p.length);

describe('CSS sin uso en components.css y global.css', () => {
  it('lee los selectores (la extracción no está rota)', () => {
    expect(CLASES).toContain('nexus-btn');
    expect(CLASES).toContain('nx-badge-primary');
    expect(PREFIJOS_DINAMICOS).toContain('nx-badge-');
  });

  it('una clase armada al ejecutar cuenta como usada, una con barra no', () => {
    expect(usada('nx-badge-error')).toBe(true);
    expect(usada('clase-que-nadie-usa-xyz')).toBe(false);
    // `border-error/30` (utilidad de Tailwind) no es la clase `.border-error`.
    expect(/(?<![\w-])border-error(?![\w/-])/.test('class="border-error/30"')).toBe(false);
  });

  for (const clase of CLASES) {
    it(`.${clase} tiene llamador en src/`, () => {
      expect(
        clase in CLASES_SIN_LLAMADOR || usada(clase),
        `.${clase} no se usa en ningún .ts/.tsx de src/. Bórrala de components.css o global.css; ` +
          'si debe quedarse, agrégala a CLASES_SIN_LLAMADOR con su motivo.',
      ).toBe(true);
    });
  }

  for (const id of IDS) {
    it(`#${id} existe como id en src/`, () => {
      expect(new RegExp(`['"\`]${escapar(id)}['"\`]|id=\\{?['"\`]${escapar(id)}`).test(codigo) || codigo.includes(`#${id}`)).toBe(true);
    });
  }

  for (const nombre of ANIMACIONES) {
    it(`@keyframes ${nombre} se usa en una animación`, () => {
      const enCss = new RegExp(`animation(?:-name)?\\s*:[^;]*(?<![\\w-])${escapar(nombre)}(?![\\w-])`).test(css);
      const enTailwind = new RegExp(`(?<![\\w-])${escapar(nombre)}(?![\\w-])`).test(textoTailwind);
      expect(enCss || enTailwind, `@keyframes ${nombre} no lo usa ninguna animación`).toBe(true);
    });
  }

  for (const variable of VARIABLES_NX) {
    it(`${variable} se lee con var()`, () => {
      expect(new RegExp(`var\\(\\s*${escapar(variable)}\\b`).test(css + codigo), `${variable} no tiene referencias`).toBe(true);
    });
  }
});
