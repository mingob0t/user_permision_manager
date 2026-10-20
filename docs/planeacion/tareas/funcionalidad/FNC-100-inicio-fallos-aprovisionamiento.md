# FNC-100 — Inicio: fallos de aprovisionamiento visibles por rol

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | estadisticas |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de datos por rol) |

## Contexto
- FNC-066 entrega `failed_access` (accesos `fallido` y `fallo_revocacion`), no los trabajos fallidos del ejecutor.
- `provisioning/consultas.visibles` (alcance por rol de los trabajos) es de FNC-062 y aún no está en `develop`.

## Alcance
- **Incluye:** campo opcional `failed_jobs` (int) en `GET /home/summary` para admin y superadmin, contado con `provisioning.consultas.visibles`; nota en el Historial de `inicio.md` (campo opcional: misma versión).
- **No incluye:** listas de trabajos, pantalla (DIS-024).

## Criterios de aceptación
- [ ] Cada rol cuenta solo los trabajos que puede ver en la bitácora de FNC-062 (pruebas).

## Impacto cruzado
- Origen ← FNC-066
- Depende de → FNC-062 (merge a develop)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada como Propuesta (FNC-066) |
