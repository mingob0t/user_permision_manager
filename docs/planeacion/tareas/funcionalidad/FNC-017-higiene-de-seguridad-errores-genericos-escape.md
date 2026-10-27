# FNC-017 — Higiene de seguridad: errores genéricos, escape en correos, validación de URLs, IP y hosts fuera del código, límites de carga

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | global |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-017-higiene-de-seguridad-errores-genericos-escape` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | Sí |

## Contexto
`str(exc)` en respuestas; plantillas sin escape HTML; `direct_link` sin validar esquema; IP literal en `auth/services.py:152`; host real en `.env.example`.

Origen (diagnóstico inicial, FNC-001):
- [`docs/seguridad/auditorias/2026-10-13-auditoria-inicial.md`](../../../seguridad/auditorias/2026-10-13-auditoria-inicial.md): SEG-21, 23, 24, 26, 29
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-19

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

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-15 | SEG-23 (escape en correos) cerrado por FNC-048: `html.escape` en HTML, asunto sin CR/LF, sustitución de una pasada; regresiones en `tests/test_notificaciones.py` (sin `xfail`). Quedan SEG-21, 24, 26, 29 |
| 2026-10-18 | SEG-21 de LDAP (`str(exc)` en prueba y búsqueda, antes `admin.py:404` y `:637`) cerrado por FNC-043 (En revisión): `503 directorio_no_disponible` genérico, detalle al log. Quedan SEG-21 del resto, 24, 26, 29 |
| 2026-10-19 | SEG-24 del backend (`direct_link`/`logo_url` sin validar, antes `crud.py:139-142`, `:158-168`) cerrado por FNC-046 (En revisión): solo `https://`, `422 validacion`; regresión `tests/platforms/test_regresion_seg24.py` (falló antes). Queda SEG-24 del frontend (`platform-card.tsx`), 21 del resto, 26, 29 |
| 2026-10-19 | SEG-24 del frontend cerrado por DIS-017 (En revisión): `platform-card.tsx` y la tabla de `platform-admin.tsx` solo pintan enlaces `https://` (`lib/enlace-seguro.ts`); regresión `tests/components/platform-card.test.tsx` (falló antes). Quedan SEG-21 del resto, 26, 29 |
| 2026-10-19 | DIS-017 (auditor-seguridad, Baja): `enlaceSeguro` ya devuelve el `href` normalizado. Propuesta: rechazar en el cliente IP literales y dominios IDN/punycode como hace `validar_url` del backend (hoy solo los filtra el backend) |
| 2026-10-27 | Hallazgo (DIS-012): `Platform.bg_color` y `text_color` solo se validan por largo (`validacion.py:26`) y admiten `url(...)` u otro valor que no es un color; el frontend los pasa como variable CSS (`.nx-chip-solid`). Propuesta: validarlos como color (hex o `rgb()`) en el backend. Relacionada con FNC-033 y DIS-048 |
