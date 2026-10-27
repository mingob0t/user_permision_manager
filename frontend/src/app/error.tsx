'use client';

import Link from 'next/link';
import { useEffect } from 'react';

/** Error de renderizado. Sustituye a templates/errors/500.html. */
export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // El detalle queda en la consola; la página no lo muestra para no filtrar
    // trazas internas al usuario.
    console.error(error);
  }, [error]);

  return (
    <div className="grid min-h-screen place-items-center p-4">
      <div className="max-w-md text-center">
        <p className="text-5xl font-semibold tabular-nums text-label">500</p>
        <h1 className="mt-3 text-xl font-medium">Algo ha fallado</h1>
        <p className="mt-2 text-sm text-label">
          No se pudo completar la operación. Vuelve a intentarlo; si persiste,
          avisa al administrador.
        </p>
        <div className="mt-6 flex justify-center gap-2">
          <button
            type="button"
            onClick={reset}
            className="inline-flex min-h-12 items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Reintentar
          </button>
          <Link
            href="/"
            className="inline-flex min-h-12 items-center justify-center rounded-lg border border-panel-border px-4 py-2 text-sm text-label outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Ir al inicio
          </Link>
        </div>
      </div>
    </div>
  );
}
