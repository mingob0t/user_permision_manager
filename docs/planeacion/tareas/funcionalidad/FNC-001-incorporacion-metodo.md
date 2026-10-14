# FNC-001 — Incorporar el proyecto al método

- **Plataforma:** infra · **Módulo:** global · **Estatus:** Hecha (merge local a `develop`, 634e9f1; sin push)
- **Rama:** `fnc/FNC-001-incorporacion-metodo` (desde `develop`)
- **Creada / inicio:** 2026-10-13

## Contexto
`pokemon` es un `git clone` local de `MI_NUEVO_PROYECTO` (NEXUS: Flask API `/api/v1` + Next.js 15 + SQLAlchemy) tomado el 2026-10-13 en el commit `0bf71e8`. Se convertirá en el gestor de accesos por áreas descrito en [REQUERIMIENTOS.md](../../../REQUERIMIENTOS.md).

## Alcance
- Estructura `docs/` del método (plantillas de `nuevo_proyecto.py`), controles `.claude/`, pre-commit y `.gitignore` base.
- Ramas `develop` y `staging` creadas desde `main`.
- Documentación de lo existente (línea base) y diagnóstico inicial (seguridad, estándares, accesibilidad, pruebas).
- **No se modifica código de la aplicación.**

## Impacto en elementos compartidos
- `.gitignore`: se agregaron las reglas de la plantilla base; ningún archivo versionado quedó ignorado (`git ls-files -ci --exclude-standard` vacío).

- `impacto.py` (contra `develop`): ninguno detectado; 85 archivos cambiados, todos de documentación, controles y `.gitignore`.

## Resultado
- Línea base: `docs/backend/README.md`, `docs/frontend/README.md`, ADR-001 aceptada, `docs/configuracion/VARIABLES.md` reescrito desde el código, `docs/operacion/ENTORNOS.md`.
- Diagnóstico consolidado: [DIAGNOSTICO-INICIAL.md](../../../DIAGNOSTICO-INICIAL.md); 46 tareas en `Propuesta` (FNC-002 a FNC-035, DIS-001 a DIS-012).
- IPs privadas citadas en el informe de estándares reemplazadas por una descripción.

## Verificación
- `validar_proyecto.py`: 0 errores, 8 avisos, todos deuda heredada con tarea asignada (FNC-009, FNC-017, DIS-009, DIS-012).
- No se ejecutó la app, ni pruebas, ni typecheck: no hay dependencias instaladas (ver diagnóstico de pruebas).
- Sin push: el dueño indicará el repositorio remoto propio.
