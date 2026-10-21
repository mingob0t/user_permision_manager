# DIS-035 — Administrar plataformas: enlace al historial y acciones de fila de 48 px

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- DIS-020 creó `/audit/platforms/[id]` y lo enlaza desde Inventario y (por usuario) desde Usuarios
- La ficha de DIS-020 pedía enlazarlo también desde Plataformas; en `platform-admin.tsx` las acciones de fila ("Editar", "Eliminar") son botones de texto de ~28 px, sin el estándar de 48 px

## Objetivo
- Acción "Historial" por plataforma (`rutaHistorialPlataforma` de `components/audit/audit-routes.ts`) junto con Editar y Eliminar, todas con 48 px (`.nexus-btn` o un menú de fila)

## Impacto cruzado
- Origen ← DIS-020
- Relacionada → DIS-008 (área táctil de botones de fila), DIS-032
