/**
 * Raíz de la aplicación (DIS-044): el `div` de `app/layout.tsx` que envuelve
 * todas las páginas. Es el contenedor que se desplaza en las páginas sin
 * `AppShell` (login, salida, errores) y el que se marca `inert` mientras hay
 * un diálogo o el menú móvil abiertos (`useScrollLock`). Sin `'use client'`:
 * `layout.tsx` es un componente de servidor y lee el valor.
 */
export const RAIZ_APP_ID = 'raiz-app';

/**
 * Los contenedores que se desplazan llevan `data-desplazable` (la raíz y el
 * `<main>` de `AppShell`); la regla `.scroll-bloqueado` de `global.css` los bloquea.
 */
