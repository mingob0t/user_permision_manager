/**
 * Ayudas de jsdom para las pruebas de foco y desplazamiento (DIS-031, DIS-044).
 *
 * - jsdom no calcula cajas: `getClientRects()` siempre viene vacío y la trampa
 *   de foco (`esVisible`) vería todo oculto. `simularCajas` da una caja a todo
 *   lo que no esté dentro de `[hidden]` o `[data-sin-caja]` (simula `display: none`).
 * - `crearRaiz` arma la raíz de `app/layout.tsx` (`#raiz-app[data-desplazable]`)
 *   para montar ahí la pantalla, como en el navegador.
 */
import { vi } from 'vitest';
import { RAIZ_APP_ID } from '@/lib/raiz-app';

export function simularCajas() {
  return vi
    .spyOn(Element.prototype, 'getClientRects')
    .mockImplementation(function (this: Element) {
      const oculto = this.closest('[hidden], [data-sin-caja]');
      return (oculto ? [] : [new DOMRect(0, 0, 10, 10)]) as unknown as DOMRectList;
    });
}

export function crearRaiz(): HTMLElement {
  document.getElementById(RAIZ_APP_ID)?.remove();
  const raiz = document.createElement('div');
  raiz.id = RAIZ_APP_ID;
  raiz.setAttribute('data-desplazable', '');
  document.body.appendChild(raiz);
  return raiz;
}
