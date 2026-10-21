/** Arma la ruta con su cadena de consulta, omitiendo valores vacíos. */
export function withQuery(
  path: string,
  params: Record<string, string | number | boolean | null | undefined> = {},
): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue;
    query.set(key, String(value));
  }
  const suffix = query.toString();
  return suffix ? `${path}?${suffix}` : path;
}

/** Cuerpo JSON de una escritura (el contrato pide JSON, también vacío). */
export function jsonBody(method: 'POST' | 'PUT' | 'DELETE', body: unknown = {}): RequestInit {
  return { method, body: JSON.stringify(body) };
}
