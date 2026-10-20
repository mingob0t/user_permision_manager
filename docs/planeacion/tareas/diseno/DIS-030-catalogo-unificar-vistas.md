# DIS-030 — Catálogo: unificar el catálogo solicitable y "Mis plataformas"

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | catalogo |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- DIS-013 dejó en `/platforms` dos secciones con su propio filtro y búsqueda: el catálogo solicitable (`access/request-catalog.tsx`) y "Mis plataformas" (`platform-catalog.tsx`, con enlace y favorito)
- `CatalogItem` no trae `direct_link` ni favorito; una sola vista necesita esos datos (posible FNC) o un cruce con `GET /platforms`

## Objetivo
- Una sola vista con estado, solicitud y apertura del enlace; un filtro y una búsqueda

## Impacto cruzado
- Origen ← DIS-013
- Depende del rediseño visual del dueño
