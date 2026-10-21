/**
 * Rutas de Auditoría (DIS-020): la general y los historiales por usuario y
 * por plataforma. Se usan desde Usuarios e Inventario.
 */

export const RUTA_AUDITORIA = '/audit';

export function rutaHistorialUsuario(userId: number): string {
  return `${RUTA_AUDITORIA}/users/${userId}`;
}

export function rutaHistorialPlataforma(platformId: number): string {
  return `${RUTA_AUDITORIA}/platforms/${platformId}`;
}

// Mismo tope que el backend para ids (`MAX_DIGITOS_ENTERO`, FNC-060).
const ID_VALIDO = /^[1-9]\d{0,8}$/;

/** Id de la ruta (`[id]`) como entero ≥ 1, o `null` si no es válido. */
export function idDeRuta(valor: string): number | null {
  return ID_VALIDO.test(valor) ? Number(valor) : null;
}
