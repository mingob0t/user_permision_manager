# DIS-051 — PlatformCard: botón dentro de enlace y foco al quitar favorito en /favorites

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-27 |

## Contexto
- `PlatformCard` es un `<a>` que contiene el botón de favorito (interactivo anidado) y, al quitar un favorito en `/favorites`, la tarjeta sale de la lista y el foco cae en `body`
- Observación del auditor de DIS-030; `/platforms` ya no tiene el problema (la estrella va fuera del enlace en `RequestCatalogCard`)

## Objetivo
- Estrella fuera del enlace (como en `RequestCatalogCard`) y foco a un destino estable al quitar un favorito
- Pruebas de componente y de foco

## Impacto cruzado
- Origen ← DIS-030

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- Tarjeta `div`; el enlace es el nombre y su `after:absolute after:inset-0` cubre la tarjeta; la estrella va en un hermano `relative z-10`. Visita y aspecto se conservan; el anillo de foco se dibuja en el pseudo-elemento.
- Foco en `/favorites`: siguiente tarjeta, si era la última la anterior, si no queda ninguna el `h1` (`tabIndex=-1`). Va a la estrella de la tarjeta destino (misma posición que el foco perdido). Anuncio con `RegionDeAnuncios`.
- Cada tarjeta se envuelve en `div.contents` con `data-favorito-id` para localizarla sin cambiar la rejilla.
- Excepción en `area-tactil.excepciones.ts` (1) para el enlace: su área real es la tarjeta completa.

## Impacto en elementos compartidos
- `PlatformCard` (`platform-card.tsx`): estructura DOM cambiada (`a` raíz pasa a `div`; enlace solo en el nombre). Usos: `favorites-list.tsx` (`/favorites`) y pruebas `platform-card.test.tsx`, `chips-contraste.test.tsx` (en verde). `RequestCatalogCard` no la usa.
- `FavoriteButton`: sin cambios.
- `tests/accesibilidad/area-tactil.excepciones.ts`: nueva excepción.

## Verificación
- `frontend/`: typecheck 0, lint 0, vitest 0 (53 archivos, 1691 pruebas), build 0; pruebas de accesibilidad en 0 fallas.
- Nuevas: `tests/components/favorites-list.test.tsx` (sin `button` dentro de `a`; foco a siguiente, anterior y encabezado; anuncio).
- No verificado en navegador (temas, móvil, foco real); auditor-accesibilidad independiente pendiente.

## Bitácora
- 2026-10-27: implementada; En revisión.
