import type { Config } from 'tailwindcss';

/**
 * Configuración portada de assets/js/tailwind-config.js del portal original,
 * con los mismos nombres de utilidad para que el marcado de las plantillas
 * funcione sin traducción. Los valores salen de src/styles/tokens.css.
 *
 * Se añade `<alpha-value>` a los tokens declarados como canales «R G B» para
 * poder usar `bg-primary/10`; los que el original define como color completo
 * (body-bg, header, input) se dejan tal cual.
 */
export default {
  content: ['./src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Main Palette
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        secondary: 'rgb(var(--color-secondary) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        'accent-sky': 'rgb(var(--color-accent-sky) / <alpha-value>)',
        'accent-violet': 'rgb(var(--color-accent-violet) / <alpha-value>)',
        peach: 'rgb(var(--color-accent-peach) / <alpha-value>)',
        violet: 'rgb(var(--color-accent-violet) / <alpha-value>)',
        sky: 'rgb(var(--color-accent-sky) / <alpha-value>)',
        brand: 'rgb(var(--color-brand) / <alpha-value>)',

        // Texto de marca por tema (DIS-001): los de arriba son rellenos.
        'primary-text': 'rgb(var(--color-primary-text) / <alpha-value>)',
        'brand-text': 'rgb(var(--color-brand-text) / <alpha-value>)',
        'accent-text': 'rgb(var(--color-accent-text) / <alpha-value>)',
        'accent-sky-text': 'rgb(var(--color-accent-sky-text) / <alpha-value>)',
        'accent-peach-text': 'rgb(var(--color-accent-peach-text) / <alpha-value>)',
        // Relleno de marca con texto encima y su texto (DIS-001).
        'primary-solid': 'rgb(var(--color-primary-solid) / <alpha-value>)',
        'on-primary': 'rgb(var(--color-on-primary) / <alpha-value>)',

        // Surfaces & Backgrounds
        'body-bg': 'var(--color-body-bg)',
        'body-text': 'var(--color-body-text)',
        header: 'var(--color-header-bg)',
        'header-text': 'var(--color-header-text)',
        'panel-fill': 'rgb(var(--color-panel-fill) / <alpha-value>)',
        'panel-border': 'rgb(var(--color-panel-border) / <alpha-value>)',
        'panel-header': 'rgb(var(--color-panel-header-bg) / <alpha-value>)',
        'panel-header-text': 'rgb(var(--color-panel-header-text) / <alpha-value>)',
        'audit-body': 'rgb(var(--color-audit-body) / <alpha-value>)',
        'surface-container': 'rgb(var(--color-surface-container-bg) / <alpha-value>)',
        'surface-container-border':
          'rgb(var(--color-surface-container-border) / <alpha-value>)',

        // Buttons & Interaction
        'button-bg': 'rgb(var(--color-button-bg) / <alpha-value>)',
        'button-text': 'rgb(var(--color-button-text) / <alpha-value>)',
        'button-disabled': 'rgb(var(--color-button-disabled-bg) / <alpha-value>)',
        'button-disabled-text':
          'rgb(var(--color-button-disabled-text) / <alpha-value>)',

        // Inputs
        input: 'var(--color-input-text)',
        'input-bg': 'rgb(var(--color-input-bg) / <alpha-value>)',
        'input-border': 'rgb(var(--color-input-border) / <alpha-value>)',
        'input-focus': 'rgb(var(--color-input-focus) / <alpha-value>)',
        label: 'rgb(var(--color-label-text) / <alpha-value>)',

        // Navigation & Tabs
        'tab-bar': 'rgb(var(--color-tab-bar-bg) / <alpha-value>)',
        'tab-active': 'rgb(var(--color-tab-active-bg) / <alpha-value>)',
        'tab-active-text': 'rgb(var(--color-tab-active-text) / <alpha-value>)',
        'tab-inactive': 'rgb(var(--color-tab-inactive-bg) / <alpha-value>)',
        'tab-inactive-text': 'rgb(var(--color-tab-inactive-text) / <alpha-value>)',

        // Business Intelligence (BI) & Status
        'bi-logistics': 'rgb(var(--color-bi-card-logistics) / <alpha-value>)',
        'bi-ring': 'rgb(var(--color-bi-ring-bg) / <alpha-value>)',
        'bi-main': 'rgb(var(--color-bi-text-main) / <alpha-value>)',
        'bi-muted': 'rgb(var(--color-bi-text-muted) / <alpha-value>)',
        'kpi-highlight': 'rgb(var(--color-kpi-highlight) / <alpha-value>)',

        // Estados: rellenos y tintes (`bg-error/10`); DIS-002 quitó los literales.
        success: 'rgb(var(--color-success) / <alpha-value>)',
        warning: 'rgb(var(--color-warning) / <alpha-value>)',
        error: 'rgb(var(--color-error) / <alpha-value>)',
        info: 'rgb(var(--color-info) / <alpha-value>)',
        // DIS-004: relleno del botón de peligro y su texto, por tema.
        'error-solid': 'rgb(var(--color-error-solid) / <alpha-value>)',
        'on-error': 'rgb(var(--color-on-error) / <alpha-value>)',
        // Estados como texto, por tema (DIS-002).
        'success-text': 'rgb(var(--color-success-text) / <alpha-value>)',
        'warning-text': 'rgb(var(--color-warning-text) / <alpha-value>)',
        'error-text': 'rgb(var(--color-error-text) / <alpha-value>)',
        'info-text': 'rgb(var(--color-info-text) / <alpha-value>)',

        // Alias usados por el marcado de base.html
        bg: 'var(--color-body-bg)',
        text: 'var(--color-body-text)',
      },
      borderRadius: {
        base: 'var(--radius-base)',
        panel: 'var(--radius-panel)',
      },
      fontFamily: {
        // base.html carga Inter desde Google Fonts.
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config;
