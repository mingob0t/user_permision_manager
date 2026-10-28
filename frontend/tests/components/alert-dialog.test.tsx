import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import React, { createRef } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AlertDialog } from '@/components/alert-dialog';

afterEach(() => {
  cleanup();
});

describe('DIS-074: AlertDialog accesible estilo SweetAlert propio', () => {
  it('renderiza con role="alertdialog", título y descripción vinculados por aria', () => {
    render(
      <AlertDialog
        open={true}
        title="¿Eliminar área?"
        message="Esta acción no se puede deshacer."
        onClose={vi.fn()}
      />,
    );

    const dialog = screen.getByRole('alertdialog', { name: '¿Eliminar área?' });
    expect(dialog).toBeDefined();
    expect(dialog.getAttribute('aria-modal')).toBe('true');

    const descId = dialog.getAttribute('aria-describedby');
    expect(descId).toBeDefined();
    expect(document.getElementById(descId!)?.textContent).toBe(
      'Esta acción no se puede deshacer.',
    );
  });

  it('pone el foco inicial en el botón seguro (Cancelar)', () => {
    render(
      <AlertDialog
        open={true}
        title="Confirmar acción"
        message="¿Proceder?"
        cancelLabel="Cancelar"
        confirmLabel="Aceptar"
        onClose={vi.fn()}
      />,
    );

    const cancelButton = screen.getByRole('button', { name: 'Cancelar' });
    expect(document.activeElement).toBe(cancelButton);
  });

  it('ejecuta onClose al presionar Escape o hacer clic en Cancelar', () => {
    const onClose = vi.fn();
    render(
      <AlertDialog
        open={true}
        title="Confirmación"
        cancelLabel="Cancelar"
        onClose={onClose}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(document.body, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it('ejecuta onConfirm al hacer clic en Confirmar', () => {
    const onConfirm = vi.fn();
    render(
      <AlertDialog
        open={true}
        title="Eliminar usuario"
        confirmLabel="Eliminar"
        onConfirm={onConfirm}
        onClose={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('con busy=true: marca aria-disabled, previene clics y no cierra', () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    render(
      <AlertDialog
        open={true}
        title="Borrando…"
        confirmLabel="Eliminando"
        busy={true}
        onConfirm={onConfirm}
        onClose={onClose}
      />,
    );

    const confirmButton = screen.getByRole('button', { name: 'Eliminando' });
    expect(confirmButton.getAttribute('aria-disabled')).toBe('true');

    fireEvent.click(confirmButton);
    expect(onConfirm).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('renderiza cuerpo con children opcionales', () => {
    render(
      <AlertDialog open={true} title="Formulario modal" onClose={vi.fn()}>
        <input data-testid="campo-extra" placeholder="Motivo" readOnly />
      </AlertDialog>,
    );

    expect(screen.getByTestId('campo-extra')).toBeDefined();
  });
});
