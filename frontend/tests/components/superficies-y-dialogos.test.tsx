import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Drawer } from '@/components/drawer';
import { Modal } from '@/components/form';
import { Card, PanelHeader } from '@/components/ui';

afterEach(() => {
  cleanup();
});

describe('DIS-061: Superficies y diálogos unificados', () => {
  describe('Card', () => {
    it('renderiza como div por defecto con variante default', () => {
      render(<Card data-testid="test-card">Contenido tarjeta</Card>);
      const card = screen.getByTestId('test-card');
      expect(card.tagName.toLowerCase()).toBe('div');
      expect(card.className).toContain('rounded-xl');
      expect(card.className).toContain('border-panel-border');
      expect(card.className).toContain('bg-panel-fill');
    });

    it('aplica la variante link para tarjetas interactivas', () => {
      render(
        <Card variant="link" data-testid="card-link">
          Tarjeta enlace
        </Card>,
      );
      const card = screen.getByTestId('card-link');
      expect(card.className).toContain('hover:border-primary');
      expect(card.className).toContain('transition-colors');
    });

    it('aplica la variante selectable para opciones de formulario', () => {
      render(
        <Card as="label" variant="selectable" data-testid="card-select">
          <input type="radio" name="opt" />
          <span>Opción</span>
        </Card>,
      );
      const card = screen.getByTestId('card-select');
      expect(card.tagName.toLowerCase()).toBe('label');
      expect(card.className).toContain('cursor-pointer');
      expect(card.className).toContain('has-[:checked]:border-primary');
    });

    it('soporta elementos polimórficos as="article" y as="fieldset"', () => {
      const { rerender } = render(<Card as="article" data-testid="poly-card">Artículo</Card>);
      expect(screen.getByTestId('poly-card').tagName.toLowerCase()).toBe('article');

      rerender(<Card as="fieldset" data-testid="poly-card">Grupo de campos</Card>);
      expect(screen.getByTestId('poly-card').tagName.toLowerCase()).toBe('fieldset');
    });
  });

  describe('PanelHeader', () => {
    it('renderiza título y acciones suplementarias en el encabezado', () => {
      render(
        <PanelHeader title="Encabezado del panel">
          <button type="button">Acción</button>
        </PanelHeader>,
      );
      expect(screen.getByText('Encabezado del panel')).toBeDefined();
      expect(screen.getByRole('button', { name: 'Acción' })).toBeDefined();
    });
  });

  describe('Modal', () => {
    it('renderiza diálogo con título, contenido y botón cerrar con icono accesible', () => {
      const onClose = vi.fn();
      render(
        <Modal onClose={onClose} title="Título Modal">
          <p>Cuerpo modal</p>
        </Modal>,
      );
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeDefined();
      expect(screen.getByText('Título Modal')).toBeDefined();
      expect(screen.getByText('Cuerpo modal')).toBeDefined();

      const botonCerrar = screen.getByRole('button', { name: 'Cerrar' });
      fireEvent.click(botonCerrar);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('cierra el diálogo al pulsar la tecla Escape', () => {
      const onClose = vi.fn();
      render(
        <Modal onClose={onClose} title="Modal Escape">
          <p>Cuerpo</p>
        </Modal>,
      );
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Drawer', () => {
    it('no renderiza nada cuando open es false', () => {
      render(
        <Drawer open={false} onClose={vi.fn()} title="Menú lateral">
          <nav>Navegación</nav>
        </Drawer>,
      );
      expect(screen.queryByRole('dialog')).toBeNull();
    });

    it('renderiza diálogo con rol dialog, backdrop y título cuando open es true', () => {
      const onClose = vi.fn();
      render(
        <Drawer open={true} onClose={onClose} title="Menú lateral">
          <nav>Enlaces</nav>
        </Drawer>,
      );
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeDefined();
      expect(dialog.getAttribute('aria-modal')).toBe('true');
      expect(screen.getByText('Menú lateral')).toBeDefined();

      const botonCerrar = screen.getByRole('button', { name: 'Cerrar' });
      fireEvent.click(botonCerrar);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('cierra el Drawer al hacer click en el backdrop', () => {
      const onClose = vi.fn();
      render(
        <Drawer open={true} onClose={onClose} title="Menú lateral">
          <p>Contenido</p>
        </Drawer>,
      );
      const backdrop = screen.getByTestId('drawer-backdrop');
      fireEvent.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('cierra el Drawer al presionar Escape', () => {
      const onClose = vi.fn();
      render(
        <Drawer open={true} onClose={onClose} title="Menú lateral">
          <p>Contenido</p>
        </Drawer>,
      );
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(onClose).toHaveBeenCalled();
    });
  });
});
