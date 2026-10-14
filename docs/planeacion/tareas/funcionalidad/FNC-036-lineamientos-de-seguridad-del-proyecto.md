# FNC-036 — Lineamientos de seguridad del proyecto

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | auditor-seguridad (redacción) + revisión del dueño |
| **Fase** | 1 |
| **Módulo / Área** | seguridad |
| **Prioridad** | Alta |
| **Estatus** | En curso |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-13 |
| **Rama** | `fnc/FNC-036-lineamientos-de-seguridad` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí |

## Contexto
El dueño decidió (2026-10-13) que la primera fase de seguridad no corrige: **define las reglas** que todo el desarrollo debe cumplir. Las correcciones del diagnóstico inicial (FNC-002 a FNC-018) van a la fase 5 (seguridad final), salvo que una tarea toque antes su módulo.

## Objetivo
Escribir `docs/seguridad/LINEAMIENTOS.md`: reglas verificables que cada tarea del proyecto debe cumplir y que `revisor` y `auditor-seguridad` usan como criterio.

## Alcance
- **Incluye** reglas, con su motivo y cómo se verifica, al menos para:
  - autenticación: Authelia, cabeceras `Remote-*` y proxy de confianza, login local y LDAP, sin credenciales por defecto, primer superadmin;
  - autorización: rol y alcance por área en cada endpoint, solo el superadmin crea admins, matriz de permisos con prueba;
  - OpenLDAP: TLS validado, cuenta de servicio con el mínimo privilegio, filtros escapados, escritura solo en los grupos de plataforma;
  - conectores API, SSH y BD: credenciales en Vaultwarden, idempotencia, bitácora, sin ejecutar entrada del usuario;
  - sesión y CSRF, cabeceras HTTP, TLS;
  - secretos y configuración: `SECRET_KEY` obligatoria, nada en claro en la BD, sin IPs;
  - auditoría: qué se registra, inmutabilidad, IP real del cliente;
  - datos personales y retención;
  - dependencias: versiones fijadas y revisión de avisos.
- **No incluye:** corregir código (eso es la fase 5 o la tarea que toque el módulo).

## Criterios de aceptación
- [ ] Cada regla tiene motivo, verificación y referencia al hallazgo que la origina (SEG-xx)
- [ ] El dueño revisó y aprobó el documento
- [ ] `docs/seguridad/README.md` enlaza el documento

## Impacto cruzado
- Genera → criterio de revisión para todas las tareas de las fases 2 a 6
- Origen ← `docs/seguridad/auditorias/2026-10-13-auditoria-inicial.md`

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta por decisión del dueño sobre el orden de fases |
| 2026-10-13 | Aprobada por el dueño; en curso |
