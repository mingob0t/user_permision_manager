// @vitest-environment node
/**
 * DIS-044 (H1 de auditor-accesibilidad): `html` y `body` tienen `overflow: hidden`
 * (global.css), así que alguien tiene que desplazarse. La raíz de `layout.tsx` es el
 * contenedor desplazable de las páginas sin `AppShell` (login, salida, 404, error);
 * con `AppShell` el marco ocupa la ventana y se desplaza su `<main>` (menu-movil.test.tsx).
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import RootLayout from '@/app/layout';
import { RAIZ_APP_ID } from '@/lib/raiz-app';

describe('contenedor desplazable de la app', () => {
  it('la raíz envuelve todas las páginas, ocupa la ventana y se desplaza', () => {
    const html = renderToStaticMarkup(<RootLayout><p>página</p></RootLayout>);
    const raiz = html.match(new RegExp(`<div id="${RAIZ_APP_ID}"[^>]*>`))?.[0] ?? '';
    expect(raiz).toContain('data-desplazable=""');
    expect(raiz).toMatch(/class="[^"]*\bh-dvh\b[^"]*\boverflow-y-auto\b/);
    expect(html).toMatch(new RegExp(`<div id="${RAIZ_APP_ID}"[^>]*><p>página</p></div>`));
  });

  it('html y body siguen sin desplazarse (por eso existe la raíz)', () => {
    const css = readFileSync(resolve(import.meta.dirname, '../../src/styles/global.css'), 'utf8');
    expect(css).toMatch(/^html \{[^}]*overflow: hidden;/m);
    expect(css).toMatch(/^body \{[^}]*overflow: hidden;/m);
  });

  it('las páginas sin AppShell no fijan su propia altura ni recortan', () => {
    for (const archivo of ['login-form.tsx', 'logout-view.tsx']) {
      const fuente = readFileSync(resolve(import.meta.dirname, '../../src/components', archivo), 'utf8');
      expect(fuente, archivo).not.toMatch(/(?<![\w-])(h-screen|h-dvh|overflow-hidden)(?![\w-])/);
    }
    for (const archivo of ['error.tsx', 'not-found.tsx']) {
      const fuente = readFileSync(resolve(import.meta.dirname, '../../src/app', archivo), 'utf8');
      expect(fuente, archivo).not.toMatch(/(?<![\w-])(h-screen|h-dvh|overflow-hidden)(?![\w-])/);
    }
  });
});
