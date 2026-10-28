'use client';

import { Button, ButtonLink } from '@/components/form';
import { Brand } from '@/components/brand';
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
        <Brand size="lg" className="mb-6 items-center" />
        <p className="text-5xl font-semibold tabular-nums text-label">500</p>
        <h1 className="mt-3 text-xl font-medium">Algo ha fallado</h1>
        <p className="mt-2 text-sm text-label">
          No se pudo completar la operación. Vuelve a intentarlo; si persiste,
          avisa al administrador.
        </p>
        <div className="mt-6 flex justify-center gap-2">
          <Button variant="primary" onClick={reset}>
            Reintentar
          </Button>
          <ButtonLink href="/" variant="secondary">
            Ir al inicio
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}
