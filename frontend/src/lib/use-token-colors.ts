'use client';

/**
 * Lee tokens de color (`--color-*`, formato "r g b") con `getComputedStyle` y los
 * entrega como `rgb(r g b)`, para librerías que dibujan en SVG y no resuelven
 * `var()` (DIS-003). Se vuelve a leer al cambiar el tema (clase o atributo de
 * `<html>`) o la preferencia de color del sistema, así que no conoce el tema.
 */

import { useEffect, useState } from 'react';

export type ColoresDeToken<K extends string> = Record<K, string>;

/** Valor de token a color CSS: hex y funciones de color tal cual; "r g b [/ a]" dentro de `rgb()`. */
export function aColor(valor: string): string {
  const v = valor.trim();
  if (!v) return 'currentColor';
  if (v.startsWith('#') || /^[a-z-]+\(/i.test(v)) return v;
  return `rgb(${v})`;
}

function leer<K extends string>(tokens: Record<K, string>): ColoresDeToken<K> {
  const estilo = getComputedStyle(document.documentElement);
  const colores = {} as ColoresDeToken<K>;
  for (const clave of Object.keys(tokens) as K[]) {
    colores[clave] = aColor(estilo.getPropertyValue(tokens[clave]));
  }
  return colores;
}

/** `tokens` asigna un nombre a cada variable: `{ eje: '--color-label-text' }`. */
export function useTokenColors<K extends string>(tokens: Record<K, string>): ColoresDeToken<K> {
  const [colores, setColores] = useState<ColoresDeToken<K>>(() => {
    const vacios = {} as ColoresDeToken<K>;
    for (const clave of Object.keys(tokens) as K[]) vacios[clave] = 'currentColor';
    return vacios;
  });

  useEffect(() => {
    const actualizar = () => setColores(leer(tokens));
    actualizar();
    const observador = new MutationObserver(actualizar);
    observador.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class', 'data-theme'],
    });
    const preferencia = window.matchMedia?.('(prefers-color-scheme: dark)');
    preferencia?.addEventListener?.('change', actualizar);
    return () => {
      observador.disconnect();
      preferencia?.removeEventListener?.('change', actualizar);
    };
    // `tokens` es una constante de módulo en los usos.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return colores;
}
