/**
 * Catálogo de eventos y resultados de la auditoría para mostrar en pantalla
 * (DIS-020; contrato `auditoria.md`, "Catálogo de `action`", y `Evento` de FNC-047).
 *
 * Los registros anteriores al catálogo traen `action` en texto libre: se
 * muestra tal cual.
 */

import type { AuditResult } from '@/lib/access/types';

export const ACCIONES: Record<string, string> = {
  area_creada: 'Área creada',
  area_editada: 'Área editada',
  area_eliminada: 'Área eliminada',
  admin_asignado: 'Administrador asignado',
  admin_retirado: 'Administrador retirado',
  rol_cambiado: 'Rol cambiado',
  plataforma_creada: 'Plataforma creada',
  plataforma_editada: 'Plataforma editada',
  solicitud_creada: 'Solicitud creada',
  solicitud_aprobada: 'Solicitud aprobada',
  solicitud_rechazada: 'Solicitud rechazada',
  acceso_otorgado: 'Acceso otorgado',
  acceso_activo: 'Acceso activo',
  acceso_fallido: 'Acceso fallido',
  acceso_revocado: 'Acceso revocado',
  revocacion_fallida: 'Revocación fallida',
  cuenta_directorio_creada: 'Cuenta de directorio creada',
  conector_configurado: 'Conector configurado',
  conector_eliminado: 'Conector eliminado',
  conector_probado: 'Conector probado',
  ejecucion_reintentada: 'Ejecución reintentada',
  ejecucion_cancelada: 'Ejecución cancelada',
  notificacion_fallida: 'Notificación fallida',
};

/** Nombre del evento; un valor fuera del catálogo se muestra tal cual. */
export function etiquetaAccion(action: string): string {
  return Object.hasOwn(ACCIONES, action) ? ACCIONES[action] : action;
}

export const RESULTADOS: Record<AuditResult, { texto: string; tono: 'success' | 'error' | 'warning' | 'slate' }> = {
  success: { texto: 'Éxito', tono: 'success' },
  error: { texto: 'Error', tono: 'error' },
  warning: { texto: 'Advertencia', tono: 'warning' },
  info: { texto: 'Información', tono: 'slate' },
};

/** Resultado (`status`) para la insignia; un valor desconocido, tal cual y en gris. */
export function resultado(status: string): { texto: string; tono: 'success' | 'error' | 'warning' | 'slate' } {
  return Object.hasOwn(RESULTADOS, status)
    ? RESULTADOS[status as AuditResult]
    : { texto: status, tono: 'slate' };
}

/** Quién actuó: el correo del actor o "Sistema" (`actor` null). */
export const ACTOR_SISTEMA = 'Sistema';
