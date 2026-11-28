/** DIS-102: tarjeta de área (icono a la izquierda, cifras, logos y «Ver plataformas»). */
import { readFileSync } from 'node:fs';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TarjetaArea, rutaPendientesArea } from '@/components/areas/tarjeta-area';
import type { Area, Platform } from '@/lib/types';
import { CONTEXTOS, RUTA_TOKENS, variablesDeBloque } from '../utils/tokens-css';
import { componer, MIN_NO_TEXTO, MIN_TEXTO, parseColor, razonContraste, type Rgba } from '../utils/wcag';

afterEach(() => cleanup());

/** Dato de prueba: el color de un área llega como hexadecimal; se arma desde sus canales. */
const hex = (r: number, g: number, b: number): string =>
  `#${[r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('')}`;
const AZUL = hex(37, 99, 235);

const AREA = {
  id: 3, name: 'Finanzas', description: 'Contabilidad y tesorería', icon: 'areas',
  color: AZUL, status: 'Activo', platforms_count: 4, users_count: 12,
} as Area;

const plataforma = (id: number, name: string, extra: Partial<Platform> = {}): Platform =>
  ({ id, name, area_id: 3, logo_url: null, bg_color: hex(15, 118, 110), ...extra }) as Platform;

const PLATAFORMAS = [plataforma(1, 'Contabilidad'), plataforma(2, 'Tesorería'), plataforma(3, 'Nómina'), plataforma(4, 'Facturas')];

describe('TarjetaArea', () => {
  it('DIS-162: KPI «Solicitudes pendientes» enlaza al Historial filtrado del área sin abrir las plataformas', () => {
    const onSelect = vi.fn();
    render(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} pendientes={2} onSelect={onSelect} />);
    const enlace = screen.getByRole('link', { name: 'Solicitudes pendientes: 2, en Finanzas. Abrir Historial.' });
    expect(enlace.getAttribute('href')).toBe('/approvals?status=pendiente&area_id=3');
    expect(enlace.textContent).toContain('Solicitudes pendientes');
    expect(enlace.className).toContain('nx-area-card__cifra');
    expect(enlace.className).toContain('foco-visible');
    expect(enlace.className).toContain('min-h-12');
    fireEvent.click(enlace);
    expect(onSelect).not.toHaveBeenCalled();
    expect(rutaPendientesArea(7)).toBe('/approvals?status=pendiente&area_id=7');
    expect(screen.queryByText(/por aprobar/)).toBeNull();
  });

  it('DIS-162: con 0 pendientes muestra 0 (singular con 1); sin dato no hay KPI', () => {
    const { rerender } = render(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} pendientes={1} onSelect={vi.fn()} />);
    expect(screen.getByRole('link', { name: 'Solicitudes pendientes: 1, en Finanzas. Abrir Historial.' })).toBeTruthy();
    rerender(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} pendientes={0} onSelect={vi.fn()} />);
    expect(screen.getByRole('link', { name: 'Solicitudes pendientes: 0, en Finanzas. Abrir Historial.' })).toBeTruthy();
    rerender(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} onSelect={vi.fn()} />);
    expect(screen.queryByRole('link')).toBeNull();
    expect(screen.queryByText('Solicitudes pendientes')).toBeNull();
  });

  it('DIS-162: fila de ancho completo con los administradores del área', () => {
    const admins = [
      { id: 1, name: 'Ana Pérez', email: 'ana@x.test' },
      { id: 2, name: 'Luis Gómez', email: 'luis@x.test' },
    ];
    const { rerender } = render(<TarjetaArea area={{ ...AREA, admins }} conteo={4} plataformas={PLATAFORMAS} pendientes={0} mostrarAdministradores onSelect={vi.fn()} />);
    expect(screen.getByText('Administradores de área')).toBeTruthy();
    const nombres = screen.getByText('Ana Pérez, Luis Gómez');
    expect(nombres.getAttribute('title')).toBe('Ana Pérez, Luis Gómez');
    expect(nombres.closest('.nx-area-card__cifra')?.className).toContain('col-span-full');
    rerender(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} pendientes={0} mostrarAdministradores onSelect={vi.fn()} />);
    expect(screen.getByText('Sin administrador')).toBeTruthy();
    // Sin `mostrarAdministradores` (catálogo y otras vistas) no se muestra.
    rerender(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} pendientes={0} onSelect={vi.fn()} />);
    expect(screen.queryByText('Administradores de área')).toBeNull();
  });

  it.each(['estandar', 'glass', 'flotante', 'portada', 'banner', 'split', 'onda', 'directorio', 'bento', 'medallon'] as const)(
    'DIS-164: variante %s con enlace de pendientes y fila de administradores',
    (variante) => {
      const onSelect = vi.fn();
      const admins = [{ id: 1, name: 'Ana Pérez', email: 'ana@x.test' }];
      const { rerender } = render(
        <TarjetaArea area={{ ...AREA, admins }} conteo={4} plataformas={PLATAFORMAS} pendientes={2} mostrarAdministradores variante={variante} onSelect={onSelect} />,
      );
      const enlace = screen.getByRole('link', { name: 'Solicitudes pendientes: 2, en Finanzas. Abrir Historial.' });
      expect(enlace.getAttribute('href')).toBe('/approvals?status=pendiente&area_id=3');
      expect(enlace.textContent).toContain('Solicitudes pendientes');
      expect(enlace.className).toContain('foco-visible');
      expect(enlace.className).toContain('min-h-12');
      fireEvent.click(enlace);
      expect(onSelect).not.toHaveBeenCalled();
      expect(screen.getByText('Administradores de área').closest('.col-span-full')).toBeTruthy();
      expect(screen.getByText('Ana Pérez').getAttribute('title')).toBe('Ana Pérez');
      rerender(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} pendientes={0} mostrarAdministradores variante={variante} onSelect={onSelect} />);
      expect(screen.getByText('Sin administrador')).toBeTruthy();
      // Sin dato de pendientes ni fila pedida (catálogo y otras vistas) no se pinta nada.
      rerender(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} variante={variante} onSelect={onSelect} />);
      expect(screen.queryByRole('link')).toBeNull();
      expect(screen.queryByText('Solicitudes pendientes')).toBeNull();
      expect(screen.queryByText('Administradores de área')).toBeNull();
    },
  );

  it('DIS-164: «Usuario/Usuarios» en lugar de «Persona/Personas» en las variantes con cifras', () => {
    for (const variante of ['glass', 'portada', 'banner', 'estandar'] as const) {
      const { unmount } = render(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} variante={variante} onSelect={vi.fn()} />);
      expect(screen.getByText('Usuarios')).toBeTruthy();
      expect(screen.queryByText(/persona/i)).toBeNull();
      unmount();
    }
    const { unmount } = render(<TarjetaArea area={{ ...AREA, users_count: 1 }} conteo={4} plataformas={PLATAFORMAS} variante="onda" onSelect={vi.fn()} />);
    expect(screen.getByText(/1 usuario •/)).toBeTruthy();
    unmount();
  });

  it('encabezado con nombre y descripción, y cifras de usuarios y plataformas', () => {
    render(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} onSelect={vi.fn()} />);
    expect(screen.getByRole('heading', { name: 'Finanzas' })).toBeTruthy();
    expect(screen.getByText('Contabilidad y tesorería')).toBeTruthy();
    expect(screen.getByText('12')).toBeTruthy();
    expect(screen.getByText('Usuarios')).toBeTruthy();
    expect(screen.getByText('4')).toBeTruthy();
    expect(screen.getByText('Plataformas')).toBeTruthy();
    expect(screen.getByText('Ver plataformas')).toBeTruthy();
  });

  it('descripción vacía: texto de respaldo; singular en las cifras', () => {
    render(<TarjetaArea area={{ ...AREA, description: null, users_count: 1 }} conteo={1} plataformas={[PLATAFORMAS[0]]} onSelect={vi.fn()} />);
    expect(screen.getByText('Área organizativa del sistema.')).toBeTruthy();
    expect(screen.getByText('Usuario')).toBeTruthy();
    expect(screen.getByText('Plataforma')).toBeTruthy();
  });

  it('muestra 3 logos y «+N» con el resto', () => {
    const { container } = render(<TarjetaArea area={AREA} conteo={6} plataformas={PLATAFORMAS} onSelect={vi.fn()} />);
    expect(container.querySelectorAll('.nx-chip-solid')).toHaveLength(3);
    expect(screen.getByText('CO')).toBeTruthy();
    expect(screen.queryByText('FA')).toBeNull();
    expect(screen.getByText('+3')).toBeTruthy();
  });

  it('sin «+N» cuando caben en 3 logos; usa logo_url seguro y descarta el inseguro', () => {
    const lista = [
      plataforma(1, 'Uno', { logo_url: 'https://cdn.ejemplo.local/uno.png' }),
      plataforma(2, 'Dos', { logo_url: 'javascript:alert(1)' }),
    ];
    const { container } = render(<TarjetaArea area={AREA} conteo={2} plataformas={lista} onSelect={vi.fn()} />);
    expect(screen.queryByText(/^\+/)).toBeNull();
    expect(container.querySelectorAll('img')).toHaveLength(1);
    expect(screen.getByText('DO')).toBeTruthy();
  });

  it('sin plataformas: «Sin plataformas» y ningún logo', () => {
    const { container } = render(<TarjetaArea area={AREA} conteo={0} plataformas={[]} onSelect={vi.fn()} />);
    expect(screen.getByText('Sin plataformas')).toBeTruthy();
    expect(container.querySelectorAll('.nx-chip-solid')).toHaveLength(0);
  });

  it('inactiva: aviso «Inactiva», estado neutro y sin color del área', () => {
    render(<TarjetaArea area={{ ...AREA, status: 'Inactivo' }} conteo={4} plataformas={PLATAFORMAS} onSelect={vi.fn()} />);
    const tarjeta = screen.getByRole('button', { name: /Área Finanzas \(Inactiva\)/ }).closest('[data-state]')!;
    expect(screen.getByText('Inactiva')).toBeTruthy();
    expect(tarjeta.getAttribute('data-state')).toBe('inactiva');
    expect(tarjeta.getAttribute('style') ?? '').not.toContain('--area-color');
  });

  it('activa: el color del área viaja como variable CSS y el icono decide su texto', () => {
    const { container } = render(<TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} onSelect={vi.fn()} />);
    expect(container.firstElementChild?.getAttribute('style')).toContain(`--area-color: ${AZUL}`);
    expect(container.querySelector('.nx-area-card__icono')?.getAttribute('data-texto')).toBe('sobre-oscuro');
  });

  it('«Ver plataformas» es el control accesible; el clic en toda la tarjeta y la activación del botón abren las plataformas', () => {
    const onSelect = vi.fn();
    const { container } = render(<TarjetaArea area={AREA} conteo={1} plataformas={[PLATAFORMAS[0]]} onSelect={onSelect} />);
    const boton = screen.getByRole('button', { name: 'Área Finanzas, 1 plataforma. Ver plataformas.' });
    fireEvent.click(boton);
    fireEvent.click(container.firstElementChild!);
    expect(onSelect).toHaveBeenCalledTimes(2);
    expect(onSelect).toHaveBeenCalledWith(AREA);
  });

  it('soporta las variantes con imagen de fondo portada y banner', () => {
    // 1. Variante portada
    const { unmount: unmountPortada } = render(
      <TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} onSelect={vi.fn()} variante="portada" />
    );
    expect(screen.getByRole('heading', { name: 'Finanzas' })).toBeTruthy();
    expect(document.querySelectorAll('img').length).toBeGreaterThan(0);
    unmountPortada();

    // 2. Variante banner
    const { unmount: unmountBanner } = render(
      <TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} onSelect={vi.fn()} variante="banner" />
    );
    expect(screen.getByRole('heading', { name: 'Finanzas' })).toBeTruthy();
    expect(document.querySelectorAll('img').length).toBeGreaterThan(0);
    unmountBanner();

    // 3. Demás variantes
    const variantes = ['split', 'onda', 'directorio', 'bento', 'medallon'] as const;
    for (const v of variantes) {
      const { unmount } = render(
        <TarjetaArea area={AREA} conteo={4} plataformas={PLATAFORMAS} onSelect={vi.fn()} variante={v} />
      );
      expect(screen.getByRole('heading', { name: 'Finanzas' })).toBeTruthy();
      unmount();
    }
  });
});

describe('TarjetaArea: CSS y contraste (AA en ambos temas)', () => {
  const CSS = readFileSync('src/styles/components.css', 'utf8');
  const tokens = readFileSync(RUTA_TOKENS, 'utf8');

  it('DIS-164: sobre imagen (portada, flotante) el enlace usa un anillo de foco con 3:1 sobre la capa oscura', () => {
    for (const variante of ['portada', 'flotante'] as const) {
      const { unmount } = render(<TarjetaArea area={AREA} conteo={2} plataformas={PLATAFORMAS} pendientes={1} variante={variante} onSelect={vi.fn()} />);
      const enlace = screen.getByRole('link', { name: 'Solicitudes pendientes: 1, en Finanzas. Abrir Historial.' });
      expect(enlace.className, variante).toContain('foco-sobre-arte');
      unmount();
    }
    expect(CSS).toMatch(/\.foco-sobre-arte:focus-visible\s*\{[^}]*outline-color:\s*rgb\(var\(--foco-anillo-sobre-arte\)\)/);
    const anillo = parseColor(variablesDeBloque(tokens, CONTEXTOS.claro)['--foco-anillo-sobre-arte']);
    // Peor caso: capa `arte-sombra` (negro) al 70 % sobre una imagen blanca.
    const fondo = componer(parseColor('0 0 0 / 0.7'), parseColor('255 255 255'));
    expect(razonContraste(anillo, fondo)).toBeGreaterThanOrEqual(MIN_NO_TEXTO);
  });

  it('DIS-104: recuadros, cifras, pie y «Ver plataformas» toman el color del área', () => {
    for (const clase of ['__cifra', '__valor', '__pie', '__ir']) {
      expect(CSS, clase).toMatch(new RegExp(`\\.nx-area-card${clase}\\s*\\{[^}]*var\\(--nx-area`));
    }
    const { container } = render(<TarjetaArea area={AREA} conteo={2} plataformas={PLATAFORMAS} pendientes={0} mostrarAdministradores onSelect={vi.fn()} />);
    // Usuarios, Plataformas, Solicitudes pendientes y Administradores de área (DIS-162).
    expect(container.querySelectorAll('.nx-area-card__cifra')).toHaveLength(4);
    expect(container.querySelectorAll('.nx-area-card__valor')).toHaveLength(3);
    expect(container.querySelector('.nx-area-card__pie')).toBeTruthy();
  });

  it('DIS-105: efectos de color (borde en degradado, aurora, halo, brillo del icono) y sin movimiento si se pide', () => {
    expect(CSS).toMatch(/\.nx-area-card\[data-state='activa'\]\s*\{[^}]*border-color: color-mix[^}]*box-shadow[^}]*var\(--nx-area\)/);
    // DIS-107: simétrica. Sin borde en degradado diagonal ni mancha en una esquina.
    expect(CSS).not.toMatch(/border-box/);
    expect(CSS).toMatch(/\.nx-area-card::after\s*\{[^}]*inset: 0 0 auto 0;[^}]*at 50% 0%/);
    expect(CSS).not.toMatch(/\.nx-area-card__cabecera::before\s*\{[^}]*at 0% 0%/);
    expect(CSS).toMatch(/\.nx-area-card\[data-state='inactiva'\]::after\s*\{\s*display: none/);
    expect(CSS).toMatch(/\.nx-area-card:hover \.nx-area-card__icono::after\s*\{\s*transform: translateX\(120%\)/);
    const reducido = CSS.slice(CSS.lastIndexOf('@media (prefers-reduced-motion: reduce) {\n    .nx-area-card,'));
    for (const sel of ['.nx-area-card::after', '.nx-area-card__icono::after', '.nx-area-card__logos > *']) {
      expect(reducido.slice(0, reducido.indexOf('}')), sel).toContain(sel);
    }
  });

  it('DIS-108: en un área inactiva los logos de sus plataformas se ven inactivos', () => {
    expect(CSS).toMatch(/\.nx-area-card\[data-state='inactiva'\] \.nx-area-card__logos > \*\s*\{[^}]*grayscale\(1\)[^}]*opacity/);
    const { container } = render(
      <TarjetaArea area={{ ...AREA, status: 'Inactivo' }} conteo={2} plataformas={PLATAFORMAS} onSelect={vi.fn()} />,
    );
    const tarjeta = container.firstElementChild as HTMLElement;
    expect(tarjeta.dataset.state).toBe('inactiva');
    expect(tarjeta.querySelector('.nx-area-card__logos')?.children.length).toBeGreaterThan(0);
  });

  it('hover eleva y respeta prefers-reduced-motion; el foco usa la clase común', () => {
    expect(CSS).toMatch(/\.nx-area-card:hover\s*\{[^}]*translateY\(-2px\)/);
    expect(CSS).toMatch(/prefers-reduced-motion: reduce\)\s*\{\s*\.nx-area-card,[\s\S]*?transform: none/);
    expect(CSS).toMatch(/\.nx-area-card:has\(\.nx-area-card__ir:focus-visible\)\s*\{\s*outline: var\(--foco-ancho\) solid rgb\(var\(--foco-anillo\)\)/);
  });

  const mezcla = (a: Rgba, b: Rgba, pa: number): Rgba => ({
    r: a.r * pa + b.r * (1 - pa), g: a.g * pa + b.g * (1 - pa), b: a.b * pa + b.b * (1 - pa), a: 1,
  });

  // «Ver plataformas» = 35 % del color del área + 65 % del texto del tema, sobre el panel.
  // Peores casos: área blanca y negra (cualquier otro color queda entre ambos).
  for (const [tema, selector] of [['claro', CONTEXTOS.claro], ['oscuro', CONTEXTOS['html.dark']]] as const) {
    it(`tema ${tema}: nombre, descripción, cifras y «Ver plataformas» >= 4,5:1`, () => {
      const val = { ...variablesDeBloque(tokens, CONTEXTOS.claro), ...variablesDeBloque(tokens, selector) };
      const resolver = (nombre: string): Rgba => {
        let v = val[nombre];
        while (v.startsWith('var(')) v = val[v.slice(4, -1)];
        return v.startsWith('#') ? parseColor(v) : parseColor(v);
      };
      const panel = resolver('--color-panel-fill');
      const cuerpo = resolver('--color-body-text');
      const etiqueta = resolver('--color-label-text');
      const mediciones: string[] = [];
      for (const canalesArea of ['255 255 255', '0 0 0', '37 99 235', '250 204 21']) {
        const c = parseColor(canalesArea);
        const resplandor = componer({ ...c, a: 0.08 }, panel); // resplandor del encabezado: 8 % del color
        const legible = mezcla(c, cuerpo, 0.35);
        const pares: [string, number][] = [
          ['nombre/encabezado', razonContraste(cuerpo, resplandor)],
          ['descripción/encabezado', razonContraste(etiqueta, resplandor)],
          // DIS-104: recuadro de cifras 8 %, pie 6 %, píldora «Ver plataformas» 14 % (20 % en hover).
          ['cifra (color del área)/recuadro teñido', razonContraste(legible, mezcla(c, panel, 0.08))],
          ['etiqueta cifra/recuadro teñido', razonContraste(etiqueta, mezcla(c, panel, 0.08))],
          ['Ver plataformas/píldora', razonContraste(legible, mezcla(c, panel, 0.14))],
          ['Ver plataformas/píldora hover', razonContraste(legible, mezcla(c, panel, 0.2))],
          ['logo «+N»/pie teñido', razonContraste(etiqueta, mezcla(c, panel, 0.06))],
          ['icono mini/recuadro teñido', razonContraste(legible, componer({ ...c, a: 0.14 }, mezcla(c, panel, 0.08)))],
        ];
        for (const [nombre, r] of pares) {
          mediciones.push(`${canalesArea} ${nombre}: ${r.toFixed(2)}`);
          expect(r, `${tema} ${canalesArea} ${nombre}`).toBeGreaterThanOrEqual(MIN_TEXTO);
        }
      }
      console.info(`DIS-102 contraste ${tema}\n${mediciones.join('\n')}`);
    });
  }
});
