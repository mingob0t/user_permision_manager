# FNC-131 — Comando de datos demo para validar en local

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Fase** | 6 |
| **Módulo / Área** | demo |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Rama** | `fnc/FNC-131-datos-demo` |
| **Creada** | 2026-10-27 |

## Origen (pedido del dueño, 2026-10-27)
- Validar en su equipo, sin Authelia ni Vaultwarden, con login local de un admin y usuarios demo; no puede validar en producción.
- Hoy solo existe la semilla `admin`. El login local de todas las cuentas ya existe (FNC-077).

## Criterios
- [x] `flask --app run:app demo cargar` con `AppGroup` propio (`app/modules/demo/cli.py`), registrado como el de `provisioning`.
- [x] Solo con `APP_ENV=development`; otro valor o vacío → salida 1 y mensaje, sin escribir.
- [x] Idempotente: lo existente no se duplica ni cambia de contraseña.
- [x] Crea con modelos y servicios: 2 áreas, 3 plataformas LDAP, 1 `admin_area`, 2 usuarios, 1 solicitud pendiente; cuentas `auth_source=local`.
- [x] Contraseñas: prompt con confirmación, `--password-desde-stdin` o aleatorias impresas una vez; ninguna en el código.
- [x] Tabla final: usuario, rol, área.
- [x] README raíz y `ENTORNOS.md` con los pasos para validar en local y la nota de LDAP.

## Decisiones (del orquestador, pendientes de validar en la prueba de concepto)
| Decisión | Motivo |
|---|---|
| Módulo `app/modules/demo/` con `datos`, `carga` y `cli` | Una responsabilidad por archivo |
| Plataformas con DN explícitos ficticios (`ou=groups,dc=demo,dc=local`) creadas con el modelo | `POST /platforms` exige directorio configurado; en local no hay OpenLDAP |
| El `admin_area` se asigna con `asignar_areas_administradas` | Reutiliza el servicio: accesos automáticos P6 y auditoría; sus trabajos fallan sin OpenLDAP (esperado) |
| La solicitud se crea con `access_requests.services.crear` | Respeta reglas y auditoría |
| Una sola contraseña (prompt o stdin) para todas las cuentas nuevas; aleatoria por cuenta sin terminal | Es demo local; menos fricción |
| Mínimo de 12 caracteres | Constante `LARGO_MINIMO_CONTRASENA` |
| Si todas las cuentas ya existen no se pide contraseña ni se cambia | Idempotencia sin pisar claves |
| No se crea un superadmin nuevo: se usa la semilla `admin` | No estaba en el pedido |
| `APP_ENV` se lee con la misma regla de `acceso_local` (función privada, duplicada en una línea) | No tocar un módulo compartido |

## Cambios
| Archivo | Qué |
|---|---|
| `app/modules/demo/{__init__,datos,carga,cli}.py` (nuevos) | Datos, carga idempotente y comando |
| `app/__init__.py` | Registra `demo_cli` en `_registrar_cli_y_manejadores` (3 líneas) |
| `tests/demo/test_demo_cargar.py` (nuevo) | 12 pruebas |
| `README.md`, `docs/operacion/ENTORNOS.md`, `docs/backend/README.md`, `CHANGELOG.md`, ROADMAP, TABLERO | Documentación |

## Verificación
| Comando | Resultado |
|---|---|
| Pruebas nuevas antes de implementar | error de recolección (módulo `app.modules.demo` inexistente); fallan |
| `pytest tests/demo` | 12 passed |
| `pytest` completo (venv de wt-054, salida a archivo) | 2577 passed, 14 xfailed; `echo $?` = 0 |

**No verificado:** ejecución manual contra la SQLite real de `instance/` y el flujo en el navegador (login desde la interfaz, aprobar la solicitud); el otorgamiento por LDAP falla sin OpenLDAP (esperado).

## Impacto en elementos compartidos
**Impacto en elementos compartidos:** solo `app/__init__.py` (`_registrar_cli_y_manejadores`, una línea de registro); sin cambio de comportamiento para el resto. Se reutilizan sin modificar `asignar_areas_administradas`, `access_requests.services.crear` y los modelos.

## Bitácora
- 2026-10-27: creada, aprobada por el dueño e implementada. Pendiente: revisor y auditor-seguridad (toca cuentas y contraseñas).
