import Link from 'next/link';

/** 404 del frontend. Sustituye a templates/errors/404.html. */
export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center p-4">
      <div className="max-w-md text-center">
        <p className="text-5xl font-semibold tabular-nums text-label">404</p>
        <h1 className="mt-3 text-xl font-medium">Página no encontrada</h1>
        <p className="mt-2 text-sm text-label">
          La dirección no existe o el recurso se ha movido.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex min-h-12 items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}
