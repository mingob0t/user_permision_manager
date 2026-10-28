import { ButtonLink } from '@/components/form';
import { Brand } from '@/components/brand';

/** 404 del frontend. Sustituye a templates/errors/404.html. */
export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center p-4">
      <div className="max-w-md text-center">
        <Brand size="lg" className="mb-6 items-center" />
        <p className="text-5xl font-semibold tabular-nums text-label">404</p>
        <h1 className="mt-3 text-xl font-medium">Página no encontrada</h1>
        <p className="mt-2 text-sm text-label">
          La dirección no existe o el recurso se ha movido.
        </p>
        <div className="mt-6 flex justify-center">
          <ButtonLink href="/" variant="primary">
            Volver al inicio
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}
