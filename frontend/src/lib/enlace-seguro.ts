/**
 * Enlaces que la interfaz puede pintar en un `href` (SEG-24 del frontend, DIS-017).
 *
 * Misma regla de entrada que el backend (`platforms/validacion.py`, FNC-046):
 * solo `https://` con host y sin credenciales. El backend ya devuelve `null` las
 * URL guardadas que no cumplen; esto es la defensa en el cliente.
 */

const ESQUEMA_PERMITIDO = 'https:';

/** El enlace si es `https://` válido; si no, `null`. */
export function enlaceSeguro(url: string | null | undefined): string | null {
  if (!url) return null;
  const valor = url.trim();
  if (!valor || /\s/.test(valor)) return null;
  try {
    const partes = new URL(valor);
    if (partes.protocol !== ESQUEMA_PERMITIDO || !partes.hostname) return null;
    if (partes.username || partes.password) return null;
    return valor;
  } catch {
    return null;
  }
}
