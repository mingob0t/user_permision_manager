/**
 * DIS-031, DIS-038 y DIS-044: `Modal` (`form.tsx`), compartido por todas las pantallas
 * con diálogo. Trampa de foco, foco inicial, devolución del foco (y destino alterno),
 * `describedBy`/`aria-labelledby`, foco estable al re-renderizar, elementos ocultos,
 * Escape ya atendido, portal, velo por token, bloqueo del desplazamiento e `inert`.
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ConfirmDialog, Modal, TextInput } from '@/components/form';
import { CLASE_SCROLL_BLOQUEADO } from '@/lib/use-scroll-lock';
import { crearRaiz, simularCajas } from '../utils/dom-simulado';

let raiz: HTMLElement;

beforeEach(() => {
  simularCajas();
  raiz = crearRaiz();
});

afterEach(cleanup);

/** Pantalla mínima: un botón abre el diálogo; `campos` decide si el cuerpo trae inputs. */
function Pantalla({ campos = true, describedBy }: { campos?: boolean; describedBy?: string }) {
  const [abierto, setAbierto] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setAbierto(true)}>Abrir</button>
      <button type="button">Fuera</button>
      {abierto ? (
        <Modal
          title="Diálogo"
          onClose={() => setAbierto(false)}
          describedBy={describedBy}
          footer={<button type="button">Aceptar</button>}
        >
          <p id="explica">Explica la acción.</p>
          {campos ? (
            <>
              <TextInput aria-label="Nombre" />
              <TextInput aria-label="Correo" />
            </>
          ) : null}
        </Modal>
      ) : null}
    </>
  );
}

function abrir() {
  const disparador = screen.getByRole('button', { name: 'Abrir' });
  disparador.focus();
  fireEvent.click(disparador);
  return { disparador, dialogo: screen.getByRole('dialog', { name: 'Diálogo' }) };
}

describe('Modal: foco', () => {
  it('el foco inicial va al primer campo del cuerpo', () => {
    render(<Pantalla />, { container: raiz });
    abrir();
    expect(document.activeElement).toBe(screen.getByLabelText('Nombre'));
  });

  it('sin campos, el foco inicial va al panel', () => {
    render(<Pantalla campos={false} />, { container: raiz });
    const { dialogo } = abrir();
    expect(document.activeElement).toBe(dialogo);
  });

  it('Tab y Mayús+Tab ciclan dentro del diálogo', () => {
    render(<Pantalla />, { container: raiz });
    abrir();
    const cerrar = screen.getByRole('button', { name: 'Cerrar' });
    const aceptar = screen.getByRole('button', { name: 'Aceptar' });

    aceptar.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(cerrar);

    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(aceptar);

    // Con el foco fuera del diálogo, Tab lo regresa al primero.
    screen.getByRole('button', { name: 'Fuera' }).focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(cerrar);
  });

  it('desde el panel (sin campos), Tab va al primero y Mayús+Tab al último', () => {
    render(<Pantalla campos={false} />, { container: raiz });
    abrir();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Cerrar' }));
    screen.getByRole('dialog').focus();
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Aceptar' }));
  });

  it('Escape cierra y devuelve el foco al disparador', () => {
    render(<Pantalla />, { container: raiz });
    const { disparador } = abrir();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(disparador);
  });

  it('el botón ✕ cierra y devuelve el foco al disparador', () => {
    render(<Pantalla />, { container: raiz });
    const { disparador } = abrir();
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(disparador);
  });

  it('no devuelve el foco si la pantalla ya lo movió a otro lado al cerrar', () => {
    function Movida() {
      const [abierto, setAbierto] = useState(true);
      return (
        <>
          <button type="button" id="destino">Destino</button>
          {abierto ? (
            <Modal
              title="Diálogo"
              onClose={() => {
                document.getElementById('destino')?.focus();
                setAbierto(false);
              }}
            >
              <p>Texto</p>
            </Modal>
          ) : null}
        </>
      );
    }
    render(<Movida />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Destino' }));
  });

  it('no roba el foco al re-renderizar con un onClose nuevo', () => {
    function Contador() {
      const [n, setN] = useState(0);
      return (
        // `onClose` es una función nueva en cada render (sin useCallback).
        <Modal title="Diálogo" onClose={() => undefined}>
          <TextInput aria-label="Nombre" />
          <TextInput aria-label="Correo" />
          <button type="button" onClick={() => setN(n + 1)}>Sumar {n}</button>
        </Modal>
      );
    }
    render(<Contador />);
    const correo = screen.getByLabelText('Correo');
    correo.focus();
    fireEvent.click(screen.getByRole('button', { name: 'Sumar 0' }));
    fireEvent.click(screen.getByRole('button', { name: 'Sumar 1' }));
    correo.focus();
    fireEvent.click(screen.getByRole('button', { name: 'Sumar 2' }));
    expect(screen.getByRole('button', { name: 'Sumar 3' })).toBeTruthy();
    // El clic no mueve el foco en jsdom: si el Modal re-enfocara, estaría en "Nombre" o en el panel.
    expect(document.activeElement).toBe(correo);
  });

  it('con un diálogo encima, solo el de arriba atiende Escape', () => {
    const cerrarAbajo = vi.fn();
    const cerrarArriba = vi.fn();
    render(
      <>
        <Modal title="Abajo" onClose={cerrarAbajo}><p>Abajo</p></Modal>
        <Modal title="Arriba" onClose={cerrarArriba}><p>Arriba</p></Modal>
      </>,
    );
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(cerrarArriba).toHaveBeenCalledTimes(1);
    expect(cerrarAbajo).not.toHaveBeenCalled();
  });
});

describe('Modal: describedBy', () => {
  it('se traduce en aria-describedby del role="dialog"', () => {
    render(<Pantalla describedBy="explica" />, { container: raiz });
    const { dialogo } = abrir();
    expect(dialogo.getAttribute('aria-describedby')).toBe('explica');
    expect(document.getElementById('explica')?.textContent).toBe('Explica la acción.');
  });

  it('sin describedBy no pone el atributo', () => {
    render(<Pantalla />, { container: raiz });
    const { dialogo } = abrir();
    expect(dialogo.hasAttribute('aria-describedby')).toBe(false);
  });

  it('ConfirmDialog liga su mensaje', () => {
    render(
      <ConfirmDialog title="Eliminar" message="Se borrará el área." onConfirm={() => undefined} onCancel={() => undefined} />,
    );
    const dialogo = screen.getByRole('dialog', { name: 'Eliminar' });
    const id = dialogo.getAttribute('aria-describedby');
    expect(id && document.getElementById(id)?.textContent).toBe('Se borrará el área.');
  });
});

describe('Modal: velo, ✕ y desplazamiento', () => {
  it('el velo usa el token (bg-overlay), sin color literal', () => {
    render(<Pantalla />, { container: raiz });
    const { dialogo } = abrir();
    const velo = dialogo.parentElement!;
    expect(velo.className).toContain('bg-overlay');
    expect(velo.className).not.toMatch(/bg-black/);
  });

  it('el botón ✕ tiene área de 48 px', () => {
    render(<Pantalla />, { container: raiz });
    abrir();
    const cerrar = screen.getByRole('button', { name: 'Cerrar' });
    expect(cerrar.className).toContain('min-w-12');
    expect(cerrar.className).toContain('min-h-12');
  });

  it('se pinta en un portal en body; la raíz queda bloqueada e inert, sin estilos inline', () => {
    render(<Pantalla />, { container: raiz });
    expect(raiz.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(false);
    const { dialogo, disparador } = abrir();
    expect(raiz.contains(dialogo)).toBe(false);
    expect(dialogo.parentElement!.parentElement).toBe(document.body);
    expect(raiz.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(true);
    expect(raiz.hasAttribute('inert')).toBe(true);
    expect(raiz.getAttribute('style')).toBeNull();
    expect(document.body.getAttribute('style')).toBeNull();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(raiz.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(false);
    expect(raiz.hasAttribute('inert')).toBe(false);
    // La raíz deja de ser `inert` antes de devolver el foco.
    expect(document.activeElement).toBe(disparador);
  });

  it('la regla de bloqueo cubre la raíz y los contenedores [data-desplazable] y gana a overflow-y-auto', async () => {
    const { readFileSync } = await import('node:fs');
    const { resolve } = await import('node:path');
    const css = readFileSync(resolve(import.meta.dirname, '../../src/styles/global.css'), 'utf8');
    expect(css).toMatch(/\.scroll-bloqueado\[data-desplazable\],\s*\.scroll-bloqueado \[data-desplazable\]\s*\{\s*overflow: hidden;/);
  });

  it('con dos diálogos, la clase y inert se quitan al cerrar el último', () => {
    const html = raiz;
    function Dos() {
      const [a, setA] = useState(true);
      const [b, setB] = useState(true);
      return (
        <>
          {a ? <Modal title="A" onClose={() => setA(false)}><p>A</p></Modal> : null}
          {b ? <Modal title="B" onClose={() => setB(false)}><p>B</p></Modal> : null}
        </>
      );
    }
    render(<Dos />, { container: raiz });
    expect(html.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(true);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog', { name: 'B' })).toBeNull();
    expect(html.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(true);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(html.classList.contains(CLASE_SCROLL_BLOQUEADO)).toBe(false);
    expect(html.hasAttribute('inert')).toBe(false);
  });
});

describe('Modal: hallazgos de auditor-accesibilidad (H3–H6)', () => {
  it('el nombre del diálogo viene del título con aria-labelledby', () => {
    render(<Pantalla />, { container: raiz });
    const { dialogo } = abrir();
    const id = dialogo.getAttribute('aria-labelledby');
    expect(dialogo.hasAttribute('aria-label')).toBe(false);
    expect(id && document.getElementById(id)?.tagName).toBe('H2');
  });

  it('ConfirmDialog ocupado: aria-disabled, ignora el clic y conserva el foco', () => {
    const confirmar = vi.fn();
    render(
      <ConfirmDialog title="Eliminar" message="Se borrará." onConfirm={confirmar} onCancel={() => undefined} busy />,
      { container: raiz },
    );
    const boton = screen.getByRole('button', { name: 'Eliminando…' });
    expect(boton.getAttribute('aria-disabled')).toBe('true');
    expect(boton.hasAttribute('disabled')).toBe(false);
    boton.focus();
    fireEvent.click(boton);
    expect(confirmar).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(boton);
  });

  it('ConfirmDialog libre: confirma con el clic', () => {
    const confirmar = vi.fn();
    render(
      <ConfirmDialog title="Eliminar" message="Se borrará." onConfirm={confirmar} onCancel={() => undefined} />,
      { container: raiz },
    );
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
    expect(confirmar).toHaveBeenCalledTimes(1);
  });

  it('los elementos ocultos, inert o en fieldset deshabilitado no rompen el ciclo', () => {
    render(
      <Modal
        title="Diálogo"
        onClose={() => undefined}
        footer={
          <>
            <button type="button">Aceptar</button>
            <button type="button" data-sin-caja="">Oculto por CSS</button>
            <div inert><button type="button">Inerte</button></div>
          </>
        }
      >
        <fieldset disabled><TextInput aria-label="Bloqueado" /></fieldset>
        <div data-sin-caja=""><TextInput aria-label="Sin caja" /></div>
        <TextInput aria-label="Visible" />
      </Modal>,
      { container: raiz },
    );
    // Foco inicial: el primer campo visible, no los ocultos.
    expect(document.activeElement).toBe(screen.getByLabelText('Visible'));
    const aceptar = screen.getByRole('button', { name: 'Aceptar' });
    aceptar.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Cerrar' }));
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(aceptar);
  });

  it('si focus() no mueve el foco, prueba con el siguiente', () => {
    render(<Pantalla />, { container: raiz });
    abrir();
    const cerrar = screen.getByRole('button', { name: 'Cerrar' });
    // Simula un elemento que rechaza el foco (p. ej. oculto en el último momento).
    vi.spyOn(cerrar, 'focus').mockImplementation(() => undefined);
    screen.getByRole('button', { name: 'Aceptar' }).focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(screen.getByLabelText('Nombre'));
  });

  it('Escape ya atendido (defaultPrevented) no cierra el diálogo', () => {
    const cerrar = vi.fn();
    render(
      <Modal title="Diálogo" onClose={cerrar}>
        <TextInput
          aria-label="Combo"
          onKeyDown={(event) => {
            if (event.key === 'Escape') event.preventDefault();
          }}
        />
      </Modal>,
      { container: raiz },
    );
    fireEvent.keyDown(screen.getByLabelText('Combo'), { key: 'Escape' });
    expect(cerrar).not.toHaveBeenCalled();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(cerrar).toHaveBeenCalledTimes(1);
  });

  it('si el disparador ya no existe, el foco va al <main> con tabIndex=-1', () => {
    function Fila() {
      const [abierto, setAbierto] = useState(false);
      const [fila, setFila] = useState(true);
      return (
        <main tabIndex={-1}>
          {fila ? <button type="button" onClick={() => setAbierto(true)}>Abrir</button> : null}
          {abierto ? (
            <Modal title="Diálogo" onClose={() => { setFila(false); setAbierto(false); }}>
              <p>Texto</p>
            </Modal>
          ) : null}
        </main>
      );
    }
    render(<Fila />, { container: raiz });
    abrir();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('button', { name: 'Abrir' })).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole('main'));
  });
});
