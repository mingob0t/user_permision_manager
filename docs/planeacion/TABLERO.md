# Tablero

| ID | Tarea | Plataforma | Fase | Módulo | Prioridad | Estatus | Creada | Inicio | Finalizada | Git | Vínculos |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FNC-001 | Incorporar el proyecto al método | infra | 0 | global | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | Merge local a develop (634e9f1) | |
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
| FNC-020 | Pruebas de protección por rol de todos los endpoints /api/v1 con guardia de rutas sin clasificar | backend | 2 | pruebas | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | `fnc/FNC-020-pruebas-proteccion-por-rol` (commit local, sin push) | Depende de FNC-019; 2 xfail hasta FNC-007 |
| FNC-021 | Pruebas de alcance por área y de escalada de privilegios | backend | 2 | pruebas | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | `fnc/FNC-021-pruebas-alcance-por-area` (commit local, sin push) | Depende de FNC-019; 7 xfail hasta FNC-007 y FNC-015 |
| FNC-022 | Pruebas de autenticación SSO, LDAP y local con dobles | backend | 2 | pruebas | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | `fnc/FNC-022-pruebas-autenticacion` (commit local, sin push) | Depende de FNC-019; 13 xfail hasta FNC-002/003/006/013/014 |
| FNC-023 | Pruebas de notificaciones, auditoría, respaldo y arranque | backend | 2 | pruebas | Media | Hecha | 2026-10-13 | 2026-10-14 | 2026-10-14 | `fnc/FNC-023-pruebas-servicios` (commit local, sin push) | Depende de FNC-019; 13 xfail hasta FNC-008/009/010/017/031 |
| FNC-024 | Línea base web: instalar dependencias, configurar ESLint y ejecutar typecheck y lint | web | 2 | pruebas | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | Merge local a develop (fd2a22d) | Build roto por 1 error de lint: decisión pendiente |
| FNC-025 | Runner de pruebas del frontend (Vitest) con prueba automática de contraste y tokens | web | 2 | pruebas | Media | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | Merge local a develop (85e220c) | Depende de FNC-024; fallas de contraste a DIS-001 a DIS-006 |
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
| FNC-036 | Lineamientos de seguridad del proyecto | backend | 1 | seguridad | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | Merge local a develop | Base de todas las fases siguientes |
| FNC-072 | Corregir los hallazgos de lint de la línea base web | web | 2 | frontend | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-13 | Merge local a develop (851846f) | Depende de FNC-024 |
| FNC-073 | Alinear la versión mínima de Node en el despliegue | infra | 6 | deploy | Baja | Propuesta | 2026-10-13 | | | — | Origen: revisión de FNC-025 |
| FNC-074 | Unificar el LDAP simulado de las pruebas | backend | 4 | pruebas | Baja | Propuesta | 2026-10-13 | | | — | Origen: revisión de FNC-022 |
| FNC-037 | Planeación de la fase 3: gestor de accesos | backend | 3 | planeacion | Alta | Hecha | 2026-10-13 | 2026-10-13 | 2026-10-14 | Merge local a develop | Plan de la fase 3; genera FNC-038 a FNC-071 y DIS-013 a DIS-024 |
| FNC-038 | Contratos v1 backend↔web del gestor de accesos | backend | 3 | contratos | Alta | Propuesta | 2026-10-13 | | | — | Depende de P1, P14, FNC-037, ADR-006 |
| FNC-039 | Migraciones versionadas de MySQL para la fase 3 (según ADR-002) | backend | 3 | bd | Alta | Hecha | 2026-10-13 | 2026-10-14 | 2026-10-14 | `fnc/FNC-039-migraciones-alembic` (commit local, sin push) | Depende de ADR-002; Alembic 1.20.0, línea base `0001`; pendiente prueba del dueño en MySQL |
| FNC-040 | Cliente LDAP centralizado con TLS validado y esquema de OpenLDAP configurable | backend | 3 | directorio | Alta | Propuesta | 2026-10-13 | | | — | Depende de ADR-004 |
| FNC-041 | Servicio de escritura en OpenLDAP: membresía de grupos y alta de cuentas | backend | 3 | directorio | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-040, ADR-004 |
| FNC-042 | Login por directorio sobre el cliente centralizado, sin purga de cuentas y sin elevar rol desde LDAP | backend | 3 | auth | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-040, FNC-047 |
| FNC-043 | Configuración del directorio: esquema de OpenLDAP en la API y credencial de bind fuera de la BD | backend | 3 | configuracion-directorio | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-040, FNC-039, FNC-038 |
| FNC-044 | Roles: solo el superadmin crea o eleva admins y asigna las áreas administradas | backend | 3 | usuarios-roles | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-038, FNC-047 |
| FNC-045 | Áreas: el admin da de alta sus áreas y queda como su administrador | backend | 3 | areas | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-044, FNC-038, FNC-047 |
| FNC-046 | Plataformas: tipo de integración y grupos LDAP por nivel | backend | 3 | plataformas | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-039, FNC-040, FNC-038, FNC-047 |
| FNC-047 | Auditoría ampliada: registro inmutable con detalle del cambio, actor, área y plataforma | backend | 3 | auditoria | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-039 |
| FNC-048 | Notificaciones del gestor de accesos: plantillas y envío por evento | backend | 3 | notificaciones | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-039, ADR-003 |
| FNC-049 | Ejecutor de aprovisionamiento: cola, worker, reintentos y bitácora (según ADR-003) | backend | 3 | aprovisionamiento | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-039, FNC-041, FNC-047, FNC-048, ADR-003 |
| FNC-050 | Conectores: interfaz, registro, configuración por plataforma y credenciales desde Vaultwarden (según ADR-005) | backend | 3 | conectores | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-049, FNC-046, ADR-005 |
| FNC-051 | Conector tipo API HTTP | backend | 3 | conectores | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-050, P9 |
| FNC-052 | Conector tipo SSH | backend | 3 | conectores | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-050, P9 |
| FNC-053 | Conector tipo base de datos | backend | 3 | conectores | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-050, P9 |
| FNC-054 | Accesos otorgados: modelo con origen y estados, y servicio de otorgar y revocar | backend | 3 | accesos | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-039, FNC-046, FNC-047, FNC-049, P5 |
| FNC-055 | Acceso automático de los admins a las plataformas de sus áreas | backend | 3 | accesos | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-054, FNC-044, FNC-045, FNC-046, P6 |
| FNC-058 | Accesos: consulta por usuario, mis accesos y revocación manual | backend | 3 | accesos | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-054, FNC-038 |
| FNC-059 | Inventario de permisos: quién tiene qué plataforma, nivel, desde cuándo y quién aprobó | backend | 3 | accesos | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-054, FNC-038 |
| FNC-063 | Visibilidad de plataformas y acceso a ellas según los accesos otorgados | backend | 3 | authz | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-054, P4 |
| FNC-065 | Retirar la asignación directa de plataformas (`user_platforms`) y migrarla a accesos | backend | 3 | accesos | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-054, FNC-063, P4 |
| FNC-056 | Solicitudes: catálogo solicitable, crear solicitud y mis solicitudes | backend | 3 | solicitudes | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-039, FNC-046, FNC-047, FNC-048, FNC-054, FNC-038, P1 |
| FNC-057 | Aprobaciones: bandeja por área, aprobar y rechazar con motivo obligatorio | backend | 3 | solicitudes | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-056, FNC-054, FNC-048, P12 |
| FNC-060 | Consulta de auditoría por rol e historial por usuario y por plataforma | backend | 3 | auditoria | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-047, FNC-038 |
| FNC-061 | API de configuración de conectores (superadmin) | backend | 3 | conectores | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-050, FNC-038 |
| FNC-062 | API de ejecuciones: bitácora de aprovisionamiento y reintento manual | backend | 3 | aprovisionamiento | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-049, FNC-038, P10 |
| FNC-064 | Usuarios: crear cuentas en OpenLDAP desde el portal | backend | 3 | usuarios | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-041, FNC-044, FNC-038, P2, P8 |
| FNC-066 | Resumen del inicio por rol: pendientes, accesos y solicitudes | backend | 3 | estadisticas | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-054, FNC-056, FNC-049, FNC-038 |
| FNC-067 | Servicio del worker de aprovisionamiento en el despliegue | infra | 3 | deploy | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-049, ADR-003 |
| FNC-068 | Credenciales de conectores y del bind LDAP desde Vaultwarden en staging y producción | infra | 3 | secretos | Alta | Propuesta | 2026-10-13 | | | — | Depende de ADR-005, FNC-050 |
| FNC-069 | Cliente y tipos web del gestor de accesos | web | 3 | lib-api | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-038 |
| FNC-070 | Navegación y rutas por rol del gestor de accesos | web | 3 | navegacion | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069 |
| FNC-071 | Refresco periódico de datos con pausa en segundo plano (según ADR-006) | web | 3 | lib-datos | Media | Propuesta | 2026-10-13 | | | — | Depende de ADR-006, FNC-069 |
| DIS-013 | Catálogo: solicitar acceso con nivel y justificación | web | 3 | catalogo | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-070, FNC-056 |
| DIS-014 | Mis solicitudes y mis accesos | web | 3 | solicitudes | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-070, FNC-071, FNC-056, FNC-058, DIS-013 |
| DIS-015 | Bandeja de aprobaciones con rechazo motivado | web | 3 | aprobaciones | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-070, FNC-071, FNC-057 |
| DIS-016 | Áreas: alta por el admin y asignación de admins por el superadmin | web | 3 | areas | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-044, FNC-045 |
| DIS-017 | Plataformas: tipo de integración y grupos por nivel | web | 3 | plataformas | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-046 |
| DIS-018 | Usuarios y accesos: accesos de un usuario y revocación | web | 3 | usuarios | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-071, FNC-058, DIS-013 |
| DIS-019 | Usuarios: alta en el directorio y elevación a admin | web | 3 | usuarios | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-064, FNC-044, DIS-018 |
| DIS-020 | Auditoría: filtros e historial por usuario y por plataforma | web | 3 | auditoria | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-060 |
| DIS-021 | Inventario de permisos | web | 3 | inventario | Alta | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-070, FNC-059 |
| DIS-022 | Configuración de conectores y bitácora de ejecuciones | web | 3 | configuracion-conectores | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-070, FNC-071, FNC-061, FNC-062 |
| DIS-023 | Ajustes: pestaña Directorio para OpenLDAP | web | 3 | configuracion-directorio | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-043 |
| DIS-024 | Inicio por rol | web | 3 | dashboard | Media | Propuesta | 2026-10-13 | | | — | Depende de FNC-069, FNC-071, FNC-066 |
