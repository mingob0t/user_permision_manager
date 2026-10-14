# DIS-013 — Catálogo: solicitar acceso con nivel y justificación

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | catalogo |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-013-catalogo-solicitar-acceso` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El catálogo (`platform-catalog.tsx`, `platform-card.tsx`) solo abre enlaces y marca favoritos; no permite solicitar (F-SOL-01)
- El admin lo usa para áreas ajenas
- Requerimientos: F-SOL-01, F-SOL-02, RF-03

## Objetivo
- Mostrar el catálogo solicitable por área con el estado del usuario en cada plataforma (sin acceso, pendiente, con acceso y nivel) y un formulario modal para solicitar nivel `usuario` o `admin` con justificación

## Alcance
- **Incluye:**
  - Vista del catálogo solicitable con filtro por área y búsqueda
  - Indicador de estado por tarjeta (texto + insignia, no solo color)
  - Modal de solicitud: nivel (radio), justificación con contador y validación visible, envío y confirmación
  - Mensajes para 409 (duplicado o ya tiene acceso)
- **No incluye:**
  - Mis solicitudes (DIS-014)
  - Rediseñar la tarjeta existente fuera de lo necesario

## Archivos previstos
- `frontend/src/components/access/request-catalog.tsx`
- `frontend/src/components/access/request-form-modal.tsx`
- `frontend/src/components/access/access-status-badge.tsx` (reutilizable)
- `frontend/src/app/platforms/page.tsx` según P1

## Reutilización
- `Modal`, `Field`, `TextArea`, `Button` de `form.tsx`; `Badge`, `Spinner`, `EmptyNote`, `ErrorNote` de `ui.tsx`; `PlatformCard` si admite la acción sin cambiar su uso en Favoritos

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `PlatformCard` | Componente | Catálogo y Favoritos (`favorites-list.tsx`) | Pendiente |

## Criterios de aceptación
- [ ] La justificación inválida se anuncia al lector de pantalla
- [ ] Tras enviar, el estado de la tarjeta cambia a "pendiente" sin recargar
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-056
- Contrato → docs/contratos/solicitudes.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
