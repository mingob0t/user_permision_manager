import { cleanup, render, screen } from '@testing-library/react';
import React, { createRef } from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import {
  Checkbox,
  ColorInput,
  Field,
  FieldErrorNote,
  FileInput,
  Radio,
  Select,
  TextArea,
  TextInput,
} from '@/components/form';

afterEach(() => {
  cleanup();
});

describe('DIS-059: Componentes de formulario unificados', () => {
  describe('TextInput', () => {
    it('renderiza con clases estándar nexus-input y altura táctil', () => {
      render(<TextInput placeholder="Nombre" />);
      const input = screen.getByPlaceholderText('Nombre');
      expect(input.className).toContain('nexus-input');
      expect(input.className).toContain('h-12');
      expect(input.className).toContain('rounded-xl');
    });

    it('aplica estilo de borde de error cuando aria-invalid="true"', () => {
      render(<TextInput placeholder="Inválido" aria-invalid="true" />);
      const input = screen.getByPlaceholderText('Inválido');
      expect(input.className).toContain('border-error-text');
    });

    it('soporta estado deshabilitado y solo lectura de forma distinguible', () => {
      const { rerender } = render(<TextInput placeholder="Test" disabled />);
      let input = screen.getByPlaceholderText('Test');
      expect(input.className).toContain('disabled:cursor-not-allowed');

      rerender(<TextInput placeholder="Test" readOnly />);
      input = screen.getByPlaceholderText('Test');
      expect(input.className).toContain('read-only:cursor-default');
    });

    it('reenvía ref correctamente al elemento input nativo', () => {
      const ref = createRef<HTMLInputElement>();
      render(<TextInput ref={ref} placeholder="Con ref" />);
      expect(ref.current).toBeInstanceOf(HTMLInputElement);
    });
  });

  describe('TextArea', () => {
    it('renderiza con clases estándar y reenvía ref', () => {
      const ref = createRef<HTMLTextAreaElement>();
      render(<TextArea ref={ref} placeholder="Descripción" />);
      expect(ref.current).toBeInstanceOf(HTMLTextAreaElement);
      expect(ref.current?.className).toContain('nexus-textarea');
      expect(ref.current?.className).toContain('py-3');
    });

    it('aplica borde de error con aria-invalid', () => {
      render(<TextArea placeholder="Inválido" aria-invalid="true" />);
      const area = screen.getByPlaceholderText('Inválido');
      expect(area.className).toContain('border-error-text');
    });
  });

  describe('Select', () => {
    it('renderiza con clase nexus-select y reenvía ref', () => {
      const ref = createRef<HTMLSelectElement>();
      render(
        <Select ref={ref} aria-label="Opciones">
          <option value="1">Uno</option>
        </Select>,
      );
      expect(ref.current).toBeInstanceOf(HTMLSelectElement);
      expect(ref.current?.className).toContain('nexus-select');
    });

    it('aplica borde de error con aria-invalid', () => {
      render(
        <Select aria-label="Inválido" aria-invalid="true">
          <option value="1">Uno</option>
        </Select>,
      );
      const select = screen.getByRole('combobox');
      expect(select.className).toContain('border-error-text');
    });
  });

  describe('Checkbox', () => {
    it('renderiza con etiqueta y área táctil de 48 px (min-h-12)', () => {
      render(<Checkbox label="Acepto los términos" />);
      const checkbox = screen.getByRole('checkbox', { name: 'Acepto los términos' });
      expect(checkbox).toBeTruthy();
      expect(checkbox.className).toContain('nexus-checkbox');

      const label = checkbox.closest('label');
      expect(label?.className).toContain('min-h-12');
    });
  });

  describe('FileInput, ColorInput y Radio', () => {
    it('FileInput tiene altura táctil mínima', () => {
      render(<FileInput aria-label="Subir archivo" />);
      const fileInput = screen.getByLabelText('Subir archivo');
      expect(fileInput.className).toContain('min-h-12');
    });

    it('ColorInput tiene altura táctil mínima de 48 px (h-12)', () => {
      render(<ColorInput aria-label="Color del área" />);
      const colorInput = screen.getByLabelText('Color del área');
      expect(colorInput.className).toContain('h-12');
      expect(colorInput.className).toContain('rounded-xl');
    });

    it('Radio usa accent-primary y cursor pointer', () => {
      render(<Radio aria-label="Opción A" />);
      const radio = screen.getByRole('radio', { name: 'Opción A' });
      expect(radio.className).toContain('accent-primary');
    });
  });

  describe('Field y FieldErrorNote', () => {
    it('Field reserva línea de error sin alterar la estructura', () => {
      render(
        <Field label="Nombre" hint="Texto de ayuda" error="Nombre requerido" errorId="nombre-err">
          <TextInput />
        </Field>,
      );
      expect(screen.getByText('Nombre')).toBeTruthy();
      expect(screen.getByText('Texto de ayuda')).toBeTruthy();
      const err = screen.getByText('Nombre requerido');
      expect(err.id).toBe('nombre-err');
      expect(err.className).toContain('min-h-5');
    });

    it('FieldErrorNote reserva línea de altura mínima para evitar saltos (CLS)', () => {
      render(<FieldErrorNote id="err-1" message="Error de validación" />);
      const err = screen.getByText('Error de validación');
      expect(err.className).toContain('min-h-5');
      expect(err.className).toContain('text-error-text');
    });
  });
});
