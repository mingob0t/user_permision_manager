'use client';

/**
 * Trampa de foco compartida (DIS-031). La usan `Modal` (`form.tsx`) y
 * `MobileMenu` (DIS-025, que tenía su propia copia local).
 *
 * - Al activarse: enfoca el primer candidato de `focoInicial` o, si
 *   ninguno, el contenedor (necesita `tabIndex={-1}`). Si el foco ya está dentro (por
 *   `autoFocus`), no lo mueve.
 * - Tab y Mayús+Tab ciclan dentro del contenedor; si el foco quedó fuera,
 *   vuelve al primero (o al último con Mayús).
 * - Escape llama a `alEscape`, si se pasa y nadie hizo `preventDefault()`.
 * - Al desactivarse: devuelve el foco a `devolverA` o al elemento que lo
 *   tenía cuando se montó el componente, salvo que otro código ya lo haya
 *   movido fuera del contenedor; si ese elemento ya no existe, al `<main>`
 *   de `AppShell` o al primer `h1`.
 * - Solo cuenta lo visible (`esVisible`); si `focus()` no mueve el foco,
 *   prueba con el siguiente.
 * - `focoInicial` y `alEscape` se leen de una referencia: cambiarlos en cada
 *   render no reinicia la trampa ni roba el foco (auditoría de DIS-019).
 * - Con varias trampas activas (diálogo sobre diálogo) solo atiende la última.
 */

import { useEffect, useRef, useState, type RefObject } from 'react';

/** Elementos que reciben foco con Tab. */
export const ENFOCABLES = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

/** Campos de formulario: el foco inicial de un diálogo va al primero. */
export const CAMPOS =
  'input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled])';

/**
 * El elemento se puede enfocar ahora: tiene caja (no `display: none` ni
 * dentro de algo oculto), no está bajo `[inert]`, `[hidden]` ni un
 * `fieldset` deshabilitado (DIS-031, H5 de auditor-accesibilidad).
 */
export function esVisible(el: HTMLElement): boolean {
  return (
    el.getClientRects().length > 0 &&
    !el.closest('[inert], [hidden], fieldset[disabled]')
  );
}

/** Enfocables visibles del contenedor, en orden de documento. */
export function enfocables(contenedor: HTMLElement): HTMLElement[] {
  return Array.from(contenedor.querySelectorAll<HTMLElement>(ENFOCABLES)).filter(esVisible);
}

/** Enfoca el primero de la lista que de verdad reciba el foco; devuelve si lo logró. */
export function enfocarPrimero(candidatos: (HTMLElement | null | undefined)[]): boolean {
  for (const el of candidatos) {
    if (!el) continue;
    el.focus();
    if (document.activeElement === el) return true;
  }
  return false;
}

/**
 * Destino alterno cuando el disparador ya no existe (H4): el `<main>` con
 * `tabIndex={-1}` de `AppShell` o, si no hay, el primer `h1`.
 */
function destinoAlterno(): HTMLElement[] {
  return [
    document.querySelector<HTMLElement>('main[tabindex="-1"]'),
    document.querySelector<HTMLElement>('h1'),
  ].filter((el): el is HTMLElement => el !== null);
}

// Trampas activas, la última encima.
const pila: symbol[] = [];

export interface OpcionesTrampa {
  /** Por omisión `true`. Un componente que sigue montado al cerrarse pasa su estado. */
  activo?: boolean;
  /** Candidatos al foco inicial, en orden; si ninguno lo recibe, el contenedor. */
  focoInicial?: (contenedor: HTMLElement) => HTMLElement[];
  /** Escape; no se llama si otro oyente ya hizo `preventDefault()` (H6). */
  alEscape?: () => void;
  /** Destino del foco al desactivarse (p. ej. el botón que abre un menú). */
  devolverA?: RefObject<HTMLElement | null>;
}

export function useFocusTrap(
  ref: RefObject<HTMLElement | null>,
  { activo = true, focoInicial, alEscape, devolverA }: OpcionesTrampa = {},
) {
  // El foco al montar: el disparador del diálogo (antes de cualquier `autoFocus`).
  const [alMontar] = useState<HTMLElement | null>(() =>
    typeof document !== 'undefined' && document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null,
  );
  const inicial = useRef(focoInicial);
  const escape = useRef(alEscape);
  useEffect(() => {
    inicial.current = focoInicial;
    escape.current = alEscape;
  });

  useEffect(() => {
    const contenedor = ref.current;
    if (!activo || !contenedor) return;
    const id = Symbol('trampa-de-foco');
    pila.push(id);
    const destino = devolverA?.current ?? alMontar;

    if (!contenedor.contains(document.activeElement)) {
      enfocarPrimero([...(inicial.current?.(contenedor) ?? []), contenedor]);
    }

    function onKey(event: KeyboardEvent) {
      if (pila[pila.length - 1] !== id || !contenedor) return;
      if (event.key === 'Escape') {
        if (event.defaultPrevented || !escape.current) return;
        event.preventDefault();
        escape.current();
        return;
      }
      if (event.key !== 'Tab') return;
      const items = enfocables(contenedor);
      if (items.length === 0) {
        event.preventDefault();
        contenedor.focus();
        return;
      }
      const activoAhora = document.activeElement;
      const fuera = !contenedor.contains(activoAhora) || activoAhora === contenedor;
      if (event.shiftKey && (activoAhora === items[0] || fuera)) {
        event.preventDefault();
        enfocarPrimero([...items].reverse());
      } else if (!event.shiftKey && (activoAhora === items[items.length - 1] || fuera)) {
        event.preventDefault();
        enfocarPrimero(items);
      }
    }

    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      pila.splice(pila.indexOf(id), 1);
      const actual = document.activeElement;
      const libre = !actual || actual === document.body || contenedor.contains(actual);
      if (!libre) return;
      enfocarPrimero([destino?.isConnected ? destino : null, ...destinoAlterno()]);
    };
  }, [activo, ref, devolverA, alMontar]);
}
