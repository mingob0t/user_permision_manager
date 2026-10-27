# DIS-030 — Catálogo: unificar el catálogo solicitable y "Mis plataformas"

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | catalogo |
| **Prioridad** | Media |
| **Estatus** | Hecha |
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
| `PlatformCard` | `favorites-list.tsx` (`/favorites`) | La estrella pasa a `FavoriteButton`; cambia su nombre accesible (`Favorito: <nombre>`) y usa `aria-disabled`; validar `/favorites` |
| `FavoriteButton` (nuevo) | `PlatformCard`, `RequestCatalogCard` | Componente nuevo |
| `RequestCatalog`, `RequestCatalogCard` | solo `/platforms` | Prop opcional `mias`/`mine`; filtros con `FilterBar` (`aria-label` iguales) |
| `platform-catalog.tsx` | — | Retirado; ya nadie lo importa |
Los demás nombres que reporta `impacto.py` (`Page`, `body`, `coincide`, `motivo`, `cerrarAviso`, `toggleFavorite`) son homónimos.

## Verificación
| Comando (en `frontend/`) | Salida |
|---|---|
| `tsc --noEmit` | 0 |
| `npm run lint` | 0 |
| `vitest run` | 0 (1685 pruebas, accesibilidad 0 fallas) |
| `npm run build` | 0 |
- Prueba nueva `tests/components/platforms-view.test.tsx`: por rol (usuario, admin de área, superadmin), estados (carga, vacío, error de ambos orígenes, 403), enlace https, favorito, visita, solicitar y `unirCatalogo`.
- **Revisión propia** (sin aprobación de `auditor-accesibilidad` ni `revisor`: no pueden lanzarse desde esta sesión). Una revisión previa dio M1, B1, B3 y observaciones, corregidas. La auditoría independiente de accesibilidad salió «Requiere cambios» y se corrigió: etiqueta fija `Favorito: <nombre>` con `aria-pressed`; `aria-disabled` en vez de `disabled` (el foco se queda); «Abrir X (se abre en una pestaña nueva)»; «Abrir» solo con acceso efectivo `activo` (con `en_proceso`, `fallido`, `revocando` o `fallo_revocacion`, solo la insignia). Pendiente: nueva auditoría independiente.
- No verificado en navegador (temas y móvil solo por tokens y pruebas).
- Propuestas: DIS-051 (`PlatformCard`: botón dentro de enlace y foco al quitar favorito) y DIS-052 (dividir `RequestCatalog`). "Abrir" duplicado con `PlatformCard` queda anotado.

## Bitácora
| 2026-10-27 | Aprobada en modo autónomo, En curso y En revisión; implementada |
| 2026-10-27 | Correcciones de la auditoría independiente de accesibilidad (4 puntos, con prueba previa); propone DIS-051 y DIS-052 |

- 2026-10-27: `auditor-accesibilidad` independiente Aprobado tras corregir nombre fijo y foco del favorito, aviso de pestaña nueva y «Abrir» solo con acceso activo (`6ca3c85`). Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto). Sin verificar en navegador.
