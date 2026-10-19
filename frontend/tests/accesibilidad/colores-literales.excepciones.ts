/**
 * Colores literales que YA existían en `src/components` y `src/app` (FNC-025).
 *
 * Es un tope por archivo: la prueba falla si un archivo tiene más literales que
 * aquí (deuda nueva) y también si tiene menos (alguien corrigió: hay que bajar
 * el número para que el tope no vuelva a subir). Medido el 2026-10-13.
 *
 * - `hex` / `funcion`: `#rrggbb` o `rgb()/hsl()` con números. Los corrige DIS-012.
 * - `paleta`: clases Tailwind de paleta fija (`text-red-600`, `bg-black/60`...).
 *   Las corrige DIS-002 con tokens semánticos (y DIS-012 donde aplica).
 */

export interface TopeLiterales {
  hex: number;
  funcion: number;
  paleta: number;
  tarea: string;
}

export const EXCEPCIONES: Record<string, TopeLiterales> = {
  'app/error.tsx': { hex: 0, funcion: 0, paleta: 1, tarea: 'DIS-004 / DIS-012' },
  'app/not-found.tsx': { hex: 0, funcion: 0, paleta: 1, tarea: 'DIS-004 / DIS-012' },
  'components/areas-list.tsx': { hex: 2, funcion: 0, paleta: 3, tarea: 'DIS-002 / DIS-012' },
  'components/dashboard.tsx': { hex: 1, funcion: 0, paleta: 0, tarea: 'DIS-003 / DIS-012' },
  'components/form.tsx': { hex: 0, funcion: 0, paleta: 1, tarea: 'DIS-012' },
  'components/notifications-list.tsx': { hex: 0, funcion: 0, paleta: 9, tarea: 'DIS-002' },
  'components/platform-admin.tsx': { hex: 0, funcion: 0, paleta: 5, tarea: 'DIS-002 / DIS-012' },
  'components/platform-card.tsx': { hex: 0, funcion: 0, paleta: 1, tarea: 'DIS-002' },
  'components/settings-panel.tsx': { hex: 2, funcion: 0, paleta: 8, tarea: 'DIS-002 / DIS-012' },
  'components/users-list.tsx': { hex: 0, funcion: 0, paleta: 3, tarea: 'DIS-002' },
};
