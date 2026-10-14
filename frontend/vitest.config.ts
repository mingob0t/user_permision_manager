/**
 * Configuración de Vitest para el frontend (FNC-025).
 *
 * - Entorno jsdom para pruebas de componentes y del cliente de la API.
 * - JSX automático de React (tsconfig usa `jsx: preserve` para Next.js).
 * - Alias `@/*` igual que en tsconfig.
 */
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  esbuild: { jsx: 'automatic' },
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.{ts,tsx}'],
    restoreMocks: true,
    unstubGlobals: true,
  },
});
