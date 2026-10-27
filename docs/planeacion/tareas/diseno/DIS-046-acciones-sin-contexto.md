# DIS-046 — Nombres con contexto en acciones de fila y cabecera de "Acciones"

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |

## Contexto
- `users-list.tsx`: "Editar" y "Eliminar" de cada tarjeta no tienen `aria-label` con el nombre del usuario (sí "Accesos" y las de rol); en una lista de lectores de pantalla se repiten sin contexto
- `platform-admin.tsx`: la columna de acciones tiene `<th>` vacío (sin texto ni `sr-only`)

## Objetivo
- `aria-label` "Editar {nombre}" / "Eliminar {nombre}" en Usuarios (como en Áreas y Plataformas) y cabecera "Acciones" (`sr-only` si el dueño no la quiere visible)
- Ajustar las pruebas que buscan por texto "Editar"

## Impacto cruzado
- Origen ← DIS-008
