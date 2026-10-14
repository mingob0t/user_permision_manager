# FNC-020 — Pruebas de protección por rol de todos los endpoints /api/v1 con guardia de rutas sin clasificar

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 2 |
| **Módulo / Área** | pruebas |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-13 |
| **Finalizada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-020-pruebas-proteccion-por-rol` |
| **Commits / PR** | `f4c8873` (más el ajuste con el hash) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No (solo pruebas; la app no cambia) |

## Contexto
90 rutas sin prueba.

Origen (diagnóstico inicial, FNC-001):
- [`docs/planeacion/diagnostico-pruebas-2026-10-13.md`](../../../planeacion/diagnostico-pruebas-2026-10-13.md): tarea 2

## Objetivo
Probar que cada endpoint `/api/v1` responde lo correcto a cada rol, y que ninguno nuevo quede sin clasificar.

## Alcance
- **Incluye:** matriz ruta × método × rol (anónimo, usuario, admin_area, administrador) de las 46 rutas `/api/v1`; entradas inválidas (400); RF-04 en el rol pedido; guardia sobre `app.url_map`.
- **No incluye:** rutas heredadas y CSRF (FNC-023; solo se excluyen en la guardia), alcance por área `scoped_*` (FNC-021), reglas de SSO/LDAP (FNC-022), corregir la app.

## Criterios de aceptación
- [x] Las 46 rutas `/api/v1` tienen caso con 401/403/2xx por rol; los 2xx ejecutan la acción (datos mínimos válidos; SMTP y LDAP simulados)
- [x] Guardia: falla si aparece una ruta `/api/v1` sin caso, un caso de ruta inexistente o una ruta fuera de `/api/v1` que no sea heredada (comprobado agregando rutas falsas)
- [x] Prueba de regresión: no aplica (no corrige defectos; los defectos quedan como `xfail`)
- [x] Pruebas ejecutadas: 218 passed, 2 xfailed, código 0
- [x] Cumple `docs/estandarizacion/`; reutiliza fixtures y fábricas de FNC-019
- [x] Sin direcciones IP ni secretos (hosts `.invalid` y claves ficticias)

## Cambios
- `tests/matriz_proteccion.py`: casos por ruta, códigos por rol, escenario de datos y simulación de SMTP/LDAP.
- `tests/test_proteccion_por_rol.py`: matriz (184 pruebas), 15 casos de 400 y 8 de RF-04.
- `tests/test_guardia_rutas.py`: 3 pruebas guardia sobre `app.url_map`.
- Documentación: `docs/backend/README.md`, catálogo de reutilización, CHANGELOG, tablero y bitácora.

## Casos `xfail` (comportamiento correcto, pendiente de corregir)
| Caso | Hoy | Esperado | Corrige |
|---|---|---|---|
| admin_area `POST /api/v1/users` con `role: admin_area` | 201 | 403 | SEG-20261013-09 / FNC-007 |
| admin_area `PUT /api/v1/users/<id>` con `role: admin_area` | 200 | 403 | SEG-20261013-09 / FNC-007 |

- Son `strict=True`: al corregir FNC-007 pasarán a "XPASS" y fallarán hasta quitar la marca.

## Verificación
- `venv/bin/pytest; echo EXIT=$?` → `218 passed, 2 xfailed, 203 warnings in 113.61s`, `EXIT=0`.
- `venv/bin/pytest --runxfail -k "eleva_admins and admin_area-P and admin_area-403"` → falla con `201 == 403` y `200 == 403` (confirma el defecto).
- Guardia: con una ruta falsa `POST /api/v1/nueva` y otra `/otra`, las dos pruebas guardia fallan con mensaje claro.
- No verificado: con MySQL real (la suite usa SQLite); la suite tarda ~2 min por crear la app en cada prueba.

## Impacto en elementos compartidos
- `impacto.py`: **ninguno detectado** (comparado contra `develop`). Solo archivos nuevos en `tests/` y documentación.

## Observaciones
- `GET /api/v1/areas/<id>` da 403 al usuario normal; se probó así (la pantalla Áreas no es para usuarios).
- Los requerimientos dicen "Superadmin: crear cuentas"; hoy un admin_area también crea usuarios (rol `usuario`). Se dejó como 201 por ser ambiguo: confirmar con el dueño.
- F-AREA-01 (Parcial) pide que el admin dé de alta sus áreas; hoy `POST /api/v1/areas` da 403 al admin_area y la matriz lo fija así. Quien implemente F-AREA-01 debe cambiar ese caso.
- SEG-09 en `managed_area_ids` (`PUT /users/<id>`) y SEG-05 (admin_area sobre otro admin_area) son de alcance: quedan para FNC-021.
- Revisión: `revisor` aprobado con observaciones (corregidas en la ficha).

## Impacto cruzado
- Depende de → FNC-019
- Los `xfail` se quitan en → FNC-007

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-13 | Aprobada por el dueño; implementada y probada (218 passed, 2 xfailed) |
