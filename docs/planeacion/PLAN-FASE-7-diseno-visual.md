# Plan — Fase 7: Diseño visual

| Campo | Valor |
|---|---|
| Pedido | Dueño, 2026-10-27: el portal «visualmente deja mucho que desear»; ampliado el mismo día: estandarizar y reutilizar componentes; simetría; sin saltos de diseño (CLS); diálogos de aviso y confirmación al estilo SweetAlert |
| Estatus | Propuesta (tareas en `Propuesta`; las aprueba el dueño) |
| Tareas | FNC-132, DIS-054 a DIS-075 (23); vinculada DIS-053 |
| Decisión | [ADR-007](../decisiones/ADR-007-dos-temas-y-modelo-de-tokens.md) (Propuesta) |
| Contrato | [preferencias.md](../contratos/preferencias.md) (Propuesta) |

## 1. Alcance
- **Se pidió:** estética propia sobre tokens; solo 2 temas (claro y oscuro); tokens cuidados; todos los estados; AA medido en los 2 temas; **un patrón, un componente** y plantillas de pantalla comunes, con control automático contra el marcado hecho a mano; simetría (una escala de espaciado, rejilla, alturas, radios, íconos); CLS ≈ 0 al abrir diálogos y al cargar; diálogo de alerta propio (sin `sweetalert2`) y migración de los confirmar y avisos actuales.
- **No se pidió (fuera):** cambios de funcionalidad, de textos, de flujo o de rutas; pantallas nuevas; modo de alto contraste; personalización de colores por el administrador; tema por área o por plataforma; Flutter/Unity; la librería `sweetalert2` (estilos en línea y colores propios: choca con los lineamientos).
- La regla vigente se mantiene: el dueño define la estética (insumos, §6); el plan prepara la estructura para que su diseño sea un cambio de valores, no de código.

## 2. Diagnóstico (medido sobre `develop` 794bc2c)

### 2.1 Tokens (`frontend/src/styles/tokens.css`, 731 líneas)
| Medida | Valor |
|---|---|
| Propiedades `--*` distintas | 99 |
| Declaraciones en total | 523, en 7 bloques (claro 99, SO oscuro 66, `html.dark` 66, esmeralda 63, obsidiana 83, rosa 63, violeta 83) |
| Sin ningún uso (CSS, TSX ni `tailwind.config.ts`) | 23: `--color-ntf-*` (11), `--color-status-active`, `--color-danger`, `--color-panel-shadow`, `--color-audit-body-alpha`, `--space-1`, `--text-sm` … `--text-3xl` (7) |
| Claves de color de Tailwind sin uso en TSX | 41 de 59 (`tab-*`, `button-*`, `input-*`, `header`, `brand`, `accent-*`, `peach`, `info`, `error-solid`…) |
| Uso concentrado | `label` 160 usos (texto secundario de casi todo), `primary` 63, `body-text` 57, `panel-border` 43 |
| Dos formatos de valor | Hex completo (`body-bg`, `body-text`, `header-*`, `input-text`) y canales `R G B` (el resto) |
| Nombres por pantalla, no por rol | `bi-*`, `ntf-*`, `audit-*`, `kpi-*`, `tab-*`, `button-*` |

**Tokens que duplican rol** (mismo valor en claro y mismo propósito):
| Rol | Tokens que lo repiten |
|---|---|
| Texto principal | `--color-body-text`, `--color-input-text`, `--color-bi-text-main` |
| Texto secundario | `--color-label-text`, `--color-bi-text-muted`, `--badge-slate-text` |
| Borde | `--color-panel-border`, `--color-input-border`, `--nx-border` (components.css) |
| Superficie elevada | `--color-surface-container-bg`, `--color-audit-body`, `--color-tab-bar-bg` ≈ `--color-panel-header-bg` |
| Acento como texto | `--color-primary-text`, `--color-info-text`, `--badge-primary-text` |
| Relleno de acento | `--color-primary-solid`, `--color-button-bg`, `--color-tab-active-bg`, `--color-input-focus` |
| Estado | 3 familias por estado: `--color-<estado>` (relleno), `--color-<estado>-text`, `--badge-<estado>-bg/-text`; además `--color-danger` (rosa, sin uso) frente a `--color-error` (rojo) y `--badge-error-*` (rosa) |
| Acentos decorativos | `accent` = `accent-violet`; `accent-peach` = `warning`; `sky`, `cyan`, `violet` sin rol semántico |

### 2.2 Temas
| Hallazgo | Evidencia |
|---|---|
| 7 contextos, 2 de ellos «oscuro» distintos | SO oscuro y `html.dark` difieren en 7 tokens (`body-bg` `#030712` vs `#0f172a`, `body-text`, 4 `ntf-*`, `ntf-text-subject`) |
| El oscuro hereda 22 tokens del claro | Entre ellos `--color-button-disabled-bg/-text` (gris claro en tema oscuro, usado por `input:disabled`), `--color-primary`, `--color-success/warning/error/info` |
| Cabecera sin sus tokens | `--color-header-bg/-text` definidos; `AppShell` usa `bg-panel-fill` |
| Tema referenciado en 10 archivos de prueba y 4 de código | `tokens.css`, `global.css` (`color-scheme`), `lib/tema.ts`, `theme-selector.tsx`; backend `users/temas.py` |

### 2.3 Forma y tipografía
| Hallazgo | Evidencia |
|---|---|
| Fuente no cargada | `'Inter'` en `global.css:15` y `tailwind.config.ts`, sin `@font-face` ni `next/font`: cae a la sans del sistema |
| Escala tipográfica sin uso | 7 de 8 `--text-*` sin uso; las pantallas usan la escala de Tailwind |
| Radios | 2 tokens; 8 valores en uso (`rounded-xl` 29, `-lg` 11, `-full` 5, `-2xl` 1, `-base` 1, botón 1rem, insignia y casilla 0.5rem, campo 10px) |
| Sombras | Sin token en uso; `shadow-sm/lg/2xl` de Tailwind y sombras de color en botones |
| Espaciado | `--space-1` sin uso |
| `!important` | 81 en `components.css`, 7 en `global.css` |
| Estilo heredado | Mayúsculas + `font-black` + `tracking` en botones, insignias y cabeceras de panel; `font-medium` en tablas y pestañas |

### 2.4 Estados (verificado en el código)
| Estado | Hoy | Problema |
|---|---|---|
| Hover | Botones (`translateY` + sombra), secundario, casilla, menú, pestañas, chips | Sin hover en filas, tarjetas y enlaces (1 `hover:underline`); recetas distintas |
| Foco visible | `focus-visible:ring-2 ring-primary` copiado a mano 38 veces en 27 archivos | `Button` sin regla propia (anillo del navegador); `TextInput` usa `focus:` y además la regla global `:focus` con halo al 10 % (< 3:1) |
| Activo/presionado | `.nexus-btn:active { scale(.96) }`; `aria-pressed` en favorito y chips | Sin token; sin `prefers-reduced-motion` (0 usos) |
| Seleccionado | Pestañas (borde + `primary-text`), menú y chips (`bg-primary/15`), conector (variante primaria) | 3 recetas; `--color-tab-*` sin uso; 2 implementaciones de pestañas idénticas (`settings-panel`, `my-requests-view`) |
| Deshabilitado | Botón `opacity-40`; campo `opacity-50` + regla global `input:disabled` (tokens + `opacity .6`) | Opacidades que se multiplican; `select`/`textarea` sin la regla global; 4 valores de opacidad |
| Cargando | `Spinner` (1 uso de `animate-spin`); `aria-busy` en 9 formularios/diálogos | Sin estilo para `aria-busy` ni botón ocupado |
| Vacío | `EmptyNote` (22 archivos) | Solo texto en tarjeta |
| Error | `ErrorNote` (52), `FieldErrorNote` | Correcto en contraste; sin ícono |
| Éxito | `SuccessNote` (solo texto), toast | Sin contenedor equivalente a `ErrorNote` |
| Aviso / info | Solo `Badge` `warning`/`sky` | Sin componente de aviso ni informativo |
| Solo lectura | Ninguno (`readOnly` sin uso ni estilo) | Sin diseño |
| Campo inválido | `aria-invalid` en 3 archivos | **Ningún estilo**: el campo no cambia |

### 2.5 Documentación
- `docs/estandarizacion/README.md` cita `01-visual.md` y `02-comportamiento.md`: no existen.
- Reglas DIS-001/DIS-002 hablan de «7 contextos».

### 2.6 Inventario de patrones (base: `03-reutilizacion.md`)
Usos del componente común frente a resoluciones a mano en `frontend/src` (TSX).

| Patrón | Componente común (usos) | Resuelto a mano | Dónde (archivo:línea) |
|---|---|---|---|
| Botón | `Button` (90) | 19 `<button>` con clases propias; 8 `Link` con `nexus-btn`; 4 «botón secundario» con clases sueltas | `users/user-card.tsx:69,77,85,95,106,114`; `areas-list.tsx:132,141,150`; `platforms/platform-columns.tsx:83,91`; `mobile-menu.tsx:85,111`; `toast.tsx:84`; `settings-panel.tsx:60`; `access/my-requests-view.tsx:90`; `favorite-button.tsx:51`; `users/tag-picker.tsx:23`; `app/error.tsx:30`. Enlaces: `access/inventory.tsx:104`, `access/request-catalog-card.tsx:93`, `audit/platform-audit-history.tsx:39`, `audit/user-audit-history.tsx:60`, `platforms/platform-integration-fields.tsx:192`, `home/role-summary.tsx:156,199`, `users/user-access-panel.tsx:331`. Sueltos: `mobile-menu.tsx:91,114`, `app-shell.tsx:133`, `app/error.tsx:39` |
| Tabla / lista de datos | `DataTable` (1: `platform-admin.tsx:147`) y `ResponsiveList` (9) | Dos componentes para el mismo patrón; listas con borde a mano | `ResponsiveList` en `access/my-requests.tsx:161`, `access/my-access.tsx:159`, `access/approvals-inbox.tsx:288`, `access/inventory-table.tsx:77`, `connectors/jobs-table.tsx:110`, `connectors/connector-list.tsx:41`, `audit/audit-table.tsx:105`, `users/user-access-panel.tsx:264`; a mano: `audit/audit-detail-modal.tsx:61`, `connectors/job-detail-modal.tsx:67` |
| Tarjeta | `Card` (66 usos, 24 archivos) | 4 paneles con el marcado de `Card` copiado | `platform-card.tsx:36`, `access/request-catalog-card.tsx:54`, `connectors/connector-param-fields.tsx:112`, `access/request-form-modal.tsx:115` |
| Cabecera de panel | `PanelHeader` (**0 usos**) | — | `ui.tsx` (código muerto) |
| Encabezado de página | **No existe** | 17 `<h1>` a mano con 3 envoltorios (`flex … justify-between` ×7, `space-y-6` ×9, `space-y-10` ×1) y 3 márgenes de subtítulo | `dashboard.tsx:30`, `favorites-list.tsx:45`, `notifications-list.tsx:59`, `audit-log.tsx:16`, `settings-panel.tsx:49`, `users-list.tsx:90`, `platform-admin.tsx:111`, `areas-list.tsx:74`, `access/my-requests-view.tsx:73`, `audit/user-audit-history.tsx:53`, `audit/platform-audit-history.tsx:34`, `app/platforms/page.tsx:12`, `app/approvals/page.tsx:14`, `app/inventory/page.tsx:17`, `app/admin/jobs/page.tsx:12`, `app/admin/connectors/page.tsx:12`; error/404: `app/error.tsx:24`, `app/not-found.tsx:9` |
| Campo de formulario | `Field` (108), `TextInput` (38), `Select` (50), `Checkbox` (13) | 3 `<input>` crudos; nota de error de campo propia | `settings/backup-tab.tsx:72`, `settings/portal-tab.tsx:104`, `access/request-form-modal.tsx:117`; `areas/area-form.tsx:24` (duplica `FieldErrorNote`) |
| Aviso de error / éxito | `ErrorNote` (79), `SuccessNote` (13) | Error dentro de `Card` con clases propias; `role="alert"` envolviendo a mano (12) | `settings/directory-tab.tsx:95-98`, `connectors/connector-panel.tsx:163-166`, `audit/audit-filters.tsx:183`; envoltorios: `connector-form.tsx:155,194,236`, `request-form-modal.tsx:149`, `reject-dialog.tsx:126`, `revoke-access-dialog.tsx:126`, `directory-account-form.tsx:122`, `area-checklist.tsx:78`, `connector-param-fields.tsx:85` |
| Aviso de advertencia / info | **No existe** | Tinte de estado a mano | `platforms/missing-link-note.tsx:8`, `notifications-list.tsx:21-23` |
| Estado vacío | `EmptyNote` (23) | Texto suelto | `users/directory-picker.tsx:60` |
| Carga | `Spinner` (32) | `aria-busy` sin estilo (9) | ver §2.4 |
| Insignia | `Badge` (43) | Ninguno (`nx-badge` solo en `ui.tsx`) | — |
| Diálogo | `Modal` (48), `ConfirmDialog` (7) | Menú móvil con `role="dialog"` propio | `mobile-menu.tsx:103` |
| Pestañas | **No existe** | 2 implementaciones idénticas | `settings-panel.tsx:58-77`, `access/my-requests-view.tsx:86-108` |
| Barra de filtros | `FilterBar` (1: `access/catalog-filters.tsx`) | 4 barras a mano | `access/inventory-filters.tsx`, `access/scope-filters.tsx`, `audit/audit-filters.tsx`, `connectors/jobs-filters.tsx` |
| Etiqueta de dato | — | `text-xs font-medium uppercase tracking-wide` copiado 7 veces | `responsive-list.tsx:11,30`, `my-requests.tsx:72,80`, `approvals-inbox.tsx:142,149`, `audit/audit-detail-modal.tsx:26` |
| Toast / anuncios | `useToast` (3), `RegionDeAnuncios` (4) | — | Correcto |

### 2.7 Simetría (escala de referencia 4/8/12/16/24/32 px = Tailwind `1/2/3/4/6/8`)
| Medida | Valor |
|---|---|
| Clases de espaciado distintas (`p/m/gap/space-*`) | 63, con 12 pasos (0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10) |
| Usos fuera de la escala | 38: `*-0.5` (6, 2 px), `*-1.5` (10, 6 px), `*-2.5` (4, 10 px), `*-5` (17, 20 px), `*-10` (1, 40 px) |
| Espaciados fuera de escala en CSS | `components.css:18` gap 6 px; `:48` padding 20 px (campo global); `:146` `min-width: 140px` |
| Valores arbitrarios de Tailwind | 31: `tracking-[…]` 9, `grid-cols-[minmax…]` 10 (una plantilla de columnas por lista), `has-[…]` 5, `min-w-[44rem]`, `z-[60]` |
| Altura de controles | 48 px en `Button` (`3rem`), `TextInput`/`Select` (`h-12`) y 20 usos de `min-h-12`; fuera: `h-10` ×3, `h-9`, `h-7` ×2, casilla 20 px, `thead tr { height: 60px }` (`components.css:31`) |
| Anchos máximos | Sin ancho de contenido común: cada pantalla ocupa todo el `main`; 5 valores sueltos (`max-w-xs/sm/md/lg/full`) en login, error y diálogo |
| Alineación de encabezado | 3 envoltorios distintos de `h1` (§2.6) |
| Radios | 8 valores (§2.3) |
| Íconos | Sin juego de íconos: 5 caracteres de texto (`✕` ×3, `✓`, `★/☆`) y monogramas de 3 tamaños (`h-7`, `h-9`, `h-10`); 1 `<img>` (logo, 40 px fijo) |

### 2.8 Saltos de diseño (CLS)
| Hallazgo | Evidencia |
|---|---|
| Al abrir un diálogo la página se mueve | `useScrollLock` pone `overflow: hidden` en la raíz y en `main` (`global.css:27-30`): desaparece la barra y el contenido se corre su ancho; `scrollbar-gutter` 0 usos |
| Diálogo sin animación definida | `Modal` aparece de golpe; sin `@keyframes` ni transición de opacidad; sin `prefers-reduced-motion` |
| Carga que cambia la altura | `Spinner` (fila de ≈ 64 px) reemplaza el contenido: `favorites-list.tsx:51`, `notifications-list.tsx:78`, `access/my-requests.tsx:143`, `access/my-requests-view.tsx:55`, `app-shell.tsx:92` y el resto de los 32 usos; esqueletos 0 |
| Avisos que empujan | `ErrorNote`/`SuccessNote` se insertan sin zona reservada (79 + 13 usos) |
| Movimiento en hover | `.nexus-btn-primary:hover { translateY(-2px) }` (`components.css:179`): no es CLS, pero no respeta reducción de movimiento |

### 2.9 Confirmaciones y avisos
| Hallazgo | Evidencia |
|---|---|
| `ConfirmDialog` (sin ícono, `role="dialog"`, foco en el panel, no en el botón seguro) | 6 archivos: `notifications-list`, `platform-admin`, `areas-list`, `areas/area-admins-panel`, `users-list`, `users/purge-panel` |
| Diálogos de confirmación propios sobre `Modal` | 6: `access/approve-dialog`, `access/reject-dialog`, `connectors/connector-delete-dialog`, `connectors/job-retry-dialog`, `users/admin-role-dialog`, `users/revoke-access-dialog` |
| Toast | 2 usos, ambos de error no crítico (`favorite-button.tsx:44`, `theme-selector.tsx:40`) |
| Resultado de acciones en línea | `SuccessNote` en 11 archivos (Ajustes ×5, `users-list`, `user-access-panel`, `connector-panel`, `approvals-inbox`, `jobs-log`, `catalog-notice`) |
| `window.confirm` / `alert` | 0 |
| Regla de cuándo usar diálogo o toast | No existe |

## 3. Principios
| # | Principio |
|---|---|
| P1 | Dos temas: claro y oscuro. «Según el sistema» elige entre ellos (§5.2); no es un tercer juego de valores |
| P2 | Tokens por **rol semántico** (superficie, texto, borde, acento, estado, interacción); ningún nombre de pantalla |
| P3 | Ningún componente conoce el tema: sin `dark:`, sin clases de tema, sin condicionales por tema en TSX |
| P4 | Todo estado se expresa con token (color, opacidad, anillo, sombra, movimiento); nada de `opacity-NN` ni colores sueltos |
| P5 | Cada token semántico existe en los 2 temas y tiene su par de contraste medido |
| P6 | El diseño del dueño cambia **primitivos**; semánticos y componentes no se tocan |
| P7 | Un formato de valor (canales `R G B`) para todo color |
| P8 | Un patrón, un componente: variantes por props, nunca marcado copiado (§4.4) |
| P9 | Simetría: una escala de espaciado (4/8/12/16/24/32 y 48 para alturas táctiles), una rejilla y anchos máximos comunes, controles de la misma fila con la misma altura, radios y bordes uniformes, un tamaño de ícono por contexto; nada fuera de la escala |
| P10 | Sin saltos: lo que aparece reserva su lugar; abrir o cerrar un diálogo no mueve el fondo; solo se animan opacidad y `transform`, y nada con reducción de movimiento |
| P11 | Diálogo para lo crítico, toast para lo breve (§4.7); los diálogos se construyen sobre `Modal` y tokens, sin librerías que inyecten estilos |

## 4. Modelo de tokens propuesto

### 4.1 Capas
| Capa | Qué contiene | Ejemplo | Quién la usa |
|---|---|---|---|
| Primitivos | Paleta tonal sin significado (neutro, marca, rojo, verde, ámbar, azul; tonos 50–950) | `--p-neutro-900`, `--p-marca-600` | Solo semánticos |
| Semánticos | Rol, un valor por tema | `--color-texto`, `--color-superficie`, `--color-accion` | Componentes y utilidades |
| Componente | Solo si un componente necesita algo que ningún semántico cubre | `--boton-alto`, `--campo-radio` | Ese componente |

Regla: primitivos solo en `tokens.css`; los temas solo reasignan semánticos a primitivos.

### 4.2 Roles semánticos mínimos
| Grupo | Tokens |
|---|---|
| Superficie | `fondo` (página), `superficie` (panel, tarjeta), `superficie-elevada` (diálogo, menú, toast), `superficie-hundida` (barra de pestañas, cabecera de tabla, campo), `velo` |
| Texto | `texto`, `texto-secundario`, `texto-tenue` (solo ≥ 4.5:1), `texto-sobre-accion`, `texto-sobre-peligro`, `texto-enlace` |
| Borde | `borde` (≥ 3:1, controles), `borde-sutil` (separadores decorativos), `borde-fuerte` |
| Acento / acción | `accion` (relleno primario), `accion-hover`, `accion-presionada`, `accion-tenue` (seleccionado), `accion-texto` |
| Estado | Por `exito`, `aviso`, `peligro`, `info`: `-relleno`, `-tenue` (fondo de aviso), `-borde`, `-texto`; `neutro` igual |
| Interacción | `foco-anillo`, `foco-ancho`, `foco-separacion`, `hover-capa`, `presionado-capa`, `seleccionado-fondo`, `seleccionado-borde`, `deshabilitado-fondo`, `deshabilitado-texto`, `deshabilitado-borde`, `invalido-borde`, `solo-lectura-fondo` |
| Forma | `radio-control`, `radio-tarjeta`, `radio-dialogo`, `radio-pastilla`; `borde-ancho`; `sombra-1..3` |
| Espaciado y medida | `espacio-1` 4 · `-2` 8 · `-3` 12 · `-4` 16 · `-6` 24 · `-8` 32 px; `control-alto` 48 px; `icono-sm` 16 · `icono-md` 20 · `icono-lg` 48 px (diálogo de alerta); `contenido-max`, `formulario-max`, `dialogo-max`; `columnas` y `canal` de la rejilla |
| Tipografía | `fuente-texto`, `fuente-mono`; `texto-xs..3xl` (mínimo 12 px); pesos `normal`, `medio`, `fuerte` |
| Movimiento | `duracion-corta`, `duracion-media`, `curva`; con `prefers-reduced-motion` → 0 |
| Datos libres | `texto-sobre-fondo-oscuro/-claro` (DIS-048, se conservan) |

Las utilidades de Tailwind se mapean a estos nombres; los nombres heredados quedan como **alias** hasta DIS-067.

### 4.3 Matriz de estados por componente
Cada celda nombra el token; «—» = no aplica.

| Componente | Reposo | Hover | Foco visible | Activo / presionado | Seleccionado | Deshabilitado | Error |
|---|---|---|---|---|---|---|---|
| Botón primario | `accion` + `texto-sobre-accion` | `accion-hover` | `foco-anillo` (2 px + separación) | `accion-presionada` | — | `deshabilitado-*` | — |
| Botón secundario | `superficie` + `borde` + `texto` | `hover-capa` + `borde-fuerte` | `foco-anillo` | `presionado-capa` | `seleccionado-*` (si es conmutador) | `deshabilitado-*` | — |
| Botón peligro | `peligro-relleno` + `texto-sobre-peligro` | `peligro-relleno` + `hover-capa` | `foco-anillo` | `presionado-capa` | — | `deshabilitado-*` | — |
| Enlace | `texto-enlace` subrayado | subrayado grueso | `foco-anillo` | `accion-presionada` | `aria-current`: `accion-texto` + peso fuerte | `texto-tenue`, sin subrayado | — |
| Campo de texto | `superficie-hundida` + `borde` | `borde-fuerte` | `foco-anillo` + borde `accion` | — | — | `deshabilitado-*` | `invalido-borde` + `peligro-texto` en la nota |
| Select | Igual que campo + flecha con token | `borde-fuerte` | `foco-anillo` | — | Opción: `color-scheme` del tema | `deshabilitado-*` | `invalido-borde` |
| Casilla | `superficie` + `borde` | `borde-fuerte` | `foco-anillo` | — | Marcada: `accion` + `texto-sobre-accion` | `deshabilitado-*` | `invalido-borde` |
| Pestaña | `texto-secundario` | `texto` + `hover-capa` | `foco-anillo` | `presionado-capa` | `seleccionado-borde` (≥ 3:1) + `accion-texto` | `deshabilitado-texto` | — |
| Fila de tabla/lista | `superficie` | `hover-capa` (si es interactiva) | `foco-anillo` interior | — | `seleccionado-fondo` + marca no cromática | — | `peligro-tenue` + ícono |
| Tarjeta | `superficie` + `borde-sutil` + `sombra-1` | `sombra-2` + `borde` (si es enlace) | `foco-anillo` | `presionado-capa` | `seleccionado-borde` | — | — |
| Ítem de menú | `texto-secundario` | `hover-capa` + `texto` | `foco-anillo` | `presionado-capa` | `aria-current`: `seleccionado-fondo` + `accion-texto` + barra | — | — |
| Chip / insignia | `<estado>-tenue` + `<estado>-texto` | Solo si conmuta: `hover-capa` | `foco-anillo` (si conmuta) | `presionado-capa` | `aria-pressed`: `seleccionado-*` + marca | `deshabilitado-*` | — |
| Aviso (nota) | `<estado>-tenue` + `<estado>-borde` + `<estado>-texto` + ícono | — | — | — | — | — | `peligro-*` |
| Diálogo | `superficie-elevada` + `borde` + `sombra-3` sobre `velo` | — | Foco inicial y atrapado (DIS-031) | — | — | — | Nota de error dentro |

Estados transversales:
| Estado | Token / patrón |
|---|---|
| Cargando | `aria-busy` → contenido `deshabilitado-texto` + `Spinner`; botón ocupado con indicador y `aria-disabled` |
| Vacío | `EmptyNote` con `texto-secundario` y acción opcional |
| Éxito / aviso / info / error | Nota con su familia de estado (§4.2) |
| Solo lectura | `solo-lectura-fondo` + `borde-sutil`; el texto conserva `texto` (≥ 4.5:1) |
| Inválido | `aria-invalid="true"` → `invalido-borde` (≥ 3:1) + `FieldErrorNote`; nunca solo color |

### 4.3.1 Simetría (DIS-072)
| Regla | Cómo se cumple |
|---|---|
| Escala única | Tailwind `spacing` reemplazado por los tokens `espacio-*` (solo 0, 1, 2, 3, 4, 6, 8 y 12 = 48 px de alto táctil); las clases fuera de escala dejan de existir y no compilan |
| Sin valores arbitrarios | Prohibido `*-[…]` de medida (`p-[13px]`, `tracking-[…]`, `min-w-[…]`); las plantillas de columnas pasan a props con nombre (`columnas="datos-5"`) definidas en un solo lugar |
| Rejilla y anchos | `main` con `contenido-max` centrado; formularios a `formulario-max`; diálogo a `dialogo-max`; rejilla de tarjetas de 1/2/3 columnas por punto de quiebre |
| Alturas en la misma fila | `Button`, `TextInput`, `Select`, `Checkbox` (fila) y `FilterBar` a `control-alto`; cabecera de tabla sin `height: 60px` suelto |
| Alineación | `PageHeader`: título a la izquierda, acciones a la derecha, mismo borde izquierdo que filtros y contenido |
| Radios y bordes | `radio-*` por tipo de pieza (§4.2); `borde-ancho` único (1 px), 2 px solo para foco y selección |
| Íconos | Componente `Icono` (SVG con `currentColor`) en 3 tamaños por contexto: en línea/botón `icono-sm`, menú y avisos `icono-md`, diálogo de alerta `icono-lg` |

### 4.3.2 Estabilidad (DIS-073)
| Situación | Regla |
|---|---|
| Abrir/cerrar diálogo o menú móvil | `scrollbar-gutter: stable` en el contenedor que se desplaza (raíz y `main`); el bloqueo no cambia el ancho ni la posición del fondo |
| Animación | Solo `opacity` y `transform`, con `duracion-*`; con `prefers-reduced-motion: reduce`, sin animación |
| Carga | `Skeleton` con la medida final: filas de tabla (n filas del tamaño de página), tarjetas (alto de `Card`), contadores (`StatTile`); `Spinner` solo dentro de un botón ocupado o en una zona de alto fijo |
| Avisos y errores | Zona reservada con alto mínimo (`RegionDeAviso`) en formularios y encabezados de lista; el error de campo reserva su línea |
| Imágenes y logos | `width`/`height` fijos y `object-contain`; el logo del portal y el favicon con medidas de token |
| Meta | CLS ≈ 0 (< 0,01) en Inicio, Plataformas, Mis solicitudes, Aprobaciones, Usuarios, Auditoría y Ajustes |

### 4.4 Regla «un patrón, un componente»
- Cada patrón tiene **un** componente común; las diferencias van por props (variante, tono, tamaño), nunca copiando marcado.
- Rediseñar el componente actualiza todas las pantallas que lo usan.
- Lo que hoy se resuelve a mano (§2.6) migra al componente; lo que no pueda, queda como excepción con motivo en la prueba de DIS-068.

| Patrón | Componente único | Acción | Tarea |
|---|---|---|---|
| Botón y enlace con aspecto de botón | `Button` (`variant`, `size`, `busy`) + `ButtonLink` (mismo estilo sobre `Link`) | Crear `ButtonLink`; migrar 8 `Link` + 4 sueltos; acción de fila sigue en `ACCION_FILA` → `Button variant="fila"` | DIS-058 |
| Campo | `Field` + `TextInput`/`TextArea`/`Select`/`Checkbox`/`ColorInput`/`FileInput` | Migrar 3 `<input>` crudos; `area-form.tsx:24` a `FieldErrorNote` | DIS-059 |
| Pestañas | `Tabs` (nuevo, `components/tabs.tsx`, con `destinoPorTecla`) | Unificar `settings-panel` y `my-requests-view` | DIS-060 |
| Conmutador (chip, favorito) | `ToggleChip` (nuevo) con `aria-pressed` | `tag-picker`, `favorite-button` | DIS-060 |
| Tarjeta y cabecera de panel | `Card` (`variant`: plana, enlace, seleccionable) + `PanelHeader` | Migrar 4 copias; usar o retirar `PanelHeader` | DIS-061 |
| Diálogo y panel lateral | `Modal`; `Drawer` para el menú móvil | Unificar `mobile-menu.tsx:103` | DIS-061 |
| Confirmación y aviso crítico | `AlertDialog` (tipo: éxito, error, aviso, info, pregunta) sobre `Modal`; `ConfirmDialog` pasa a ser un atajo de `AlertDialog` | Crear; migrar 6 `ConfirmDialog` y 6 diálogos propios | DIS-074, DIS-075 |
| Esqueleto de carga | `Skeleton` (fila, tarjeta, contador) | Crear; integrarlo en el componente de datos, `Card` y `StatTile` | DIS-073 |
| Ícono | `Icono` | Crear; reemplazar los 5 caracteres de texto | DIS-072 |
| Aviso | `Note` (`tono`: error, éxito, aviso, info) con `ErrorNote`/`SuccessNote` como atajos | Crear aviso/info; migrar `directory-tab`, `connector-panel`, `missing-link-note`, tintes de `notifications-list`; `role` dentro del componente | DIS-062 |
| Vacío / carga | `EmptyNote` (con acción opcional), `Spinner`, estilo para `aria-busy` | `directory-picker.tsx:60` | DIS-062 |
| Insignia / estado | `Badge` | Sin cambio de uso | DIS-062 |
| Tabla / lista de datos | Un solo componente (`DataTable` adaptable, absorbe `ResponsiveList`) + `ListPager` + `DataLabel` (etiqueta de dato) | 9 `ResponsiveList`, 2 listas a mano, 7 etiquetas copiadas | DIS-071 |
| Barra de filtros | `FilterBar` | Migrar 4 barras a mano | DIS-069 |
| Encabezado de página | `PageHeader` (título, descripción, acciones, foco del `h1`) | 17 `h1` a mano | DIS-070 |

### 4.5 Plantillas de pantalla
Componentes de composición en `frontend/src/components/plantillas/` (DIS-070). Todas: `PageHeader` → acciones → filtros → contenido → estados (carga, vacío, error, sin permiso).

| Plantilla | Estructura | Pantallas |
|---|---|---|
| Listado | `PageHeader` (+ acción crear) · `FilterBar` · tabla/lista · `ListPager` · estados | Plataformas (admin), Áreas, Usuarios, Inventario, Aprobaciones, Auditoría, Ejecuciones, Notificaciones, Mis solicitudes |
| Detalle | `PageHeader` (+ volver) · resumen (`Card` + `DataLabel`) · secciones · estados | Historial de usuario y de plataforma, Conectores (panel de configuración) |
| Formulario | `PageHeader` o `Modal` · secciones de `Field` · errores (`FieldErrorNote`, `focusFirstError`) · barra de acciones (primaria a la derecha) | Ajustes (pestañas), formularios en diálogo |
| Panel | `PageHeader` · rejilla de `StatTile`/`Card` · estados por bloque | Inicio, Catálogo, Favoritos |

### 4.6 Diálogo de alerta (estilo SweetAlert, propio)
| Aspecto | Regla |
|---|---|
| Forma | Centrado; ícono `icono-lg` por tipo (éxito, error, aviso, info, pregunta) con su familia de estado; título; texto; botones con verbo («Eliminar área», «Cancelar») |
| Base | `Modal` + `useFocusTrap` + `useScrollLock`; tokens y los 2 temas; sin `sweetalert2` ni estilos en línea |
| ARIA | `role="alertdialog"`, `aria-labelledby` (título), `aria-describedby` (texto) |
| Foco | Inicial en el botón **seguro** (Cancelar); Escape = cancelar; al cerrar vuelve al disparador |
| Cierre | Nunca automático si contiene información necesaria; el clic en el velo no confirma |
| Movimiento | Entrada con opacidad y escala; nada con `prefers-reduced-motion` |
| Ocupado | Botón de confirmar con `busy` (`aria-disabled`), sin cerrar hasta el resultado |

### 4.7 Diálogo o toast (tabla de decisión; va a `02-comportamiento.md`)
| Situación | Patrón | Se cierra solo |
|---|---|---|
| Acción destructiva o irreversible (eliminar, revocar, purgar, rechazar) | `AlertDialog` tipo pregunta/aviso; botón de peligro con verbo | No |
| Acción con efecto importante sobre otros (aprobar, reintentar, cambiar rol) | `AlertDialog` tipo pregunta | No |
| Resultado que el usuario debe leer o copiar (error que bloquea, resultado con datos) | `AlertDialog` éxito/error con «Entendido» | No |
| Éxito de rutina (guardado, marcado) | Toast éxito | Sí (≥ 5 s, pausa con hover y foco) |
| Error recuperable no crítico (favorito, tema) | Toast error | No mientras tenga foco; con botón cerrar |
| Error de validación de un campo | `FieldErrorNote` en línea | — |
| Error al cargar una vista | `ErrorNote` en la zona reservada | — |
| Estado persistente de la pantalla (falta configuración, sin enlace) | `Note` en línea | — |

## 5. Retiro de los 5 temas extra

### 5.1 Impacto por lugar
| Lugar | Cambio | Tarea |
|---|---|---|
| `tokens.css` | Borrar `theme-emerald-light`, `theme-obsidian-dark`, `theme-rose-light`, `theme-violet-dark`; SO oscuro = `html.dark` (mismos valores, prueba de igualdad) | DIS-054 |
| Pruebas de contraste | `tests/utils/tokens-css.ts` `CONTEXTOS` a 3 (claro, so-oscuro, html.dark); `contraste`, `velo`, `fallas-contraste-conocidas`, `chips-contraste`, comentarios de `pares-contraste` y `hover-botones` | DIS-054 |
| `lib/tema.ts` | `TEMAS` a 3; mapa de retirados (`esmeralda`/`rosa` → `claro`, `obsidiana`/`violeta` → `oscuro`) en `leerTema` y `aplicarTemaDeCuenta` | DIS-054 |
| Selector | Sin cambio de código (lee `TEMAS`); pruebas `tema.test.tsx`, `theme-selector-cuenta.test.tsx` | DIS-054 |
| Script de `<head>` | Se genera de `TEMAS`; agregar el mapa de retirados para `localStorage` | DIS-054 |
| `color-scheme` (`global.css`) | Quitar los 4 selectores `theme-*`; `tema-diseno.test.ts` | DIS-054 |
| Backend `TEMAS_VALIDOS` | `{sistema, claro, oscuro}` | FNC-132 |
| `pref_theme` guardado | Migración Alembic **0012**: `esmeralda`, `rosa` → `claro`; `obsidiana`, `violeta` → `oscuro`; cualquier otro fuera de la lista → `sistema`; `downgrade` sin cambio de datos (no se puede saber el original) | FNC-132 |
| FNC-123 (selector en la cuenta) | Sigue válido; un valor retirado en la cuenta se traduce en cliente, no cae a «sistema» | DIS-054 |
| Contrato | `preferences.theme` ∈ {`sistema`, `claro`, `oscuro`} ([preferencias.md](../contratos/preferencias.md)) | Antes de DIS-054 y FNC-132 |
| Docs | `03-reutilizacion.md`, `docs/frontend/README.md` §6, `estandarizacion/README.md`, `docs/backend/README.md`, `VARIABLES.md`/`HISTORIAL.md` (tokens) | DIS-054, FNC-132 |

Orden de despliegue: frontend (DIS-054) **antes o junto** con el backend (FNC-132); al revés, un cliente viejo que envíe `esmeralda` recibe `422` y ve el aviso de FNC-123.

### 5.2 «Según el sistema»: propuesta
- **Se queda, como opción por defecto.** Motivos:
  - todas las cuentas tienen hoy `pref_theme = 'sistema'` (valor por defecto de la migración 0011); retirarlo obliga a decidir por cada usuario;
  - respeta la preferencia del sistema operativo, que muchos usuarios fijan por fatiga visual o por la hora;
  - no cuesta un tercer tema: elige entre claro y oscuro.
- **Condición:** el bloque `@media (prefers-color-scheme: dark)` debe ser idéntico a `html.dark`, con una prueba que lo exija (ADR-007, alternativa A). Hoy difieren en 7 tokens.

## 6. Insumos del dueño (antes del bloque B)
| Insumo | Para qué | Tarea | Si no lo da: propuesta neutra | Motivo |
|---|---|---|---|---|
| Referencia visual o identidad de Vivaro | Tono general | DIS-055 | Interfaz administrativa sobria: neutros fríos, un solo acento | Herramienta interna de uso diario: legibilidad sobre decoración |
| Paleta (color de marca y, si hay, secundario) | Primitivos `marca` | DIS-055 | Azul (`#2563eb`, el actual) como único acento; estados rojo/verde/ámbar/azul estándar | Ya cumple AA medido y es el color que el personal reconoce |
| Tipografía y su licencia | `fuente-texto` | DIS-057 | Pila del sistema (`system-ui`, …), sin descargar fuentes | Sin licencia que verificar, sin peticiones externas, carga inmediata y sin salto por cambio de fuente |
| Logo (SVG, versión clara y oscura) | Cabecera, login, favicon | DIS-063 | Nombre del portal en texto con `fuente-texto` peso fuerte | No inventar una marca |
| Densidad (cómoda o compacta) | `espacio-*`, alto de controles | DIS-072 | Cómoda: controles de 48 px (ya exigido por área táctil) | Cumple área táctil sin excepciones |
| Juego de íconos (si Vivaro usa uno) | `Icono` | DIS-072 | SVG propios de trazo simple para los 5 tipos de alerta y las acciones actuales | Sin dependencia nueva; `currentColor` sigue el tema |
| Decisión DIS-053 (A o B) | Formularios de plataforma y Portal | DIS-053 | Opción A (retirar «Color de texto») | Opción B contradice P3 (colores libres sin contraste garantizado) |
| ADR-007 | Estructura de temas y nombres | DIS-054, DIS-055 | Recomendaciones del ADR | — |

## 7. Orden de ejecución
Máximo 2 agentes a la vez. «∥» = en paralelo (worktrees distintos).

Secuencia: **tokens → componentes base con todos sus estados → plantillas → migración de cada pantalla**. Rediseñar un componente actualiza todas las pantallas que lo usan.

| Bloque | Tareas | Depende de | Paralelo | Notas |
|---|---|---|---|---|
| 0 | Contrato `preferencias.md` + ADR-007 aprobados; insumos (§6) | — | — | Lo hace el dueño |
| A | DIS-054 ∥ FNC-132 | Bloque 0 (contrato, ADR) | Sí: archivos disjuntos | Integrar juntas (§5.1); no requieren insumos visuales |
| B — tokens | DIS-055 → DIS-056 → DIS-057 → DIS-072, ∥ DIS-068 → DIS-053 | A; insumos de paleta, tipografía y densidad | Tokens en serie (editan `tokens.css` y `tailwind.config.ts`); el segundo agente hace DIS-068 (pruebas y docs) y después DIS-053 (si se aprueba A) | DIS-068 congela el inventario: desde aquí no entra marcado nuevo a mano |
| C1 — componentes | DIS-058 ∥ DIS-060 | B | Sí | Botones (`form.tsx` `Button`, `.nexus-btn*`) ∥ pestañas y conmutadores (`tabs.tsx` nuevo, `settings-panel`, `my-requests-view`, `tag-picker`, `favorite-button`) |
| C2 | DIS-059 ∥ DIS-062 | C1 | Sí (mismo `components.css`, secciones distintas; las junta el `integrador`) | Campos ∥ avisos y estados |
| C3 | DIS-061 ∥ DIS-071 | C2 (DIS-061 toca `form.tsx` `Modal`) | Sí | Superficies y diálogos ∥ tablas y listas |
| C4 | DIS-069 ∥ DIS-063 | C3; DIS-063 necesita el logo | Sí | Filtros ∥ marco e identidad |
| C5 | DIS-073 ∥ DIS-074 | C3 (`Modal`, componente de datos), DIS-062 (`Note`) | Sí (`form.tsx`: `Modal` en DIS-073, `ConfirmDialog` en DIS-074) | Estabilidad (esqueletos, `scrollbar-gutter`, animación) ∥ `AlertDialog` |
| Control | `auditor-estandar` | C1–C5 cerradas | — | Duplicados y CSS repetido; lo confirmado entra como tarea Propuesta |
| P — plantillas | DIS-070 ∥ DIS-075 | C | Sí | `PageHeader` y 4 plantillas ∥ migración de confirmar y avisos |
| D1 — pantallas | DIS-064 ∥ DIS-065 | P | Sí | Usuario final ∥ gestión de accesos |
| D2 | DIS-066 | D1; DIS-053 decidida | — | Sistema |
| E | DIS-067 + `auditor-estandar` | D2 | — | Retiro de alias y de excepciones, CLS final, auditoría final |

### 7.1 Tareas
| ID | Plataforma | Título | Bloque | Depende de |
|---|---|---|---|---|
| FNC-132 | backend | `TEMAS_VALIDOS` a 3 y migración 0012 de `pref_theme` | A | Contrato |
| DIS-054 | web | Retirar los 5 temas extra y unificar el oscuro | A | Contrato, ADR-007 |
| DIS-055 | web | Tokens por capas: primitivos y semánticos | B | DIS-054, insumos |
| DIS-056 | web | Tokens de interacción y estado | B | DIS-055 |
| DIS-057 | web | Escalas: tipografía, radios, bordes y sombras | B | DIS-056, insumos |
| DIS-072 | web | Simetría: escala de espaciado, alturas, rejilla, anchos e íconos | B | DIS-057, insumos |
| DIS-068 | web | Prueba «un patrón, un componente» e inventario de patrones | B | DIS-054 |
| DIS-058 | web | Botones y enlaces: estados y `ButtonLink` | C1 | DIS-072, DIS-068 |
| DIS-060 | web | Pestañas y conmutadores: `Tabs` y `ToggleChip` | C1 | DIS-072, DIS-068 |
| DIS-059 | web | Campos de formulario: estados (inválido, solo lectura) | C2 | DIS-058 |
| DIS-062 | web | Avisos y estados: `Note`, vacío, carga, insignias, toast | C2 | DIS-058 |
| DIS-061 | web | Superficies y diálogos: `Card`, `PanelHeader`, `Modal`, `Drawer` | C3 | DIS-059 |
| DIS-071 | web | Tablas y listas: un solo componente de datos | C3 | DIS-058, DIS-062 |
| DIS-069 | web | Barras de filtros: todas sobre `FilterBar` | C4 | DIS-059 |
| DIS-063 | web | Marco e identidad: cabecera, menú, login, 404/500 | C4 | DIS-061, logo |
| DIS-073 | web | Sin saltos de diseño: esqueletos, zonas reservadas y diálogos estables | C5 | DIS-061, DIS-071, DIS-062 |
| DIS-074 | web | `AlertDialog` propio (estilo SweetAlert) y tabla diálogo/toast | C5 | DIS-061, DIS-062, DIS-072 |
| DIS-070 | web | `PageHeader` y plantillas de pantalla | P | C1–C5 |
| DIS-075 | web | Migrar los confirmar y avisos actuales a `AlertDialog`/toast | P | DIS-074 |
| DIS-064 | web | Pantallas de usuario final | D1 | DIS-070, DIS-075 |
| DIS-065 | web | Pantallas de gestión de accesos | D1 | DIS-070, DIS-075 |
| DIS-066 | web | Pantallas de sistema | D2 | DIS-070, DIS-075, DIS-053 |
| DIS-067 | web | Cierre: retiro de alias y excepciones, registro y auditoría | E | D1, D2 |

## 8. Verificación
| Tipo | Qué | Dónde / tarea |
|---|---|---|
| Automática: contraste | Cada token semántico de texto y borde medido en claro, SO oscuro y `html.dark` (`pares-contraste.ts`, `contraste.test.ts`) | DIS-054, DIS-055, DIS-056 |
| Automática: oscuro único | SO oscuro y `html.dark` con el mismo conjunto y valores | DIS-054 (nueva) |
| Automática: completitud | Todo semántico definido en los 2 temas; ningún primitivo usado fuera de `tokens.css` | DIS-055 (nueva) |
| Automática: estados con token | Cada clase/componente de la matriz §4.3 declara sus estados con `var(--…)`; sin `opacity-NN` ni `dark:` en TSX | DIS-056 (nueva), ampliada en C1–C5 |
| Automática: escala | `escala-simetria.test.ts`: sin clases de espaciado, alto o ancho fuera de la escala ni valores arbitrarios (`p-[13px]`, `tracking-[…]`, `min-w-[…]`, `grid-cols-[…]`), sin `px`/`rem` sueltos en `components.css`/`global.css` fuera de `tokens.css`; excepciones con motivo que solo pueden bajar | DIS-072 (nueva) |
| Automática: un patrón, un componente | `patrones-unicos.test.ts`: sin `<table>` fuera del componente de datos, sin `nexus-btn`/clases de botón fuera de `Button`/`ButtonLink`, sin `<input>`/`<select>`/`<textarea>` fuera de `form.tsx`, sin `role="dialog"`/`"alertdialog"` fuera de `Modal`/`Drawer`/`AlertDialog`, sin `<h1>` fuera de `PageHeader`, sin `role="tablist"` fuera de `Tabs`, sin tintes de estado (`bg-<estado>/NN`) fuera de `Note`/`Badge`; excepciones con motivo y tarea, que solo pueden bajar | DIS-068 (nueva); cada tarea C/P/D retira sus excepciones; DIS-067 deja la lista vacía o justificada |
| Automática: estabilidad | `scrollbar-gutter: stable` en los contenedores desplazables; `Modal` sin animar propiedades de caja; `Skeleton` con alto igual al del contenido final (prueba de componente) | DIS-073 (nueva) |
| Automática: alerta | `AlertDialog`: `role="alertdialog"`, `aria-labelledby`/`-describedby`, foco en el botón seguro, Escape cancela y devuelve el foco, sin cierre automático, sin animación con reducción de movimiento | DIS-074 (nueva) |
| `auditor-estandar` | Duplicados, CSS repetido y componentes que se saltan el catálogo | Al cerrar C1–C5 y en DIS-067 |
| Documentación | `03-reutilizacion.md` (catálogo y duplicados D-18+), `01-visual.md` (tokens, matriz, simetría), `02-comportamiento.md` (plantillas, estados, estabilidad y tabla diálogo/toast) | DIS-055, DIS-068, DIS-072, DIS-073, DIS-074, DIS-070, DIS-067 |
| Automática: existentes | `colores-literales`, `sin-estilos-inline`, `css-sin-uso`, `texto-minimo`, `area-tactil`, `hover-botones`, `velo` en verde | Todas |
| Automática: backend | `test_tema_en_la_cuenta.py`, `test_migracion_0012.py` (nueva), `test_migraciones.py` | FNC-132 |
| Visual en navegador | Cada pantalla en claro y oscuro, 360 px y 1280 px, con estados de carga, vacío y error; captura o nota en la ficha | C1–D2 |
| CLS en navegador | Panel de rendimiento o Lighthouse: CLS < 0,01 al cargar y al abrir/cerrar un diálogo en Inicio, Plataformas, Mis solicitudes, Aprobaciones, Usuarios, Auditoría y Ajustes; valor anotado en la ficha | DIS-073 (línea base), D1, D2, DIS-067 |
| `auditor-accesibilidad` | Cierra cada tarea DIS (contraste medido en los 2 temas, foco, tamaños) | Todas las DIS |
| `auditor-seguridad` | Migración de datos de usuario | FNC-132 |

## 9. Riesgos
| Riesgo | Mitigación |
|---|---|
| Regresiones de contraste al cambiar paleta o renombrar | Pares por token semántico; alias con el mismo valor hasta DIS-067; `auditor-accesibilidad` en cada tarea |
| Romper preferencias guardadas (`pref_theme`, `localStorage` `nexus-tema`) | Migración 0012 con prueba; mapa de retirados en cliente; despliegue frontend antes o junto al backend |
| Pantallas con colores libres (chips de DIS-048: `bg_color`, `area.color`) | No se tocan las garantías de DIS-048 (`textoLegible`, texto del tema en `.nx-chip-tint`); DIS-062 las vuelve a medir en los 2 temas |
| DIS-053: «Color de texto» sin efecto | Decisión del dueño antes de DIS-066; recomendada la opción A |
| Renombre masivo (`label` 160 usos, `primary` 63) | Alias temporales; migración por componente y pantalla; retiro al final (DIS-067) |
| Escala estricta rompe composiciones actuales (38 usos fuera de escala, 10 plantillas de columnas) | Excepciones con motivo en la prueba; se retiran en la migración de cada pantalla |
| Diálogos de confirmación que hoy llevan formulario (motivo de rechazo, rol) | `AlertDialog` admite cuerpo con campos; mantiene `aria-busy` y errores en línea |
| `scrollbar-gutter` reserva un canal vacío en pantallas sin desplazamiento | Aceptado: es el costo de no mover el fondo; se valida en móvil (barras superpuestas no ocupan canal) |
| Conflictos en `tokens.css`/`components.css`/`form.tsx` con agentes en paralelo | Bloque B en serie; en C, pares con archivos disjuntos o secciones distintas |
| FNC-131 (en curso) edita `ROADMAP.md` y `TABLERO.md` | Conflicto solo de texto al integrar; lo resuelve el `integrador` |
| Prueba sin versionar `color-legible-hex.PENDIENTE.test.tsx` | No se toca; sigue pendiente de decisión del dueño (DIS-048) |
| Diseño subjetivo sin insumos | Propuesta neutra documentada (§6); los valores viven en primitivos y se cambian sin tocar componentes |

## 10. Sugerencias fuera de alcance (sin tarea)
- Retirar el mapa de temas retirados del cliente una versión después del despliegue.
- Contraste de los colores que elige el usuario al guardar (FNC-033, ya en Propuesta).
- Modo de alto contraste (`prefers-contrast: more`).
- Catálogo visual de componentes (página interna o Storybook).
- Medición continua de CLS en CI (Lighthouse CI) cuando exista el CI (FNC-026).
