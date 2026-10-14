# FNC-022 — Pruebas de autenticación SSO, LDAP y local con dobles

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
| **Rama** | `fnc/FNC-022-pruebas-autenticacion` |
| **Commits / PR** | `1abfd6e` y corrección de la revisión (locales, sin push) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No (solo pruebas; la app no cambia) |

## Contexto
Autenticación sin pruebas.

Origen (diagnóstico inicial, FNC-001):
- [`docs/planeacion/diagnostico-pruebas-2026-10-13.md`](../../../planeacion/diagnostico-pruebas-2026-10-13.md): tarea 4

## Objetivo
Probar login local, por directorio, SSO, logout y sesión sin servicios reales, y fijar los defectos de seguridad conocidos como `xfail`.

## Alcance
- **Incluye:** login local, login por directorio (`ldap3` simulado), SSO por cabeceras `Remote-*`, `/context`, logout y sesión.
- **No incluye:** corregir la app; nginx y Next.js (FNC-004, FNC-005); CSRF y rutas heredadas (FNC-023).

## Criterios de aceptación
- [x] Hallazgos de origen: no se corrigen aquí; quedan como `xfail(strict=True)` con su tarea
- [x] Prueba de regresión que primero falla: los 13 `xfail` fallan hoy por el defecto (comprobado con `--runxfail`)
- [x] Pruebas ejecutadas: 253 passed, 15 xfailed, código 0
- [x] Reutiliza `conftest.py`, `fabricas.py` y constantes de `matriz_proteccion.py`
- [x] Sin direcciones IP ni secretos (orígenes y hosts `.invalid`, claves ficticias)

## Cambios
- `tests/directorio_falso.py`: directorio LDAP simulado (personas, grupos, binds y filtros recibidos).
- `tests/peticiones_auth.py`: login por API, usuario en sesión y búsqueda en auditoría.
- `tests/test_login_local.py`: 8 pruebas (éxito, clave mala, cuenta inexistente, inactivo, mensaje uniforme).
- `tests/test_login_directorio.py`: 16 pruebas (usuario sombra, fallos, mapeo de grupos).
- `tests/test_sso.py`: 16 pruebas (proxy de confianza, origen ajeno, cabeceras faltantes, Remote-Groups, `/context`).
- `tests/test_sesion_y_logout.py`: 8 pruebas (cookie, sesión, cuenta desactivada, logout, URL de cierre de Authelia).
- Documentación: `docs/backend/README.md`, catálogo de reutilización, CHANGELOG, tablero y bitácora.

## Casos `xfail` (comportamiento correcto, pendiente de corregir)
| Prueba | Hoy | Esperado | Corrige |
|---|---|---|---|
| `test_cuenta_no_local_no_entra_por_login_local[ldap]` | 200 | 401 | SEG-02 / FNC-003 |
| `test_cuenta_no_local_no_entra_por_login_local[sso]` | 200 | 401 | SEG-02 / FNC-003 |
| `test_limite_de_intentos_responde_429` | 401 | 429 tras 20 fallos | SEG-11 / FNC-014 |
| `test_login_fallido_no_borra_cuentas_locales` | borra la cuenta | la conserva | SEG-01 / FNC-002 |
| `test_mensaje_uniforme_en_los_fallos` (directorio) | 2 mensajes | 1 mensaje | SEG-12 / FNC-002 |
| `test_filtro_ldap_escapa_comodines` | `j*` | `j\2a` | SEG-12 / FNC-002 |
| `test_error_del_directorio_no_se_filtra_al_cliente` | error textual | genérico | SEG-12 / FNC-002 |
| `test_grupo_parecido_no_cambia_el_rol[grupo_admin_heredado]` | administrador | usuario | SEG-10 / FNC-013 |
| `test_grupo_parecido_no_cambia_el_rol[mapeo_json]` | admin_area | usuario | SEG-10 / FNC-013 |
| `test_directorio_no_asigna_administrador` | administrador | otro rol | SEG-10 / FNC-013 |
| `test_conserva_admin_area_asignado_localmente` (directorio) | usuario | admin_area | SEG-10 / FNC-013 |
| `test_remote_groups_no_asigna_administrador` (SSO) | administrador | otro rol | SEG-10 / FNC-013 |
| `test_sin_secreto_compartido_del_proxy_se_rechaza` (SSO) | 200 | 401 | SEG-04 / FNC-006 |

- Son `strict=True`: al corregir, pasan a XPASS y fallan hasta quitar la marca.
- FNC-014: el umbral de 20 es provisional (`INTENTOS_ANTES_DEL_LIMITE`); se ajusta al definirlo.
- FNC-006: al exigir el secreto, las demás pruebas de SSO deben enviarlo.
- FNC-004 y FNC-005 (nginx y Next.js) no se pueden probar desde Flask.

## Verificación
- `python3.12 -m venv venv && venv/bin/pip install -r requirements.txt -r requirements-dev.txt` → código 0.
- `venv/bin/pytest; echo EXIT=$?` → `253 passed, 15 xfailed, 231 warnings in 205.16s`, `EXIT=0` (13 `xfail` nuevos + 2 de FNC-020).
- `venv/bin/pytest --runxfail tests/test_login_local.py tests/test_login_directorio.py tests/test_sso.py` → los 13 fallan por el defecto esperado (p. ej. `'Contraseña LDAP incorrecta' != 'Usuario no encontrado…'`, `'(sAMAccountName=j*)' != '(sAMAccountName=j\2a)'`).
- No verificado: contra OpenLDAP y Authelia reales, ni con MySQL (la suite usa SQLite y dobles).

## Impacto en elementos compartidos
- `impacto.py` (contra `develop`): reporta 8 nombres (`__enter__`, `__exit__`, `__init__`, `agregar`, `buscar`, `directorio`, `search`, `unbind`). Son funciones nuevas en archivos nuevos de `tests/` que se llaman igual que código existente: homónimos, sin impacto real.

## Observaciones
- SEG-14 (parte "desactivar no saca al usuario"): **no se reproduce**. En Flask-Login 0.6.3 `is_authenticated` devuelve `is_active`, y la sesión da 401. Queda como prueba normal. El resto de SEG-14 (remember de 365 días) sigue en FNC-008.
- Login local de una cuenta inactiva con la clave correcta responde 403 "La cuenta está desactivada." (distinto de 401). Confirma que la clave es buena; SEC-AUTH-09 pide respuesta idéntica: confirmar con el dueño.
- Logout sin `BASE_URL` arma la URL de cierre con `Host` (SEC-AUTH-13). Sin tarea asignada; no se probó como `xfail`.
- Revisión: no se lanzaron revisores (indicación del orquestador).

## Impacto cruzado
- Depende de → Depende de FNC-019

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-13 | Aprobada por el dueño; implementada y probada (253 passed, 15 xfailed) |
- revisor (2026-10-13): Requiere cambios de documentación e integración; corregidos (impacto, commit, CHANGELOG, actualización con develop). Unificar los dos LDAP simulados queda como FNC-074 (Propuesta).
