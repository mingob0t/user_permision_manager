import { cleanup, render, screen } from '@testing-library/react';
import React from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { Badge, EmptyNote, ErrorNote, Note, Spinner, SuccessNote } from '@/components/ui';

afterEach(() => {
  cleanup();
});

describe('DIS-062: Avisos y estados unificados', () => {
  describe('Note', () => {
    it('renderiza con tono info por defecto, rol status e icono accesible', () => {
      render(<Note message="Información del sistema" />);
      const note = screen.getByRole('status');
      expect(note).toBeDefined();
      expect(note.textContent).toContain('Información del sistema');
      expect(note.className).toContain('border-primary/30');
      expect(note.className).toContain('text-primary-text');
    });

    it('renderiza con tono error y rol alert automáticamente', () => {
      render(<Note tone="error" message="Fallo de conexión" />);
      const alert = screen.getByRole('alert');
      expect(alert).toBeDefined();
      expect(alert.textContent).toContain('Fallo de conexión');
      expect(alert.className).toContain('border-error/30');
      expect(alert.className).toContain('text-error-text');
    });

    it('renderiza con tono success y rol status', () => {
      render(<Note tone="success" message="Operación exitosa" />);
      const note = screen.getByRole('status');
      expect(note).toBeDefined();
      expect(note.textContent).toContain('Operación exitosa');
      expect(note.className).toContain('border-success/30');
      expect(note.className).toContain('text-success-text');
    });

    it('renderiza con tono warning y rol status', () => {
      render(<Note tone="warning" message="Advertencia de caducidad" />);
      const note = screen.getByRole('status');
      expect(note).toBeDefined();
      expect(note.textContent).toContain('Advertencia de caducidad');
      expect(note.className).toContain('border-warning/40');
      expect(note.className).toContain('text-warning-text');
    });

    it('soporta título y acción personalizada', () => {
      render(
        <Note
          tone="warning"
          title="Atención requerida"
          message="Revisa la configuración"
          action={<button type="button">Corregir</button>}
        />,
      );
      expect(screen.getByText('Atención requerida')).toBeDefined();
      expect(screen.getByText('Revisa la configuración')).toBeDefined();
      expect(screen.getByRole('button', { name: 'Corregir' })).toBeDefined();
    });

    it('permite sobrescribir el rol accesible explícitamente', () => {
      render(<Note tone="info" role="region" message="Mensaje en región" />);
      expect(screen.getByRole('region')).toBeDefined();
    });
  });

  describe('Atajos ErrorNote y SuccessNote', () => {
    it('ErrorNote actúa como atajo para Note de error con rol alert', () => {
      render(<ErrorNote message="No se pudo guardar" />);
      const alert = screen.getByRole('alert');
      expect(alert).toBeDefined();
      expect(alert.textContent).toContain('No se pudo guardar');
      expect(alert.className).toContain('text-error-text');
    });

    it('SuccessNote renderiza mensaje de éxito en línea con token text-success-text', () => {
      render(<SuccessNote>Guardado con éxito</SuccessNote>);
      const note = screen.getByText('Guardado con éxito');
      expect(note).toBeDefined();
      expect(note.className).toContain('text-success-text');
    });
  });

  describe('EmptyNote', () => {
    it('renderiza mensaje de estado vacío en Card', () => {
      render(<EmptyNote message="Sin registros encontrados." />);
      const note = screen.getByText('Sin registros encontrados.');
      expect(note).toBeDefined();
    });

    it('soporta botón de acción opcional en estado vacío', () => {
      render(
        <EmptyNote
          message="No hay solicitudes"
          action={<button type="button">Crear solicitud</button>}
        />,
      );
      expect(screen.getByText('No hay solicitudes')).toBeDefined();
      expect(screen.getByRole('button', { name: 'Crear solicitud' })).toBeDefined();
    });
  });

  describe('Spinner', () => {
    it('renderiza con rol status y texto accesible', () => {
      render(<Spinner label="Procesando datos…" />);
      const status = screen.getByRole('status');
      expect(status.textContent).toContain('Procesando datos…');
    });

    it('soporta tamaño sm para botones y elementos en línea', () => {
      const { container } = render(<Spinner size="sm" label="Guardando" />);
      const wrapper = container.querySelector('[role="status"]');
      expect(wrapper?.className).toContain('gap-2');
    });
  });

  describe('Badge', () => {
    it('renderiza con clase nx-badge y el tono correspondiente', () => {
      render(<Badge tone="success">Activo</Badge>);
      const badge = screen.getByText('Activo');
      expect(badge.className).toContain('nx-badge');
      expect(badge.className).toContain('nx-badge-success');
    });
  });
});
