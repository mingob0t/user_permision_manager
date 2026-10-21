/**
 * Fecha de los contratos (ISO 8601 UTC con `Z`) para mostrar en pantalla
 * (DIS-014), en la zona horaria del navegador.
 */

/** Idioma de las fechas de la interfaz. */
export const LOCALE_FECHAS = 'es-MX';

const FORMATO = new Intl.DateTimeFormat(LOCALE_FECHAS, {
  dateStyle: 'medium',
  timeStyle: 'short',
});

/** Sin valor o inválida: "—". */
export function formatearFecha(iso: string | null | undefined): string {
  if (!iso) return '—';
  const fecha = new Date(iso);
  return Number.isNaN(fecha.getTime()) ? '—' : FORMATO.format(fecha);
}
