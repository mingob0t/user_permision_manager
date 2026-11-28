'use client';

/**
 * Lista de navegación con secciones, iconos y contador (DIS-078). La usan la barra lateral
 * (expandida o colapsada) y el cajón móvil (DIS-025). Colapsada: solo iconos, con el nombre en
 * `aria-label` y `title`; el activo se marca con `aria-current`, los tokens `--color-activo-*` y una barra lateral (DIS-085:
 * no depende solo del color).
 */

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Icono } from '../icono';
import { useSession } from '../session-provider';
import { entradaDeRuta, seccionesVisibles } from './nav-items';
import {
  ModalTransicionPortal,
  guardarOmitirModalPortal,
  leerOmitirModalPortal,
} from './modal-transicion-portal';

/** «1 pendiente» / «2 pendientes». */
function textoPendientes(n: number): string {
  return `${n} ${n === 1 ? 'pendiente' : 'pendientes'}`;
}

export interface NavPrincipalProps {
  onNavigate?: () => void;
  colapsada?: boolean;
  /** Contador por `href` (p. ej. aprobaciones pendientes); solo se muestra si es mayor que cero. */
  contadores?: Readonly<Record<string, number>>;
  /** Aplica los tokens específicos del menú lateral oscuro (por defecto true). */
  enBarraLateral?: boolean;
}

function useSafeRouter(): { push: (href: string) => void } | null {
  try {
    return useRouter();
  } catch {
    return null;
  }
}

export function NavPrincipal({
  onNavigate,
  colapsada = false,
  contadores = {},
  enBarraLateral = true,
}: NavPrincipalProps) {
  const { session } = useSession();
  const pathname = usePathname();
  const router = useSafeRouter();
  const [modalPortalAbierto, setModalPortalAbierto] = useState(false);

  if (!session) return null;

  const alHacerClicItem = (
    event: React.MouseEvent<HTMLAnchorElement>,
    href: string
  ) => {
    if (href === '/platforms' && pathname !== '/platforms') {
      const omitir = leerOmitirModalPortal();
      if (!omitir) {
        event.preventDefault();
        setModalPortalAbierto(true);
        return;
      }
    }
    onNavigate?.();
  };

  const handleConfirmarTransicion = (omitirSiguientes: boolean) => {
    if (omitirSiguientes) {
      guardarOmitirModalPortal(true);
    }
    setModalPortalAbierto(false);
    onNavigate?.();
    if (router) {
      router.push('/platforms');
    } else if (typeof window !== 'undefined') {
      window.location.assign('/platforms');
    }
  };

  const handleCancelarTransicion = () => {
    setModalPortalAbierto(false);
  };

  return (
    <nav className="flex flex-col gap-0.5" aria-label="Principal">
      {seccionesVisibles(session.permissions).map(({ seccion, entradas }, indice) => (
        <div key={seccion} className="flex flex-col gap-0.5">
          {colapsada ? (
            indice > 0 ? (
              <hr className={`mx-3 my-2 ${enBarraLateral ? 'border-barra-lateral-borde' : 'border-borde-sutil'}`} />
            ) : null
          ) : (
            <p
              className={`px-3 pb-2 text-xs font-semibold uppercase tracking-wide ${
                enBarraLateral ? 'text-barra-lateral-secundario' : 'text-texto-secundario'
              } ${indice > 0 ? 'pt-5' : 'pt-1'}`}
            >
              {seccion}
            </p>
          )}
          {entradas.map((item) => {
            // DIS-163: también activo en sus subrutas (`/approvals/historial`), como las migas.
            const activo = entradaDeRuta(pathname)?.href === item.href;
            const contador = contadores[item.href] ?? 0;
            const nombre = contador > 0 ? `${item.label}, ${textoPendientes(contador)}` : item.label;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={activo ? 'page' : undefined}
                aria-label={colapsada ? nombre : undefined}
                title={colapsada ? nombre : undefined}
                onClick={(e) => alHacerClicItem(e, item.href)}
                className={`relative flex min-h-11 items-center gap-3 rounded-control px-3.5 text-sm outline-none transition-colors focus-visible:ring-2 ${
                  enBarraLateral ? 'focus-visible:ring-barra-lateral-foco' : 'focus-visible:ring-primary'
                } ${
                  colapsada ? 'justify-center' : ''
                } ${
                  activo
                    ? 'bg-activo-fondo font-semibold text-activo-texto shadow-xs'
                    : enBarraLateral
                      ? 'font-medium text-barra-lateral-nav hover:bg-barra-lateral-hover hover:text-barra-lateral-texto active:bg-barra-lateral-presionado'
                      : 'font-medium text-navegacion hover:bg-surface-container hover:text-body-text active:bg-surface-container'
                }`}
              >
                {activo ? (
                  <span
                    aria-hidden="true"
                    className="absolute inset-y-2 left-0 w-1 rounded-pastilla bg-activo-texto"
                  />
                ) : null}
                <Icono nombre={item.icono} />
                <span className={colapsada ? 'sr-only' : 'min-w-0 flex-1 truncate'}>{item.label}</span>
                {contador > 0 ? (
                  <span
                    className={`flex h-5 min-w-5 items-center justify-center rounded-pastilla bg-error-solid px-1.5 text-xs font-bold text-on-error ${
                      colapsada ? 'absolute right-1.5 top-1' : ''
                    }`}
                  >
                    <span aria-hidden="true">{contador}</span>
                    <span className="sr-only">{`, ${textoPendientes(contador)}`}</span>
                  </span>
                ) : null}
              </Link>
            );
          })}
        </div>
      ))}
      {modalPortalAbierto ? (
        <ModalTransicionPortal
          abierto={modalPortalAbierto}
          onConfirm={handleConfirmarTransicion}
          onCancel={handleCancelarTransicion}
        />
      ) : null}
    </nav>
  );
}
