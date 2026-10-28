/**
 * Tema de la interfaz (FNC-032): lista de temas, aplicación de su clase en
 * `<html>`, persistencia por dispositivo y script que la restaura antes de
 * pintar. Los valores salen de `styles/tokens.css`: sin clase rige la
 * preferencia de color del sistema; `light` y `dark` la fuerzan (DIS-054: solo 2 temas).
 */

export interface Tema {
  id: string;
  etiqueta: string;
  /** Clase de `<html>`; `null` = seguir la preferencia del sistema. */
  clase: string | null;
}

export const TEMAS: readonly Tema[] = [
  { id: 'sistema', etiqueta: 'Según el sistema', clase: null },
  { id: 'claro', etiqueta: 'Claro', clase: 'light' },
  { id: 'oscuro', etiqueta: 'Oscuro', clase: 'dark' },
];

export const TEMA_POR_DEFECTO = 'sistema';

/**
 * Temas retirados (DIS-054, ADR-007) y el que los reemplaza. Un valor viejo puede
 * llegar de `localStorage` o de la cuenta antes de que el backend (FNC-132) migre.
 * Cualquier otro valor desconocido cae a «sistema».
 */
export const TEMAS_RETIRADOS: Readonly<Record<string, string>> = {
  esmeralda: 'claro',
  rosa: 'claro',
  obsidiana: 'oscuro',
  violeta: 'oscuro',
};

/** Id vigente de un valor externo: válido tal cual, retirado traducido, o el de por defecto. */
export function normalizarTema(valor: unknown): string {
  if (typeof valor !== 'string') return TEMA_POR_DEFECTO;
  if (esTemaValido(valor)) return valor;
  return Object.hasOwn(TEMAS_RETIRADOS, valor) ? TEMAS_RETIRADOS[valor] : TEMA_POR_DEFECTO;
}

/** Llave en `localStorage` (preferencia por navegador; no es un secreto). */
export const CLAVE_TEMA = 'nexus-tema';

const CLASES = TEMAS.flatMap((t) => (t.clase ? [t.clase] : []));

export function esTemaValido(id: unknown): id is string {
  return typeof id === 'string' && TEMAS.some((t) => t.id === id);
}

/** Tema guardado; cualquier valor ausente, inválido o inaccesible cae al de por defecto. */
export function leerTema(): string {
  try {
    const guardado = window.localStorage.getItem(CLAVE_TEMA);
    return guardado === null ? TEMA_POR_DEFECTO : normalizarTema(guardado);
  } catch {
    return TEMA_POR_DEFECTO;
  }
}

/** Deja en `<html>` solo la clase del tema elegido. */
export function aplicarTema(id: string): void {
  const raiz = document.documentElement;
  raiz.classList.remove(...CLASES);
  const clase = TEMAS.find((t) => t.id === id)?.clase;
  if (clase) raiz.classList.add(clase);
}

/** Aplica y guarda el tema; si el almacenamiento falla, el tema rige igual en esta sesión. */
export function elegirTema(id: string): void {
  if (!esTemaValido(id)) return;
  aplicarTema(id);
  try {
    window.localStorage.setItem(CLAVE_TEMA, id);
  } catch {
    /* almacenamiento bloqueado: sin persistencia */
  }
}

/**
 * Tema que viene de la cuenta (`preferences.theme` de `/me`, FNC-123). Es un dato
 * externo: pasa por `esTemaValido` y `aplicarTema`, nunca se usa como clase directa;
 * un tema retirado se traduce a su equivalente y un valor desconocido cae a «sistema». Ausente (`undefined`/`null`) = conserva el
 * del navegador. Devuelve el id aplicado, o `null` si no hubo nada que aplicar.
 */
export function aplicarTemaDeCuenta(valor: unknown): string | null {
  if (valor === undefined || valor === null) return null;
  const id = normalizarTema(valor);
  elegirTema(id);
  return id;
}

/** Aplica el tema guardado (lo usa el selector al montar y las pruebas). */
export function restaurarTema(): string {
  const id = leerTema();
  aplicarTema(id);
  return id;
}

/**
 * Script en línea de `<head>`: restaura la clase antes del primer pintado para
 * evitar el destello del tema equivocado. Mismas reglas que `restaurarTema`.
 */
export const SCRIPT_RESTAURAR_TEMA = `(function(){try{var m=${JSON.stringify({
  ...Object.fromEntries(TEMAS.filter((t) => t.clase).map((t) => [t.id, t.clase])),
  ...Object.fromEntries(
    Object.entries(TEMAS_RETIRADOS).map(([viejo, nuevo]) => [viejo, TEMAS.find((t) => t.id === nuevo)?.clase]),
  ),
})};var c=m[localStorage.getItem(${JSON.stringify(CLAVE_TEMA)})];if(c)document.documentElement.classList.add(c)}catch(e){}})();`;
