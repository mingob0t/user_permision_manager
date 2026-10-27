'use client';

/**
 * Trampa de foco compartida (DIS-031). La usan `Modal` (`form.tsx`) y
 * `MobileMenu` (DIS-025, que tenía su propia copia local).
 *
 * - Al activarse: enfoca lo que diga `focoInicial` o, si no hay, el
 *   contenedor (necesita `tabIndex={-1}`). Si el foco ya está dentro (por
 *   `autoFocus`), no lo mueve.
 * - Tab y Mayús+Tab ciclan dentro del contenedor; si el foco quedó fuera,
 *   vuelve al primero (o al último con Mayús).
 * - Escape llama a `alEscape`, si se pasa.
 * - Al desactivarse: devuelve el foco a `devolverA` o al elemento que lo
 *   tenía cuando se montó el componente, salvo que otro código ya lo haya
 *   movido fuera del contenedor.
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

/** Enfocables visibles del contenedor, en orden de documento. */
export function enfocables(contenedor: HTMLElement): HTMLElement[] {
  return Array.from(contenedor.querySelectorAll<HTMLElement>(ENFOCABLES)).filter(
    (el) => !el.closest('[hidden]'),
  );
}

// Trampas activas, la última encima.
const pila: symbol[] = [];

export interface OpcionesTrampa {
  /** Por omisión `true`. Un componente que sigue montado al cerrarse pasa su estado. */
  activo?: boolean;
  /** Elemento que recibe el foco al activarse; `null` = el contenedor. */
  focoInicial?: (contenedor: HTMLElement) => HTMLElement | null;
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
      (inicial.current?.(contenedor) ?? contenedor).focus();
    }

    function onKey(event: KeyboardEvent) {
      if (pila[pila.length - 1] !== id || !contenedor) return;
      if (event.key === 'Escape' && escape.current) {
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
      const primero = items[0];
      const ultimo = items[items.length - 1];
      const activoAhora = document.activeElement;
      const fuera = !contenedor.contains(activoAhora) || activoAhora === contenedor;
      if (event.shiftKey && (activoAhora === primero || fuera)) {
        event.preventDefault();
        ultimo.focus();
      } else if (!event.shiftKey && (activoAhora === ultimo || fuera)) {
        event.preventDefault();
        primero.focus();
      }
    }

    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      pila.splice(pila.indexOf(id), 1);
      const actual = document.activeElement;
      const libre = !actual || actual === document.body || contenedor.contains(actual);
      if (libre && destino?.isConnected) destino.focus();
    };
  }, [activo, ref, devolverA, alMontar]);
}
