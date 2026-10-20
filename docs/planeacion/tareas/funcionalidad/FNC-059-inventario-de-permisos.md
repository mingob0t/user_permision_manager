# FNC-059 — Inventario de permisos: quién tiene qué plataforma, nivel, desde cuándo y quién aprobó

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local |
| **Rama** | `fnc/FNC-059-inventario-permisos` |
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

Realizados (FNC-058 trabaja `access/api.py` en paralelo: blueprint propio):
- `app/modules/access/inventario.py` (consulta: `visibles`, `filtrar`, `ordenados`)
- `app/modules/access/inventario_api.py` (ruta y parámetros, `ACCESS_INVENTORY_PAGE_SIZE_MAX`)
- `app/modules/access/inventario_serializacion.py` (forma `Access` provisional, ver FNC-095)
- `app/__init__.py` (registro del blueprint), `tests/matriz_proteccion.py` (caso y 400)
- `tests/access/test_inventario.py`

## Reutilización
- Modelo de FNC-054
- `scoped_platforms` o `managed_area_ids` de `app/authz.py`

## Variables y configuración
- `ACCESS_INVENTORY_PAGE_SIZE_MAX` (constante registrada).

## Decisiones
| Tema | Decisión | Fuente |
|---|---|---|
| Usuario | Sin inventario: `403` (usa `/me/access`); reemplaza "usuario lo suyo" del objetivo | Dueño; contrato `accesos.md` 1.1 |
| Admin | Accesos de las plataformas de las áreas que administra (incluye los de otros admins del área); sin áreas, lista vacía | Dueño; Anexo A |
| Filtro fuera de alcance (`area_id`, `platform_id`, `user_id` ajenos) | `200` con lista vacía, no `404`: es una lista (contrato: "no aparecen"), igual que `GET /audit`. El `404` de SEC-AUTHZ-04 aplica a recursos por id, que aquí no hay | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| `status` por defecto | `vigente` (excluye `revocado`) | Contrato |
| `q` | Nombre o correo del usuario, sin distinguir mayúsculas, comodines literales, ≤ 100 | Contrato; `leer_filtros` |
| `per_page` máx. | `ACCESS_INVENTORY_PAGE_SIZE_MAX` = `POR_PAGINA_MAX` (100) | Convenciones `README.md`; decisión del orquestador (pendiente de validar en la prueba de concepto) |
| `last_job_id` | Se incluye (solo lo ven admins y superadmin) | Contrato |
| CSV | No se exporta (fuera de alcance de la ficha) | Ficha |

## Criterios de aceptación
- [x] Un admin no ve accesos de áreas ajenas, ni filtrando por ellas (prueba `test_admin_no_ve_lo_ajeno_ni_filtrando`)
- [x] Un usuario no tiene inventario: `403` (decisión del dueño; prueba `test_usuario_no_tiene_inventario`)
- [x] Paginación con límite máximo como constante registrada (`ACCESS_INVENTORY_PAGE_SIZE_MAX`)
- [x] Criterios comunes backend (FNC-037): protección explícita, matriz de protección, `400 parametro_invalido`, formato paginado estándar, solo lectura (sin auditoría de escritura)

## Impacto cruzado
- Genera → DIS-021
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-038
- Contrato → docs/contratos/accesos.md

## Impacto en elementos compartidos
Salida de `impacto.py`:

**Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 15 archivos cambiados).

Revisado a mano (no son elementos de UI, pero se comparten):
- `app/__init__.py`: una línea de import y el blueprint en la tupla de la API v1. Afecta el arranque de toda la app (suite completa en verde). Puede chocar al integrar con FNC-058, que también registra blueprints.
- `tests/matriz_proteccion.py`: un `Caso` y dos `CASOS_400` nuevos. Lo usan `test_proteccion_por_rol.py` y `test_guardia_rutas.py`.
- No se modificaron `audit/parametros.py`, `access_requests/serializacion.py` ni `authz.py`: solo se importan.

## Verificación
| Comando | Resultado |
|---|---|
| `pytest tests/access/test_inventario.py` sin la ruta registrada | 19 failed (404): las regresiones fallan primero |
| `pytest tests/test_proteccion_por_rol.py tests/test_guardia_rutas.py` sin la ruta registrada | 7 failed |
| `pytest tests/test_proteccion_por_rol.py tests/test_guardia_rutas.py tests/access` | 357 passed |
| `pytest` completo | 1408 passed, 14 xfailed, salida 0 |

Sin verificar: no se lanzaron `revisor` ni `auditor-seguridad` (lo pidió el orquestador). La ficha exige `auditor-seguridad`, así que queda pendiente. No hay migraciones, así que tampoco se probó MySQL real.

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada (modo autónomo) e implementada en blueprint propio; usuario 403; serialización provisional hasta FNC-095. En revisión; pendientes revisor y auditor-seguridad |
