# FNC-046 — Plataformas: tipo de integración y grupos LDAP por nivel

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-046-plataformas-integracion-grupos-nivel` |
| **Requiere migración BD** | Sí (columnas nuevas en `platforms`) |
| **Requiere auditor-seguridad** | Sí (validación de URL y DN) |

## Contexto
- `Platform` (`app/modules/core/models.py:37`) no tiene tipo de integración ni grupos (F-PLAT-01)
- `direct_link` y `logo_url` aceptan cualquier esquema (SEG-24)
- Requerimientos: F-PLAT-01, RF-01, RF-02

## Objetivo
- Agregar a la plataforma `integration_type` (`ldap` o `conector`) y los DN de sus grupos de nivel `usuario` y `admin`, validados contra la convención de ADR-004 y, si es posible, contra el directorio

## Alcance
- **Incluye:**
  - Columnas `integration_type`, `ldap_group_user_dn`, `ldap_group_admin_dn` (nulos solo si es `conector` y ADR-004 lo permite)
  - Validación en `POST/PUT /platforms`: DN dentro de `LDAP_GROUPS_BASE_DN`, grupos distintos por nivel, existencia comprobada con el cliente de FNC-040 (aviso si no existe)
  - Validación de `direct_link` y `logo_url`: solo `https://` (o `http://` si el dueño lo justifica)
  - Cambiar el tipo o los grupos con accesos activos responde 409 (no hay migración de miembros en v1)
  - `to_dict` incluye los campos nuevos; deja de exponer `user_ids` si FNC-065 se aprueba
- **No incluye:**
  - Configuración del conector (FNC-050, FNC-061)
  - Crear los grupos en el directorio (ADR-004)
  - Pantalla (DIS-017)

## Hallazgos de seguridad que absorbe
- **FNC-017** parcial: SEG-24 (validación de URL en `crud.py:139-142`, `:158-168`).

## Archivos previstos
- `app/modules/core/models.py` (`Platform`)
- `app/modules/core/validators.py` (nuevo)
- `app/modules/api/crud.py` (`create_platform`, `update_platform`)
- Migración (ADR-002)
- `tests/platforms/`

## Reutilización
- Cliente de FNC-040 para comprobar grupos
- `platform_manage_required`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `Platform.to_dict` | Serialización | `GET /platforms`, `/favorites`, `/stats`, catálogo, favoritos, administración de plataformas | Pendiente |
| Modelo `Platform` | Modelo | Todos los módulos que leen plataformas | Pendiente |

## Criterios de aceptación
- [ ] Alta de plataforma `ldap` sin grupos responde 400 (prueba)
- [ ] DN fuera de la base de grupos responde 400 (prueba)
- [ ] `javascript:` en `direct_link` responde 400 (prueba de regresión)
- [ ] Cambio de grupos con accesos activos responde 409 (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-017
- Genera → FNC-050
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, FNC-040, FNC-038, FNC-047
- Contrato → docs/contratos/plataformas-integracion.md

## Riesgos y reversión
- Plataformas existentes quedan sin grupos: la migración las marca `ldap` sin grupos y no se pueden solicitar hasta completarlas.
- Reversión: bajar la migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
