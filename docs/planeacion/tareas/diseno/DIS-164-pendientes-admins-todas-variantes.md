# DIS-164 — Tarjeta de área: pendientes y administradores en todas las variantes

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (reclamo del dueño: DIS-162 solo cubrió la variante estándar) |

## Cambios (`areas/tarjeta-area.tsx`)
- Piezas comunes: `EnlacePendientes` (enlace con `stopPropagation`, nombre accesible, `foco-visible min-h-12 min-w-12`; también lo usa `Cifra`), `nombrePendientes`, `textoAdministradores`, `estiloKpi` (clases por estilo de cifra), `KpiPendientes` y `FilaAdministradores`.
- Sin dato (`pendientes === undefined`) no se pinta la cifra; sin `mostrarAdministradores` no se pinta la fila.

| Variante | Qué se hizo |
|---|---|
| estandar | Sin cambios (DIS-162) |
| glass, portada | Tercera cifra con el estilo de sus cifras (rejilla de 3 columnas si hay dato) y fila completa debajo; portada con las clases `arte-luz` del texto existente sobre la capa oscura |
| banner | Ídem con el estilo claro de sus cifras |
| flotante | Sin cifras: bloque en el panel oscuro, sobre el pie, con estilo `arte-luz` |
| split, directorio, bento | Sin cifras de pendientes: bloque (cifra + fila) bajo el contenido, estilo claro |
| onda, medallon | Ídem, alineado a la izquierda dentro de la tarjeta centrada |

- DIS-162 solo retiró «N por aprobar» de la estándar (ninguna otra variante lo tenía): ahora las 10 tienen indicación de pendientes.
- Texto «Persona/Personas» y «persona/personas» → «Usuario/Usuarios» en todas las variantes (nunca hubo `title` ni nombres accesibles con «persona»); la variable `personas` no cambia.
- Comentarios de `pendientes` y `mostrarAdministradores` actualizados.
- Sin CSS ni tokens nuevos; `platform-admin.tsx` sin cambios.

## Impacto en elementos compartidos
- `TarjetaArea` (todas las variantes) y `Cifra`: usadas por Plataformas > Áreas y las vistas previas del cajón «Diseño»; las vistas previas y el catálogo no pasan `pendientes` ni `mostrarAdministradores`: no cambian salvo el texto «Usuarios».

## Verificación
- `npm run typecheck` 0, `npm run lint` 0, `npx vitest run` 0 (3742 pruebas). Pruebas nuevas en `tarjeta-area.test.tsx` (parametrizada por las 10 variantes; «Usuario/Usuarios»); ajustadas las que buscaban «Persona».
- Visual claro/oscuro, móvil y escritorio: no realizada (sin app levantada). Con 3 columnas las etiquetas pueden truncarse en tarjetas angostas (verlo en pantalla). Contraste: se reutilizan las mismas clases de texto de cada capa; no medido de nuevo.

## Correcciones de auditor-accesibilidad
- Foco del enlace sobre imagen (portada, flotante): token `--foco-anillo-sobre-arte` (96 165 250) y clase `foco-sobre-arte` (3:1 sobre la capa oscura; el anillo global no cambia).
- Nombre accesible: «Solicitudes pendientes: N, en {área}. Abrir Historial.» (contiene el texto visible también con 1; WCAG 2.5.3).
- Verificación: tsc 0, eslint 0, vitest 3744/3744 (salida 0); 13 pruebas fallan sin el cambio.
