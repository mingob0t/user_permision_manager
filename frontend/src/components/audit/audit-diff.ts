/**
 * Antes y después de un registro de auditoría como lista de campos (DIS-020,
 * F-AUD-03; contrato `auditoria.md`: `before`/`after` objeto o null).
 *
 * Todo valor se convierte a texto plano; la interfaz lo pinta como texto
 * (React lo escapa), nunca como HTML.
 */

export interface CampoCambio {
  campo: string;
  antes: string;
  despues: string;
  cambio: boolean;
}

/** Valor ausente o null. */
export const SIN_VALOR = '—';

/** Un valor del JSON como texto legible. */
export function valorLegible(valor: unknown): string {
  if (valor === undefined || valor === null || valor === '') return SIN_VALOR;
  if (typeof valor === 'boolean') return valor ? 'Sí' : 'No';
  if (typeof valor === 'string') return valor;
  if (typeof valor === 'number' || typeof valor === 'bigint') return String(valor);
  try {
    return JSON.stringify(valor);
  } catch {
    return SIN_VALOR;
  }
}

/**
 * Campos de `before` y `after`, en el orden en que aparecen (primero los de
 * `before`). Vacío si ambos son null (p. ej. para el usuario, que los recibe en null).
 */
export function compararCampos(
  before: Record<string, unknown> | null,
  after: Record<string, unknown> | null,
): CampoCambio[] {
  const antes = before ?? {};
  const despues = after ?? {};
  const campos = [...new Set([...Object.keys(antes), ...Object.keys(despues)])];
  return campos.map((campo) => {
    const a = valorLegible(Object.hasOwn(antes, campo) ? antes[campo] : undefined);
    const d = valorLegible(Object.hasOwn(despues, campo) ? despues[campo] : undefined);
    return { campo, antes: a, despues: d, cambio: a !== d };
  });
}
