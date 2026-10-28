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
  'components/toast.tsx': {
    cantidad: 1,
    tarea: 'DIS-074',
    motivo: 'z-[60] arbitrario heredado en contenedor de toast; será reemplazado en DIS-074',
  },
  'components/filter-bar.tsx': {
    cantidad: 1,
    tarea: 'DIS-069',
    motivo: 'min-w-56 fuera de escala en FilterBar; será normalizado en DIS-069',
  },
  'components/data-table.tsx': {
    cantidad: 1,
    tarea: 'DIS-071',
    motivo: 'min-w-[44rem] heredado en tabla de datos; será normalizado a escala en DIS-071',
  },
};
