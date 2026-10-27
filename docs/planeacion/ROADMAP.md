# Roadmap

Orden de fases decidido por el dueño el 2026-10-13. Detalle de los hallazgos: [DIAGNOSTICO-INICIAL.md](../DIAGNOSTICO-INICIAL.md).

**Regla:** las correcciones de seguridad esperan a la fase 5, **salvo** que una tarea anterior modifique el módulo afectado; en ese caso la tarea lo deja cumpliendo `docs/seguridad/LINEAMIENTOS.md`. El portal no se expone en un entorno accesible antes de cerrar la fase 5.

## Fase 0 — Incorporación
- [x] Estructura, línea base y diagnóstico inicial (FNC-001)

## Fase 1 — Lineamientos de seguridad
- [x] Reglas de seguridad del proyecto (FNC-036)

## Fase 2 — Pruebas
- [x] Suite base y pruebas de lo crítico y línea base web (FNC-019 a FNC-025, FNC-072)
- [ ] CI (FNC-026): espera el repositorio remoto del dueño

## Fase 3 — Gestor de accesos ✅ (cerrada 2026-10-26, FNC-117; FNC-039 pendiente de prueba en MySQL)
Plan: FNC-037. Requiere: fases 1 y 2, ADR-002 a ADR-006 y preguntas P1 a P14 (ficha FNC-037).

1. [x] FNC-038 Contratos v1 · FNC-039 Migraciones versionadas
2. [x] FNC-047 Auditoría ampliada · FNC-040 Cliente LDAP · FNC-048 Notificaciones
3. [x] FNC-041 Escritura LDAP · FNC-042 Login por directorio · FNC-043 Config. directorio · FNC-044 Roles · FNC-046 Plataformas
4. [x] FNC-045 Áreas · FNC-049 Ejecutor de aprovisionamiento
5. [x] FNC-054 Accesos otorgados · FNC-050 Conectores (base) · FNC-067 Worker en despliegue · FNC-068 Vaultwarden
6. [x] FNC-055 Acceso automático · FNC-056 Solicitudes · FNC-058 Revocación · FNC-059 Inventario · FNC-060 Consulta de auditoría · FNC-061 API conectores · FNC-062 API ejecuciones · FNC-063 Visibilidad · FNC-064 Alta en LDAP
7. [x] FNC-057 Aprobaciones · FNC-066 Resumen de inicio · FNC-065 Retirar `user_platforms` (si P4) · FNC-051/052/053 Conectores API/SSH/BD (según P9)
8. [x] Web, desde el paso 2 con datos simulados: FNC-069 Cliente · FNC-071 Refresco · FNC-070 Navegación
9. [x] Pantallas, tras su backend: DIS-013 Catálogo · DIS-014 Mis solicitudes · DIS-015 Aprobaciones · DIS-016 Áreas · DIS-017 Plataformas · DIS-018 Accesos de usuario → DIS-019 Alta y elevación · DIS-020 Auditoría · DIS-021 Inventario · DIS-022 Conectores · DIS-023 Directorio · DIS-024 Inicio

## Fase 4 — Estándares, modularidad y accesibilidad ✅ (cerrada 2026-10-27; DIS-053 queda en Propuesta, pendiente de decisión del dueño)
- [x] FNC-027 a FNC-034, DIS-001 a DIS-012
- [x] Propuestas de auditorías de fase 3: DIS-030, DIS-031, DIS-032, DIS-033, DIS-035, DIS-036, DIS-037, DIS-038, DIS-039, DIS-040, DIS-041, DIS-042

## Fase 5 — Seguridad final

> ⏸ **En pausa** (decisión del dueño, 2026-10-27): primero el sistema funcional. Tras la fase 4 sigue la fase 6; la fase 5 se retoma cuando el dueño lo indique. Sigue vigente que el portal no se expone antes de cerrarla.
- [ ] Auditoría de seguridad completa del proyecto terminado
- [ ] Correcciones pendientes del diagnóstico inicial (FNC-002 a FNC-018) y de la auditoría final
- [ ] FNC-130 (endurecimientos del instalador: build sin root, hardlinks, logdir)
- [ ] FNC-126 (`.env` fuera de rutas escribibles por la cuenta de servicio)
- [ ] FNC-120 (lista blanca estricta de campos; movida desde la fase 4 el 2026-10-27)
- [ ] Propuestas de auditorías de fase 3: FNC-075, FNC-078, FNC-079, FNC-083, FNC-084, FNC-085, FNC-086, FNC-087, FNC-088, FNC-089, FNC-096, FNC-106, FNC-100, FNC-107, FNC-110, FNC-115, FNC-116

## Fase 6 — Documentación y operación ✅ (cerrada 2026-10-27; validación en servidor pendiente del dueño)
- [x] FNC-035
- [x] FNC-073
- [x] FNC-124
- [x] FNC-125 (despliegue en RHEL 9: servicio de BD real en las unidades; `.env` del prefijo intacto)
- [x] FNC-127 (puertos de backend y frontend configurables en el instalador)
- [x] FNC-129 (instalador en sitio, nombre desde la carpeta y `--force`)
- [ ] FNC-131 (comando de datos demo para validar en local; En revisión)
