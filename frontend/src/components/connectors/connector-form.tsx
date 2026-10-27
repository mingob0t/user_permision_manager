'use client';

/**
 * Formulario del conector de una plataforma (DIS-022, F-CON-01,
 * `PUT /platforms/<id>/connector`, contrato `conectores-y-ejecuciones.md` 1.1).
 *
 * - Tipo, host, puerto, parámetros del tipo, referencia de la credencial y
 *   activo. Los parámetros cambian con el tipo (`PARAMETROS_POR_TIPO`: `api`,
 *   `ssh` y `bd`, DIS-042) y el error del servidor por `params.<ruta>` se
 *   marca en su campo.
 * - Ningún campo pide ni muestra contraseñas: la credencial es la referencia
 *   del ítem en el gestor de secretos (ADR-005).
 * - Patrón de `DirectoryAccountForm` (DIS-019): `required` y `aria-required`,
 *   pistas y errores con `aria-describedby`, foco en el primer error y
 *   `aria-disabled` durante el envío para que el foco no caiga en `body`.
 */

import { useState } from 'react';
import { connectorsApi } from '@/lib/access/connectors';
import type { Connector } from '@/lib/access/types';
import { Button, Checkbox, Field, Select, TextInput } from '../form';
import { FieldErrorNote, FieldHint, describedBy, focusFirstError } from '../platforms/field-notes';
import { ErrorNote } from '../ui';
import {
  type CampoConector, type FormularioConector, HOST_MAX, PUERTO_MAX, PUERTO_MIN, REFERENCIA_MAX,
  TIPOS_CONECTOR, cuerpoConector, esTipoConocido, formularioDesde, parametrosConservados,
  parametrosDelTipo, validarConector, validarParametros,
} from './connector-catalog';
import { avisoVisibilidad, resumenParametros } from './connector-params';
import { RegionDeAnuncios } from '../region-de-anuncios';
import { ConnectorParamFields, idParametro } from './connector-param-fields';
import { MENSAJE_REVISA, describeConnectorSaveError } from './connector-errors';

const PREFIJO = 'conector';
const IDS: Record<Exclude<CampoConector, 'params' | 'active'>, string> = {
  type: `${PREFIJO}-tipo`,
  host: `${PREFIJO}-host`,
  port: `${PREFIJO}-puerto`,
  credential_ref: `${PREFIJO}-credencial`,
};
/** `fieldset` de los parámetros: recibe el foco si el servidor marca `params` (DIS-022). */
export const PARAMS_FIELDSET_ID = `${PREFIJO}-params`;
const ORDEN: [CampoConector, string][] = [
  ['type', IDS.type], ['host', IDS.host], ['port', IDS.port], ['credential_ref', IDS.credential_ref],
  ['params', PARAMS_FIELDSET_ID],
];
const PARAMS_ERROR_ID = `${PREFIJO}-params-error`;

export function ConnectorForm({
  platformId,
  guardado,
  onSaved,
  onStale,
}: {
  platformId: number;
  /** Configuración guardada; `null` si la plataforma aún no tiene. */
  guardado: Connector | null;
  onSaved: (connector: Connector) => void;
  /** La plataforma o la configuración cambió en el servidor: recargar. */
  onStale: () => void;
}) {
  const [form, setForm] = useState<FormularioConector>(() => formularioDesde(guardado));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Partial<Record<CampoConector, string>>>({});
  const [paramErrors, setParamErrors] = useState<Record<string, string>>({});
  const [anuncio, setAnuncio] = useState('');

  const campos = parametrosDelTipo(form.type);
  const conservados = Object.keys(parametrosConservados(guardado, form.type));
  const tipoCambio = guardado !== null && guardado.type !== form.type;

  /** Al cambiar de tipo se vuelve a lo guardado de ese tipo, o a vacío (se descartan los del anterior). */
  function cambiarTipo(tipo: string) {
    const params = guardado?.type === tipo ? formularioDesde(guardado).params : {};
    setForm((prev) => ({ ...prev, type: tipo, params }));
    setParamErrors({});
    setAnuncio(resumenParametros(esTipoConocido(tipo) ? TIPOS_CONECTOR[tipo] : tipo, tipo, params));
  }

  function cambiarParametro(clave: string, valor: string) {
    const params = { ...form.params, [clave]: valor };
    setForm((prev) => ({ ...prev, params: { ...prev.params, [clave]: valor } }));
    const aviso = avisoVisibilidad(form.type, form.params, params);
    if (aviso) setAnuncio(aviso);
  }

  /** Orden de foco: campos base y luego los parámetros visibles. */
  function ordenCon(errParams: Record<string, string>): [string, string][] {
    const delTipo: [string, string][] = campos
      .filter((c) => errParams[c.clave]).map((c) => [c.clave, idParametro(PREFIJO, c.clave)]);
    return [...ORDEN.slice(0, 4), ...delTipo, ORDEN[4]];
  }

  function cambiar<K extends keyof FormularioConector>(campo: K, valor: FormularioConector[K]) {
    setForm((prev) => ({ ...prev, [campo]: valor }));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (sending) return;
    const errores = validarConector(form);
    const erroresParams = validarParametros(form.type, form.params);
    if (Object.keys(errores).length > 0 || Object.keys(erroresParams).length > 0) {
      const total = Object.keys(errores).length + Object.keys(erroresParams).length;
      setError(total === 1 ? MENSAJE_REVISA : `Revisa ${total} campos marcados.`);
      setFields(errores);
      setParamErrors(erroresParams);
      focusFirstError(ordenCon(erroresParams), { ...errores, ...erroresParams } as Record<string, string>);
      return;
    }
    setSending(true);
    setError(null);
    setFields({});
    setParamErrors({});
    try {
      const result = await connectorsApi.save(platformId, cuerpoConector(form, guardado));
      setSending(false);
      onSaved(result.connector);
    } catch (err) {
      const view = describeConnectorSaveError(err, form.type);
      setError(view.message);
      setFields(view.fields);
      setParamErrors(view.paramFields);
      setSending(false);
      if (view.stale) onStale();
      focusFirstError(ordenCon(view.paramFields), { ...view.fields, ...view.paramFields } as Record<string, string>);
    }
  }

  function campoTexto(
    campo: 'host' | 'port' | 'credential_ref',
    label: string,
    pista: string,
    extra: React.InputHTMLAttributes<HTMLInputElement> = {},
  ) {
    const pistaId = `${IDS[campo]}-pista`;
    const errorId = `${IDS[campo]}-error`;
    return (
      <div>
        <Field label={`${label} *`}>
          <TextInput
            id={IDS[campo]}
            value={form[campo]}
            onChange={(event) => cambiar(campo, event.target.value)}
            required
            aria-required="true"
            autoComplete="off"
            spellCheck={false}
            {...extra}
            {...describedBy([errorId, fields[campo]], [pistaId, true])}
          />
        </Field>
        <FieldHint id={pistaId}>{pista}</FieldHint>
        <div role="alert">
          <FieldErrorNote id={errorId} message={fields[campo]} />
        </div>
      </div>
    );
  }

  const tipoPista = `${IDS.type}-pista`;
  const tipoError = `${IDS.type}-error`;

  return (
    <form onSubmit={submit} noValidate aria-busy={sending} className="space-y-5" aria-label="Configuración del conector">
      <p className="text-sm text-label">Los campos con * son obligatorios.</p>
      <RegionDeAnuncios mensaje={anuncio} />

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <Field label="Tipo de conector *">
            <Select
              id={IDS.type}
              value={form.type}
              onChange={(event) => cambiarTipo(event.target.value)}
              required
              aria-required="true"
              {...describedBy([tipoError, fields.type], [tipoPista, true])}
            >
              {(Object.keys(TIPOS_CONECTOR) as (keyof typeof TIPOS_CONECTOR)[]).map((tipo) => (
                <option key={tipo} value={tipo}>{TIPOS_CONECTOR[tipo]}</option>
              ))}
              {/* Un tipo guardado sin editor aquí (p. ej. `noop` en dev) se conserva. */}
              {guardado && !esTipoConocido(guardado.type)
                ? <option value={guardado.type}>{guardado.type}</option> : null}
            </Select>
          </Field>
          <FieldHint id={tipoPista}>
            {tipoCambio
              ? 'Cambiaste el tipo: se descartan los parámetros del tipo anterior.'
              : 'Cómo se conecta el portal con la plataforma.'}
          </FieldHint>
          <div role="alert">
            <FieldErrorNote id={tipoError} message={fields.type} />
          </div>
        </div>
        {campoTexto('port', 'Puerto', `Número entre ${PUERTO_MIN} y ${PUERTO_MAX}.`, {
          inputMode: 'numeric', pattern: '[0-9]*',
        })}
      </div>

      {campoTexto('host', 'Host', 'Nombre de host autorizado por el despliegue, sin protocolo ni dirección IP.', {
        maxLength: HOST_MAX, autoCapitalize: 'none',
      })}

      {campoTexto('credential_ref', 'Referencia de la credencial',
        `Nombre del ítem en el gestor de secretos, por ejemplo equipo/plataforma-api. Hasta ${REFERENCIA_MAX} caracteres. Nunca escribas aquí la contraseña.`,
        { maxLength: REFERENCIA_MAX, autoCapitalize: 'none' })}

      <fieldset
        id={PARAMS_FIELDSET_ID}
        tabIndex={-1}
        className="space-y-3 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary"
        aria-describedby={fields.params ? PARAMS_ERROR_ID : undefined}
      >
        <legend className="mb-2 block text-xs font-black uppercase tracking-[0.1em] text-label">
          Parámetros del tipo
        </legend>
        {campos.length === 0 ? (
          <p className="text-sm text-label">Este tipo no tiene parámetros editables por ahora.</p>
        ) : (
          <ConnectorParamFields
            tipo={form.type}
            valores={form.params}
            errores={paramErrors}
            prefijo={PREFIJO}
            onChange={cambiarParametro}
          />
        )}
        {conservados.length > 0 ? (
          <p className="break-words text-sm text-label">
            Se conservan sin cambios: {conservados.join(', ')}.
          </p>
        ) : null}
        <div role="alert">
          <FieldErrorNote id={PARAMS_ERROR_ID} message={fields.params} />
        </div>
      </fieldset>

      <Checkbox
        label="Conector activo"
        checked={form.active}
        onChange={(event) => cambiar('active', event.target.checked)}
      />

      {error ? <ErrorNote message={error} /> : null}

      <div className="flex flex-wrap justify-end gap-3">
        <Button
          type="submit"
          aria-disabled={sending || undefined}
          className="aria-disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary"
        >
          {sending ? 'Guardando…' : 'Guardar conector'}
        </Button>
      </div>
    </form>
  );
}
