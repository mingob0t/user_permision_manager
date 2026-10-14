# DIS-017 — Plataformas: tipo de integración y grupos por nivel

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-017-plataformas-integracion-grupos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `platform-admin.tsx` (327 líneas) no tiene tipo de integración ni grupos (F-PLAT-01) y asigna usuarios directamente (`user_platforms`)
- Requerimientos: F-PLAT-01, RF-02

## Objetivo
- Agregar al formulario de plataforma el tipo (`ldap`/`conector`), los grupos de nivel usuario y admin con ayuda de formato, y el enlace a la configuración del conector (superadmin); retirar la asignación directa de usuarios si FNC-065 se aprueba

## Alcance
- **Incluye:**
  - Sección "Integración" en un componente propio
  - Mensajes de validación del backend (DN fuera de base, grupos iguales)
  - Aviso de que cambiar grupos con accesos activos no está permitido
- **No incluye:**
  - Dividir `platform-admin.tsx` (DIS-011)
  - Estilos inline existentes (DIS-012)

## Archivos previstos
- `frontend/src/components/platforms/platform-integration-fields.tsx`
- `frontend/src/components/platform-admin.tsx` (importación y retiro de la asignación si aplica)

## Reutilización
- `Field`, `TextInput`, `Select` de `form.tsx`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `platform-admin.tsx` | Pantalla | `/admin/platforms` | Pendiente |

## Criterios de aceptación
- [ ] Los textos explican "grupo de acceso" sin exigir conocer LDAP más allá del DN
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-046
- Contrato → docs/contratos/plataformas-integracion.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
