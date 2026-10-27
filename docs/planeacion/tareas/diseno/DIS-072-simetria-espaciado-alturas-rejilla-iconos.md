# DIS-072 — Simetría: escala única de espaciado, alturas de control, rejilla, anchos máximos e íconos, con prueba automática

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | tokens |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-072-simetria-espaciado-alturas-rejilla-iconos` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- 63 clases de espaciado con 12 pasos; 38 usos fuera de 4/8/12/16/24/32; 31 valores arbitrarios; alturas `h-7/9/10` y `thead` 60 px; sin ancho de contenido común; íconos como caracteres de texto (plan §2.7).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Una escala de espaciado y medida como tokens que Tailwind no permita saltar, y una prueba que rechace valores fuera de ella (plan §4.3.1).

## Alcance
- **Incluye:**
  - Tokens `espacio-1/2/3/4/6/8`, `control-alto` (48 px), `contenido-max`, `formulario-max`, `dialogo-max`, rejilla (`columnas`, `canal`), `icono-sm/md/lg`
  - `tailwind.config.ts`: `spacing`, `height`, `maxWidth` reemplazados (no extendidos) por la escala
  - Componente `Icono` (`components/icono.tsx`, SVG con `currentColor`, prop `tamano`) con los íconos actuales (cerrar, marca, favorito) y los 5 de alerta (éxito, error, aviso, info, pregunta)
  - Prueba nueva `escala-simetria.test.ts`: sin clases de espaciado/alto/ancho fuera de escala ni arbitrarias (`p-[13px]`, `tracking-[…]`, `min-w-[…]`, `grid-cols-[…]`), sin `px`/`rem` sueltos en `components.css`/`global.css`; excepciones con motivo y tarea, que solo pueden bajar
  - `01-visual.md`: simetría, rejilla e íconos; densidad elegida
- **No incluye:**
  - Migrar cada componente o pantalla a la escala (C1–D2 retiran sus excepciones)
  - Íconos nuevos fuera de los listados

## Archivos previstos
- `frontend/src/styles/tokens.css`
- `frontend/tailwind.config.ts`
- `frontend/src/components/icono.tsx` (nuevo)
- `frontend/tests/accesibilidad/escala-simetria.test.ts` (nuevo) y su archivo de excepciones
- `docs/estandarizacion/01-visual.md`

## Reutilización
Patrón de excepciones de `colores-literales.excepciones.ts` y `area-tactil.excepciones.ts`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `tailwind.config.ts` (`spacing`, `height`, `maxWidth`) | configuración | todas las pantallas: las clases fuera de escala dejan de generar CSS; se listan como excepciones o se corrigen en esta tarea si es trivial | No |
| `Icono` (nuevo) | componente | lo adoptan DIS-058, DIS-062, DIS-063, DIS-074 | No |

## Variables y configuración
Tokens de espaciado, medida e íconos: registro y historial.

## Criterios de aceptación
- [ ] `escala-simetria.test.ts` en verde con la lista de excepciones inicial (38 usos y 31 arbitrarios contados, cada uno con su tarea)
- [ ] Una clase fuera de escala nueva hace fallar la prueba (verificado)
- [ ] Ninguna pantalla cambia de aspecto por clases que dejen de existir (verificado en navegador)
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← Pedido del dueño 2026-10-27 (simetría); PLAN-FASE-7 §2.7, §4.3.1
- Depende de → DIS-057; insumos de densidad e íconos (o propuesta neutra)

## Riesgos y reversión
Reemplazar `spacing` puede romper clases en uso: congelar como excepciones antes de borrar. Reversión: revertir el commit.

## Verificación
Pendiente (tarea en Propuesta).

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | | |
| revisor | | |
| auditor-accesibilidad | | |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
