# FNC-061 — API de configuración de conectores (superadmin)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-061-api-configuracion-conectores` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (configuración de credenciales) |

## Contexto
- La configuración de conectores la hace solo el superadmin (REQUERIMIENTOS §2 y tabla de pantallas)
- Sin API no se puede dar de alta un conector
- Requerimientos: F-CON-01

## Objetivo
- Exponer el CRUD de `platform_connectors` y una prueba de conexión (`check`) que no otorga ni revoca

## Alcance
- **Incluye:**
  - `GET/PUT /platforms/<id>/connector`, `DELETE` si no hay accesos activos
  - `POST /platforms/<id>/connector/test` con mensaje genérico
  - Validación de parámetros por tipo y de la referencia de credencial (existe, sin leer el valor en la respuesta)
  - Solo `admin_required`
- **No incluye:**
  - Pantalla (DIS-022)
  - Alta de ítems en Vaultwarden (lo hace el superadmin en Vaultwarden)

## Archivos previstos
- `app/modules/connectors/api.py`
- `app/__init__.py` (registro)
- `tests/connectors/test_api.py`

## Reutilización
- Modelo, registro y resolvedor de FNC-050
- `admin_required`

## Criterios de aceptación
- [ ] Admin de área y usuario reciben 403 (prueba)
- [ ] Ninguna respuesta incluye secretos (prueba)
- [ ] Parámetros inválidos para el tipo responden 400 (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-022
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-050, FNC-038
- Contrato → docs/contratos/conectores-y-ejecuciones.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
