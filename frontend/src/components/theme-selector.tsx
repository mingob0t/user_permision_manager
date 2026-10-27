'use client';

/** Selector de tema (FNC-032): aplica la clase en `<html>` y la guarda por dispositivo. */

import { useEffect, useState } from 'react';
import { Select } from './form';
import { TEMAS, TEMA_POR_DEFECTO, elegirTema, restaurarTema } from '@/lib/tema';

export function ThemeSelector() {
  const [tema, setTema] = useState(TEMA_POR_DEFECTO);

  // El script de `<head>` ya puso la clase; aquí se sincroniza el control.
  useEffect(() => { setTema(restaurarTema()); }, []);

  return (
    <div className="w-28 min-w-0 sm:w-40">
      <Select
        aria-label="Tema de la interfaz"
        value={tema}
        onChange={(e) => { setTema(e.target.value); elegirTema(e.target.value); }}
      >
        {TEMAS.map((t) => <option key={t.id} value={t.id}>{t.etiqueta}</option>)}
      </Select>
    </div>
  );
}
