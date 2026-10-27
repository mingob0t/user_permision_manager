/**
 * Región `polite` solo para lectores de pantalla (DIS-050). Se monta siempre,
 * aunque esté vacía, para que el lector detecte el cambio de texto.
 * Se alimenta con `useCambiosDeEstado`.
 */
export function RegionDeAnuncios({ mensaje }: { mensaje: string }) {
  return (
    <div aria-live="polite" aria-atomic="true" data-region-anuncios className="sr-only">
      {mensaje}
    </div>
  );
}
