import type { NextConfig } from 'next';
import { rewritesDeDesarrollo } from './rewrites-dev';

/**
 * El backend Flask es la única fuente de datos y de sesión.
 *
 * Solo en desarrollo (`NODE_ENV=development`) `rewrites` reenvía /api/* a
 * Flask para que el navegador vea un mismo origen y la cookie viaje sin CORS.
 * `next build` y `next start` no generan ningún rewrite: en producción es
 * nginx quien enruta (FNC-005, FNC-118).
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return rewritesDeDesarrollo(process.env);
  },
};

export default nextConfig;
