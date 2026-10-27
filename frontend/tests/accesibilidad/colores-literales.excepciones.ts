/**
 * Colores literales que se aceptan en `src/components`, `src/app` y los CSS de
 * `src/styles` (excepto `tokens.css`, donde viven los valores). Es un tope por
 * archivo: la prueba falla si un archivo tiene más literales que aquí (deuda
 * nueva) y también si tiene menos (alguien corrigió: hay que bajar el número).
 *
 * - `hex` / `funcion`: `#rrggbb` o `rgb()/hsl()` con números.
 * - `paleta`: clases Tailwind de paleta fija (`text-red-600`, `bg-black/60`...).
 * - `nombre`: nombres de color (`white`, `black`...) en declaraciones CSS.
 *
 * Historial: DIS-002 quitó los de estado; DIS-038 cambió `bg-black/60` del velo
 * por `--color-overlay`; DIS-009 y DIS-012 (2026-10-27) dejaron en 0 los CSS y
 * `text-white` de `app/error.tsx` y `app/not-found.tsx` (ahora `text-on-primary`).
 */

export interface TopeLiterales {
  hex: number;
  funcion: number;
  paleta: number;
  nombre?: number;
  tarea: string;
}

export const EXCEPCIONES: Record<string, TopeLiterales> = {
  // DIS-012 (decisión del orquestador, pendiente de validar): no es estilo, es un
  // dato. El valor de `<input type="color">` exige `#rrggbb` y estos son los
  // valores por defecto de `Settings.bg_color` / `text_color` (el backend usa
  // `#0f172a` en `app/modules/settings/models.py`). No se pasan por un token
  // porque el usuario los elige y se guardan en la base de datos.
  'components/settings-panel.tsx': { hex: 2, funcion: 0, paleta: 0, tarea: 'DIS-012 (dato, no estilo)' },
};
