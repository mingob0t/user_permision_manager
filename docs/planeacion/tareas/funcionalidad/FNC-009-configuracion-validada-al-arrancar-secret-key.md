# FNC-009 — Configuración validada al arrancar: SECRET_KEY obligatoria, sin debug ni 0.0.0.0, DB_ENGINE explícito

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | config |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-009-configuracion-validada-al-arrancar-secret-key` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | Sí |

## Contexto
`SECRET_KEY` cae a un valor fijo (`app/__init__.py:34`); `run.py:6` arranca con `debug=True` en todas las interfaces; si `DB_ENGINE` no es `mysql` cae en silencio a SQLite; `.env.example` no coincide con lo que lee el código.

Origen (diagnóstico inicial, FNC-001):
- [`docs/seguridad/auditorias/2026-10-13-auditoria-inicial.md`](../../../seguridad/auditorias/2026-10-13-auditoria-inicial.md): SEG-07, SEG-18
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-02, H-16, H-20 a H-22

> **Regla de fases (2026-10-13):** esta corrección se hace en la fase 5 (seguridad final), **salvo** que una tarea anterior modifique este módulo: en ese caso la tarea debe dejarlo cumpliendo `docs/seguridad/LINEAMIENTOS.md` y corrige este hallazgo de paso.

## Objetivo
_Se completa al aprobar la tarea._

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** _se precisa al aprobar._

## Criterios de aceptación
- [ ] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [ ] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [ ] Cumple `docs/estandarizacion/` y no duplica código existente
- [ ] Sin direcciones IP ni secretos

## Recomendaciones agregadas
- 2026-10-27 (auditoría de FNC-030, vía FNC-119): **exigir `BASE_URL`** (validar al arrancar, sin valor por omisión). Hoy el aviso de bienvenida del login de directorio (`auth/services.py`) usa `BASE_URL` o cadena vacía y el SSO (`api/auth.py`) cae al `Host` de la petición; sin `BASE_URL` el enlace del correo es relativo o depende del encabezado. No se implementa en FNC-119.

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-15 | Deuda registrada por FNC-042: `BASE_URL` sin valor deja relativo el enlace del correo de bienvenida (`auth/services.py`); validarla al arrancar en producción |
| 2026-10-27 | Recomendación anotada desde FNC-119: exigir `BASE_URL` |

## Nota (2026-10-13)
- `load_dotenv()` busca `.env` subiendo carpetas: si el proyecto no tiene uno, carga el de la carpeta superior (es de otro proyecto). Cargar solo el `.env` de la raíz del proyecto.
- Al implementar: en `tests/test_arranque.py:86,95,105,115` cambiar `pytest.raises(Exception)` por la excepción o mensaje específico; retirar `CLAVE_POR_DEFECTO` (`:15`) cuando se quite la clave por defecto (revisión de FNC-023).
