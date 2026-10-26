/**
 * Pares de tokens texto/fondo que se miden en cada tema (FNC-025).
 *
 * Salen de la auditoría de accesibilidad inicial
 * (docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md, sección 1).
 * `sobre` indica la superficie donde se compone un fondo con alpha y
 * `alfaFondo` la opacidad que el marcado aplica al fondo (`bg-primary/15`).
 * DIS-001: el color de marca como texto se mide con su variante `*-text`.
 * DIS-002: los estados (success, error, warning, info) como texto, con su
 * variante `*-text`, sobre panel y sobre su propio tinte (`bg-success/15`...).
 */
import { ESTADOS as ESTADOS_ACCESO } from '@/components/access/access-status-badge';
import { ESTADOS_SOLICITUD } from '@/components/access/request-status-badge';
import { ESTADOS_CREDENCIAL } from '@/components/connectors/connector-catalog';
import { ESTADOS_EJECUCION, RESULTADOS_INTENTO } from '@/components/connectors/job-catalog';
import { ESTADOS_DIRECTORIO } from '@/components/settings/directory-catalog';
import { MIN_NO_TEXTO, MIN_TEXTO } from '../utils/wcag';

export interface ParContraste {
  id: string;
  texto: string;
  fondo: string;
  sobre?: string;
  alfaFondo?: number;
  /** Opacidad que el marcado aplica al texto (`text-x/NN`). */
  alfaTexto?: number;
  minimo: number;
}

const texto = (id: string, t: string, fondo: string, sobre?: string): ParContraste =>
  ({ id, texto: t, fondo, sobre, minimo: MIN_TEXTO });

/** Texto sobre un tinte del relleno (`bg-x/NN`) compuesto sobre panel. */
const tinte = (id: string, t: string, fondo: string, alfaFondo: number): ParContraste =>
  ({ ...texto(id, t, fondo, '--color-panel-fill'), alfaFondo });

const TONOS_ESTADO = ['success', 'error', 'warning', 'info'];
const TONOS_BADGE = ['primary', 'success', 'error', 'warning', 'violet', 'sky', 'slate', 'cyan'];

export const PARES: ParContraste[] = [
  texto('body-text/body-bg', '--color-body-text', '--color-body-bg'),
  texto('header-text/header-bg', '--color-header-text', '--color-header-bg'),
  texto('panel-header-text/panel-header-bg', '--color-panel-header-text', '--color-panel-header-bg', '--color-panel-fill'),
  texto('button-text/button-bg', '--color-button-text', '--color-button-bg'),
  texto('tab-active-text/tab-active-bg', '--color-tab-active-text', '--color-tab-active-bg'),
  texto('tab-inactive-text/tab-inactive-bg', '--color-tab-inactive-text', '--color-tab-inactive-bg'),
  texto('label-text/panel', '--color-label-text', '--color-panel-fill'),
  texto('label-text/input-bg', '--color-label-text', '--color-input-bg'),
  // DIS-013: placeholder de `form.tsx` (`placeholder:text-label/85` sobre `bg-surface-container/30` en panel).
  { ...texto('placeholder/input', '--color-label-text', '--color-surface-container-bg', '--color-panel-fill'),
    alfaFondo: 0.3, alfaTexto: 0.85 },
  // DIS-014: texto de `EmptyNote` en `ui.tsx` (`text-label/85` sobre `Card`, antes /60: 2,9–3,4:1).
  { ...texto('empty-note/panel', '--color-label-text', '--color-panel-fill'), alfaTexto: 0.85 },
  texto('input-text/input-bg', '--color-input-text', '--color-input-bg'),
  texto('bi-text-main/panel', '--color-bi-text-main', '--color-panel-fill'),
  texto('bi-text-muted/panel', '--color-bi-text-muted', '--color-panel-fill'),
  texto('bi-text-muted/surface-container', '--color-bi-text-muted', '--color-surface-container-bg'),
  texto('secondary/panel', '--color-secondary', '--color-panel-fill'),
  texto('primary-text/body-bg', '--color-primary-text', '--color-body-bg'),
  texto('primary-text/panel', '--color-primary-text', '--color-panel-fill'),
  // DIS-014: sobre el fondo de página (fuera de `Card`): subtítulo, paginación y
  // pestaña inactiva (`text-label`); pestaña activa (`text-primary-text`, ya en
  // `primary-text/body-bg`) y su indicador `border-primary` (no textual, 3:1).
  texto('label-text/body-bg', '--color-label-text', '--color-body-bg'),
  { id: 'tab-indicador/body-bg', texto: '--color-primary', fondo: '--color-body-bg', minimo: MIN_NO_TEXTO },
  // Entrada activa del menú, chips y pestañas: texto sobre `bg-primary/15` y `/10`.
  { ...texto('primary-text/primary-15', '--color-primary-text', '--color-primary', '--color-panel-fill'), alfaFondo: 0.15 },
  { ...texto('primary-text/primary-10', '--color-primary-text', '--color-primary', '--color-panel-fill'), alfaFondo: 0.1 },
  texto('on-primary/primary-solid', '--color-on-primary', '--color-primary-solid'),
  // DIS-002: texto de estado sobre panel (mensajes, estrella de favorito).
  ...TONOS_ESTADO.map((tono) =>
    texto(`${tono}-text/panel`, `--color-${tono}-text`, '--color-panel-fill')),
  // DIS-002: chips de notificación (`bg-<tono>/15`) y ErrorNote / hover de Eliminar (`bg-error/10`).
  ...TONOS_ESTADO.map((tono) => tinte(`${tono}-text/${tono}-15`, `--color-${tono}-text`, `--color-${tono}`, 0.15)),
  tinte('error-text/error-10', '--color-error-text', '--color-error', 0.1),
  // DIS-002: tarjeta "sin enlace" de Administrar plataformas (`bg-warning/10`).
  tinte('body-text/warning-10', '--color-body-text', '--color-warning', 0.1),
  texto('accent-peach-text/panel', '--color-accent-peach-text', '--color-panel-fill'),
  texto('accent-text/panel', '--color-accent-text', '--color-panel-fill'),
  texto('accent-sky-text/panel', '--color-accent-sky-text', '--color-panel-fill'),
  texto('brand-text/panel', '--color-brand-text', '--color-panel-fill'),
  texto('ntf-text-subject/ntf-card', '--color-ntf-text-subject', '--color-ntf-card-bg', '--color-ntf-panel-bg'),
  texto('status-active/panel', '--color-status-active', '--color-panel-fill'),
  ...TONOS_BADGE.map((tono) =>
    texto(`badge-${tono}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  // DIS-014: insignias de estado de solicitud (`RequestStatusBadge`) sobre `Card`.
  ...Object.entries(ESTADOS_SOLICITUD).map(([estado, { tono }]) =>
    texto(`badge-solicitud-${estado}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  // DIS-015: Aprobaciones. Texto de las filas y de los diálogos (`text-body-text` en `Card` y
  // `.nx-modal-glass`, ambos `--color-panel-fill`) y botón secundario ("Rechazar", "Cancelar":
  // `.nexus-btn-secondary`, `--color-tab-inactive-text` sobre `--color-surface-container-bg`).
  texto('body-text/panel', '--color-body-text', '--color-panel-fill'),
  // DIS-015 (auditor-accesibilidad): `.nexus-btn-primary` de `components.css` (antes blanco sobre
  // `--color-primary`: 2,56–4,23:1 en obsidian, rose, emerald y violet).
  texto('nexus-btn-primary', '--color-on-primary', '--color-primary-solid'),
  texto('btn-secondary-text/btn-secondary-bg', '--color-tab-inactive-text', '--color-surface-container-bg'),
  // DIS-018: accesos de un usuario. Insignias de estado de acceso (`AccessStatusBadge`) sobre `Card`;
  // el resto del panel reutiliza pares ya medidos (`body-text/panel`, `label-text/panel`,
  // `success-text/panel`, `btn-secondary-*`, `nexus-btn-primary`, `primary-text/primary-10`,
  // `label-text/body-bg`, `body-text/body-bg`; anillo de foco `ring-primary` en la página = `tab-indicador/body-bg`).
  ...Object.entries(ESTADOS_ACCESO).map(([estado, { tono }]) =>
    texto(`badge-acceso-${estado}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  // DIS-021: inventario. Filtros y buscador fuera de `Card`, sobre el fondo de página: texto del
  // control (`text-body-text`) y placeholder (`text-label/85`) sobre `bg-surface-container/30`
  // compuesto sobre `--color-body-bg`. Las filas reutilizan pares ya medidos.
  { ...texto('input-text/input-sobre-body-bg', '--color-body-text', '--color-surface-container-bg', '--color-body-bg'),
    alfaFondo: 0.3 },
  { ...texto('placeholder/input-sobre-body-bg', '--color-label-text', '--color-surface-container-bg', '--color-body-bg'),
    alfaFondo: 0.3, alfaTexto: 0.85 },
  // DIS-020: auditoría. Error del rango de fechas (`text-error-text`) bajo los filtros, sobre el
  // fondo de página. Filas, insignias (`TONOS_BADGE`), detalle en `.nx-modal-glass` y enlaces
  // `.nexus-btn-secondary` reutilizan pares ya medidos.
  texto('error-text/body-bg', '--color-error-text', '--color-body-bg'),
  // DIS-024: inicio por rol. Contadores (`StatTile` en `Link`) y títulos reutilizan pares ya medidos
  // (`label-text/panel`, `bi-text-main/panel`, `body-text/body-bg`, `label-text/body-bg`, botones).
  // Nuevo: anillo de foco `ring-primary` del contador, junto al borde del `Card` (no textual, 3:1);
  // del lado del fondo de página ya lo mide `tab-indicador/body-bg`.
  { id: 'foco-primary/panel', texto: '--color-primary', fondo: '--color-panel-fill', minimo: MIN_NO_TEXTO },
  // DIS-025 (auditor-accesibilidad): borde `border-primary` del panel del menú móvil y anillo de
  // foco de sus botones y enlaces; del lado del panel lo mide `foco-primary/panel` y del lado del
  // contenido, `tab-indicador/body-bg` (no textuales, 3:1). Sin par nuevo.
  // DIS-019: alta en el directorio y elevación a admin, en `.nx-modal-glass` (`--color-panel-fill`).
  // Textos, pistas, errores, aviso y botones reutilizan pares ya medidos (`label-text/panel`,
  // `body-text/panel`, `error-text/panel`, `success-text/panel`, `nexus-btn-primary`,
  // `btn-secondary-*`, `primary-text/primary-10`; anillo `ring-primary` = `foco-primary/panel`).
  // Nuevo: relleno de la casilla marcada (`.nexus-checkbox:checked`, `--color-primary` sobre panel),
  // no textual. El borde de la casilla sin marcar (`--color-panel-border`) linda con el panel
  // (`--color-panel-fill`, fondo real del modal) y falla 3:1 en los 7 temas (1,42–2,02:1, medido por
  // auditor-accesibilidad): es de `.nexus-checkbox` (compartido) y lo corrige DIS-039.
  { id: 'checkbox-marcada/panel', texto: '--color-primary', fondo: '--color-panel-fill', minimo: MIN_NO_TEXTO },
  // DIS-022: conectores y ejecuciones. Insignias de estado de ejecución y de intento (en `Card` y en
  // `.nx-modal-glass`) y de la credencial, sobre `--color-panel-fill`. El resto (filas, avisos
  // `success-text`/`error-text` en `Card`, pistas, botones y anillos de foco) reutiliza pares ya medidos.
  ...Object.entries(ESTADOS_EJECUCION).map(([estado, { tono }]) =>
    texto(`badge-ejecucion-${estado}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  ...Object.entries(RESULTADOS_INTENTO).map(([resultado, { tono }]) =>
    texto(`badge-intento-${resultado}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  ...Object.entries(ESTADOS_CREDENCIAL).map(([estado, { tono }]) =>
    texto(`badge-credencial-${estado}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  // DIS-023: pestaña Directorio de Ajustes. Aviso de origen (`text-body-text` sobre `bg-primary/10`)
  // fuera de `Card`, sobre el fondo de página; insignia de estado del directorio sobre `Card`. Valores,
  // origen (`text-label`), avisos `success-text`/`error-text` en `Card`, pista, botón secundario y
  // anillos de foco reutilizan pares ya medidos. DIS-034: las pestañas (`text-primary-text`/`text-label` sobre la página,
  // indicador y anillo `primary`) reutilizan los pares de DIS-014.
  { ...texto('body-text/primary-10-sobre-body-bg', '--color-body-text', '--color-primary', '--color-body-bg'),
    alfaFondo: 0.1 },
  ...Object.entries(ESTADOS_DIRECTORIO).map(([estado, { tono }]) =>
    texto(`badge-directorio-${estado}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  // DIS-004: botón `danger` de `form.tsx` (antes blanco sobre `--color-error`: 3,76:1) y hover de
  // `.nexus-btn-secondary` (`--color-primary-text` sobre `primary/5`) en `Card`/modal y en la página.
  texto('on-error/error-solid', '--color-on-error', '--color-error-solid'),
  tinte('btn-secondary-hover/panel', '--color-primary-text', '--color-primary', 0.05),
  { ...texto('btn-secondary-hover/body-bg', '--color-primary-text', '--color-primary', '--color-body-bg'),
    alfaFondo: 0.05 },
  // No textuales (bordes de control): 3:1.
  { id: 'input-border/panel', texto: '--color-input-border', fondo: '--color-panel-fill', minimo: MIN_NO_TEXTO },
  { id: 'panel-border/body-bg', texto: '--color-panel-border', fondo: '--color-body-bg', minimo: MIN_NO_TEXTO },
];
