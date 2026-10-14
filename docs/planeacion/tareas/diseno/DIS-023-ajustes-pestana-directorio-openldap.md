# DIS-023 — Ajustes: pestaña Directorio para OpenLDAP

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-directorio |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-023-ajustes-pestana-directorio-openldap` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- La pestaña Directorio de `settings-panel.tsx` (745 líneas) pide contraseña de bind, usa `sAMAccountName` por defecto y mapeos de rol que dejan de existir (FNC-042, FNC-043)
- Requerimientos: F-ACC-01, RNF-03

## Objetivo
- Pestaña que muestra la configuración efectiva y su origen, permite editar solo lo no sensible que permita ADR-004 y prueba la conexión; sin campos de contraseña ni mapeos de rol

## Alcance
- **Incluye:**
  - Pestaña extraída a `components/settings/directory-tab.tsx`; `settings-panel.tsx` solo la importa
  - Estados de conexión y origen de cada valor
- **No incluye:**
  - Las demás pestañas y la división completa de `settings-panel.tsx` (DIS-011)

## Archivos previstos
- `frontend/src/components/settings/directory-tab.tsx`
- `frontend/src/components/settings-panel.tsx` (reemplazo de la pestaña por la importación)

## Reutilización
- `Field`, `TextInput`, `Button`, `ErrorNote`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `settings-panel.tsx` | Pantalla | `/settings` (todas las pestañas) | Pendiente |

## Criterios de aceptación
- [ ] Las demás pestañas no cambian (verificación visual)
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-043
- Contrato → docs/contratos/usuarios-directorio.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
