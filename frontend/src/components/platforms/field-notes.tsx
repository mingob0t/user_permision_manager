/**
 * Pista y error de un campo del formulario de plataforma (DIS-017), fuera del
 * `<label>` de `Field` y ligados al control con `aria-describedby`. Mismo
 * patrón que `areas/area-form.tsx` (DIS-016); sin tocar `form.tsx`.
 */

/** Error de un campo; `null` si no hay mensaje. */
export function FieldErrorNote({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return (
    <span id={id} className="mt-1.5 block text-xs font-bold text-error">
      {message}
    </span>
  );
}

/** Pista o nota de un campo (formato, motivo de que esté deshabilitado). */
export function FieldHint({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <span id={id} className="mt-1.5 block text-xs text-label">
      {children}
    </span>
  );
}

/**
 * Atributos de un control: `aria-describedby` con las notas presentes y
 * `aria-invalid` si hay error. Cada entrada es `[id, presente]`.
 */
export function describedBy(error: [string, unknown], ...notas: [string, unknown][]) {
  const ids = [...notas, error].filter(([, presente]) => Boolean(presente)).map(([id]) => id);
  return {
    'aria-describedby': ids.length > 0 ? ids.join(' ') : undefined,
    'aria-invalid': error[1] ? true : undefined,
  };
}

/** Enfoca el primer control con error, en el orden del formulario. */
export function focusFirstError(order: [campo: string, controlId: string][], errors: Record<string, string>) {
  const primero = order.find(([campo]) => errors[campo]);
  if (primero) document.getElementById(primero[1])?.focus();
}
