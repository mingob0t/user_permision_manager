# DIS-051 — PlatformCard: botón dentro de enlace y foco al quitar favorito en /favorites

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |

## Contexto
- `PlatformCard` es un `<a>` que contiene el botón de favorito (interactivo anidado) y, al quitar un favorito en `/favorites`, la tarjeta sale de la lista y el foco cae en `body`
- Observación del auditor de DIS-030; `/platforms` ya no tiene el problema (la estrella va fuera del enlace en `RequestCatalogCard`)

## Objetivo
- Estrella fuera del enlace (como en `RequestCatalogCard`) y foco a un destino estable al quitar un favorito
- Pruebas de componente y de foco

## Impacto cruzado
- Origen ← DIS-030
