'use client';

/** Cierre de sesión: avisa a Flask y, con SSO, salta al cierre de Authelia. */

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card } from './ui';

export function LogoutView() {
  const [done, setDone] = useState(false);

  useEffect(() => {
    let active = true;
    api.logout()
      .then((result) => {
        if (!active) return;
        // Con SSO hay que cerrar también en Authelia, o volvería a entrar solo.
        if (result.redirect) {
          window.location.href = result.redirect;
          return;
        }
        setDone(true);
      })
      .catch(() => {
        if (active) setDone(true);
      });
    return () => { active = false; };
  }, []);

  return (
    <div className="grid min-h-screen place-items-center p-4">
      <Card className="w-full max-w-sm text-center">
        <p className="font-medium">
          {done ? 'Sesión cerrada' : 'Cerrando sesión…'}
        </p>
        {done ? (
          <a
            href="/login"
            className="mt-3 inline-flex min-h-12 min-w-12 items-center text-sm text-primary-text hover:underline outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Volver a iniciar sesión
          </a>
        ) : null}
      </Card>
    </div>
  );
}
