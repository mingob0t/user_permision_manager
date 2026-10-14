# FNC-023 — Pruebas de notificaciones, auditoría, respaldo y arranque

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 2 |
| **Módulo / Área** | pruebas |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-14 |
| **Finalizada** | 2026-10-14 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-023-pruebas-servicios` |
| **Commits / PR** | Commit local `[FNC-023]` en `fnc/FNC-023-pruebas-servicios` (sin push) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No (solo pruebas; la app no cambia) |

## Contexto
Sin pruebas.

Origen (diagnóstico inicial, FNC-001):
- [`docs/planeacion/diagnostico-pruebas-2026-10-13.md`](../../../planeacion/diagnostico-pruebas-2026-10-13.md): tareas 5-7 (P1 y P2)

## Objetivo
Probar notificaciones, auditoría del CRUD, respaldo, secretos en respuestas, rutas heredadas, CSRF y arranque, sin servicios reales, y fijar los defectos conocidos como `xfail`.

## Alcance
- **Incluye:** `send_notification_by_slug`, `resolve_smtp_settings`, `/notifications`, eventos de auditoría del CRUD, límite de `/audit`, casos límite del CRUD, `/backup`, GET/PUT de SMTP y LDAP, 45 rutas heredadas, CSRF y `create_app`.
- **No incluye:** corregir la app; alcance de `/audit` por rol (ya en FNC-021); protección por rol (FNC-020).

## Criterios de aceptación
- [x] Hallazgos de origen: no se corrigen aquí; quedan como `xfail(strict=True)` con su tarea
- [x] Prueba de regresión que primero falla: los 13 `xfail` fallan hoy por el defecto (comprobado con `--runxfail`)
- [x] Pruebas ejecutadas: ver Verificación
- [x] Reutiliza `conftest.py`, `fabricas.py`, `matriz_proteccion.py`, `directorio_falso.py` y `peticiones_auth.py`
- [x] Sin direcciones IP ni secretos (hosts `.invalid`, claves ficticias)

## Cambios
- `tests/smtp_falso.py`: SMTP simulado (mensajes, conexiones, logins y fallo a demanda).
- `tests/test_notificaciones.py`: 34 pruebas (plantillas, SMTP BD/entorno, `SMTP_FORCE_ENV`, fallo de correo en SSO y directorio, `/notifications`).
- `tests/test_auditoria_crud.py`: 31 pruebas (actor, acción y objetivo de 12 acciones CRUD, límite de `/audit`, duplicados, 404, purga, preferencias).
- `tests/test_respaldo.py`: 12 pruebas (exportar, importar, ida y vuelta, paquetes inválidos).
- `tests/test_secretos_en_respuestas.py`: 7 pruebas (GET/PUT de SMTP y LDAP sin contraseñas; clave vacía no borra).
- `tests/test_rutas_heredadas.py`: 7 pruebas (45 rutas, con y sin sesión y `FRONTEND_URL`).
- `tests/test_csrf.py`: 5 pruebas (400 JSON del CSRF, exención de heredadas, SameSite y peticiones de otro sitio).
- `tests/test_arranque.py`: 9 pruebas (`create_app` mínima, MySQL, sesión; SECRET_KEY y DB_ENGINE faltantes o inválidos).
- Documentación: `docs/backend/README.md`, catálogo de reutilización, CHANGELOG, tablero y bitácora.

## Casos `xfail` (comportamiento correcto, pendiente de corregir)
| Prueba | Hoy | Esperado | Corrige |
|---|---|---|---|
| `test_plantilla_html_escapa_los_valores_del_contexto` | HTML sin escapar | `&lt;a` | SEG-23 / FNC-017 |
| `test_leer_una_global_no_la_marca_para_los_demas` | leída para todos | sigue sin leer para otros | FNC-031 |
| `test_exportar_no_incluye_hashes_de_contrasena` | incluye `password_hash` | sin hashes | SEG-17 / FNC-010 |
| `test_importar_no_crea_superadmins` | crea `administrador` | no lo crea | SEG-17 / FNC-010 |
| `test_cookie_de_sesion_con_samesite` | `None` | `Lax` o `Strict` | SEG-06 / FNC-008 |
| `test_formulario_de_otro_sitio_no_importa_un_respaldo` | procesa el archivo | 403 o error CSRF | SEG-06 / FNC-008 |
| `test_post_de_otro_sitio_no_purga_cuentas` | 200, purga | 400/403 | SEG-06 / FNC-008 |
| `test_sin_secret_key_no_arranca` | arranca con clave por defecto | falla al arrancar | SEG-07 / FNC-009 |
| `test_secret_key_conocida_no_arranca` | arranca | falla al arrancar | SEG-07 / FNC-009 |
| `test_db_engine_invalido_no_arranca[postgresql/MySQL/otro]` (3) | cae a SQLite | falla al arrancar | FNC-009 |
| `test_sin_db_engine_no_arranca` | cae a SQLite | falla al arrancar | FNC-009 |

- Son `strict=True`: al corregir, pasan a XPASS y fallan hasta quitar la marca.
- FNC-008: las pruebas de otro sitio mandan `Origin` y `Sec-Fetch-Site: cross-site`; aceptan 403 o el error CSRF.
- FNC-027: al retirar las heredadas se borra `test_rutas_heredadas.py` y la prueba de exención en `test_csrf.py`.

## Verificación
- `python3.12 -m venv venv && venv/bin/pip install -r requirements.txt -r requirements-dev.txt` → código 0.
- `venv/bin/pytest; echo EXIT=$?` → `426 passed, 35 xfailed, 441 warnings in 104.59s`, `EXIT=0` (105 pruebas nuevas, 13 `xfail` nuevos).
- `venv/bin/pytest --runxfail tests/test_arranque.py tests/test_csrf.py tests/test_respaldo.py tests/test_notificaciones.py` → los 13 fallan por el defecto (p. ej. `DID NOT RAISE`, `assert None in ('Lax', 'Strict')`, `'<a href' in '<p>Hola <a href=...'`).
- No verificado: SMTP, MySQL y navegador reales (todo simulado); CSRF desde un navegador real de otro sitio.

## Impacto en elementos compartidos
- `impacto.py` (contra `develop`): `ninguno detectado (comparado contra develop; 13 archivos cambiados)`.
- Solo se agregaron archivos en `tests/` y documentación; la app no cambia.

## Observaciones
- `GET /` heredada sin `FRONTEND_URL` responde 200 con JSON informativo (evita un bucle); se acepta como excepción.
- `core_bp` lee `FRONTEND_URL` al importar, no por petición: cambiarlo exige reiniciar (lo retira FNC-027).
- `create_app` captura cualquier error de BD al arrancar y sigue (solo imprime); entra en FNC-009.
- Revisión: no se lanzaron revisores (indicación del orquestador).

## Impacto cruzado
- Depende de → Depende de FNC-019

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-14 | Aprobada por el dueño; implementada y probada (426 passed, 35 xfailed, código 0) |
