import { ButtonLink } from '@/components/form';
import { Brand } from '@/components/brand';
import { PageHeader } from '@/components/page-header';

/** 404 del frontend. Sustituye a templates/errors/404.html. */
export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center p-4">
      <div className="max-w-md text-center">
        <Brand size="lg" className="mb-6 items-center" />
        <p className="text-5xl font-semibold tabular-nums text-label">404</p>
        <PageHeader
          title="Página no encontrada"
          description="La dirección no existe o el recurso se ha movido."
          className="text-center sm:flex-col sm:items-center"
        />
        <div className="mt-6 flex justify-center">
          <ButtonLink href="/" variant="primary">
            Volver al inicio
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}
