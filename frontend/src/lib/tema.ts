/**
 * Tema de la interfaz (FNC-032): lista de temas, aplicación de su clase en
 * `<html>`, persistencia por dispositivo y script que la restaura antes de
 * pintar. Los valores salen de `styles/tokens.css`: sin clase rige la
 * preferencia de color del sistema; `light`, `dark` y `theme-*` los fuerzan.
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
  { id: 'esmeralda', etiqueta: 'Esmeralda (claro)', clase: 'theme-emerald-light' },
  { id: 'obsidiana', etiqueta: 'Obsidiana (oscuro)', clase: 'theme-obsidian-dark' },
  { id: 'rosa', etiqueta: 'Rosa (claro)', clase: 'theme-rose-light' },
  { id: 'violeta', etiqueta: 'Violeta (oscuro)', clase: 'theme-violet-dark' },
];

export const TEMA_POR_DEFECTO = 'sistema';

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
    return esTemaValido(guardado) ? guardado : TEMA_POR_DEFECTO;
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
export const SCRIPT_RESTAURAR_TEMA = `(function(){try{var m=${JSON.stringify(
  Object.fromEntries(TEMAS.filter((t) => t.clase).map((t) => [t.id, t.clase])),
)};var c=m[localStorage.getItem(${JSON.stringify(CLAVE_TEMA)})];if(c)document.documentElement.classList.add(c)}catch(e){}})();`;
