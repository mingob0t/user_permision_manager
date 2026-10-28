// @vitest-environment jsdom
/**
 * DIS-058: Pruebas de estados, hover, foco y accesibilidad para botones y enlaces.
 * PLAN-FASE-7 §4.3 (Matriz de estados por componente).
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Button, CLASES_VARIANTE_BOTON, type ButtonVariant } from '../../src/components/button';
import { ButtonLink } from '../../src/components/button-link';

const RUTA_CSS = resolve(import.meta.dirname, '../../src/styles/components.css');
const cssComponentes = readFileSync(RUTA_CSS, 'utf8');

describe('DIS-058: Matriz de estados y clases de botones en CSS', () => {
  it('define todas las variantes de boton requeridas', () => {
    const variantes: ButtonVariant[] = ['primary', 'secondary', 'danger', 'fila', 'fila-peligro'];
    for (const v of variantes) {
      const clase = CLASES_VARIANTE_BOTON[v].split(' ')[0];
      expect(cssComponentes, `Falta la clase .${clase} en components.css`).toContain(`.${clase}`);
    }
  });

  it('define foco visible con anillo y separacion para nexus-btn', () => {
    expect(cssComponentes).toContain('.nexus-btn:focus-visible');
    expect(cssComponentes).toContain('--foco-anillo');
    expect(cssComponentes).toContain('--foco-separacion');
  });

  it('define estado deshabilitado para disabled y aria-disabled="true"', () => {
    expect(cssComponentes).toContain('.nexus-btn:disabled');
    expect(cssComponentes).toContain('.nexus-btn[aria-disabled="true"]');
    expect(cssComponentes).toContain('--deshabilitado-fondo');
    expect(cssComponentes).toContain('--deshabilitado-texto');
    expect(cssComponentes).toContain('--deshabilitado-borde');
  });

  it('neutraliza animaciones de hover y active con prefers-reduced-motion', () => {
    expect(cssComponentes).toContain('@media (prefers-reduced-motion: reduce)');
    const regexMotion = /@media\s*\(prefers-reduced-motion:\s*reduce\)[\s\S]*?\.nexus-btn[\s\S]*?transform:\s*none/i;
    expect(regexMotion.test(cssComponentes), 'Debe cancelar transform en prefers-reduced-motion').toBe(true);
  });

  it('cumple la simetria de altura de control (48px / 3rem)', () => {
    expect(cssComponentes).toContain('height: 3rem');
  });
});

describe('DIS-058: Componente Button y ButtonLink en React', () => {
  it('renderiza Button con variante primaria por defecto', () => {
    render(React.createElement(Button, null, 'Guardar'));
    const btn = screen.getByRole('button', { name: 'Guardar' });
    expect(btn.classList.contains('nexus-btn')).toBe(true);
    expect(btn.classList.contains('nexus-btn-primary')).toBe(true);
  });

  it('renderiza Button con variantes secundarias, peligro y fila', () => {
    const { rerender } = render(React.createElement(Button, { variant: 'secondary' }, 'Cancelar'));
    let btn = screen.getByRole('button', { name: 'Cancelar' });
    expect(btn.classList.contains('nexus-btn-secondary')).toBe(true);

    rerender(React.createElement(Button, { variant: 'danger' }, 'Eliminar'));
    btn = screen.getByRole('button', { name: 'Eliminar' });
    expect(btn.classList.contains('nexus-btn-danger')).toBe(true);

    rerender(React.createElement(Button, { variant: 'fila' }, 'Editar'));
    btn = screen.getByRole('button', { name: 'Editar' });
    expect(btn.classList.contains('nexus-btn-fila')).toBe(true);

    rerender(React.createElement(Button, { variant: 'fila-peligro' }, 'Borrar'));
    btn = screen.getByRole('button', { name: 'Borrar' });
    expect(btn.classList.contains('nexus-btn-fila-peligro')).toBe(true);
  });

  it('soporta estado busy con aria-busy y aria-disabled (reteniendo foco sin disabled HTML)', () => {
    render(React.createElement(Button, { busy: true }, 'Procesando'));
    const btn = screen.getByRole('button', { name: 'Procesando' });
    expect(btn.getAttribute('aria-busy')).toBe('true');
    expect(btn.getAttribute('aria-disabled')).toBe('true');
    expect(btn.hasAttribute('disabled')).toBe(false);
  });

  it('Button reenvía ref correctamente', () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(React.createElement(Button, { ref }, 'Con ref'));
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it('renderiza ButtonLink con atributos de navegación y clases de botón', () => {
    render(React.createElement(ButtonLink, { href: '/plataformas', variant: 'secondary' }, 'Ir a plataformas'));
    const link = screen.getByRole('link', { name: 'Ir a plataformas' });
    expect(link.getAttribute('href')).toBe('/plataformas');
    expect(link.classList.contains('nexus-btn')).toBe(true);
    expect(link.classList.contains('nexus-btn-secondary')).toBe(true);
  });
});
