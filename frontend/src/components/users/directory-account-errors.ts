/**
 * Validación y mensajes del alta en el directorio (DIS-019, `POST /users/directory`,
 * contrato `usuarios-directorio.md` v1). Las reglas son espejo de
 * `app/modules/users/directory_accounts.py`; el servidor vuelve a validarlas.
 * Nunca se muestra el texto del servidor: los mensajes salen de aquí por
 * `ApiError.code`, por campo o por estado HTTP.
 */

import { ApiError } from '@/lib/api';
import type { DirectoryAccountInput } from '@/lib/access/types';

export const UID_MIN = 3;
export const UID_MAX = 64;
export const UID_PATRON = /^[a-z][a-z0-9._-]*$/;
/** `users.email` es `String(120)` (contrato v1, 2026-10-19). */
export const CORREO_MAX = 120;
/** Forma básica; el servidor aplica su patrón completo. */
const CORREO_PATRON = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const NOMBRE_MAX = 100;

export type CampoAlta = 'uid' | 'email' | 'given_name' | 'surname' | 'area_ids';

export interface FormularioAlta {
  uid: string;
  email: string;
  given_name: string;
  surname: string;
  area_ids: number[];
}

const OBLIGATORIO = 'Es obligatorio.';

/** Mensaje fijo por campo para un `422 validacion` (no se repite el del servidor). */
export const MENSAJES_CAMPO: Record<CampoAlta, string> = {
  uid: `De ${UID_MIN} a ${UID_MAX} caracteres: minúsculas, números, punto, guion o guion bajo; empieza con letra.`,
  email: `Escribe un correo válido, sin acentos, de hasta ${CORREO_MAX} caracteres.`,
  given_name: `De 1 a ${NOMBRE_MAX} caracteres.`,
  surname: `De 1 a ${NOMBRE_MAX} caracteres.`,
  area_ids: 'Elige al menos un área de tu alcance.',
};

export const MENSAJE_UID_DUPLICADO = 'Ese identificador ya existe en el directorio o en el portal.';
export const MENSAJE_CORREO_DUPLICADO = 'El correo ya está registrado.';
export const MENSAJE_REVISA = 'Revisa los campos marcados.';

const MENSAJES_POR_CODIGO: Record<string, string> = {
  directorio_no_disponible: 'No se pudo crear la cuenta en el directorio; intenta más tarde.',
};

const MENSAJES_POR_ESTADO: Record<number, string> = {
  401: 'Tu sesión terminó. Vuelve a iniciar sesión.',
  403: 'No tienes permiso para crear cuentas.',
  // Áreas ajenas o inexistentes para un admin de área (SEC-AUTHZ-03/04).
  404: 'Alguna de las áreas elegidas ya no está en tu alcance. Recarga la página.',
  503: 'No se pudo crear la cuenta en el directorio; intenta más tarde.',
};

const MENSAJE_GENERICO = 'No se pudo crear la cuenta. Inténtalo de nuevo.';

/**
 * Errores por campo antes de enviar. `areasObligatorias`: el admin de área
 * debe elegir al menos una (el superadmin puede dejarla vacía).
 */
export function validarAlta(
  form: FormularioAlta,
  areasObligatorias: boolean,
): Partial<Record<CampoAlta, string>> {
  const errores: Partial<Record<CampoAlta, string>> = {};
  const uid = form.uid.trim();
  if (!uid) errores.uid = OBLIGATORIO;
  else if (uid.length < UID_MIN || uid.length > UID_MAX || !UID_PATRON.test(uid)) {
    errores.uid = MENSAJES_CAMPO.uid;
  }
  const correo = form.email.trim();
  if (!correo) errores.email = OBLIGATORIO;
  else if (correo.length > CORREO_MAX || !/^[\x21-\x7e]+$/.test(correo) || !CORREO_PATRON.test(correo)) {
    errores.email = MENSAJES_CAMPO.email;
  }
  for (const campo of ['given_name', 'surname'] as const) {
    const valor = form[campo].trim();
    if (!valor) errores[campo] = OBLIGATORIO;
    else if (valor.length > NOMBRE_MAX) errores[campo] = MENSAJES_CAMPO[campo];
  }
  if (areasObligatorias && form.area_ids.length === 0) errores.area_ids = MENSAJES_CAMPO.area_ids;
  return errores;
}

/** Cuerpo del contrato: textos recortados y sin campos extra (lista blanca). */
export function cuerpoAlta(form: FormularioAlta): DirectoryAccountInput {
  return {
    uid: form.uid.trim(),
    email: form.email.trim(),
    given_name: form.given_name.trim(),
    surname: form.surname.trim(),
    area_ids: form.area_ids,
  };
}

export interface AltaErrorView {
  message: string;
  fields: Partial<Record<CampoAlta, string>>;
}

function esCampo(clave: string): clave is CampoAlta {
  return clave in MENSAJES_CAMPO;
}

export function describeDirectoryAccountError(err: unknown): AltaErrorView {
  if (!(err instanceof ApiError)) return { message: MENSAJE_GENERICO, fields: {} };
  if (err.code === 'uid_duplicado') {
    return { message: MENSAJE_REVISA, fields: { uid: MENSAJE_UID_DUPLICADO } };
  }
  if (err.code === 'correo_duplicado') {
    return { message: MENSAJE_REVISA, fields: { email: MENSAJE_CORREO_DUPLICADO } };
  }
  if (err.status === 422) {
    const fields: Partial<Record<CampoAlta, string>> = {};
    for (const clave of Object.keys(err.fields)) {
      if (esCampo(clave)) fields[clave] = MENSAJES_CAMPO[clave];
    }
    return { message: MENSAJE_REVISA, fields };
  }
  const message = (err.code && MENSAJES_POR_CODIGO[err.code])
    ?? MENSAJES_POR_ESTADO[err.status] ?? MENSAJE_GENERICO;
  return { message, fields: {} };
}
