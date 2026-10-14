# FNC-021 — Pruebas de alcance por área y de escalada de privilegios

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
| **Rama** | `fnc/FNC-021-pruebas-alcance-por-area` |
| **Commits / PR** | `e96f9a3` y corrección de la revisión (locales, sin push) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No (solo pruebas; la app no cambia) |

## Contexto
`scoped_*` y `can_*` de `app/authz.py` sin pruebas.

Origen (diagnóstico inicial, FNC-001):
- [`docs/planeacion/diagnostico-pruebas-2026-10-13.md`](../../../planeacion/diagnostico-pruebas-2026-10-13.md): tarea 3

## Objetivo
Probar que cada actor solo ve y modifica lo de su área, y que no puede escalar privilegios con ids ajenos.

## Alcance
- **Incluye:** escenario con áreas A y B y 5 actores (superadmin, admin de A, admin de B, usuario de A, usuario de B); áreas, plataformas, usuarios, favoritos, visitas, estadísticas y auditoría; escalada con áreas, plataformas y `managed_area_ids` ajenos y sobre otro admin_area; funciones `scoped_*`, `can_*` y `managed_area_ids` de `app/authz.py`.
- **No incluye:** corregir la app (FNC-007, FNC-015); contraseña local puesta por un admin_area a cuentas ldap/sso de su área (SEG-05, parte 2: queda para FNC-007); rutas heredadas, SSO/LDAP y servicios (FNC-022, FNC-023).

## Criterios de aceptación
- [x] Listados filtrados por alcance para los 5 actores (áreas, plataformas, usuarios, favoritos, estadísticas, auditoría)
- [x] GET/PUT/DELETE de ids ajenos → 403/404, y el dato no cambia
- [x] Escalada con ids fuera de alcance probada; lo incorrecto queda como `xfail(strict=True)`
- [x] Prueba de regresión: no aplica (no corrige defectos)
- [x] Pruebas ejecutadas: 299 passed, 9 xfailed, código 0
- [x] Reutiliza `conftest.py`, `fabricas.py` y `matriz_proteccion.py` (constante de contraseña)
- [x] Sin direcciones IP ni secretos (claves ficticias)

## Cambios
- `tests/test_alcance_por_area.py` (nuevo): 88 pruebas (81 pasan, 7 `xfail`).
- Documentación: `docs/backend/README.md`, CHANGELOG, tablero, bitácora y esta ficha.

## Casos `xfail` (comportamiento correcto, pendiente de corregir)
| Prueba | Hoy | Esperado | Corrige |
|---|---|---|---|
| `test_admin_area_no_asigna_managed_area_ids[A]` y `[B]` | 200 | 403 | SEG-20261013-09 / FNC-007 |
| `test_admin_area_no_toma_cuenta_de_otro_admin_area` (contraseña, rol, `is_active`, DELETE) | 200 | 403 | SEG-20261013-05 / FNC-007 |
| `test_admin_area_no_ve_auditoria_de_otra_area` | ve el registro | no lo ve | SEG-20261013-16 / FNC-015 |

- Son `strict=True`: al corregir pasarán a XPASS y fallarán hasta quitar la marca.

## Verificación
- `venv/bin/pytest; echo EXIT=$?` → `299 passed, 9 xfailed, 329 warnings in 74.46s`, `EXIT=0` (2 xfail son de FNC-020).
- `venv/bin/pytest tests/test_alcance_por_area.py --runxfail -k "managed_area_ids or toma_cuenta or auditoria_de_otra"` → los 7 fallan con `200 in (403,)` y con el registro visible (confirma los defectos).
- No verificado: con MySQL real (la suite usa SQLite).

## Impacto en elementos compartidos
- `impacto.py` (contra `develop`): reporta `Alcance` (clase) y `alcance` (fixture) del test nuevo; son coincidencias con la palabra "alcance" en `app/authz.py`, `app/modules/api/*` y `frontend/src/components/*`. Falso positivo: no se modificó ningún elemento compartido.

## Observaciones
- Hoy un admin de B que **no** es miembro de A queda fuera del alcance del admin de A (pasa); el defecto aparece cuando es miembro de A.
- `POST /users` con un área ajena descarta esa área en silencio (201): la cuenta no la recibe. Se prueba que no la reciba, no el código.
- `managed_area_ids` ajeno se descarta en silencio: B nunca se asigna (pasa); el defecto es aceptar `managed_area_ids` (xfail SEG-09).

## Impacto cruzado
- Depende de → FNC-019, FNC-020
- Los `xfail` se quitan en → FNC-007 (SEG-05, SEG-09) y FNC-015 (SEG-16)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-13 | Aprobada por el dueño; implementada y probada (299 passed, 9 xfailed) |
- revisor (2026-10-13): Aprobado con 4 observaciones menores; corregidas la ficha (impacto, commit) y la prueba de cuentas ajenas, que ahora también verifica que no cambien áreas ni plataformas.
