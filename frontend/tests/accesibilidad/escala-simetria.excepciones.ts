/**
 * Excepciones de simetría (DIS-072): clases de espaciado, alturas o anchos
 * fuera de la escala 8pt o medidas arbitrarias heredadas que serán migradas
 * en bloques C1–D2.
 *
 * Cada archivo tiene un contador estricto: no puede aumentar; solo puede reducirse.
 */
export interface ExcepcionSimetria {
  cantidad: number;
  tarea: string;
  motivo: string;
}

export const EXCEPCIONES_SIMETRIA: Record<string, ExcepcionSimetria> = {
  // 0 excepciones: 100% de componentes y pantallas usan tokens y escala canónica 8pt (DIS-067).
};

