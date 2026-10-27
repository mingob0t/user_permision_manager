'use client';

/**
 * Selector de tema (FNC-032, FNC-123): aplica la clase en `<html>`, la guarda en el
 * navegador (respaldo y sin destello) y la guarda en la cuenta del usuario. Al
 * iniciar sesión manda el tema de la cuenta. Si el guardado en la cuenta falla,
 * se avisa y la vista no se revierte.
 */

import { useEffect, useState } from 'react';
import { Select } from './form';
import { useSession } from './session-provider';
import { useToast } from './toast';
import { api } from '@/lib/api';
import {
  TEMAS, TEMA_POR_DEFECTO, aplicarTemaDeCuenta, elegirTema, restaurarTema,
} from '@/lib/tema';

export function ThemeSelector() {
  const [tema, setTema] = useState(TEMA_POR_DEFECTO);
  const { session } = useSession();
  const { avisar } = useToast();
  const temaDeCuenta = session?.preferences?.theme;

  // El script de `<head>` ya puso la clase; aquí se sincroniza el control.
  useEffect(() => { setTema(restaurarTema()); }, []);

  // El tema de la cuenta manda sobre el del navegador.
  useEffect(() => {
    const aplicado = aplicarTemaDeCuenta(temaDeCuenta);
    if (aplicado) setTema(aplicado);
  }, [temaDeCuenta]);

  async function elegir(id: string) {
    setTema(id);
    elegirTema(id);
    try {
      await api.savePreferences({ theme: id });
    } catch {
      avisar('error', 'No se pudo guardar el tema en tu cuenta. Rige solo en este navegador.');
    }
  }

  return (
    <div className="w-28 min-w-0 sm:w-40">
      <Select
        aria-label="Tema de la interfaz"
        value={tema}
        onChange={(e) => { void elegir(e.target.value); }}
      >
        {TEMAS.map((t) => <option key={t.id} value={t.id}>{t.etiqueta}</option>)}
      </Select>
    </div>
  );
}
