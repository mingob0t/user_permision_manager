import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import React, { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Tabs, TabPanel, destinoPorTecla } from '@/components/tabs';
import { ToggleChip } from '@/components/toggle-chip';

afterEach(() => {
  cleanup();
});

describe('destinoPorTecla', () => {
  it('calcula la siguiente pestaña cíclica con ArrowRight', () => {
    expect(destinoPorTecla('ArrowRight', 0, 3)).toBe(1);
    expect(destinoPorTecla('ArrowRight', 2, 3)).toBe(0);
  });

  it('calcula la pestaña previa cíclica con ArrowLeft', () => {
    expect(destinoPorTecla('ArrowLeft', 1, 3)).toBe(0);
    expect(destinoPorTecla('ArrowLeft', 0, 3)).toBe(2);
  });

  it('calcula inicio y fin con Home y End', () => {
    expect(destinoPorTecla('Home', 2, 3)).toBe(0);
    expect(destinoPorTecla('End', 0, 3)).toBe(2);
  });

  it('devuelve null para otras teclas o total inválido', () => {
    expect(destinoPorTecla('Enter', 0, 3)).toBeNull();
    expect(destinoPorTecla('ArrowRight', 0, 0)).toBeNull();
  });
});

describe('Componente Tabs', () => {
  const tabs = [
    { id: 'tab1', label: 'Primera' },
    { id: 'tab2', label: 'Segunda' },
    { id: 'tab3', label: 'Tercera' },
  ];

  function TestHarness({ inicial = 'tab1' }: { inicial?: string }) {
    const [tab, setTab] = useState(inicial);
    return (
      <div>
        <Tabs tabs={tabs} value={tab} onChange={setTab} ariaLabel="Prueba de pestañas" />
        <TabPanel id={`${tab}-panel`} tabId={`${tab}-tab`}>
          Contenido de {tab}
        </TabPanel>
      </div>
    );
  }

  it('pinta el contenedor tablist y las pestañas con role="tab"', () => {
    render(<TestHarness />);
    const tablist = screen.getByRole('tablist', { name: 'Prueba de pestañas' });
    expect(tablist).toBeTruthy();

    const buttons = screen.getAllByRole('tab');
    expect(buttons).toHaveLength(3);
    expect(buttons[0].getAttribute('aria-selected')).toBe('true');
    expect(buttons[0].tabIndex).toBe(0);
    expect(buttons[1].getAttribute('aria-selected')).toBe('false');
    expect(buttons[1].tabIndex).toBe(-1);
  });

  it('cambia de pestaña al hacer clic y actualiza aria-selected y roving tabIndex', () => {
    render(<TestHarness />);
    const buttons = screen.getAllByRole('tab');

    fireEvent.click(buttons[1]);
    expect(buttons[0].getAttribute('aria-selected')).toBe('false');
    expect(buttons[0].tabIndex).toBe(-1);
    expect(buttons[1].getAttribute('aria-selected')).toBe('true');
    expect(buttons[1].tabIndex).toBe(0);
    expect(screen.getByText('Contenido de tab2')).toBeTruthy();
  });

  it('navega cíclicamente con el teclado (ArrowRight y ArrowLeft)', () => {
    render(<TestHarness />);
    const buttons = screen.getAllByRole('tab');

    buttons[0].focus();
    fireEvent.keyDown(buttons[0], { key: 'ArrowRight' });
    expect(buttons[1].getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(buttons[1]);

    fireEvent.keyDown(buttons[1], { key: 'ArrowLeft' });
    expect(buttons[0].getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(buttons[0]);
  });

  it('navega al primer y último elemento con Home y End', () => {
    render(<TestHarness />);
    const buttons = screen.getAllByRole('tab');

    buttons[0].focus();
    fireEvent.keyDown(buttons[0], { key: 'End' });
    expect(buttons[2].getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(buttons[2]);

    fireEvent.keyDown(buttons[2], { key: 'Home' });
    expect(buttons[0].getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(buttons[0]);
  });

  it('no activa pestañas deshabilitadas', () => {
    const tabsConDeshabilitada = [
      { id: 'tab1', label: 'Primera' },
      { id: 'tab2', label: 'Segunda', disabled: true },
    ];
    const onChange = vi.fn();
    render(<Tabs tabs={tabsConDeshabilitada} value="tab1" onChange={onChange} />);

    const buttons = screen.getAllByRole('tab');
    expect(buttons[1].hasAttribute('disabled')).toBe(true);
    fireEvent.click(buttons[1]);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('TabPanel tiene role="tabpanel", foco por teclado (tabIndex=0) y enlazado accesible', () => {
    render(
      <TabPanel id="panel-1" tabId="tab-1">
        Panel de prueba
      </TabPanel>,
    );
    const panel = screen.getByRole('tabpanel');
    expect(panel.tabIndex).toBe(0);
    expect(panel.getAttribute('aria-labelledby')).toBe('tab-1');
    expect(panel.id).toBe('panel-1');
  });
});

describe('Componente ToggleChip', () => {
  it('soporta variante chip con aria-pressed y distinción no cromática', () => {
    const { rerender } = render(<ToggleChip pressed={false}>Etiqueta</ToggleChip>);
    const chip = screen.getByRole('button', { name: 'Etiqueta' });
    expect(chip.getAttribute('aria-pressed')).toBe('false');
    expect(chip.className).toContain('min-h-12');
    expect(chip.className).toContain('min-w-12');
    expect(chip.className).toContain('rounded-full');

    rerender(<ToggleChip pressed={true}>Etiqueta</ToggleChip>);
    expect(chip.getAttribute('aria-pressed')).toBe('true');
    expect(chip.className).toContain('font-medium');
    expect(chip.className).toContain('border-primary');
  });

  it('soporta variante icon para botones de alternancia (favorito)', () => {
    render(
      <ToggleChip variant="icon" pressed={true} aria-label="Favorito">
        ★
      </ToggleChip>,
    );
    const btn = screen.getByRole('button', { name: 'Favorito' });
    expect(btn.getAttribute('aria-pressed')).toBe('true');
    expect(btn.className).toContain('min-h-12');
    expect(btn.className).toContain('min-w-12');
    expect(btn.className).toContain('rounded');
  });

  it('llama a onPressedChange y onClick al pulsar', () => {
    const onPressedChange = vi.fn();
    const onClick = vi.fn();
    render(
      <ToggleChip pressed={false} onPressedChange={onPressedChange} onClick={onClick}>
        Etiqueta
      </ToggleChip>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Etiqueta' }));
    expect(onPressedChange).toHaveBeenCalledWith(true);
    expect(onClick).toHaveBeenCalled();
  });

  it('ignora clics cuando está deshabilitado', () => {
    const onPressedChange = vi.fn();
    render(
      <ToggleChip pressed={false} disabled onPressedChange={onPressedChange}>
        Etiqueta
      </ToggleChip>,
    );
    const chip = screen.getByRole('button', { name: 'Etiqueta' });
    fireEvent.click(chip);
    expect(onPressedChange).not.toHaveBeenCalled();
  });
});
