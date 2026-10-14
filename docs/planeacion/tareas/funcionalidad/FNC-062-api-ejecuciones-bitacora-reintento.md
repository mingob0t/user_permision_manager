# FNC-062 — API de ejecuciones: bitácora de aprovisionamiento y reintento manual

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | aprovisionamiento |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-062-api-ejecuciones-bitacora-reintento` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (acciones privilegiadas) |

## Contexto
- Las ejecuciones (FNC-049) tienen bitácora, pero nadie la ve; un acceso `fallido` tras agotar reintentos no tiene salida salvo revocar y volver a solicitar
- Requerimientos: F-CON-01

## Objetivo
- Exponer la bitácora de ejecuciones (por plataforma, usuario, estado) y el reintento manual según P10

## Alcance
- **Incluye:**
  - `GET /provisioning/jobs` con filtros y paginación; detalle con intentos
  - Alcance: superadmin todo; admin las de sus áreas (lectura)
  - `POST /provisioning/jobs/<id>/retry` para trabajos `fallido` (rol según P10)
- **No incluye:**
  - Cancelar trabajos (no pedido)
  - Pantalla (DIS-022, DIS-018)

## Archivos previstos
- `app/modules/provisioning/api.py`
- `app/__init__.py` (registro)
- `tests/provisioning/test_api.py`

## Reutilización
- Modelos y cola de FNC-049

## Criterios de aceptación
- [ ] Matriz de permisos por rol (pruebas)
- [ ] Reintentar un trabajo no fallido responde 409 (prueba)
- [ ] Los errores mostrados están saneados (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-022
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-049, FNC-038, Respuesta a P10
- Contrato → docs/contratos/conectores-y-ejecuciones.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
