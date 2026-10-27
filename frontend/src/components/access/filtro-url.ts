/**
 * Filtros que llegan por la URL (DIS-036): los enlaces del Inicio abren la
 * pantalla ya filtrada (`?status=fallido`, `?tab=accesos`). Se leen una vez al
 * montar; un valor que no es de la lista se ignora y la pantalla usa su valor
 * por defecto. Solo frontend: el backend recibe el filtro como siempre.
 */

/** `valor` si es uno de los permitidos; si no, `undefined`. */
export function valorPermitido<T extends string>(
  valor: string | null | undefined,
  permitidos: readonly T[],
): T | undefined {
  return permitidos.find((permitido) => permitido === valor);
}

/** Ruta con su consulta (`/requests?tab=accesos&status=fallido`), sin parámetros vacíos. */
export function rutaConFiltro(ruta: string, consulta: Record<string, string>): string {
  const params = new URLSearchParams(consulta);
  const texto = params.toString();
  return texto ? `${ruta}?${texto}` : ruta;
}
