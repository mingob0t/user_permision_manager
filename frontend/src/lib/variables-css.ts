import type { CSSProperties } from 'react';

/**
 * Pasa a un elemento valores que solo se conocen al ejecutar (el color de una
 * plataforma o de un área, que vienen de los datos) como variables CSS `--*`
 * (DIS-012). Una clase de `styles/components.css` las consume
 * (`.nx-chip-solid`, `.nx-chip-tint`); el componente nunca fija una propiedad
 * visual en línea. Es la única forma de `style` aceptada en `src/`
 * (`tests/accesibilidad/sin-estilos-inline.test.ts`).
 */
export function variablesCss(variables: Record<`--${string}`, string | undefined>): CSSProperties {
  return variables as CSSProperties;
}
