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
import { MIN_NO_TEXTO, MIN_TEXTO } from '../utils/wcag';

export interface ParContraste {
  id: string;
  texto: string;
  fondo: string;
  sobre?: string;
  alfaFondo?: number;
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
  texto('input-text/input-bg', '--color-input-text', '--color-input-bg'),
  texto('bi-text-main/panel', '--color-bi-text-main', '--color-panel-fill'),
  texto('bi-text-muted/panel', '--color-bi-text-muted', '--color-panel-fill'),
  texto('bi-text-muted/surface-container', '--color-bi-text-muted', '--color-surface-container-bg'),
  texto('secondary/panel', '--color-secondary', '--color-panel-fill'),
  texto('primary-text/body-bg', '--color-primary-text', '--color-body-bg'),
  texto('primary-text/panel', '--color-primary-text', '--color-panel-fill'),
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
  // No textuales (bordes de control): 3:1.
  { id: 'input-border/panel', texto: '--color-input-border', fondo: '--color-panel-fill', minimo: MIN_NO_TEXTO },
  { id: 'panel-border/body-bg', texto: '--color-panel-border', fondo: '--color-body-bg', minimo: MIN_NO_TEXTO },
];
