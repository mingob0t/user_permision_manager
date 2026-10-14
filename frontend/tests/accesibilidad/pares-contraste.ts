/**
 * Pares de tokens texto/fondo que se miden en cada tema (FNC-025).
 *
 * Salen de la auditoría de accesibilidad inicial
 * (docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md, sección 1).
 * `sobre` indica la superficie donde se compone un fondo con alpha.
 */
import { MIN_NO_TEXTO, MIN_TEXTO } from '../utils/wcag';

export interface ParContraste {
  id: string;
  texto: string;
  fondo: string;
  sobre?: string;
  minimo: number;
}

const texto = (id: string, t: string, fondo: string, sobre?: string): ParContraste =>
  ({ id, texto: t, fondo, sobre, minimo: MIN_TEXTO });

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
  texto('primary/body-bg', '--color-primary', '--color-body-bg'),
  texto('primary/panel', '--color-primary', '--color-panel-fill'),
  texto('success/panel', '--color-success', '--color-panel-fill'),
  texto('accent-peach/panel', '--color-accent-peach', '--color-panel-fill'),
  texto('accent/panel', '--color-accent', '--color-panel-fill'),
  texto('accent-sky/panel', '--color-accent-sky', '--color-panel-fill'),
  texto('brand/panel', '--color-brand', '--color-panel-fill'),
  texto('ntf-text-subject/ntf-card', '--color-ntf-text-subject', '--color-ntf-card-bg', '--color-ntf-panel-bg'),
  texto('status-active/panel', '--color-status-active', '--color-panel-fill'),
  ...TONOS_BADGE.map((tono) =>
    texto(`badge-${tono}`, `--badge-${tono}-text`, `--badge-${tono}-bg`, '--color-panel-fill')),
  // No textuales (bordes de control): 3:1.
  { id: 'input-border/panel', texto: '--color-input-border', fondo: '--color-panel-fill', minimo: MIN_NO_TEXTO },
  { id: 'panel-border/body-bg', texto: '--color-panel-border', fondo: '--color-body-bg', minimo: MIN_NO_TEXTO },
];
