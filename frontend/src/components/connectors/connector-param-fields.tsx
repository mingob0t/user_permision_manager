'use client';

/**
 * Campos de los parámetros de un conector, agrupados (DIS-042). Una sola
 * solución para los tres tipos: etiqueta, pista y error asociados con
 * `aria-describedby`, obligatorios marcados con `*` y grupos opcionales
 * (consultar) que solo exigen lo obligatorio si se completan.
 * Ningún campo pide secretos: la credencial es la referencia del gestor.
 */

import { Field, Select, TextArea, TextInput } from '../form';
import { FieldErrorNote, describedBy } from '../platforms/field-notes';
import { type CampoParametro, GRUPOS, type GrupoId, camposVisibles } from './connector-params';

const ORDEN_GRUPOS: GrupoId[] = ['general', 'auth', 'otorgar', 'revocar', 'consultar'];

/** Id del control de un parámetro (`otorgar.ruta` → `conector-param-otorgar-ruta`). */
export function idParametro(prefijo: string, clave: string): string {
  return `${prefijo}-param-${clave.replace(/\./g, '-')}`;
}

function ParamField({
  campo, prefijo, valor, error, exigido, condicional, onChange,
}: {
  campo: CampoParametro;
  prefijo: string;
  valor: string;
  error?: string;
  /** Obligatorio en el HTML solo fuera de grupos opcionales. */
  exigido: boolean;
  /** Obligatorio solo si se completa su grupo opcional. */
  condicional: boolean;
  onChange: (valor: string) => void;
}) {
  const id = idParametro(prefijo, campo.clave);
  const pistaId = `${id}-pista`;
  const errorId = `${id}-error`;
  const comunes = {
    id,
    value: valor,
    required: exigido || undefined,
    'aria-required': exigido ? ('true' as const) : undefined,
    ...describedBy([errorId, error], [pistaId, true]),
  };
  const etiqueta = campo.obligatorio ? `${campo.etiqueta} *` : campo.etiqueta;
  let control: React.ReactNode;
  if (campo.tipo === 'select') {
    control = (
      <Select {...comunes} onChange={(e) => onChange(e.target.value)}>
        <option value="">{campo.obligatorio ? 'Elige una opción' : 'Por defecto'}</option>
        {(campo.opciones ?? []).map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
      </Select>
    );
  } else if (campo.tipo === 'area' || campo.tipo === 'json' || (campo.tipo === 'lista' && campo.unir === '\n')) {
    control = (
      <TextArea
        {...comunes}
        rows={campo.tipo === 'json' ? 4 : 3}
        className={campo.tipo === 'json' ? 'font-mono' : undefined}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="off"
        spellCheck={false}
      />
    );
  } else {
    control = (
      <TextInput
        {...comunes}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="off"
        spellCheck={false}
        autoCapitalize="none"
        inputMode={campo.tipo === 'entero' ? 'numeric' : undefined}
      />
    );
  }
  return (
    <div>
      <Field label={etiqueta}>{control}</Field>
      {/* `FieldHint` es compartido: aquí la pista además corta palabras largas (320 px). */}
      <span id={pistaId} className="mt-1.5 block break-words text-xs text-label">
        {campo.pista}
        {condicional ? ' Obligatorio si completas este grupo.' : ''}
      </span>
      <div role="alert">
        <FieldErrorNote id={errorId} message={error} />
      </div>
    </div>
  );
}

export function ConnectorParamFields({
  tipo, valores, errores, prefijo, onChange,
}: {
  tipo: string;
  valores: Record<string, string>;
  /** Errores por clave de campo. */
  errores: Record<string, string>;
  prefijo: string;
  onChange: (clave: string, valor: string) => void;
}) {
  const visibles = camposVisibles(tipo, valores);
  return (
    <>
      {ORDEN_GRUPOS.map((grupo) => {
        const campos = visibles.filter((c) => (c.grupo ?? 'general') === grupo);
        if (campos.length === 0) return null;
        const { titulo, opcional } = GRUPOS[grupo];
        return (
          <fieldset
            key={grupo}
            className="min-w-0 space-y-4 rounded-xl border border-panel-border p-4"
            aria-describedby={opcional ? `${prefijo}-grupo-${grupo}-nota` : undefined}
          >
            <legend className="px-2 text-xs font-black uppercase tracking-[0.1em] text-label">{titulo}</legend>
            {opcional ? (
              <p id={`${prefijo}-grupo-${grupo}-nota`} className="break-words text-sm text-label">
                Déjalo vacío para no consultar. Si completas un campo, los marcados con * son obligatorios.
              </p>
            ) : null}
            {campos.map((campo) => (
              <ParamField
                key={campo.clave}
                campo={campo}
                prefijo={prefijo}
                valor={valores[campo.clave] ?? ''}
                error={errores[campo.clave]}
                exigido={Boolean(campo.obligatorio) && !opcional}
                condicional={Boolean(campo.obligatorio) && Boolean(opcional)}
                onChange={(valor) => onChange(campo.clave, valor)}
              />
            ))}
          </fieldset>
        );
      })}
    </>
  );
}
