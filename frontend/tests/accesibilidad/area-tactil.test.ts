// @vitest-environment node
/**
 * Área táctil mínima (DIS-008, DIS-035): ningún botón, enlace ni control con
 * `role` interactivo de `src/` puede quedar por debajo de 44 px de alto o de
 * ancho según sus clases. Análisis estático, al estilo de `texto-minimo` y
 * `colores-literales`.
 *
 * Qué revisa:
 * - Etiquetas `<button>`, `<a>`, `<Link>`, `<summary>` y cualquier etiqueta con
 *   `role="button" | "tab" | "link" | "menuitem" | "option" | "switch"`.
 * - Las clases de `className`: cadenas, plantillas (también lo de `${…}`) y
 *   constantes (`const X = '…'`) del mismo archivo o importadas de otro de `src/`.
 *
 * Cómo mide (escala de Tailwind: 1 = 4 px; `[44px]` y `[3rem]` también):
 * - Alto: `nexus-btn` (48 px), o el mayor de `min-h-*`, `h-*` y `size-*`; si no
 *   hay ninguno, se estima con el relleno vertical (`py-*` o `p-*`) × 2 + 16 px
 *   (alto de línea de `text-xs`). Falta o queda bajo 44 px → falla.
 * - Ancho: `nexus-btn`, `min-w-*`, `w-*` o `size-*` ≥ 44 px, o relleno horizontal
 *   (`px-*` o `p-*`) de al menos 12 px por lado (texto). Sin eso se supone un
 *   control de solo ícono → falla.
 * - Una clase con variante (`md:h-8`, `sm:min-w-0`) que baje de 44 px falla.
 *
 * Límites (lo que NO detecta):
 * - No mide el texto ni el ícono: con `px-3` se acepta aunque el texto sea de
 *   una letra; un control de solo ícono necesita `min-w-12`.
 * - Junta las dos ramas de un ternario (`a ? 'min-h-12' : ''`): basta que una
 *   tenga el tamaño. Tampoco sigue `props.className` ni clases calculadas en
 *   funciones; los componentes (`<Button>`) se revisan en su definición.
 * - No aplica CSS de `styles/` salvo `nexus-btn`; no ve `!important` ni el
 *   orden de las clases en conflicto (`h-10 h-12`).
 * - No revisa `<input>`, `<select>` ni casillas: los cubren `INPUT` (`h-12`) y
 *   la etiqueta de `Checkbox` (`min-h-12`) en `form.tsx`.
 * - Lo que mide 44 px por su contenido (una tarjeta que es un enlace) va en
 *   `area-tactil.excepciones.ts` con su motivo.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { EXCEPCIONES } from './area-tactil.excepciones';

const MINIMO_PX = 44;
const RELLENO_TEXTO_PX = 12;
const LINEA_PX = 16;
const ALTO_NEXUS_BTN = 48;
const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const ETIQUETAS = /<(button|a|Link|summary)(?=[\s>/])/g;
const CON_ROL = /<([A-Za-z][\w.]*)(?=[^>]*?\brole=["'](?:button|tab|link|menuitem|option|switch)["'])/g;

function archivos(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta);
    return extname(entrada.name) === '.tsx' ? [ruta] : [];
  });
}

const clave = (ruta: string): string => relative(RAIZ_SRC, ruta).split('\\').join('/');
const linea = (texto: string, indice: number): number => texto.slice(0, indice).split('\n').length;

/** Reemplaza los comentarios por espacios (conserva posiciones). */
function sinComentarios(texto: string): string {
  const blanco = (m: string): string => m.replace(/[^\n]/g, ' ');
  return texto
    .replace(/\/\*[\s\S]*?\*\//g, blanco)
    .replace(/^(\s*)(\/\/.*)$/gm, (_m, sangria: string, resto: string) => sangria + blanco(resto));
}

/** Índice del cierre de una cadena que empieza en `inicio` (comilla incluida). */
function finDeCadena(texto: string, inicio: number): number {
  const comilla = texto[inicio];
  let i = inicio + 1;
  while (i < texto.length && texto[i] !== comilla) i += texto[i] === '\\' ? 2 : 1;
  return i;
}

/** Índice de la `}` que cierra la `{` de `inicio`, saltando cadenas. */
function finDeLlaves(texto: string, inicio: number): number {
  let profundidad = 0;
  for (let i = inicio; i < texto.length; i += 1) {
    const c = texto[i];
    if (c === '"' || c === "'" || c === '`') i = finDeCadena(texto, i);
    else if (c === '{') profundidad += 1;
    else if (c === '}' && (profundidad -= 1) === 0) return i;
  }
  return texto.length;
}

/** Texto de la etiqueta de apertura que empieza en `inicio` (hasta su `>`). */
function etiquetaDeApertura(texto: string, inicio: number): string {
  for (let i = inicio + 1; i < texto.length; i += 1) {
    const c = texto[i];
    if (c === '"' || c === "'") i = finDeCadena(texto, i);
    else if (c === '{') i = finDeLlaves(texto, i);
    else if (c === '>') return texto.slice(inicio, i + 1);
  }
  return texto.slice(inicio);
}

/** Valor de `className=` (cadena o expresión entre llaves), o `null`. */
function valorClassName(etiqueta: string): string | null {
  const m = /\bclassName=/.exec(etiqueta);
  if (!m) return null;
  const i = m.index + m[0].length;
  if (etiqueta[i] === '{') return etiqueta.slice(i + 1, finDeLlaves(etiqueta, i));
  if (etiqueta[i] === '"' || etiqueta[i] === "'") return etiqueta.slice(i, finDeCadena(etiqueta, i) + 1);
  return null;
}

/** Cadenas (y texto de plantillas) e identificadores sueltos de una expresión. */
function piezas(expresion: string): { cadenas: string[]; ids: string[] } {
  const cadenas: string[] = [];
  const ids: string[] = [];
  for (let i = 0; i < expresion.length; i += 1) {
    const c = expresion[i];
    if (c === '"' || c === "'") {
      const fin = finDeCadena(expresion, i);
      cadenas.push(expresion.slice(i + 1, fin));
      i = fin;
    } else if (c === '`') {
      let texto = '';
      let j = i + 1;
      while (j < expresion.length && expresion[j] !== '`') {
        if (expresion[j] === '$' && expresion[j + 1] === '{') {
          const fin = finDeLlaves(expresion, j + 1);
          const dentro = piezas(expresion.slice(j + 2, fin));
          cadenas.push(...dentro.cadenas);
          ids.push(...dentro.ids);
          texto += ' ';
          j = fin + 1;
        } else {
          texto += expresion[j];
          j += 1;
        }
      }
      cadenas.push(texto);
      i = j;
    } else if (/[A-Za-z_$]/.test(c) && !/[\w$.]/.test(expresion[i - 1] ?? '')) {
      const id = /^[A-Za-z_$][\w$]*/.exec(expresion.slice(i))![0];
      ids.push(id);
      i += id.length - 1;
    }
  }
  return { cadenas, ids };
}

/** Ruta de un módulo importado (`@/…` o relativo), o `null` si no es de `src/`. */
function rutaDeModulo(desde: string, especificador: string): string | null {
  const base = especificador.startsWith('@/')
    ? join(RAIZ_SRC, especificador.slice(2))
    : especificador.startsWith('.') ? resolve(dirname(desde), especificador) : null;
  if (!base) return null;
  return ['.ts', '.tsx', '/index.ts', '/index.tsx'].map((ext) => base + ext).find(existsSync) ?? null;
}

const cache = new Map<string, string>();
function leer(ruta: string): string {
  if (!cache.has(ruta)) cache.set(ruta, sinComentarios(readFileSync(ruta, 'utf8')));
  return cache.get(ruta)!;
}

/** Expresión asignada a `const nombre` en el texto, o `null`. */
function valorDeConstante(texto: string, nombre: string): string | null {
  const m = new RegExp(`\\bconst\\s+${nombre}\\b\\s*(?::[^=]+)?=`).exec(texto);
  if (!m) return null;
  const inicio = m.index + m[0].length;
  for (let i = inicio; i < texto.length; i += 1) {
    const c = texto[i];
    if (c === '"' || c === "'" || c === '`') i = finDeCadena(texto, i);
    else if (c === '{') i = finDeLlaves(texto, i);
    else if (c === ';') return texto.slice(inicio, i);
  }
  return texto.slice(inicio);
}

/** Clases de una expresión de `className`, siguiendo constantes locales e importadas. */
function clases(expresion: string, ruta: string, profundidad = 0): string[] {
  const { cadenas, ids } = piezas(expresion);
  const resultado = cadenas.flatMap((c) => c.split(/\s+/)).filter(Boolean);
  if (profundidad > 4) return resultado;
  const texto = leer(ruta);
  for (const id of ids) {
    const local = valorDeConstante(texto, id);
    if (local !== null) {
      resultado.push(...clases(local, ruta, profundidad + 1));
      continue;
    }
    const importacion = new RegExp(`import\\s*\\{[^}]*\\b${id}\\b[^}]*\\}\\s*from\\s*['"]([^'"]+)['"]`).exec(texto);
    const destino = importacion ? rutaDeModulo(ruta, importacion[1]) : null;
    const externo = destino ? valorDeConstante(leer(destino), id) : null;
    if (destino && externo !== null) resultado.push(...clases(externo, destino, profundidad + 1));
  }
  return resultado;
}

/** Medida en px de un valor de la escala (`12`, `2.5`, `[44px]`, `[3rem]`), o `null`. */
function aPx(valor: string): number | null {
  if (/^\d*\.?\d+$/.test(valor)) return Number(valor) * 4;
  if (valor === 'px') return 1;
  const arbitrario = /^\[(\d*\.?\d+)(px|rem)\]$/.exec(valor);
  if (arbitrario) return Number(arbitrario[1]) * (arbitrario[2] === 'rem' ? 16 : 1);
  return null;
}

interface Medidas {
  alto: number | null;
  ancho: boolean;
  variantesChicas: string[];
}

function medir(lista: string[]): Medidas {
  const base: Record<string, number> = {};
  const variantesChicas: string[] = [];
  for (const cruda of lista) {
    const clase = cruda.replace(/^!/, '');
    const m = /^((?:[^\s:]+:)*)!?(min-h|min-w|h|w|size|py|px|p)-(.+)$/.exec(clase);
    if (!m) continue;
    const px = aPx(m[3]);
    if (px === null) continue;
    if (m[1]) {
      if (['min-h', 'min-w', 'h', 'w', 'size'].includes(m[2]) && px < MINIMO_PX) variantesChicas.push(cruda);
      continue;
    }
    base[m[2]] = Math.max(base[m[2]] ?? 0, px);
  }
  const nexus = lista.includes('nexus-btn');
  const alturas = [base['min-h'], base.h, base.size].filter((v): v is number => v !== undefined);
  const relleno = base.py ?? base.p;
  const alto = nexus
    ? ALTO_NEXUS_BTN
    : alturas.length > 0 ? Math.max(...alturas)
    : relleno !== undefined ? relleno * 2 + LINEA_PX : null;
  const anchos = [base['min-w'], base.w, base.size].filter((v): v is number => v !== undefined);
  const rellenoX = base.px ?? base.p ?? 0;
  const ancho = nexus || anchos.some((v) => v >= MINIMO_PX) || rellenoX >= RELLENO_TEXTO_PX;
  return { alto, ancho, variantesChicas };
}

/** Motivo de la falla, o `null` si cumple. */
function problema(lista: string[]): string | null {
  const { alto, ancho, variantesChicas } = medir(lista);
  if (alto === null) return 'sin alto (usa min-h-12)';
  if (alto < MINIMO_PX) return `alto de ${alto} px (usa min-h-12)`;
  if (!ancho) return 'sin ancho mínimo ni relleno de texto (usa min-w-12)';
  if (variantesChicas.length > 0) return `variante menor a 44 px: ${variantesChicas.join(' ')}`;
  return null;
}

interface Hallazgo {
  archivo: string;
  donde: string;
  motivo: string;
}

function revisarArchivo(ruta: string): Hallazgo[] {
  const texto = leer(ruta);
  const inicios = new Set<number>();
  for (const patron of [ETIQUETAS, CON_ROL]) for (const m of texto.matchAll(patron)) inicios.add(m.index ?? 0);
  const hallazgos: Hallazgo[] = [];
  for (const inicio of [...inicios].sort((a, b) => a - b)) {
    const etiqueta = etiquetaDeApertura(texto, inicio);
    const valor = valorClassName(etiqueta);
    const motivo = problema(valor === null ? [] : clases(valor, ruta));
    if (motivo) hallazgos.push({ archivo: clave(ruta), donde: `${clave(ruta)}:${linea(texto, inicio)}`, motivo });
  }
  return hallazgos;
}

/** Revisa un fragmento suelto (ejemplos del detector). */
function enEjemplo(codigo: string): Hallazgo[] {
  const ruta = join(RAIZ_SRC, '__ejemplo__.tsx');
  cache.set(ruta, sinComentarios(codigo));
  try {
    return revisarArchivo(ruta);
  } finally {
    cache.delete(ruta);
  }
}

describe('detector de áreas táctiles menores a 44 px', () => {
  it.each([
    '<button className="rounded px-2 py-1 text-xs">Editar</button>',
    '<button className="rounded p-1 text-lg">★</button>',
    '<a className="rounded-lg border px-3 py-1.5 text-sm" href="/x">Salir</a>',
    '<Link href="/x" className="text-sm hover:underline">Volver</Link>',
    '<button className="min-h-12 p-1">✕</button>',
    '<button className="h-8 w-8">✕</button>',
    '<button className="min-h-12 min-w-12 md:h-8">✕</button>',
    '<button className="min-h-[40px] px-4">Ir</button>',
    '<div role="button" tabIndex={0} className="px-2 py-1">x</div>',
    '<button onClick={() => abrir()} className={`rounded ${on ? "px-2" : "px-1"} py-1`}>x</button>',
    'const CHICO = "rounded px-2 py-1";\nconst x = <button className={CHICO}>x</button>;',
  ])('detecta %s', (ejemplo) => {
    expect(enEjemplo(ejemplo)).toHaveLength(1);
  });

  it.each([
    '<button className="min-h-12 min-w-12 rounded">✕</button>',
    '<button className="inline-flex min-h-12 items-center px-3 text-xs">Editar</button>',
    '<Link href="/x" className="nexus-btn nexus-btn-secondary">Historial</Link>',
    '<a className="flex flex-col rounded-xl p-4" href="/x">Tarjeta</a>',
    '<button className="min-h-[3rem] px-4">Ir</button>',
    '<button className={`-mb-px min-h-12 border-b-2 px-3 py-3 ${activa ? "a" : "b"}`}>Pestaña</button>',
    'const OK = "min-h-12 min-w-12";\nconst x = <button onClick={() => y()} className={`${OK} rounded`}>x</button>;',
    'const x = <button className={ACCION_FILA}>x</button>;\nimport { ACCION_FILA } from "@/components/acciones-fila";',
    '<aside className="p-1"><abbr title="x">x</abbr></aside>',
  ])('acepta %s', (ejemplo) => {
    expect(enEjemplo(ejemplo)).toEqual([]);
  });
});

describe('área táctil mínima (44 px) en src', () => {
  const hallazgos = archivos(RAIZ_SRC).flatMap(revisarArchivo);

  it('revisa botones y enlaces reales (el detector encuentra controles)', () => {
    const total = archivos(RAIZ_SRC).reduce((suma, ruta) => suma + [...leer(ruta).matchAll(ETIQUETAS)].length, 0);
    expect(total).toBeGreaterThan(20);
  });

  it('ningún control interactivo queda bajo 44 px fuera de las excepciones', () => {
    const nuevos = hallazgos.filter((h) => !(h.archivo in EXCEPCIONES));
    expect(nuevos.map((h) => `${h.donde}: ${h.motivo}`), 'Usa min-h-12 (y min-w-12 si es solo ícono)').toEqual([]);
  });

  it('cada excepción coincide exactamente con lo que se encuentra', () => {
    const conteo: Record<string, number> = {};
    for (const h of hallazgos) if (h.archivo in EXCEPCIONES) conteo[h.archivo] = (conteo[h.archivo] ?? 0) + 1;
    const esperado = Object.fromEntries(Object.entries(EXCEPCIONES).map(([archivo, e]) => [archivo, e.cantidad]));
    expect(conteo).toEqual(esperado);
  });
});
