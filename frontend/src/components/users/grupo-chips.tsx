/** Grupo de chips con `fieldset`/`legend` (DIS-045). */

import { useId } from 'react';

/**
 * Grupo de chips: la leyenda, con el estilo de la etiqueta de
 * `Field`, nombra al grupo sin asociarse al primer chip como haría un `<label>`.
 */
export function GrupoChips({
  legend,
  hint,
  children,
}: {
  legend: string;
  hint?: string;
  children: React.ReactNode;
}) {
  const pistaId = useId();
  return (
    <fieldset aria-describedby={hint ? pistaId : undefined}>
      <legend className="mb-2 block text-xs font-black uppercase tracking-[0.1em] text-label">
        {legend}
      </legend>
      {children}
      {hint ? <p id={pistaId} className="mt-1.5 text-xs text-label/85">{hint}</p> : null}
    </fieldset>
  );
}
