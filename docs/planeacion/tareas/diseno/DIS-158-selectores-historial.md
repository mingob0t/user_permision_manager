# DIS-158 — Historial de solicitudes: selectores con el estándar de la barra

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (reclamo del dueño: DIS-156 usó `Select` nativo) |

## Cambios
- `selector-toolbar.tsx` (nuevo): `SelectorToolbar`, el patrón de `platform-admin.tsx` («Estado: Todos»): botón 48 px con ícono, «Etiqueta: valor», chevron; menú `listbox` con la elegida marcada; clic fuera/Escape cierran y devuelven el foco; flechas, Inicio y Fin. Valor anunciado con `aria-describedby`.
- `access/approvals-inbox-toolbar.tsx`: Estado (`inventario`), Área (`areas`) y Plataforma (`plataformas`) usan `SelectorToolbar`.
- `access/approvals-inbox.tsx`: «Todas las áreas» → «Todas» (la etiqueta ya dice «Área:»).
- Pruebas: `selector-toolbar.test.tsx` (nuevo), `tests/utils/selector-toolbar.ts` (ayudas), bandeja y `filtro-url` migradas.

## Impacto en elementos compartidos
- `SelectorToolbar` es nuevo; solo lo usa el Historial. `platform-admin.tsx` sigue con su copia escrita a mano: migrarlo es DIS-159 (Propuesta).
