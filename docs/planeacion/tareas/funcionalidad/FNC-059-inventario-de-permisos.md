# FNC-059 — Inventario de permisos: quién tiene qué plataforma, nivel, desde cuándo y quién aprobó

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-059-inventario-de-permisos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de datos por rol) |

## Contexto
- F-AUD-02 pide un inventario de permisos; hoy no existe y los datos nacen con FNC-054
- Requerimientos: F-AUD-02, F-AUD-04, RF-05

## Objetivo
- Exponer `GET /access/inventory` con filtros (área, plataforma, usuario, nivel, estado, origen) y paginación, con alcance superadmin todo, admin sus áreas y usuario lo suyo

## Alcance
- **Incluye:**
  - Consulta paginada y filtrable desde `platform_access_grants`
  - Columnas: usuario, plataforma, área, nivel, origen, desde, quién aprobó, estado
  - Alcance por rol
- **No incluye:**
  - Exportar a CSV o Excel (sugerencia fuera de alcance)
  - Conciliación con LDAP (RF-05)
  - Pantalla (DIS-021)

## Archivos previstos
- `app/modules/access/inventory.py`
- `app/modules/access/api.py` (una ruta)
- `tests/access/test_inventory.py`

## Reutilización
- Modelo de FNC-054
- `scoped_platforms` o `managed_area_ids` de `app/authz.py`

## Variables y configuración
- `ACCESS_INVENTORY_PAGE_SIZE_MAX` (constante registrada).

## Criterios de aceptación
- [ ] Un admin no ve accesos de áreas ajenas, ni filtrando por ellas (prueba)
- [ ] Un usuario solo ve los suyos (prueba)
- [ ] Paginación con límite máximo como constante registrada
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-021
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-038
- Contrato → docs/contratos/accesos.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
