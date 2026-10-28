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
 * - o es `nx-badge-<tono>` con un tono del tipo `tone` de `Badge` (`ui.tsx`):
 *   las demás clases armadas al ejecutar no tienen permiso (`PREFIJOS_DINAMICOS`);
 * - o está en `CLASES_SIN_LLAMADOR` (hoy vacío, con el motivo de cada una).
 * También se exige llamador a cada id, a cada selector de elemento (`select`,
 * `thead`...) y a cada atributo (`input[type="color"]`, `[data-desplazable]`):
 * el elemento, el atributo o el valor deben aparecer en el código.
 * Los comentarios (CSS y TS/TSX) no cuentan. `tokens.css` se exige solo de
 * variables (DIS-047): ninguna regla de componente, ninguna animación.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const CSS_REVISADOS = ['components.css', 'global.css'].map((n) => join(RAIZ_SRC, 'styles', n));
const CONFIG_TAILWIND = resolve(import.meta.dirname, '../../tailwind.config.ts');

/** Clases que se mantienen sin llamador en `src/`: nombre → motivo. */
const CLASES_SIN_LLAMADOR: Record<string, string> = {
  'foco-visible': 'DIS-056: anillo unico de foco accesible para adopcion en C1-C5',
  'estado-deshabilitado': 'DIS-056: estado deshabilitado unificado para adopcion en C1-C5',
  'estado-invalido': 'DIS-056: estado invalido unificado para adopcion en C1-C5',
  'solo-lectura': 'DIS-056: estado solo lectura unificado para adopcion en C1-C5',
};

function archivos(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta);
    return ['.ts', '.tsx'].includes(extname(entrada.name)) ? [ruta] : [];
  });
}

const sinComentarios = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));
const escapar = (t: string): string => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// Comentarios fuera: una clase nombrada solo en un comentario no es un llamador.
const sinComentariosTs = (texto: string): string =>
  texto.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:'"`\w])\/\/.*$/gm, '$1');
const codigo = archivos(RAIZ_SRC).map((r) => sinComentariosTs(readFileSync(r, 'utf8'))).join('\n');
const textoTailwind = readFileSync(CONFIG_TAILWIND, 'utf8');
const css = CSS_REVISADOS.map((r) => sinComentarios(readFileSync(r, 'utf8'))).join('\n');

/** Texto de los selectores: lo que va antes de cada `{`, sin reglas `@…`. */
const selectores = [...css.matchAll(/([^{};]+)\{/g)].map((m) => m[1]).filter((s) => !s.trim().startsWith('@')).join('\n');

const CLASES = [...new Set([...selectores.matchAll(/\.([a-zA-Z_][\w-]*)/g)].map((m) => m[1]))].sort();
const IDS = [...new Set([...selectores.matchAll(/#([a-zA-Z_][\w-]*)/g)].map((m) => m[1]))].sort();
const ANIMACIONES = [...css.matchAll(/@keyframes\s+([\w-]+)/g)].map((m) => m[1]);
const VARIABLES_NX = [...new Set([...css.matchAll(/(--nx-[\w-]+)\s*:/g)].map((m) => m[1]))].sort();

/** Tonos que acepta `Badge` (tipo `Tone` en ui.tsx, DIS-010). */
const TONOS_BADGE = [
  ...(/export type Tone\s*=\s*([^;]+);/.exec(readFileSync(join(RAIZ_SRC, 'components/ui.tsx'), 'utf8'))?.[1] ?? '').matchAll(/'([\w-]+)'/g),
].map((m) => m[1]);
/** Clases armadas al ejecutar que se aceptan: prefijo → sufijos válidos. */
const PREFIJOS_DINAMICOS: Record<string, string[]> = { 'nx-badge-': TONOS_BADGE };

const usada = (clase: string): boolean =>
  new RegExp(`(?<![\\w-])${escapar(clase)}(?![\\w/-])`).test(codigo) ||
  Object.entries(PREFIJOS_DINAMICOS).some(([p, sufijos]) => clase.startsWith(p) && sufijos.includes(clase.slice(p.length)));

/** Un id se usa si el código lo asigna: `id="x"`, `id: 'x'`, `id={'x'}` o `htmlFor`/`aria-*` no cuentan. */
const idUsado = (id: string): boolean => new RegExp(`\\bid\\s*[=:]\\s*\\{?\\s*['"\`]${escapar(id)}['"\`]`).test(codigo);

// Selectores de elemento y de atributo.
const GLOBALES = new Set(['html', 'body']);
const ATRIBUTOS = [...selectores.matchAll(/\[\s*([\w-]+)\s*(?:[~|^$*]?=\s*["']?([^"'\]]*)["']?)?\s*\]/g)].map((m) => ({ nombre: m[1], valor: m[2] }));
const ELEMENTOS = [
  ...new Set(
    selectores
      .replace(/\[[^\]]*\]/g, ' ')
      .replace(/[.#][\w-]+/g, ' ')
      .replace(/::?(?:where|is|not|has)\(/g, '(')
      .replace(/::?[\w-]+(\([^)]*\))?/g, ' ')
      .match(/(?<![\w-])[a-z][a-z0-9]*(?![\w-])/g) ?? [],
  ),
].filter((e) => !GLOBALES.has(e)).sort();
const ATRIBUTOS_UNICOS = [...new Map(ATRIBUTOS.map((a) => [`${a.nombre}=${a.valor ?? ''}`, a])).values()];

describe('CSS sin uso en components.css y global.css', () => {
  it('lee los selectores (la extracción no está rota)', () => {
    expect(CLASES).toContain('nexus-btn');
    expect(CLASES).toContain('nx-badge-primary');
    expect(TONOS_BADGE).toContain('primary');
    expect(TONOS_BADGE).toContain('cyan');
    expect(ELEMENTOS).toContain('select');
    expect(ATRIBUTOS_UNICOS.length).toBeGreaterThan(0);
  });

  it('el código sin comentarios no cuenta como llamador y un tono inexistente no pasa', () => {
    expect(sinComentariosTs('/* nx-fantasma */ // otro-fantasma\nconst a = 1;')).not.toMatch(/fantasma/);
    expect(usada('nx-badge-inexistente')).toBe(false);
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
      expect(idUsado(id), `#${id}: ningún elemento de src/ tiene ese id`).toBe(true);
    });
  }

  for (const el of ELEMENTOS) {
    it(`el elemento <${el}> existe en src/`, () => {
      expect(new RegExp(`<${el}[\\s>/]|createElement\\(\\s*['"]${el}['"]`).test(codigo), `<${el}> no aparece en src/`).toBe(true);
    });
  }

  for (const { nombre, valor } of ATRIBUTOS_UNICOS) {
    it(`el atributo [${nombre}${valor ? `=${valor}` : ''}] tiene llamador en src/`, () => {
      const atributo = new RegExp(`(?<![\\w-])${escapar(nombre)}(?![\\w-])`).test(codigo);
      const conValor = !valor || new RegExp(`['"\`]${escapar(valor)}['"\`]`).test(codigo);
      expect(atributo && conValor, `[${nombre}${valor ? `="${valor}"` : ''}] no aparece en src/`).toBe(true);
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

describe('tokens.css solo tiene variables (DIS-047)', () => {
  const tokens = sinComentarios(readFileSync(join(RAIZ_SRC, 'styles', 'tokens.css'), 'utf8'));
  const declaraciones = [...tokens.matchAll(/([\w-]+)\s*:[^;{}]*;/g)].map((m) => m[1]);

  it('lee las variables (la extracción no está rota)', () => {
    expect(declaraciones.filter((d) => d.startsWith('--')).length).toBeGreaterThan(100);
  });

  it('toda declaración es una variable --*', () => {
    expect(declaraciones.filter((d) => !d.startsWith('--'))).toEqual([]);
  });

  it('no define @keyframes', () => {
    expect(tokens).not.toMatch(/@keyframes/);
  });

  it('solo selecciona :root, html y los temas', () => {
    const sel = [...tokens.matchAll(/([^{};]+)\{/g)].map((m) => m[1].trim()).filter((s) => !s.startsWith('@'));
    expect(sel.filter((s) => !/^(:root|html)\b/.test(s))).toEqual([]);
  });
});
