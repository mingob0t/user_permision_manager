import type { Metadata } from 'next';
import { RAIZ_APP_ID } from '@/lib/raiz-app';
// El orden importa: primero los tokens del portal, que definen las variables;
// después sus clases; y al final las utilidades de Tailwind, que las consumen.
import '../styles/tokens.css';
import '../styles/global.css';
import '../styles/components.css';
import './globals.css';

export const metadata: Metadata = {
  title: 'Nexus',
  description: 'Catálogo centralizado de plataformas',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body>
        {/* DIS-044: `html` y `body` no se desplazan (global.css); lo hace esta raíz
            (páginas sin `AppShell`) o el `<main>` de `AppShell`. Los diálogos se
            pintan fuera, en un portal, y la raíz se marca `inert` mientras están abiertos. */}
        <div id={RAIZ_APP_ID} data-desplazable="" className="h-dvh overflow-y-auto">
          {children}
        </div>
      </body>
    </html>
  );
}
