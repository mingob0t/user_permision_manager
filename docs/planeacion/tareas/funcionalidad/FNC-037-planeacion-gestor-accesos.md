# FNC-037 — Planeación de la fase 3: gestor de accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | planificador |
| **Fase** | 3 |
| **Módulo / Área** | planeacion |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama de planeación creada desde `develop` (worktree `pokemon-wt-plan`) |
| **Rama** | `fnc/FNC-037-planeacion-gestor-accesos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- La fase 3 del ROADMAP ("Gestor de accesos") estaba pendiente de planificar
- Los requerimientos F-AREA, F-PLAT, F-USR, F-SOL, F-ACC, F-CON, F-AUD y F-NOT de `docs/REQUERIMIENTOS.md` están en estado Parcial o Falta, y el dueño ya tomó las decisiones base (OpenLDAP como fuente de verdad, dos grupos por plataforma, conectores en segundo plano con credenciales en Vaultwarden, solo el superadmin eleva admins, auditoría basada en lo registrado en el portal, MySQL, frontend Next.js existente)
- Requerimientos: todas las F-* de las secciones 3 y 4, RF-01 a RF-06 y la tabla de pantallas por rol

## Objetivo
- Partir la fase 3 en tareas de una sola plataforma y un solo módulo, con dependencias, contratos, elementos compartidos afectados, hallazgos de seguridad que absorbe cada una y un orden de ejecución, más los ADR propuestos y las preguntas que el dueño debe resolver antes de aprobar

## Alcance
- **Incluye:**
  - Fichas FNC-038 a FNC-071 y DIS-013 a DIS-024 en estado Propuesta, con su fila en el tablero
  - Sección "Fase 3" detallada en `docs/planeacion/ROADMAP.md`
  - ADR-002 a ADR-006 en estado Propuesta (migraciones, cola y worker, grupos y esquema de OpenLDAP, credenciales de conectores, refresco de la interfaz)
  - Entrada en `docs/logs/2026-10-13.md`
- **No incluye:**
  - Código de la aplicación
  - Aprobar tareas (solo el dueño las pasa a Pendiente)
  - Redactar los contratos (es la tarea FNC-038)
  - Lo que la sección "Fuera de la v1" de REQUERIMIENTOS excluye

## Archivos previstos
- `docs/planeacion/tareas/funcionalidad/FNC-037..FNC-071-*.md`
- `docs/planeacion/tareas/diseno/DIS-013..DIS-024-*.md`
- `docs/planeacion/TABLERO.md`
- `docs/planeacion/ROADMAP.md`
- `docs/decisiones/ADR-002..ADR-006-*.md` y `docs/decisiones/README.md`
- `docs/logs/2026-10-13.md`

## Reutilización
- Plantilla `docs/planeacion/plantillas/TAREA.md`
- Referencia de solo lectura del flujo retirado: `nexus_master/app/modules/requests/routes.py` (estados Pendiente/Aprobado/Rechazado, rechazo de duplicados pendientes). No se copia código.

## Criterios de aceptación
- [ ] Cada tarea es de una plataforma y un módulo, con agente asignado y dependencias explícitas
- [ ] Cada ficha indica los hallazgos FNC-002 a FNC-018 que absorbe o que deja para la fase 5
- [ ] Preguntas al dueño listadas en esta ficha (P1 a P14)
- [ ] **Criterios comunes backend:** pytest por endpoint (401/403/2xx y respuesta) y por regla (permitido/denegado); rutas delgadas y lógica en servicios del módulo; errores genéricos; cumple `docs/seguridad/LINEAMIENTOS.md` y `docs/estandarizacion/`; sin IPs ni secretos; variables en `VARIABLES.md` + `HISTORIAL.md`; tabla de `impacto.py` en la ficha
- [ ] **Criterios comunes web:** pruebas Vitest de lo que cambia; `typecheck` y `lint` en verde; sin `any`; sin IPs ni secretos; tabla de `impacto.py`
- [ ] **Criterios comunes de diseño:** solo tokens, sin estilos inline ni colores literales; claro/oscuro, 360 px y 1280 px verificados; estados de carga, vacío, error y sin permiso; AA medido por `auditor-accesibilidad`; objetivos táctiles de 44 px y foco visible; reutiliza `ui.tsx`/`form.tsx`; lo nuevo en archivos propios (no crece monolitos); tabla de `impacto.py`
- [ ] **Criterios comunes infra:** evidencia en máquina de prueba; `docs/operacion/` actualizado; variables registradas

## Impacto cruzado
- Genera → FNC-038 a FNC-071, DIS-013 a DIS-024
- Genera → ADR-002 a ADR-006 (Propuestos)
- Origen ← ROADMAP, fase 3 (decisión del dueño del 2026-10-13)
- Depende de → FNC-001 (incorporación)

## Riesgos y reversión
- Solo documentación: se revierte descartando la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada y ejecutada por el planificador; queda en Propuesta hasta que el dueño la apruebe junto con el plan |
## Preguntas para el dueño
- P1. Catálogo solicitable: ¿todas las plataformas activas de todas las áreas, o solo las de áreas a las que pertenece el usuario? (FNC-056)
- P2. ¿El admin de área puede crear cuentas en OpenLDAP o solo el superadmin? (FNC-064)
- P3. OpenLDAP: convención de nombres de grupos y OUs; clase de grupo (`groupOfNames`/`member` o `posixGroup`/`memberUid`); ¿overlay `memberOf`?; ¿quién crea los grupos de cada plataforma?; ACL de la cuenta de servicio; ¿quién mantiene las reglas de Authelia por grupo? (ADR-004)
- P4. Tras la fase, ¿"mis plataformas" = accesos activos? ¿Qué se hace con `user_areas` y `user_platforms` existentes: migrar como `heredado` (¿con qué nivel?) o descartar? (FNC-063, FNC-065)
- P5. Niveles `usuario` y `admin`: ¿excluyentes o acumulables? (FNC-054)
- P6. Acceso automático del admin: ¿nivel `admin`?, ¿se revoca al quitarle el área?, ¿aplica al superadmin? (FNC-055)
- P7. ¿La revocación exige motivo? (FNC-058)
- P8. Contraseña inicial de cuentas creadas en LDAP: ¿sin contraseña y restablecimiento por Authelia? (FNC-064)
- P9. Primeras plataformas con conector, su tipo (API/SSH/BD) y motores de BD. (FNC-051 a FNC-053)
- P10. Fallo de aprovisionamiento: ¿avisar a admins del área y al superadmin?, ¿se respeta `pref_email_notifications`?, ¿reintento manual y quién lo hace? (FNC-048, FNC-062)
- P11. Baja de áreas: ¿solo el superadmin? (FNC-045)
- P12. ¿Se prohíbe decidir la propia solicitud? (FNC-057)
- P13. Regla de absorber hallazgos: ¿por función/archivo tocado (supuesto del plan) o por módulo completo? ¿Se adelanta FNC-008 (CSRF) a antes de la fase 3?
- P14. Decidir ADR-002 (migraciones), ADR-003 (cola y worker), ADR-004 (OpenLDAP), ADR-005 (Vaultwarden en ejecución) y ADR-006 (refresco de la interfaz).

## Respuestas del dueño (2026-10-13)
- P1: el catálogo muestra solo las plataformas de las áreas del usuario.
- P5: un solo nivel por plataforma (usuario **o** admin); subir a admin reemplaza al de usuario.
- P2: el superadmin y los admins pueden crear cuentas en OpenLDAP (el admin, para sus áreas).
- P9: aún no hay plataformas con conector definidas; se hace la base (FNC-049, FNC-050) y los tipos FNC-051 a FNC-053 esperan.
- P3: la convención de OpenLDAP (servidor, base DN, OU y formato de nombres de grupos) va en variables del `.env`; el dueño agrega después los valores y todo dato sensible (servidores, contraseñas). Las tareas solo crean las variables y las registran en `docs/configuracion/VARIABLES.md`.
- P4: los accesos actuales de NEXUS (`user_platforms`) se descartan; no se migran.
- P14/ADR-003: cola de conectores con Redis + RQ.
- P6/P12: el superadmin tiene acceso por defecto. Cuando un admin da de alta una plataforma, el sistema le otorga acceso automáticamente y la auditoría registra dos eventos: "admin X dio de alta la plataforma Y" y "sistema dio permisos de acceso a admin X".

## Respuestas del dueño (2026-10-14)
- P7: revocar no requiere motivo.
- P8: el portal no maneja contraseñas de cuentas LDAP; la contraseña la maneja Authelia.
- P10: avisar a los admins del área y al superadmin; reintento manual solo el superadmin.
- P11: el admin de un área también puede darla de baja (además del superadmin); 409 si tiene plataformas o accesos vigentes.
- P10 (2026-10-15): el aviso de fallo de aprovisionamiento respeta `pref_email_notifications`, como los demás avisos (FNC-048).
- P6 (2026-10-14): acceso automático nivel `usuario`, para todos los admins del área; se revoca al quitarle el área; el superadmin no entra a los grupos LDAP.
| 2026-10-15 | Respuesta del dueño sobre P10 (resto): el aviso de fallo respeta `pref_email_notifications`; aplicada en FNC-048 y en `conectores-y-ejecuciones.md` |

## Respuestas del dueño (2026-10-15)
- P3 (último miembro de `groupOfNames`): miembro de relleno configurable (`LDAP_GROUP_PLACEHOLDER_MEMBER`, FNC-041).
- P3 (cuenta de servicio): una sola cuenta LDAP para lectura y escritura (`LDAP_BIND_DN`); ACL acotada en `docs/operacion/ENTORNOS.md`.
- Contraseñas (revisión de FNC-044): el admin de área sí cambia la contraseña de cuentas `local` con rol `usuario` de sus áreas, además del superadmin; nunca de cuentas `ldap`/`sso`.
- Login local: se deshabilitará; todo irá por Authelia, salvo el acceso de emergencia del superadmin (FNC-077).
