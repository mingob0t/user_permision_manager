# Diagnóstico inicial — pokemon (2026-10-13)

Incorporación al método (FNC-001) de `pokemon`, clon de NEXUS (`MI_NUEVO_PROYECTO`, commit `0bf71e8`). Es un análisis **estático**: no se levantó la app, no se instalaron dependencias y nada se reprodujo en ejecución.

Informes de origen (fotos, no se editan):
- Seguridad: [seguridad/auditorias/2026-10-13-auditoria-inicial.md](seguridad/auditorias/2026-10-13-auditoria-inicial.md)
- Estándares: [estandarizacion/auditorias/2026-10-13-auditoria-inicial.md](estandarizacion/auditorias/2026-10-13-auditoria-inicial.md)
- Accesibilidad: [estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md](estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md)
- Pruebas: [planeacion/diagnostico-pruebas-2026-10-13.md](planeacion/diagnostico-pruebas-2026-10-13.md)
- Línea base: [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md), [configuracion/VARIABLES.md](configuracion/VARIABLES.md), [operacion/ENTORNOS.md](operacion/ENTORNOS.md)

## Resumen ejecutivo

| Área | Estado | Motivo |
|---|---|---|
| Seguridad | 🔴 | 4 críticas (borrado de cuentas sin sesión, `nexus123`, `admin/admin123`, suplantación por SSO), 4 altas, 12 medias, 9 bajas |
| Pruebas | 🔴 | 0 pruebas automatizadas sobre 90 rutas; ni typecheck ni lint verificables (sin dependencias instaladas) |
| Accesibilidad | 🔴 | El tema oscuro y los temas no se activan; contrastes de 1.4 a 3.8 en modales, insignias, botones y textos de estado |
| Estándares | 🟠 | 44 rutas heredadas muertas, 154/170 clases CSS sin uso, 260 colores literales, 1 IP en código |
| Modularidad | 🟠 | Monolitos: `admin.py` (645), `crud.py` (480), `settings-panel.tsx` (745), `users-list.tsx` (581) |
| Variables | 🟡 | Registro reescrito desde el código (39 variables); `.env.example` desalineado |
| Operación | 🟡 | Despliegue Rocky 8 + systemd + nginx documentado; sin TLS, sin CI, staging y producción sin definir |
| Documentación | 🟢 | Línea base escrita en FNC-001; `ARCHITECTURE.md` y `business_rules.md` marcados como obsoletos |

## Hallazgos consolidados

Los hallazgos que reportó más de un agente aparecen una sola vez con todas sus fuentes.

| # | Hallazgo | Severidad | Fuentes | Tarea |
|---|---|---|---|---|
| 1 | Un anónimo puede borrar cuentas locales vía login de directorio | Crítica | SEG-01 | FNC-002 |
| 2 | Contraseña fija `nexus123` para usuarios importados; login local sin comprobar `auth_source` | Crítica | SEG-02 | FNC-003 |
| 3 | Superadmin automático `admin/admin123` | Crítica | SEG-03, EST H-07, línea base | FNC-003 |
| 4 | Suplantación por SSO (nginx no limpia `Remote-*` en `location /`; rewrites de Next.js activos en producción) | Crítica | SEG-04, SEG-15 | FNC-004, FNC-005, FNC-006 |
| 5 | Admin de área toma cuentas de otros admins y eleva a `admin_area` | Alta | SEG-05, SEG-09 | FNC-007 |
| 6 | CSRF exento en toda la API; sesión larga sin `Secure` | Alta | SEG-06, SEG-14 | FNC-008 |
| 7 | `SECRET_KEY` por defecto, `debug=True` en todas las interfaces, caída silenciosa a SQLite | Alta | SEG-07, SEG-18, EST H-02, línea base | FNC-009 |
| 8 | Secretos de SMTP y LDAP en claro en la BD; respaldo con hashes | Alta | SEG-08, SEG-17 | FNC-010 |
| 9 | Posibles secretos en el historial de git | Alta (por confirmar) | SEG-20 | FNC-011 |
| 10 | LDAP sin validar TLS, tres conexiones duplicadas, atributos de Active Directory con OpenLDAP | Alta | SEG-13, EST, línea base | FNC-012 |
| 11 | Sin pruebas automatizadas | Alta | Pruebas, EST | FNC-019 a FNC-026 |
| 12 | Tema oscuro y temas inalcanzables | Alta | ACC estructural, EST H-11 | FNC-032 |
| 13 | Contrastes por debajo de AA en modales, insignias, gráfica, botones y estados | Alta | ACC H-01 a H-09 | DIS-001 a DIS-005 |
| 14 | Código heredado muerto (blueprints, CSS, scratch, utils PSX5K) | Media | EST H-01, H-03, H-07, H-08 | FNC-027, FNC-028, DIS-009 |
| 15 | Monolitos backend y frontend | Media | EST H-05, H-06 | FNC-029, DIS-011 |
| 16 | `user_platforms` no limita lo que ve el usuario | Media | Línea base | Se resuelve en el gestor de accesos (F-ACC) |
| 17 | Notificaciones globales marcadas como leídas para todos | Media | Línea base | FNC-031 |

La lista completa, con archivo y línea, está en cada informe y en las fichas de `planeacion/tareas/`.

## Fases (decididas por el dueño el 2026-10-13)

0. **Incorporación** (FNC-001).
1. **Lineamientos de seguridad** (FNC-036): reglas que todo el desarrollo debe cumplir.
2. **Pruebas** (FNC-019 a FNC-026).
3. **Gestor de accesos**: requerimientos F-* de [REQUERIMIENTOS.md](REQUERIMIENTOS.md), pendiente de planificar.
4. **Estándares, modularidad y accesibilidad** (FNC-027 a FNC-034, DIS-001 a DIS-012).
5. **Seguridad final**: auditoría completa y correcciones (FNC-002 a FNC-018 y lo que encuentre la auditoría final).
6. **Documentación y operación** (FNC-035).

Regla: una tarea que modifique un módulo con un hallazgo de seguridad abierto lo deja cumpliendo los lineamientos y corrige el hallazgo de paso. El portal no se expone en un entorno accesible antes de cerrar la fase 5.

## Decisiones que le tocan al dueño

- **Prioridad:** confirmar el orden de fases, o si el gestor de accesos arranca en paralelo con la fase 1.
- **Secretos en el historial (FNC-011):** confirmar si son reales y rotarlos.
- **Repositorio remoto propio** para `pokemon`: no se hace push hasta tenerlo.
- **Temas (FNC-032):** implementar el selector de tema o retirar los cuatro temas con nombre.
- **Valores de `.env.example`:** confirmar si `auth.vivaro.com`, `AUTHELIA_GROUP_ADMIN` y `DB_NAME=admin_test` son solo de ejemplo.

## No verificado

- Ejecución de la app, pruebas dinámicas, `npm audit` y `pip-audit`.
- Typecheck y lint del frontend: faltan dependencias.
- Configuración real de Authelia, OpenLDAP, MySQL y Redis en los servidores.
