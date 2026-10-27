# DIS-030 — Catálogo: unificar el catálogo solicitable y "Mis plataformas"

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | catalogo |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-20 |

## Contexto
- DIS-013 dejó en `/platforms` dos secciones con su propio filtro y búsqueda: el catálogo solicitable (`access/request-catalog.tsx`) y "Mis plataformas" (`platform-catalog.tsx`, con enlace y favorito)
- `CatalogItem` no trae `direct_link` ni favorito; una sola vista necesita esos datos (posible FNC) o un cruce con `GET /platforms`

## Objetivo
- Una sola vista con estado, solicitud y apertura del enlace; un filtro y una búsqueda

## Impacto cruzado
- Origen ← DIS-013
- Depende del rediseño visual del dueño

## Decisiones
- Decisión del orquestador (pendiente de validar en la prueba de concepto): cruce en el cliente de `GET /access-requests/catalog` con `GET /platforms`; **sin FNC** (no se toca el backend).
- Decisión del orquestador (pendiente de validar en la prueba de concepto): opción que menos cambia la navegación: sigue `/platforms`, `RequestCatalog` es la vista única y `PlatformCatalog` se retira; título "Catálogo".
- Decisión del orquestador (pendiente de validar en la prueba de concepto): las abribles que el catálogo no trae se agregan como "Con acceso" sin solicitar; admin de área y superadmin (estado nulo en el catálogo) muestran "Con acceso" si pueden abrirla.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): estrella extraída a `FavoriteButton`; "Abrir" con `nexus-btn-primary`; sin permiso al catálogo (403) se muestran igual las propias.

## Impacto en elementos compartidos
| Elemento | Usado en | Qué cambió |
|---|---|---|
| `PlatformCard` | `favorites-list.tsx` (`/favorites`) | La estrella pasa a `FavoriteButton`, mismo marcado y clases; validar `/favorites` |
| `FavoriteButton` (nuevo) | `PlatformCard`, `RequestCatalogCard` | Componente nuevo |
| `RequestCatalog`, `RequestCatalogCard` | solo `/platforms` | Prop opcional `mias`/`mine`; filtros con `FilterBar` (`aria-label` iguales) |
| `platform-catalog.tsx` | — | Retirado; ya nadie lo importa |
Los demás nombres que reporta `impacto.py` (`Page`, `body`, `coincide`, `motivo`, `cerrarAviso`, `toggleFavorite`) son homónimos.

## Verificación
| Comando (en `frontend/`) | Salida |
|---|---|
| `tsc --noEmit` | 0 |
| `npm run lint` | 0 |
| `vitest run` | 0 (1679 pruebas, accesibilidad 0 fallas) |
| `npm run build` | 0 |
- Prueba nueva `tests/components/platforms-view.test.tsx`: por rol (usuario, admin de área, superadmin), estados (carga, vacío, error de ambos orígenes, 403), enlace https, favorito, visita, solicitar y `unirCatalogo`.
- auditor-accesibilidad: Aprobado (contraste medido, 48 px, nombres). Revisor: M1 (insignia "Sin acceso" con "Abrir"), B1, B3 corregidos.
- No verificado en navegador (temas y móvil solo por tokens y pruebas).
- Pendientes menores: "(se abre en una pestaña nueva)" en el nombre de "Abrir"; `FavoriteButton` con `disabled` durante la petición pierde el foco (heredado); etiqueta de la estrella sin nombre de plataforma; `RequestCatalog` (~175 líneas) como monolito previo; "Abrir" duplicado con `PlatformCard`.

## Bitácora
| 2026-10-27 | Aprobada en modo autónomo, En curso y En revisión; implementada, revisor y auditor-accesibilidad atendidos |
