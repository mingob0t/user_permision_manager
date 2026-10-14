# Tablero

| ID | Tarea | Plataforma | Fase | Módulo | Prioridad | Estatus | Creada | Inicio | Finalizada | Git | Vínculos |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FNC-001 | Incorporar el proyecto al método | infra | 0 | global | Alta | En curso | 2026-10-13 | 2026-10-13 | | `fnc/FNC-001-incorporacion-metodo` | |
| FNC-002 | Login de directorio seguro: sin purga de cuentas, filtro LDAP escapado y mensajes genéricos | backend | 5 | auth | Crítica | Propuesta | 2026-10-13 | | | — |  |
| FNC-003 | Eliminar credenciales por defecto y crear el primer superadmin con un comando explícito | backend | 5 | auth | Crítica | Propuesta | 2026-10-13 | | | — |  |
| FNC-004 | nginx: limpiar cabeceras Remote-* en todas las location, bloquear /api y /auth sin distinguir mayúsculas, TLS y cabeceras de seguridad | infra | 5 | deploy | Crítica | Propuesta | 2026-10-13 | | | — | Junto con FNC-005 y FNC-006 cierra SEG-04 |
| FNC-005 | Next.js: rewrites hacia la API solo en desarrollo y sin IP por defecto en BACKEND_URL | web | 5 | config | Crítica | Propuesta | 2026-10-13 | | | — | Junto con FNC-004 y FNC-006 |
| FNC-006 | SSO: autenticar al proxy con un secreto compartido además de la IP | backend | 5 | auth | Alta | Propuesta | 2026-10-13 | | | — | Junto con FNC-004 y FNC-005 |
| FNC-007 | Alcance del admin de área sobre cuentas: sin gestionar otros admins ni contraseñas no locales; solo el superadmin asigna admin_area | backend | 5 | authz | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-008 | CSRF en la API y endurecimiento de la sesión (SameSite, Secure, remember, revocación al desactivar) | backend | 5 | auth | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-009 | Configuración validada al arrancar: SECRET_KEY obligatoria, sin debug ni 0.0.0.0, DB_ENGINE explícito | backend | 5 | config | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-010 | Secretos de servicio fuera de la BD; respaldo sin hashes ni roles privilegiados | backend | 5 | settings | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-011 | Revisar y rotar los posibles secretos del historial de git | infra | 5 | repositorio | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-012 | LDAP para OpenLDAP: TLS validado, conexión centralizada y atributos configurables (uid, memberOf/groupOfNames) | backend | 5 | auth | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-013 | Rol desde el directorio con DN exacto y un solo superadmin | backend | 5 | auth | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-012 |
| FNC-014 | Límite de intentos en el login | backend | 5 | auth | Media | Propuesta | 2026-10-13 | | | — |  |
| FNC-015 | Auditoría filtrada por área e IP real del cliente | backend | 5 | audit | Media | Propuesta | 2026-10-13 | | | — |  |
| FNC-016 | Dependencias: npm audit y pip-audit, fijar versiones y quitar las que no se usan | infra | 5 | dependencias | Media | Propuesta | 2026-10-13 | | | — |  |
| FNC-017 | Higiene de seguridad: errores genéricos, escape en correos, validación de URLs, IP y hosts fuera del código, límites de carga | backend | 5 | global | Baja | Propuesta | 2026-10-13 | | | — |  |
| FNC-018 | Retención de datos personales y seudonimización | infra | 5 | operacion | Baja | Propuesta | 2026-10-13 | | | — |  |
| FNC-019 | Suite base de pruebas del backend (pytest, fixtures, cliente por rol, excluir utils/test_*) | backend | 2 | pruebas | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | `fnc/FNC-019-suite-base-pruebas-backend` (commit local, sin push) |  |
| FNC-020 | Pruebas de protección por rol de todos los endpoints /api/v1 con guardia de rutas sin clasificar | backend | 2 | pruebas | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-019 |
| FNC-021 | Pruebas de alcance por área y de escalada de privilegios | backend | 2 | pruebas | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-019 |
| FNC-022 | Pruebas de autenticación SSO, LDAP y local con dobles | backend | 2 | pruebas | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-019 |
| FNC-023 | Pruebas de notificaciones, auditoría, respaldo y arranque | backend | 2 | pruebas | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-019 |
| FNC-024 | Línea base web: instalar dependencias, configurar ESLint y ejecutar typecheck y lint | web | 2 | pruebas | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-025 | Runner de pruebas del frontend (Vitest) con prueba automática de contraste y tokens | web | 2 | pruebas | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-024 |
| FNC-026 | CI que ejecute pytest, typecheck, lint y los controles del pre-commit | infra | 2 | ci | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-019 y FNC-024; requiere repositorio remoto |
| FNC-027 | Retirar los blueprints heredados (44 rutas) y app/decorators.py | backend | 4 | global | Alta | Propuesta | 2026-10-13 | | | — | Antes de FNC-020 |
| FNC-028 | Limpiar scratch/ y utils/ (PSX5K) y adoptar Alembic con las migraciones 001-004 | backend | 4 | bd | Media | Propuesta | 2026-10-13 | | | — |  |
| FNC-029 | Dividir app/modules/api/admin.py, crud.py y create_app | backend | 4 | api | Media | Propuesta | 2026-10-13 | | | — | Después de FNC-020 |
| FNC-030 | Unificar helpers duplicados del backend (usuario creado, purga, _payload/_error, auditoría) | backend | 4 | api | Media | Propuesta | 2026-10-13 | | | — |  |
| FNC-031 | Corregir notificaciones globales marcadas como leídas para todos | backend | 4 | notifications | Media | Propuesta | 2026-10-13 | | | — |  |
| FNC-032 | Selector de tema: aplicar la clase en <html> o retirar los temas sin uso | web | 4 | tema | Alta | Propuesta | 2026-10-13 | | | — |  |
| FNC-033 | Validar el contraste de los colores elegidos por el usuario (onColor) | web | 4 | tema | Media | Propuesta | 2026-10-13 | | | — | Depende de DIS-001 |
| FNC-034 | Semántica accesible: aria-label contextual, scope en th y texto del tipo de notificación | web | 4 | global | Media | Propuesta | 2026-10-13 | | | — |  |
| FNC-035 | Depurar documentación obsoleta (business_rules, ARCHITECTURE, README raíz, deploy/README) | infra | 6 | docs | Baja | Propuesta | 2026-10-13 | | | — |  |
| DIS-001 | Completar tokens por tema: panel-header-text, badge, on-primary, brand y accent en oscuro | web | 4 | tokens | Alta | Propuesta | 2026-10-13 | | | — |  |
| DIS-002 | Tokens semánticos de texto (success, danger, warning, primary) y sustituir clases Tailwind literales | web | 4 | tokens | Alta | Propuesta | 2026-10-13 | | | — |  |
| DIS-003 | Gráfica del inicio: corregir variables --nx-* inexistentes y colores de ejes | web | 4 | dashboard | Alta | Propuesta | 2026-10-13 | | | — |  |
| DIS-004 | Botones: texto sobre primary por token, peligro y advertencia, hover del secundario | web | 4 | componentes | Media | Propuesta | 2026-10-13 | | | — | Depende de DIS-001 |
| DIS-005 | Texto atenuado con tokens muted de 4.5:1 | web | 4 | tokens | Media | Propuesta | 2026-10-13 | | | — |  |
| DIS-006 | Bordes de campo a 3:1 y foco visible | web | 4 | componentes | Media | Propuesta | 2026-10-13 | | | — |  |
| DIS-007 | Tamaño mínimo de texto 12 px | web | 4 | componentes | Media | Propuesta | 2026-10-13 | | | — |  |
| DIS-008 | Áreas táctiles de 44-48 px en acciones de fila, chips y favorito | web | 4 | componentes | Media | Propuesta | 2026-10-13 | | | — |  |
| DIS-009 | Depurar components.css y global.css: clases sin uso y colores literales a tokens | web | 4 | estilos | Alta | Propuesta | 2026-10-13 | | | — |  |
| DIS-010 | Componentes comunes: DataTable, botón de peligro, filtros, tonos de estado y toast | web | 4 | componentes | Media | Propuesta | 2026-10-13 | | | — |  |
| DIS-011 | Dividir settings-panel.tsx, users-list.tsx y platform-admin.tsx | web | 4 | componentes | Media | Propuesta | 2026-10-13 | | | — | Después de DIS-010 |
| DIS-012 | Eliminar estilos inline y colores literales en TSX | web | 4 | estilos | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-033 |
| FNC-036 | Lineamientos de seguridad del proyecto | backend | 1 | seguridad | Alta | Propuesta | 2026-10-13 | | | — | Base de todas las fases siguientes |
