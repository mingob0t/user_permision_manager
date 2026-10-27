/**
 * Parámetros por tipo de conector (DIS-042; contrato `conectores-y-ejecuciones.md`
 * 1.4: `api` FNC-051, `ssh` FNC-052, `bd` FNC-053).
 *
 * - Cada campo tiene una clave con puntos (`otorgar.metodo`) que se arma como
 *   objeto anidado al enviar. El servidor valida el esquema cerrado; aquí solo
 *   se anticipa lo evidente y se marca el campo si responde `params.<ruta>`.
 * - Sin secretos: el usuario y el secreto salen de la credencial del gestor
 *   (ADR-005). `huellas` son huellas públicas de la llave del host.
 * - Sin SQL libre ni marcas de usuario: las marcas son datos del servidor.
 */

import type { Connector, ConnectorType } from '@/lib/access/types';

export type TipoCampo = 'texto' | 'area' | 'select' | 'lista' | 'enteros' | 'entero' | 'json';

export interface CampoParametro {
  /** Ruta con puntos dentro de `params` (`base_path`, `otorgar.ruta`). */
  clave: string;
  etiqueta: string;
  pista: string;
  tipo?: TipoCampo;
  grupo?: GrupoId;
  obligatorio?: boolean;
  opciones?: { valor: string; texto: string }[];
  /** Separador al mostrar una lista (`lista` y `enteros`). */
  unir?: string;
  /** Solo se muestra (y se envía) si devuelve `true`. */
  visible?: (valores: Record<string, string>) => boolean;
  /** Mensaje de error de formato; `null` si es válido. Recibe el valor recortado. */
  validar?: (valor: string, valores: Record<string, string>) => string | null;
}

export type GrupoId = 'general' | 'auth' | 'otorgar' | 'revocar' | 'consultar';

export const GRUPOS: Record<GrupoId, { titulo: string; opcional?: boolean }> = {
  general: { titulo: 'General' },
  auth: { titulo: 'Autenticación' },
  otorgar: { titulo: 'Otorgar acceso' },
  revocar: { titulo: 'Revocar acceso' },
  consultar: { titulo: 'Consultar acceso (opcional)', opcional: true },
};

export const OBLIGATORIO_PARAM = 'Es obligatorio.';
export const MARCAS = ['correo', 'nivel', 'plataforma'] as const;
const MARCAS_TEXTO = MARCAS.map((m) => `{${m}}`).join(', ');

const SEPARADOR = /[\s,]+/;
const partes = (valor: string) => valor.split(SEPARADOR).filter(Boolean);

// --- Validadores de formato (espejo parcial del backend; el servidor decide) ---

function rutaValida(permiteMarcas: boolean) {
  return (valor: string): string | null => {
    let resto = valor;
    if (permiteMarcas) for (const m of MARCAS) resto = resto.split(`{${m}}`).join('x');
    const ok = /^\/[A-Za-z0-9._~/:-]*$/.test(resto) && !resto.includes('..');
    return ok ? null : 'Empieza con "/", usa letras, dígitos y . _ ~ / : - y no incluyas "..".';
  };
}

function enterosEn(min: number, max: number, maxItems = 20) {
  return (valor: string): string | null => {
    const lista = partes(valor);
    const ok = lista.length <= maxItems
      && lista.every((n) => /^\d{1,3}$/.test(n) && Number(n) >= min && Number(n) <= max);
    return ok ? null : `Usa números enteros entre ${min} y ${max}, separados por comas.`;
  };
}

function objetoJson(valor: string, tipoValores?: 'texto'): string | null {
  let dato: unknown;
  try {
    dato = JSON.parse(valor);
  } catch {
    return 'Escribe un objeto JSON válido.';
  }
  if (typeof dato !== 'object' || dato === null || Array.isArray(dato)) return 'Escribe un objeto JSON válido.';
  if (tipoValores === 'texto') {
    const entradas = Object.entries(dato as Record<string, unknown>);
    if (entradas.length > 5 || entradas.some(([, v]) => typeof v !== 'string')) {
      return 'Hasta 5 campos, todos de texto.';
    }
  }
  return null;
}

const METODOS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((m) => ({ valor: m, texto: m }));
const CON_CUERPO = (valores: Record<string, string>, op: string) =>
  ['POST', 'PUT', 'PATCH'].includes(valores[`${op}.metodo`] ?? '');

function operacionApi(op: 'otorgar' | 'revocar' | 'consultar'): CampoParametro[] {
  const obligatorio = true; // en `consultar` solo se exige si el grupo se completa
  return [
    { clave: `${op}.metodo`, etiqueta: 'Método HTTP', tipo: 'select', grupo: op, obligatorio, opciones: METODOS,
      pista: 'Método de la llamada.' },
    { clave: `${op}.ruta`, etiqueta: 'Ruta', grupo: op, obligatorio, validar: rutaValida(true),
      pista: `Empieza con "/". Admite las marcas ${MARCAS_TEXTO}, por ejemplo /usuarios/{correo}.` },
    { clave: `${op}.consulta`, etiqueta: 'Parámetros de consulta (JSON)', tipo: 'json', grupo: op,
      validar: (v) => objetoJson(v, 'texto'),
      pista: `Opcional. Objeto con hasta 5 campos de texto; admite marcas, por ejemplo {"email": "{correo}"}.` },
    { clave: `${op}.cuerpo`, etiqueta: 'Cuerpo (JSON)', tipo: 'json', grupo: op,
      visible: (v) => CON_CUERPO(v, op), validar: (v) => objetoJson(v),
      pista: 'Opcional, solo con POST, PUT o PATCH. Objeto JSON de hasta 4 niveles; las marcas solo en valores de texto.' },
    { clave: `${op}.sin_cambios`, etiqueta: 'Estados «ya estaba así»', tipo: 'enteros', grupo: op, unir: ', ',
      validar: enterosEn(400, 499),
      pista: 'Opcional. Estados HTTP 400 a 499 separados por comas, por ejemplo 404, 410.' },
  ];
}

function operacionSsh(op: 'otorgar' | 'revocar' | 'consultar'): CampoParametro[] {
  const obligatorio = true; // en `consultar` solo se exige si el grupo se completa
  const comando: CampoParametro = {
    clave: `${op}.comando`, etiqueta: 'Comando', grupo: op, obligatorio, tipo: 'lista', unir: ' ',
    validar: (v) => {
      const piezas = partes(v);
      const ok = piezas.length >= 1 && piezas.length <= 8
        && piezas.every((p) => p.length <= 100 && /^[A-Za-z0-9._/=:+-]+$/.test(p))
        && piezas[0].startsWith('/') && !piezas.some((p) => p.includes('..'));
      return ok ? null : 'Hasta 8 palabras de letras, dígitos y . _ / = : + -; la primera, una ruta absoluta sin "..".';
    },
    pista: 'Comando fijo, separado por espacios; el primero es una ruta absoluta, por ejemplo /usr/local/bin/acceso otorgar. Los datos de la solicitud viajan por la entrada estándar, no en el comando.',
  };
  const codigos = (clave: string, etiqueta: string, pista: string): CampoParametro => ({
    clave: `${op}.${clave}`, etiqueta, pista, grupo: op, tipo: 'enteros', unir: ', ', validar: enterosEn(1, 255),
  });
  const campos = [comando];
  if (op !== 'consultar') {
    campos.push(codigos('sin_cambios', 'Códigos «ya estaba así»', 'Opcional. Códigos de salida 1 a 255 separados por comas.'));
  } else {
    campos.push(codigos('ausente', 'Códigos «sin acceso»', 'Opcional. Códigos de salida 1 a 255 que significan que no tiene acceso.'));
  }
  campos.push(codigos('transitorios', 'Códigos transitorios',
    'Opcional. Códigos 1 a 255 que se reintentan (por defecto 75). No puede repetirse en otra lista.'));
  return campos;
}

function operacionBd(op: 'otorgar' | 'revocar' | 'consultar'): CampoParametro[] {
  const obligatorio = true; // en `consultar` solo se exige si el grupo se completa
  const verbos = op === 'otorgar' ? ['INSERT', 'UPDATE'] : op === 'revocar' ? ['DELETE', 'UPDATE'] : ['SELECT'];
  const campos: CampoParametro[] = [
    {
      clave: `${op}.sentencia`, etiqueta: 'Sentencia', tipo: 'area', grupo: op, obligatorio,
      validar: (v, valores) => {
        if (v.length > 500 || /[\r\n]/.test(v)) return 'Una sola línea de hasta 500 caracteres.';
        if (!verbos.includes((v.split(/\s+/)[0] ?? '').toUpperCase())) return `Debe empezar con ${verbos.join(' o ')}.`;
        if (/^(UPDATE|DELETE)/i.test(v) && !/\bWHERE\b/i.test(v)) return 'UPDATE y DELETE llevan WHERE.';
        const marcadores = (v.match(/%s/g) ?? []).length;
        if (marcadores !== partes(valores[`${op}.parametros`] ?? '').length) {
          return 'Cada %s necesita una marca en «Parámetros», en el mismo orden.';
        }
        return null;
      },
      pista: `Plantilla fija de una línea; ${verbos.join(' o ')}. Los valores van como %s y se llenan con «Parámetros». Sin ";", comentarios ni comillas.`,
    },
    {
      clave: `${op}.parametros`, etiqueta: 'Parámetros de la sentencia', grupo: op, tipo: 'lista', unir: ', ',
      validar: (v) => {
        const lista = partes(v);
        return lista.length <= 10 && lista.every((m) => (MARCAS as readonly string[]).includes(m))
          ? null : `Hasta 10 marcas entre ${MARCAS.join(', ')}.`;
      },
      pista: `Una marca por cada %s, separadas por comas: ${MARCAS.join(', ')}.`,
    },
  ];
  if (op !== 'consultar') {
    campos.push({
      clave: `${op}.max_filas`, etiqueta: 'Máximo de filas afectadas', grupo: op, tipo: 'entero',
      validar: (v) => (/^\d+$/.test(v) && Number(v) >= 1 && Number(v) <= 10 ? null : 'Usa un entero entre 1 y 10.'),
      pista: 'Opcional, de 1 a 10 (por defecto 1). Si se afectan más filas, el cambio se deshace.',
    });
  }
  return campos;
}

/** Parámetros con editor por tipo (sin secretos). */
export const PARAMETROS_POR_TIPO: Record<ConnectorType, CampoParametro[]> = {
  api: [
    { clave: 'base_path', etiqueta: 'Ruta base', grupo: 'general', validar: (v) => (v.includes('{') ? 'No admite marcas.' : rutaValida(false)(v)),
      pista: 'Opcional. Ruta de la API, por ejemplo /usuarios.' },
    { clave: 'auth.esquema', etiqueta: 'Esquema de autenticación', tipo: 'select', grupo: 'auth', obligatorio: true,
      opciones: [
        { valor: 'bearer', texto: 'Bearer (Authorization: Bearer)' },
        { valor: 'basic', texto: 'Basic (Authorization: Basic)' },
        { valor: 'cabecera', texto: 'Cabecera propia' },
      ],
      pista: 'Cómo se envía la credencial del gestor. Basic requiere que la credencial traiga usuario.' },
    { clave: 'auth.nombre', etiqueta: 'Nombre de la cabecera', grupo: 'auth', obligatorio: true,
      visible: (v) => v['auth.esquema'] === 'cabecera',
      validar: (v) => (/^[A-Za-z0-9-]{1,100}$/.test(v) ? null : 'Usa letras, dígitos y guion.'),
      pista: 'Cabecera donde viaja el secreto, por ejemplo X-Api-Key. No puede ser Host, Authorization ni Content-Type.' },
    ...operacionApi('otorgar'), ...operacionApi('revocar'), ...operacionApi('consultar'),
  ],
  ssh: [
    { clave: 'huellas', etiqueta: 'Huellas de la llave del host', tipo: 'lista', unir: '\n', grupo: 'general',
      validar: (v) => {
        const lista = partes(v);
        return lista.length >= 1 && lista.length <= 5 && lista.every((h) => /^SHA256:[A-Za-z0-9+/]+={0,2}$/.test(h))
          ? null : 'De 1 a 5 huellas con el formato SHA256:<base64>.';
      },
      pista: 'Una por línea, formato SHA256:<base64> (ssh-keygen -lf). Varias sirven para rotar la llave. Obligatoria salvo que el despliegue tenga un archivo de hosts conocidos.' },
    { clave: 'auth.metodo', etiqueta: 'Método de autenticación', tipo: 'select', grupo: 'auth',
      opciones: [{ valor: 'llave', texto: 'Llave privada (recomendado)' }, { valor: 'contrasena', texto: 'Contraseña' }],
      pista: 'Opcional (por defecto llave). Usuario y secreto salen de la credencial del gestor; la contraseña solo si la plataforma no admite llave.' },
    ...operacionSsh('otorgar'), ...operacionSsh('revocar'), ...operacionSsh('consultar'),
  ],
  bd: [
    { clave: 'motor', etiqueta: 'Motor', tipo: 'select', grupo: 'general', obligatorio: true,
      opciones: [{ valor: 'mysql', texto: 'MySQL o MariaDB' }, { valor: 'postgresql', texto: 'PostgreSQL' }],
      pista: 'Motor de la base de datos del host indicado arriba.' },
    { clave: 'base_datos', etiqueta: 'Base de datos', grupo: 'general', obligatorio: true,
      validar: (v) => (/^[A-Za-z0-9_-]{1,64}$/.test(v) ? null : 'Usa letras, dígitos, "_" y "-", hasta 64.'),
      pista: 'Nombre de la base, hasta 64 caracteres. Usuario y contraseña salen de la credencial del gestor.' },
    ...operacionBd('otorgar'), ...operacionBd('revocar'), ...operacionBd('consultar'),
  ],
};

export function parametrosDe(tipo: string): CampoParametro[] {
  return tipo in PARAMETROS_POR_TIPO ? PARAMETROS_POR_TIPO[tipo as ConnectorType] : [];
}

// --- Conversión entre el objeto `params` y los valores de texto del formulario ---

function leer(objeto: Record<string, unknown>, clave: string): unknown {
  let actual: unknown = objeto;
  for (const parte of clave.split('.')) {
    if (typeof actual !== 'object' || actual === null) return undefined;
    actual = (actual as Record<string, unknown>)[parte];
  }
  return actual;
}

function escribir(objeto: Record<string, unknown>, clave: string, valor: unknown) {
  const partesClave = clave.split('.');
  let actual = objeto;
  for (const parte of partesClave.slice(0, -1)) {
    const siguiente = actual[parte];
    actual[parte] = typeof siguiente === 'object' && siguiente !== null ? siguiente : {};
    actual = actual[parte] as Record<string, unknown>;
  }
  actual[partesClave[partesClave.length - 1]] = valor;
}

function aTexto(campo: CampoParametro, valor: unknown): string {
  if (valor === undefined || valor === null) return '';
  switch (campo.tipo) {
    case 'lista': case 'enteros':
      return Array.isArray(valor) ? valor.map(String).join(campo.unir ?? ', ') : '';
    case 'json':
      return typeof valor === 'object' ? JSON.stringify(valor, null, 2) : '';
    default:
      return typeof valor === 'string' || typeof valor === 'number' ? String(valor) : '';
  }
}

function desdeTexto(campo: CampoParametro, texto: string): unknown {
  switch (campo.tipo) {
    case 'lista': return partes(texto);
    case 'enteros': return partes(texto).map(Number);
    case 'entero': return Number(texto);
    case 'json': return JSON.parse(texto);
    default: return texto;
  }
}

/** Valores de texto de los parámetros guardados de un conector del tipo dado. */
export function valoresDesde(connector: Connector | null): Record<string, string> {
  const valores: Record<string, string> = {};
  if (!connector) return valores;
  for (const campo of parametrosDe(connector.type)) {
    valores[campo.clave] = aTexto(campo, leer(connector.params, campo.clave));
  }
  return valores;
}

const raiz = (clave: string) => clave.split('.')[0];

/** Claves de primer nivel sin editor: se conservan al guardar (mismo tipo). */
export function parametrosSinEditor(connector: Connector | null, tipo: string): Record<string, unknown> {
  if (!connector || connector.type !== tipo) return {};
  const conEditor = new Set(parametrosDe(tipo).map((c) => raiz(c.clave)));
  return Object.fromEntries(Object.entries(connector.params).filter(([clave]) => !conEditor.has(clave)));
}

/** Campos visibles según los valores (p. ej. la cabecera solo con ese esquema). */
export function camposVisibles(tipo: string, valores: Record<string, string>): CampoParametro[] {
  return parametrosDe(tipo).filter((c) => !c.visible || c.visible(valores));
}

/** Objeto `params` del contrato: los campos vacíos y los ocultos no se envían. */
export function construirParams(tipo: string, valores: Record<string, string>): Record<string, unknown> {
  const params: Record<string, unknown> = {};
  for (const campo of camposVisibles(tipo, valores)) {
    const texto = (valores[campo.clave] ?? '').trim();
    if (!texto) continue;
    try {
      escribir(params, campo.clave, desdeTexto(campo, texto));
    } catch {
      /* JSON inválido: `validarParametros` ya lo marcó y no se envía. */
    }
  }
  return params;
}

/** Errores por clave; los grupos opcionales solo exigen lo obligatorio si tienen algo escrito. */
export function validarParametros(tipo: string, valores: Record<string, string>): Record<string, string> {
  const errores: Record<string, string> = {};
  const visibles = camposVisibles(tipo, valores);
  const grupoUsado = (grupo?: GrupoId) => visibles.some(
    (c) => c.grupo === grupo && (valores[c.clave] ?? '').trim() !== '',
  );
  for (const campo of visibles) {
    const texto = (valores[campo.clave] ?? '').trim();
    const exige = campo.obligatorio && (!campo.grupo || !GRUPOS[campo.grupo].opcional || grupoUsado(campo.grupo));
    if (!texto) {
      if (exige) errores[campo.clave] = OBLIGATORIO_PARAM;
      continue;
    }
    const invalido = campo.validar?.(texto, valores);
    if (invalido) errores[campo.clave] = invalido;
  }
  return errores;
}

/**
 * Campo que corresponde a una ruta del servidor (`otorgar.cuerpo.email`,
 * `huellas.0`): el de clave más larga que sea su prefijo. `null` si no hay.
 */
export function claveDeError(tipo: string, ruta: string): string | null {
  const claves = parametrosDe(tipo).map((c) => c.clave)
    .filter((clave) => ruta === clave || ruta.startsWith(`${clave}.`))
    .sort((a, b) => b.length - a.length);
  return claves[0] ?? null;
}
